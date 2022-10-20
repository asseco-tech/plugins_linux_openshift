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
	import datetime
	from dateutil.relativedelta import relativedelta
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
	parser = argparse.ArgumentParser(prog=v_basename, usage='\n\t %(prog)s --ohost <ocp_cluster> --oport <ocp_port> --phost <host_prometheus> --pport <port_prometheus> --token <file_with_token> --node <node>', description='Nagios plugin to check OpenShift pod availability and performance')
	parser.add_argument('--ohost', action='store', help='name or ip address of OCP cluster', required=True)
	parser.add_argument('--oport', action='store', help='port of OCP cluster', required=True)
	parser.add_argument('--phost', action='store', help='name or ip address of Prometheus on OCP', required=True)
	parser.add_argument('--pport', action='store', help='port of Prometheus', required=True)
	parser.add_argument('--token', action='store', help='file with user''s token to connect to OCP cluster', required=True)
	parser.add_argument('--namespace', action='store', help='name of OCP namespace', required=True)
	parser.add_argument('--pod', action='store', help='name of OCP pod which is created in namespace', required=True)
	parser.add_argument('--memwarn', action='store', help='memory threshold - warning', required=True)
	parser.add_argument('--memcrit', action='store', help='memory threshold - critical', required=True)
	parser.add_argument('--restartwarn', action='store', help='pod restart threshold - warning', required=True)
	parser.add_argument('--restartcrit', action='store', help='pod restart threshold - critical', required=True)
	parser.add_argument('--version', action='version', version='%(prog)s ' + v_version)
	args = parser.parse_args()
	return args.ohost, args.oport, args.phost, args.pport, args.token, args.namespace, args.pod, args.memwarn, args.memcrit, args.restartwarn, args.restartcrit


# Functions
#===================================
# Program output in Nagios/Icinga format
#-----------------------------------
def exitus(status=Status.OK, message="all is well", perfdata=""):
	print "[%s] - %s|%s" % (nagios_codes[status], message, perfdata)
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
		# print 'onnection error to OCP
		output_perfData = 'pod_status=2;0;2;0'
		status=Status.CRITICAL
		print "[%s] - %s|%s" % (nagios_codes[status], "'Connection error to OCP",output_perfData)
		exit(Status.CRITICAL)
	
	if response.status_code == 200:
		dataJson = response.json()
	else:
		output_perfData = 'pod_status=2;0;2;0'
		status=Status.CRITICAL	
		print "[%s] - %s|%s" % (nagios_codes[status], "'Connection error to OCP status_code=" + str(response.status_code),output_perfData)
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
		output_perfData = 'pod_status=2;0;2;0'
		status=Status.CRITICAL
		print "[%s] - %s|%s" % (nagios_codes[status], "'Connection error to Prometheus",output_perfData)
		exit(Status.CRITICAL)	    
	
	if response.status_code == 200:
		dataJson = response.json()
	else:
		output_perfData = 'pod_status=2;0;2;0'
		status=Status.CRITICAL
		print "[%s] - %s|%s" % (nagios_codes[status], "'Connection error to Prometheus status_code=" + str(response.status_code),output_perfData)
		exit(Status.CRITICAL)	    
	
	return dataJson

# Query to Prometheus (CPU, Mem. etc)
#-----------------------------------
def get_metric_from_prometheus(host, port, token, url, typ):
	dataJson = QueryPrometheus(host, port, token, url)

	if dataJson['status'] == 'success':
		 wynik = 0
	
		 for a in dataJson['data']['result']:
			 if typ == 'int':
				 wynik = wynik + int(a['value'][1])
			 else:
				 wynik = wynik + float(a['value'][1])
	
	else:
		 print "Wrong answer from Prometheus!"
		 print url
		 print dataJson
	
	return wynik

