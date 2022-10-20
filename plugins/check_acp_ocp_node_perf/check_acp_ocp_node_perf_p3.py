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
	import subprocess
	import datetime
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
v_threshold_cpu_warn = 70
v_threshold_cpu_crit = 80
v_threshold_mem_warn = 90
v_threshold_mem_crit = 95
v_threshold_fs_warn = 85
v_threshold_fs_crit = 90
v_threshold_pods_warn = 80
v_threshold_pods_crit = 90
v_threshold_net_in_warn = 1100
v_threshold_net_in_crit = 1500
v_threshold_net_out_warn = 1100
v_threshold_net_out_crit = 1500
v_file_out = "/var/log/icinga2/repair_acp_top_pods_"

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
	parser = argparse.ArgumentParser(prog=v_basename, usage='\n\t %(prog)s --ohost <host_ocp> --oport <port_ocp> --phost <host_prometheus> --pport <port_prometheus> --token <file_with_token> --node <node> --ipnode <address IP>', description='Nagios plugin to check OpenShift node performance')
	parser.add_argument('--ohost', action='store', help='name or ip address of OCP cluster', required=True)
	parser.add_argument('--oport', action='store', help='port of OCP cluster', required=True)
	parser.add_argument('--phost', action='store', help='name or ip address of Prometheus on OCP', required=True)
	parser.add_argument('--pport', action='store', help='port of Prometheus', required=True)
	parser.add_argument('--token', action='store', help='file with user''s token to connect to OCP cluster', required=True)
	parser.add_argument('--node', action='store', help='name of OCP node', required=True)
	parser.add_argument('--ipnode', action='store', help='IP node', required=True)
	parser.add_argument('--version', action='version', version='%(prog)s ' + v_version)
	args = parser.parse_args()
	return args.ohost, args.oport, args.phost, args.pport, args.token, args.node, args.ipnode


# Functions
#===================================
# Program output in Nagios/Icinga format
#-----------------------------------
def exitus(status=Status.OK, message="all is well", perfdata=""):
	print("[" + nagios_codes[status] + "] - " + message + "|" + perfdata)
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
		print('Connection error to OCP')
		exit(Status.CRITICAL)
	
	if response.status_code == 200:
		dataJson = response.json()
	else:
		print("Connection error to OCP status_code=" + str(response.status_code))
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
		print('Connection error to Prometheus')
		exit(Status.CRITICAL)	    
	
	if response.status_code == 200:
		dataJson = response.json()
	else:
		print("Connection error to Prometheus status_code=" + str(response.status_code))
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
		print("Wrong answer from Prometheus!")
		print(url)
		print(dataJson)
	
	return wynik

#Query to OCP (selected information about the node)
#-----------------------------------
def get_node_info_from_ocp(host, port, token, url):
	dataJson = QueryOcp(host, port, token, url)

	for a in dataJson['status']['addresses']:
		if a['type'] == 'Hostname':
			node_name = a['address']
		if a['type'] == 'InternalIP':
			node_ip = a['address']
	
	cpu_cores_total = float(dataJson['status']['capacity']['cpu'])
	mem_total = dataJson['status']['capacity']['memory']
	fs_total = dataJson['status']['capacity']['ephemeral-storage']
	pods_total = int(dataJson['status']['capacity']['pods'])
	
	if 'Ki' in mem_total:
		mem_total = mem_total.replace('Ki', '')
		mem_total = int(mem_total)*1024
	
	if 'Ki' in fs_total:
		fs_total = fs_total.replace('Ki', '')
		fs_total = int(fs_total)*1024
	
	return node_ip, cpu_cores_total, mem_total, fs_total, pods_total

