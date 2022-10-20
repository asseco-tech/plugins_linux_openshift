#!/usr/bin/python2
# -*- coding: ISO-8859-2 -*-
#
# Author: Asseco Poland S.A., Rzeszow, Poland
# Contact: bks_puse@asseco.pl
# License: Apache License, Version 2.0
#


# Modules
#===================================
try:
	import requests, json, urllib3
	import argparse, sys, os
except ImportError as e:
        print str(e)
        exit(3)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# Primary variables
#===================================
v_basename = os.path.basename(__file__)
v_version = "1.0"


# Variables
#===================================
nagios_codes = [ 'OK', 'WARNING', 'CRITICAL', 'UNKNOWN' ]


# Class
#===================================
# tutaj opi klasy
#-----------------------------------
class Status:
	OK = 0
	WARNING = 1
	CRITICAL = 2
	UNKNOWN = 3


# Primary functions
#===================================
# Parsing arguments
#-----------------------------------
def f_get_params(v_basename, v_version):
	parser = argparse.ArgumentParser(prog=v_basename, usage='\n\t %(prog)s --host <ocp_cluster>  --port <port> --token <file_with_token> --node <node>', description='Nagios plugin to check OpenShift node availability')
	parser.add_argument('--host', action='store', help='name or ip address of OCP cluster', required=True)
	parser.add_argument('--port', action='store', help='port of OCP cluster', required=True)
	parser.add_argument('--token', action='store', help='file with user''s token to connect to OCP cluster', required=True)
	parser.add_argument('--node', action='store', help='name of OCP node', required=True)
	parser.add_argument('--version', action='version', version='%(prog)s ' + v_version)
	args = parser.parse_args()
	return args.host, args.port, args.token, args.node


# Functions
#===================================
# Program output in Nagios/Icinga format
#-----------------------------------
def exitus(status=Status.OK, message="all is well", perfdata=""):
	print "[" + nagios_codes[status] + "] - " + message + "|" + perfdata
	sys.exit(status)

# Returns the name of the status
#-----------------------------------
def get_status_name(status):
	if status == 0:
		return "OK"
	if status == 1:
		return "WARNING"
	if status == 2:
		return "CRITICAL"

# Query to API OCP
#-----------------------------------
def QueryOcp(ocpHost, ocpPort, ocpToken, qUrl):
	ocpUri = qUrl
	ocpAuthorization = ('Bearer {}').format(ocpToken)

	url = ('https://{}:{}/{}').format(ocpHost, ocpPort, ocpUri)
	headers = {'Authorization': ocpAuthorization}
	
	try:
		response = requests.get(url, headers=headers, verify=False)
	except:
		print 'Connection error to OCP'
		exit(Status.CRITICAL)
	
	if response.status_code == 200:
		dataJson = response.json()
	else:
		print "Connection error to OCP status_code=" + str(response.status_code)
		exit(Status.CRITICAL)
	return dataJson

# Query to Prometheus
#-----------------------------------
def QueryPrometheus(ocpHost, ocpPort, ocpToken, qUrl):
	ocpUri = qUrl
	ocpAuthorization = ('Bearer {}').format(ocpToken)

	url = ('https://{}:{}/{}').format(ocpHost, ocpPort, ocpUri)
	headers = {'Authorization': ocpAuthorization}
	
	try:
		response = requests.get(url, headers=headers, verify=False)
	except:
		print 'Connection error to Prometheus'
		exit(Status.CRITICAL)	    
	
	if response.status_code == 200:
		dataJson = response.json()
	else:
		print "Connection error to Prometheus status_code=" + str(response.status_code)
		exit(Status.CRITICAL)	    
	return dataJson

# Query to OCP (selected information about the node)
#-----------------------------------
def get_node_info_from_ocp(host, port, token, url):
	dataJson = QueryOcp(host, port, token, url)

	v_MemoryPressure_status = 0
	v_MemoryPressure_reason = ''
	v_DiskPressure_status = 0
	v_DiskPressure_reason = ''
	v_PIDPressure_status = 0
	v_PIDPressure_reason = ''
	v_KubeletReady_status = 0
	v_KubeletReady_reason = ''
	
	# node health
	for a in dataJson['status']['conditions']:
		if a['type'] == 'MemoryPressure' and a['status'] == "True":
			v_MemoryPressure_status = 2
			v_MemoryPressure_reason = a['reason']
		
		if a['type'] == 'DiskPressure' and a['status'] == "True":
			v_DiskPressure_status = 2
			v_DiskPressure_reason = a['reason']
	
		if a['type'] == 'PIDPressure' and a['status'] == "True":
			v_PIDPressure_status = 2
			v_PIDPressure_reason = a['reason']
	
		if a['type'] == 'KubeletReady' and a['type'] == "False":
			v_KubeletReady_status = 2
			v_KubeletReady_reason = a['reason']
	
	return v_MemoryPressure_status, v_MemoryPressure_reason, v_DiskPressure_status, v_DiskPressure_reason, v_PIDPressure_status, v_PIDPressure_reason, v_KubeletReady_status, v_KubeletReady_reason

