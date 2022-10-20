#!/usr/bin/python3 
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
        print(str(e))
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
	parser = argparse.ArgumentParser(prog=v_basename, usage='\n\t %(prog)s --host <ocp_cluster> --port <ocp_port> --token <file_with_token> ', description='Nagios plugin to check OpenShift cluster status')
	parser.add_argument('--host', action='store', help='name or ip address of OCP cluster', required=True)
	parser.add_argument('--port', action='store', help='port of OCP cluster', required=True)
	parser.add_argument('--token', action='store', help='file with user''s token to connect to OCP cluster', required=True)
	parser.add_argument('--version', action='version', version='%(prog)s ' + v_version)
	args = parser.parse_args()
	return args.host, args.port, args.token


# Functions
#===================================
# Program output in Nagios/Icinga format
#-----------------------------------
def exitus(status=Status.OK, message="all is well", perfdata=""):
	print("%s - %s|%s" % (nagios_codes[status], message, perfdata))
	sys.exit(status)

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
		print('Connection error to OCP')
		exit(Status.CRITICAL)
	
	if response.text == "ok":
		output_perfData = 'apiserver_status=0;0;0;0'
		status=Status.OK
		print("[%s] - %s|%s" % (nagios_codes[status], "Cluster Status: Apiserver is running",output_perfData))
	else:
		output_perfData = 'apiserver_status=2;0;2;0'
		status=Status.CRITICAL
		print("[%s] - %s|%s" % (nagios_codes[status], "Cluster Status: Apiserver is indeterminate",output_perfData))
	
		exit(Status.CRITICAL)

# Query to API OCP (infomation about the cluster)
#-----------------------------------
def get_info_from_ocp(host, port, token, url):
	datainfo = QueryOcp(host, port, token, url)


# Main
#===================================
if __name__ == '__main__':
	# Parsing arguments
	v_token = ""
	v_host, v_port, v_token = f_get_params(v_basename, v_version)

	# is there a token file
	if not os.path.isfile(v_token):
		print('No access to the token file')
		exit(Status.CRITICAL)
	else:
		# token reading
		f = open(v_token, 'r')
		v_token = f.readline().rstrip('\n')
		f.close()
	
		v_query = ('healthz')
		QueryOcp(v_host, v_port, v_token, v_query)