# Determination of status, output and performance
#-----------------------------------
def calculate_status(v_node_name, v_node_cpu_cores_total, v_node_cpu_cores_usage, v_node_memory_total, v_node_memory_usage, v_node_filesystem_total, v_node_filesystem_usage, v_node_pods_total, v_node_pods_usage, v_net_in, v_net_out):
	# CPU 
	v_node_cpu_percent = 100 - (float(v_node_cpu_cores_total - v_node_cpu_cores_usage)/float(v_node_cpu_cores_total))*100

	# Memory
	v_node_mem_percent = 100 - (float(v_node_memory_total - v_node_memory_usage)/float(v_node_memory_total))*100
	
	# Filesystem
	v_node_fs_percent = 100 - (float(v_node_filesystem_total - v_node_filesystem_usage)/float(v_node_filesystem_total))*100
	
	# Pods
	v_node_pods_percent = 100 - (float(v_node_pods_total - v_node_pods_usage)/float(v_node_pods_total))*100
	
	v_status_cpu = 0
	v_status_mem = 0
	v_status_fs = 0
	v_status_pods = 0
	v_status_ok = 0
	v_status_warn = 0
	v_status_crit = 0
	v_status_net = 0
	
	# status CPU
	if v_node_cpu_percent >= v_threshold_cpu_warn and v_node_cpu_percent < v_threshold_cpu_crit:
		v_status_cpu = 1
		v_status_warn = v_status_warn + 1
	if v_node_cpu_percent >= v_threshold_cpu_crit:
		v_status_cpu = 2
		v_status_crit = v_status_crit + 1
	
	# status MEM
	if v_node_mem_percent >= v_threshold_mem_warn and v_node_mem_percent < v_threshold_mem_crit:
		v_status_mem = 1
		v_status_warn = v_status_warn + 1
	if v_node_mem_percent >= v_threshold_mem_crit:
		v_status_mem = 2
		v_status_crit = v_status_crit + 1
	
	# status FS
	if v_node_fs_percent >= v_threshold_fs_warn and v_node_fs_percent < v_threshold_fs_crit:
		v_status_fs = 1
		v_status_warn = v_status_warn + 1
	if v_node_fs_percent >= v_threshold_fs_crit:
		v_status_fs = 2
		v_status_crit = v_status_crit + 1
	
	# status pods
	if v_node_pods_percent >= v_threshold_pods_warn and v_node_pods_percent < v_threshold_pods_crit:
		v_status_pods = 1
		v_status_warn = v_status_warn + 1
	if v_node_pods_percent >= v_threshold_pods_crit:
		v_status_pods = 2
		v_status_crit = v_status_crit + 1
	
	# siec (in)
	v_net_in_perf = round(float(v_net_in), 2)
	v_net_in = v_net_in_perf
	v_net_in = float(v_net_in/1024/1024)
	v_net_in = round(v_net_in, 2)
	
	# siec (out)
	v_net_out_perf = round(float(v_net_out), 2)
	v_net_out = v_net_out_perf
	v_net_out = float(v_net_out/1024/1024)
	v_net_out = round(v_net_out, 2)
	
	# status network
	if (v_net_in >= v_threshold_net_in_warn and v_net_in < v_threshold_net_in_crit) or (v_net_out >= v_threshold_net_out_warn and v_net_out < v_threshold_net_out_crit):
		v_status_net = 1
		v_status_warn = v_status_warn + 1
	if (v_net_in > v_threshold_net_in_crit) or (v_net_out > v_threshold_net_out_crit):
		v_status_net = 2
		v_status_crit = v_status_crit + 1
	
	v_status_ok = 5 - v_status_crit - v_status_warn
	
	# final status
	status = 0
	
	if v_status_cpu == 2 or v_status_mem == 2 or v_status_fs == 2 or v_status_pods == 2 or v_status_net == 2:
		status = 2
	
	if status == 0 and (v_status_cpu == 1 or v_status_mem == 1 or v_status_fs == 1 or v_status_pods == 1  or v_status_net == 1):
		status = 1
	
	# output
	
	output = ('{} - Node Utilization: ({} OK, {} WARNING, {} CRITICAL)\n> [{}] CPU Cores Usage {}% ({}/{} [core])\n> [{}] Memory Usage {}% ({}/{} [MiB])\n> [{}] Filesystem Usage {}% ({}/{} [MiB])\n> [{}] Network {}/{} (in/out) [MBps])\n> [{}] Pods {}% ({}/{} [count])').format( v_node_name, v_status_ok, v_status_warn, v_status_crit, get_status_name(v_status_cpu),round(v_node_cpu_percent), round(v_node_cpu_cores_usage, 2), v_node_cpu_cores_total, get_status_name(v_status_mem), round(v_node_mem_percent), round(v_node_memory_usage/1024/1024), round(v_node_memory_total/1024/1024), get_status_name(v_status_fs), round(v_node_fs_percent), round(v_node_filesystem_usage/1024/1024), round(v_node_filesystem_total/1024/1024), get_status_name(v_status_net), str(v_net_in), str(v_net_out),get_status_name(v_status_pods), round(v_node_pods_percent), str(v_node_pods_count), str(v_node_pods_total))
	# performance data
	output_perfData = 'cpu_cores_total=' + str(v_node_cpu_cores_total) + ';0;0;0 cpu_cores_usage=' + str(round(v_node_cpu_cores_usage, 2)) + ';0;0;0 cpu_cores_usage_perc=' + str(round(v_node_cpu_percent, 2)) + ';0;0;0 mem_total=' + str(v_node_memory_total) + ';0;0;0 mem_usage=' + str(v_node_memory_usage) + ';0;0;0 mem_usage_perc=' + str(round(v_node_mem_percent, 2)) + ';0;0;0  fs_total=' + str(v_node_filesystem_total) + ';0;0;0 fs_usage=' + str(v_node_filesystem_usage) + ';0;0;0 fs_usage_perc=' + str(round(v_node_fs_percent, 2)) + ';0;0;0 pods_total=' + str(v_node_pods_total) + ';0;0;0 ' + 'network_in=' + str(v_net_in_perf) + ';0;0;0 ' + 'network_out=' + str(v_net_out_perf) + ';0;0;0 pods_count=' + str(v_node_pods_count) + ';0;0;0'
	
	return status, output, output_perfData, v_status_cpu, v_status_mem, v_status_fs, v_status_pods

