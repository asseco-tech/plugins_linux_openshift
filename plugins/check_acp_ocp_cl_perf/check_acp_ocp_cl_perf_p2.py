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
v_cluster_cpu_percent_th_w = 70
v_cluster_cpu_percent_th_c = 80
v_node_mem_percent_th_w = 90
v_node_mem_percent_th_c = 95
v_node_fs_percent_th_w = 80
v_node_fs_percent_th_c = 90
v_net_warn = 80000
v_net_crit = 92000
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
	parser = argparse.ArgumentParser(prog=v_basename, usage='\n\t %(prog)s --host <host> --port <port> --token <file_with_token>', description='Nagios plugin to check OpenShift cluster availability')
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
		print "Connection error to Prometheu status_code=" + str(response.status_code)
		exit(Status.CRITICAL)	    
	
	return dataJson

# Query to Prometheus
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

# Query to Prometheus (network query)
#-----------------------------------
def get_network_from_prometheus(host, port, token, url, typ):
	dataJson = QueryPrometheus(host, port, token, url)

	if dataJson['status'] == 'success':
		wynik = 0
	
		for a in dataJson['data']['result']:
			wynik = float(a['value'][1])
	
	else:
		print "Wrong answer from Prometheus!"
		print url
		print dataJson
	
	return wynik

# Determination of status, output and performance
#-----------------------------------
def calculate_status(v_cluster_cpu_cores_total, v_cluster_cpu_cores_usage, v_node_memory_total, v_node_memory_usage, v_node_filesystem_total, v_node_filesystem_usage, v_pods_count, v_net_in, v_net_out):
	# CPU percent
	v_cluster_cpu_percent = 100 - (float(v_cluster_cpu_cores_total - v_cluster_cpu_cores_usage)/float(v_cluster_cpu_cores_total))*100

	# Memory percent
	v_node_mem_percent = 100 - (float(v_node_memory_total - v_node_memory_usage)/float(v_node_memory_total))*100
	
	# Filesystem percent
	v_node_fs_percent = 100 - (float(v_node_filesystem_total - v_node_filesystem_usage)/float(v_node_filesystem_total))*100
	
	v_status_cpu = 0
	v_status_mem = 0
	v_status_fs = 0
	v_status_net = 0 
	v_status_warn = 0
	v_status_crit = 0
	
	# status CPU
	if v_cluster_cpu_percent >= v_cluster_cpu_percent_th_w and v_cluster_cpu_percent < v_cluster_cpu_percent_th_c:
		v_status_cpu = 1
		v_status_warn = v_status_warn + 1
	if v_cluster_cpu_percent >= v_cluster_cpu_percent_th_c:
		v_status_cpu = 2
		v_status_crit = v_status_crit + 1
	
	# status MEM
	if v_node_mem_percent >= v_node_mem_percent_th_w and v_node_mem_percent < v_node_mem_percent_th_c:
		v_status_mem = 1
		v_status_warn = v_status_warn + 1
	if v_node_mem_percent >= v_node_mem_percent_th_c:
		v_status_mem = 2
		v_status_crit = v_status_crit + 1
	
	# status FS
	if v_node_fs_percent >= v_node_fs_percent_th_w and v_node_fs_percent < v_node_fs_percent_th_c:
		v_status_fs = 1
		v_status_warn = v_status_warn + 1
	if v_node_fs_percent >= v_node_fs_percent_th_c:
		v_status_fs = 2
		v_status_crit = v_status_crit + 1
	 
	# status network
	if (int(v_net_in/1024/1024) >= int(v_net_warn) and int(v_net_in/1024/1024) < v_net_crit) or (int(v_net_out/1024/1024) >= int(v_net_warn) and int(v_net_out/1024/1024) < int(v_net_crit)): 	
		v_status_net = 1
		v_status_warn = v_status_warn + 1
	if (int(v_net_in/1024/1024) >= int(v_net_crit)) or (int(v_net_out/1024/1024) >= int(v_net_crit)): 
		v_status_net = 2
		v_status_crit = v_status_crit + 1
	 
	v_status_ok = 4 - v_status_warn - v_status_crit
	
	# Final status
	status = 0
	
	if v_status_cpu == 2 or v_status_mem == 2 or v_status_fs == 2 or v_status_net == 2:
		status = 2
	
	if status == 0 and (v_status_cpu == 1 or v_status_mem == 1 or v_status_fs == 1 or v_status_net == 1):
		status = 1
	
	# output
	output = ('Cluster Utilization: ({} OK, {} WARNING, {} CRITICAL)\n> [{}] CPU Cores Usage {}% ({}/{} [core])\n> [{}] Memory Usage {}% ({}/{} [GiB])\n> [{}] Filesystem Usage {}% ({}/{} [GiB])\n> [{}] Network {}/{} (in/out) [MBps]').format(v_status_ok, v_status_warn, v_status_crit, get_status_name(v_status_cpu), round(v_cluster_cpu_percent), round(v_cluster_cpu_cores_usage), v_cluster_cpu_cores_total, get_status_name(v_status_mem), round(v_node_mem_percent), round(v_node_memory_usage/1024/1024/1024), round(v_node_memory_total/1024/1024/1024), get_status_name(v_status_fs), round(v_node_fs_percent), round(v_node_filesystem_usage/1024/1024/1024), round(v_node_filesystem_total/1024/1024/1024), get_status_name(v_status_net), str(int(v_net_in/1024/1024)), str(int(v_net_out/1024/1024)))
	
	# performance data
	output_perfData = 'cpu_cores_total=' + str(v_cluster_cpu_cores_total) + ';0;0;0 cpu_cores_usage=' + str(round(v_cluster_cpu_cores_usage, 2)) + ';0;0;0 cpu_cores_usage_perc=' + str(round(v_cluster_cpu_percent, 2)) + ';70;80;0 mem_total=' + str(v_node_memory_total) + ';0;0;0 mem_usage=' + str(v_node_memory_usage) + ';0;0;0 mem_usage_perc=' + str(round(v_node_mem_percent, 2)) + ';90;95;0  fs_total=' + str(v_node_filesystem_total) + ';0;0;0 fs_usage=' + str(v_node_filesystem_usage) + ';0;0;0 fs_usage_perc=' + str(round(v_node_fs_percent, 2)) + ';80;90;0 pods_count=' + str(v_pods_count) + ';0;0;0 network_in=' + str(round(v_net_in)) + ';' + str(v_net_warn) + ';' + str(v_net_crit) + ';0 network_out=' + str(round(v_net_out)) + ';' + str(v_net_warn) + ';' + str(v_net_crit) + ';0'
	
	return status, output, output_perfData