# Query to OCP (selected information about pods)
#-----------------------------------
def get_pod_avail_perf(host, port, phost, pport, token, namespace, pod_name, restartwarn, restartcrit):
	# query from OCP
	url = ('api/v1/namespaces/{}/pods').format(v_namespace)
	dataJson = QueryOcp(host, port, token, url)

	v_pods_count = 0
	v_pods_info = ''
	v_pods_cpu = 0
	v_pods_mem = 0
	v_pods_mem = 0
	v_pod_mem = 0
	v_pod_name_mem = ''
	v_pods_status = Status.OK
	v_pod_restart = 0
	v_pod_restart_multi = 0
	v_net_in_perf = 0
	v_net_out_perf = 0
	
	# for each pod in the namespace
	for a in dataJson['items']:
		v_pod_name_full = a['metadata']['name']
	
		if pod_name in v_pod_name_full and v_pod_name_full[len(pod_name)] == "-" and	v_pod_name_full[len(pod_name) + 1].isdigit() == True:
			v_node_name = a['spec']['nodeName']
	
			if a['status']['containerStatuses'][0]['ready'] == True:
				v_pod_status = Status.OK
	
				# the number of instances of the pod running
				v_pods_count = v_pods_count + 1
	
				# the age of the pod and the number of reboots
				v_pod_restart = int(a['status']['containerStatuses'][0]['restartCount'])
				if v_pod_restart_multi < v_pod_restart:
					v_pod_restart_multi = v_pod_restart
					#print v_pod_restart_multi
	
				v_pod_started_at = a['status']['containerStatuses'][0]['state']['running']['startedAt']
				v_dt_pod_str = v_pod_started_at.replace('Z', '').replace('T', ' ')
				v_dt_pod_obj = datetime.datetime.strptime(v_dt_pod_str, '%Y-%m-%d %H:%M:%S')
	
				diff = relativedelta(datetime.datetime.now(), v_dt_pod_obj)
				if diff.days > 0:
					v_pod_created_info = ('{} days ago').format(diff.days)
				else:
					if diff.hours > 0:
						v_pod_created_info = ('{} hours ago').format(diff.hours)
					else:
						v_pod_created_info = ('{} minutes ago').format(diff.minutes)
	
				v_pod_created = diff.days*24*60 + diff.hours*60 + diff.minutes
	
				# pod availability status (the age of the pod and the number of reboots)
				if v_pod_restart >= 5 and v_pod_created <= 5:
					v_pod_status = Status.OK
				if v_pod_restart > int(restartwarn) and v_pod_restart <= int(restartcrit):
					v_pod_status = 1
				if v_pod_restart > int(restartcrit):
					#v_pod_status = 1
					v_pod_status = 2
				
				# performance - CPU from Prometheus
				v_query = ('api/v1/query?query=pod%3Acontainer_cpu_usage%3Asum%7Bpod%3D%27{}%27%2Cnamespace%3D%27{}%27%7D').format(v_pod_name_full, namespace)
				v_pod_cpu_cores_usage = get_metric_from_prometheus(phost, pport, token, v_query, 'float')
				v_pods_cpu = v_pods_cpu + v_pod_cpu_cores_usage
	
				# round cpu_usage (pod)
				v_pod_cpu_cores_usage = round(v_pod_cpu_cores_usage, 3)
	
				# performance - MEM from Prometheus
				v_query = ('api/v1/query?query=sum(container_memory_working_set_bytes%7Bpod%3D%27{}%27%2Cnamespace%3D%27{}%27%2Ccontainer%3D%27%27%2C%7D)%20BY%20(pod%2C%20namespace)').format(v_pod_name_full, namespace)
				v_pod_mem_usage = get_metric_from_prometheus(phost, pport, token, v_query, 'int')
	
				if v_pod_mem < v_pod_mem_usage:
					v_pod_mem = v_pod_mem_usage
					v_pod_name_mem = v_pod_name_full
					v_pods_mem = v_pods_mem + v_pod_mem_usage
	
					# convert from bytes to megabytes
					v_pod_mem_usage = round(float(v_pod_mem_usage)/1024/1024)
	
				# performance - Network
				query = "api/v1/query?query=(sum(irate(container_network_receive_bytes_total{pod='" + v_pod_name_full + "', namespace='" + namespace + "'}[5m])) by (pod, namespace, interface))"
	
				v_net = get_metric_from_prometheus(phost, pport, token, query, 'float')
				v_net_in_perf = v_net_in_perf + round(float(v_net), 2)
				v_net_in = float(v_net)
				v_net_in = round(v_net_in, 2)
	
				data = "api/v1/query?query=(sum(irate(container_network_transmit_bytes_total{pod='" + v_pod_name_full + "', namespace='" + namespace + "'}[5m])) by (pod, namespace, interface))"
				v_net = get_metric_from_prometheus(phost, pport, token, query, 'float')
				v_net_out_perf = v_net_out_perf + round(float(v_net), 2)
				v_net_out = float(v_net)
				v_net_out = round(v_net_out, 2)
	
				# create information about pods
				if v_pods_count == 1:
					v_pods_info = ('\n> [{}] {} (created: {}, node: {})\n  > CPU Usage {} [core]\n  > MEM Usage {} [MiB]\n  > Network {}/{} (in/out) [Bps]\n  > Restart {} [count]').format(get_status_name(v_pod_status),v_pod_name_full,v_pod_created_info, v_node_name, v_pod_cpu_cores_usage, v_pod_mem_usage, str(v_net_in), str(v_net_out), v_pod_restart)
				else:
					v_pods_info = v_pods_info + ('\n> [{}] {} (created: {}), node: {})\n	> CPU usage {} [core]\n  > MEM usage {} [MiB]\n  > Network {}/{} (in/out) [Bps]\n  > Restart {} [count]').format(get_status_name(v_pod_status), v_pod_name_full, v_pod_created_info, v_node_name, v_pod_cpu_cores_usage, v_pod_mem_usage,str(v_net_in), str(v_net_out),  v_pod_restart)
	
				# final status (all instances of pods)
				if v_pods_status < v_pod_status:
	 
					v_pods_status = v_pod_status
					v_pod_restart = v_pod_restart_multi
	
	return v_pods_count, v_pods_status, v_pods_info, v_pods_cpu, v_pods_mem, v_pod_mem, v_pod_name_mem, v_pod_restart, v_net_in_perf, v_net_out_perf