# Determination of status, output and performance
#-----------------------------------
def calculate_status(v_node_name, v_MemoryPressure_status, v_MemoryPressure_reason, v_DiskPressure_status, v_DiskPressure_reason, v_PIDPressure_status, v_PIDPressure_reason, v_KubeletReady_status, v_KubeletReady_reason):
	# final status
	status = 0
	v_status_ok = 0
	v_status_warn = 0
	v_status_crit = 0

	if v_MemoryPressure_status == 2 or v_DiskPressure_status == 2 or v_PIDPressure_status == 2 or v_KubeletReady_status == 2:
		status = 2
	
	# output
	if v_MemoryPressure_status == 2:
		output = ('{} - Node Status: \n> [{}] MemoryPressure ({})').format(v_node_name, get_status_name(v_MemoryPressure_status), v_MemoryPressure_reason)
		v_status_crit = v_status_crit + 1
	elif v_MemoryPressure_status == 1:
		output = ('{} - Node Status: \n> [{}] MemoryPressure').format(v_node_name, get_status_name(v_MemoryPressure_status))
		v_status_warn = v_status_warn + 1	
	else:
		output = ('{} - Node Status: \n> [{}] MemoryPressure').format(v_node_name, get_status_name(v_MemoryPressure_status))
		v_status_ok = v_status_ok + 1
	
	if v_DiskPressure_status == 2:
		output = ('{} \n> [{}] DiskPressure ({})').format(output, get_status_name(v_DiskPressure_status), v_DiskPressure_reason)
		v_status_crit = v_status_crit + 1
	elif v_DiskPressure_status == 1:
		output = ('{} \n> [{}] DiskPressure').format(output, get_status_name(v_DiskPressure_status))
		v_status_warn = v_status_warn + 1	
	else:
		output = ('{} \n> [{}] DiskPressure').format(output, get_status_name(v_DiskPressure_status))
		v_status_ok = v_status_ok + 1
	
	if v_PIDPressure_status == 2:
		output = ('{} \n> [{}] PIDPressure ({})').format(output, get_status_name(v_PIDPressure_status), v_PIDPressure_reason)
		v_status_crit = v_status_crit + 1
	elif v_PIDPressure_status == 1:
		output = ('{} \n> [{}] PIDPressure').format(output, get_status_name(v_PIDPressure_status))
		v_status_warn = v_status_warn + 1	
	else:
		output = ('{} \n> [{}] PIDPressure').format(output, get_status_name(v_PIDPressure_status))
		v_status_ok = v_status_ok + 1
	
	if v_KubeletReady_status == 2:
		output = ('{} \n> [{}] KubeletReady ({})').format(output, get_status_name(v_KubeletReady_status), v_KubeletReady_reason)
		v_status_crit = v_status_crit + 1
	elif v_KubeletReady_status == 1:
		output = ('{} \n> [{}] KubeletReady').format(output, get_status_name(v_KubeletReady_status))
		v_status_warn = v_status_warn + 1	
	else:
		output = ('{} \n> [{}] KubeletReady').format(output, get_status_name(v_KubeletReady_status))
		v_status_ok = v_status_ok + 1
	
	output = output.replace('Node Status:', 'Node Status: (' + str(v_status_ok) + ' OK, ' + str(v_status_warn) + ' WARNING, ' + str(v_status_crit) + ' CRITICAL)')
	
	# performance data
	output_perfData = 'MemoryPressure_status=' + str(v_MemoryPressure_status) + ';0;2;0 DiskPressure_status=' + str(v_DiskPressure_status) + ';0;2;0 PIDPressure_status=' + str(v_PIDPressure_status) + ';0;2;0 KubeletReady_status=' + str(v_KubeletReady_status) + ';0;2;0'
	return status, output, output_perfData


# Main
#===================================
if __name__ == '__main__':
	# Parsing arguments
	v_token = ""
	v_host, v_port, v_token, v_node = f_get_params(v_basename, v_version)

	# is there a token file
	if not os.path.isfile(v_token):
		print 'No access to the token file'
		exit(Status.CRITICAL)	    
	else:
		# token reading
		f = open(v_token, 'r')
		v_token = f.readline().rstrip('\n')
		f.close()
	
	# Query to API Prometheus (node availability)
	v_query = ('api/v1/nodes/{}').format(v_node)
	MemoryPressure_status, MemoryPressure_reason, DiskPressure_status, DiskPressure_reason, PIDPressure_status, PIDPressure_reason, KubeletReady_status, KubeletReady_reason = get_node_info_from_ocp(v_host, v_port, v_token, v_query)
	
	# processing responses from Prometheus
	status, message, output_perfData = calculate_status(v_node, MemoryPressure_status, MemoryPressure_reason, DiskPressure_status, DiskPressure_reason, PIDPressure_status, PIDPressure_reason, KubeletReady_status, KubeletReady_reason)
	
	# output in Nagios/Icinga format
	exitus(status, message, output_perfData)