# write to file (selected information about the node)
#-----------------------------------
def f_get_top_pods(host, port, token, ip_node, v_status_cpu, v_status_mem, v_status_fs, v_status_pods, v_file_out):
	status_info = ''
	if v_status_cpu == 1:
		status_info = status_info + 'WARNING - CPU   '
	if v_status_cpu == 2:
		status_info = status_info + 'CRITICAL - CPU   '
	if v_status_mem == 1:
		status_info = status_info + 'WARNING - MEM   '
	if v_status_mem == 2:
		status_info = status_info + 'CRITICAL - MEM   '

	code_file = 0 
	try:
		file_repair = open(v_file_out + ip_node + '.log', 'r')
		old_file = file_repair.read()
	except:
		code_file = 1
	
	file_repair = open(v_file_out + ip_node + '.log', 'w')
	czas = datetime.datetime.now().strftime('%H:%M:%S')
	
	# url
	url = ('https://{}:{}/api/v1/query?').format(host, port)
	# headres
	Authorization = ('Bearer {}').format(token)
	headers = {'Authorization': Authorization}
	
	# top pods CPU
	data = "query=topk(15, sort_desc(sum(rate(container_cpu_usage_seconds_total{container=\"\",pod!=\"\", instance=~'" + v_ipnode + ":.*'}[5m])) by (pod, namespace)))"
	
	try:
		out  = requests.get(url, headers=headers, params=data, verify=False)
	except:
		print('Connection error to Prometheus')
		exit(3)
	
	dataJson = out.json()
	
	file_repair.write("------------------------------------------------------------------------------------------\n")
	heading = "Time: " + czas + " " + status_info
	file_repair.write("%-50s" % heading + "Node: " + v_node + " (" + v_ipnode + ")")
	file_repair.write("\n------------------------------------------------------------------------------------------\n   PROJECT \t\t\t\t   POD \t\t\t\t\tCPU [core]\n")
	
	for pod in dataJson['data']['result'][0:]:
		file_repair.write("%-40s" % pod['metric']['namespace'] + "%-40s" % pod['metric']['pod'] + "%8.4f" % float(pod['value'][1]) + '\n')
	
	# top pods Memory
	data = "query=topk(15, sort_desc(sum(avg_over_time(container_memory_working_set_bytes{container=\"\",pod!=\"\", instance=~'" + v_ipnode + ".*'}[5m])) by (pod, namespace)))"
	
	try:
		out  = requests.get(url, headers=headers, params=data, verify=False)
	except:
		print('Connection error to Prometheus')
		exit(3)
	
	dataJson = out.json()
	
	file_repair.write("\n   PROJECT \t\t\t\t   POD \t\t\t\t\t MEM [KB]\n")
	for pod in dataJson['data']['result'][0:]:
		file_repair.write("%-40s" % pod['metric']['namespace'] + "%-40s" %  pod['metric']['pod'] + "%8.2f" % (float(pod['value'][1])/1024/1024) + '\n')
	file_repair.write("\r")
	if code_file == 0:
		file_repair.write(old_file)


	file_repair.close()