# Query to OCP (selected information about the node)
#-----------------------------------
def get_dc_info_from_ocp(host, port, token, url, pod_name):
	dataJson = QueryOcp(host, port, token, url)

	v_pod_scale = 0
	if dataJson['metadata']['name'] == pod_name:
		#print str(dataJson['status']['replicas'])
		#exit()
		# zxc tutaj problem z nieuruchomionym podem
		# może lipiej warunek na ['spes'] == "" !!!!! 
		if int(dataJson['status']['replicas']) == 0:
			v_pod_scale = 0
		else:	
			v_pod_scale = int(dataJson['spec']['replicas'])
	
	return v_pod_scale

# Determination of status, output and performance
#-----------------------------------
def calculate_status(v_namespace, v_pod_name, v_pods_scale, v_pods_count, v_pods_status, v_pods_info, v_pods_cpu, v_pods_mem, v_pod_mem, v_pod_name_mem, v_mem_warn, v_mem_crit, v_pod_restart, restartwarn, restartcrit, v_net_in_perf, v_net_out_perf):
	# final status
	status = Status.OK
	status = 0 
		
	if (v_pods_scale == v_pods_count and v_pods_status == Status.WARNING) or (int(v_pod_mem/1024/1024) >= int(v_mem_warn)):
		status = Status.OK
	
	if (int(v_pod_mem/1024/1024) >= int(v_mem_warn)):
		status = Status.WARNING
	
	if (v_pods_scale > v_pods_count) or (int(v_pod_mem/1024/1024) >= int(v_mem_crit)):
		status = Status.CRITICAL
	
	if v_pods_scale == 0:
		status = Status.CRITICAL
	
	# output
	# create list from v_pods_info to determinate status for each pods(memory)
	l_pods_info=v_pods_info.split(" ")
	for pos, value in enumerate(l_pods_info):
		if value == 'MEM':
			if (int(float(l_pods_info[pos+2])) >= int(v_mem_warn)):
					if (int(float(l_pods_info[pos+2])) >= int(v_mem_crit)):
	  					v_pods_info = v_pods_info.replace('[OK] ' + l_pods_info[pos-15], '[CRITICAL] ' + l_pods_info[pos-15])
					else:	
	  					v_pods_info = v_pods_info.replace('[OK] ' + l_pods_info[pos-15], '[WARNING] ' + l_pods_info[pos-15])
					output = ('Pod {} ({}) - Status: {} of {} pods, MEM usage: {} MiB {}').format(v_pod_name, v_namespace, v_pods_count, v_pods_scale, round(float(v_pod_mem)/1024/1024), v_pods_info)
	 		else:
					output = ('Pod {} ({}) - Status: {} of {} pods {}').format(v_pod_name, v_namespace, v_pods_count, v_pods_scale, v_pods_info)
	
	if v_pods_scale == 0 and v_pods_count == 0 :
		status = Status.OK
		output = ('Pod {} ({}) zatrzymany - Status: {} of {} pods {}').format(v_pod_name, v_namespace, v_pods_count, v_pods_scale, v_pods_info)
	if v_pods_count == 0 and v_pods_scale != 0:
		output = ('Pod {} ({}) zatrzymany - Status: {} of {} pods {}').format(v_pod_name, v_namespace, v_pods_count, v_pods_scale, v_pods_info)
	
	# performance data
	output_perfData = 'scale=' + str(v_pods_scale) + ';0;0;0 ready=' + str(v_pods_count) + ';0;0;0 status=' + str(status) + ';0;2;0 cpu_cores_usage=' + str(round(v_pods_cpu, 3)) + ';0;0;0 mem_usage=' + str(v_pods_mem) + ';' + v_mem_warn + ';' + v_mem_crit + ';' + '0 restart=' + str(v_pod_restart) + ';' + restartwarn + ';' + restartcrit + ';0 network_in=' + str(round(v_net_in_perf)) + ';0;0;0 network_out=' + str(round(v_net_out_perf)) + ';0;0;0'
	
	return status, output, output_perfData