# Main
#===================================
if __name__ == '__main__':
	# Parsing arguments
	v_token = ""
	v_host, v_port, v_token = f_get_params(v_basename, v_version)
	# is there a token file
	if not os.path.isfile(v_token):
		print 'No access to the token file'
		exit(Status.CRITICAL)	    
	else:
		# token reading
		f = open(v_token, 'r')
		v_token = f.readline().rstrip('\n')
		f.close()

	# Query to API Prometheus
	v_cluster_cpu_cores_total = get_metric_from_prometheus(v_host, v_port, v_token, 'api/v1/query?query=cluster:capacity_cpu_cores:sum', 'int')
	v_cluster_cpu_cores_usage = get_metric_from_prometheus(v_host, v_port, v_token, 'api/v1/query?query=cluster:cpu_usage_cores:sum', 'float')
	
	v_node_memory_total = get_metric_from_prometheus(v_host, v_port, v_token, 'api/v1/query?query=sum(node_memory_MemTotal_bytes)', 'int')
	v_node_memory_usage = get_metric_from_prometheus(v_host, v_port, v_token, 'api/v1/query?query=sum(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes)', 'int')
	 
	v_node_filesystem_total = get_metric_from_prometheus(v_host, v_port, v_token, 'api/v1/query?query=sum(node_filesystem_size_bytes{mountpoint="/"})', 'int')
	v_node_filesystem_usage = get_metric_from_prometheus(v_host, v_port, v_token, 'api/v1/query?query=(sum(node_filesystem_size_bytes{mountpoint="/"}) - sum(node_filesystem_free_bytes{mountpoint="/"}))', 'int')
	
	v_pods_count = get_metric_from_prometheus(v_host, v_port, v_token, 'api/v1/query?query=count(kube_pod_info)', 'int')
	
	v_net_in = get_network_from_prometheus(v_host, v_port, v_token, 'api/v1/query?query=sum(instance:node_network_receive_bytes_excluding_lo:rate1m)', 'int')
	v_net_out = get_network_from_prometheus(v_host, v_port, v_token, 'api/v1/query?query=sum(instance:node_network_transmit_bytes_excluding_lo:rate1m)', 'int')
	
	# processing responses from Prometheus
	status, message, output_perfData = calculate_status(v_cluster_cpu_cores_total, v_cluster_cpu_cores_usage, v_node_memory_total, v_node_memory_usage, v_node_filesystem_total, v_node_filesystem_usage, v_pods_count, v_net_in, v_net_out)
	
	# output in Nagios/Icinga format
	exitus(status, message, output_perfData)