# Main
#===================================
if __name__ == '__main__':
	# Parsing arguments
	v_token = ""
	v_ohost, v_oport, v_phost, v_pport, v_token, v_node, v_ipnode = f_get_params(v_basename, v_version)

	# is there a token file
	if not os.path.isfile(v_token):
		print('No access to the token file')
		exit(Status.CRITICAL)	    
	else:
		# token reading
		f = open(v_token, 'r')
		v_token = f.readline().rstrip('\n')
		f.close()
	
	# query API Prometheus
	
	# get nod ip address, cpu number, momory size
	v_query = ('api/v1/nodes/{}').format(v_node)
	v_node_ip, v_node_cpu_cores_total, v_node_memory_total, v_node_filesystem_total, v_node_pods_total = get_node_info_from_ocp(v_ohost, v_oport, v_token, v_query)
	
	v_query = ('api/v1/query?query=instance%3Anode_cpu%3Arate%3Asum%7Binstance%3D%22{}%22%7D').format(v_node)
	v_node_cpu_cores_usage = get_metric_from_prometheus(v_phost, v_pport, v_token, v_query, 'float')
	
	v_query = ('api/v1/query?query=node_memory_MemTotal_bytes%7Binstance%3D%22{}%22%7D+-+node_memory_MemAvailable_bytes%7Binstance%3D%22{}%22%7D').format(v_node,v_node)
	v_node_memory_usage = get_metric_from_prometheus(v_phost, v_pport, v_token, v_query, 'int')
	
	v_query = ('api/v1/query?query=node_filesystem_size_bytes%7Binstance%3D%22{}%22%2Cmountpoint%3D%22%2F%22%7D+-+node_filesystem_avail_bytes%7Binstance%3D%22{}%22%2Cmountpoint%3D%22%2F%22%7D').format(v_node,v_node)
	v_node_filesystem_usage = get_metric_from_prometheus(v_phost, v_pport, v_token, v_query, 'int')
	
	v_query = ('api/v1/query?query=kubelet_running_pods%7Binstance%3D%7E%22{}%3A.*%22%7D').format(v_node_ip)
	v_node_pods_count = get_metric_from_prometheus(v_phost, v_pport, v_token, v_query, 'int')
	
	# network 
	v_query = "api/v1/query?query=instance:node_network_receive_bytes:rate:sum{instance='" + v_node + "'}"
	v_net_in = get_metric_from_prometheus(v_phost, v_pport, v_token, v_query, 'float')
	
	v_query = "api/v1/query?query=instance:node_network_transmit_bytes:rate:sum{instance='" + v_node + "'}"
	v_net_out = get_metric_from_prometheus(v_phost, v_pport, v_token, v_query, 'float')
	
	# processing responses from Prometheus
	status, message, output_perfData, v_status_cpu, v_status_mem, v_status_fs, v_status_pods = calculate_status(v_node, v_node_cpu_cores_total, v_node_cpu_cores_usage, v_node_memory_total, v_node_memory_usage, v_node_filesystem_total, v_node_filesystem_usage, v_node_pods_total, v_node_pods_count, v_net_in, v_net_out)
	
	# write to file (selected information about the node)
	if int(status) != 0:
		f_get_top_pods(v_phost, v_pport, v_token, v_ipnode, v_status_cpu, v_status_mem, v_status_fs, v_status_pods, v_file_out)
	
	# output in Nagios/Icinga format
	exitus(status, message, output_perfData)