# Main
#===================================
if __name__ == '__main__':
	# Parsing arguments
	v_token = ""
	v_ohost, v_oport, v_phost, v_pport, v_token, v_namespace, v_pod, v_memwarn, v_memcrit, v_restartwarn, v_restartcrit = f_get_params(v_basename, v_version)
	# sprawdzam, czy istnieje plik z tokenem
	if not os.path.isfile(v_token):
		print 'No access to the token file'
		exit(Status.CRITICAL)	    
	else:
		# token reading
		f = open(v_token, 'r')
		v_token = f.readline().rstrip('\n')
		f.close()

	# get information from OCP about numbers instances of pods
	v_query = ('apis/apps.openshift.io/v1/namespaces/{}/deploymentconfigs/{}/scale').format(v_namespace, v_pod)
	v_pods_scale = get_dc_info_from_ocp(v_ohost, v_oport, v_token, v_query, v_pod)
	
	# get information from OCP about pods availability and performance
	v_pods_count, v_pods_status, v_pods_info, v_pods_cpu, v_pods_mem, v_pod_mem, v_pod_name_mem, v_pod_restart, v_net_in_perf, v_net_out_perf = get_pod_avail_perf(v_ohost, v_oport, v_phost, v_pport, v_token, v_namespace, v_pod, v_restartwarn, v_restartcrit)
	
	# processing responses from OCP and Prometheus 
	status, message, output_perfData = calculate_status(v_namespace, v_pod, v_pods_scale, v_pods_count, v_pods_status, v_pods_info, v_pods_cpu, v_pods_mem, v_pod_mem, v_pod_name_mem, v_memwarn, v_memcrit, v_pod_restart, v_restartwarn, v_restartcrit, v_net_in_perf, v_net_out_perf)
	
	# output in Nagios/Icinga format
	exitus(status, message, output_perfData)

