# ***check_acp_ocp***



1. [About](#about)
2. [History](#history)
3. [Requirements](#requirements)
4. [License](#license)
5. [Getting Started](#getting-started)

### About

The package `check_acp_ocp` is a set of plugins monitoring the platform elements [Redhat OpenShift Container Platform](https://www.redhat.com/en/technologies/cloud-computing/openshift).

### History

Base version: 1.01.001

### Requirements

* ReadHat verion 7.8, Centos version 7.8
* OpenShift ReadHat version 4.6
* Icinga Web 2 version 2.8.2+
* PHP version 5.6.+ or 7.+
* PHP-CURL version 7.29
* Python version 2.7, version 3.6

### License

Licensed under the [Apache License, Version 2.0](LICENSE).

### Getting Started

Read the installation and configuration instructions for monitoring plugins:

| Plugin Name                                                  | Description                                                  |
| :----------------------------------------------------------- | :----------------------------------------------------------- |
| [check_acp_ocp_cl_avail](/doc/plugins/check_acp_ocp_cl_avail.md) | Cluster availability monitoring                              |
| [check_acp_ocp_cl_perf](/doc/plugins/check_acp_ocp_cl_perf.md) | Cluster performance monitoring                               |
| [check_acp_ocp_node_avail](/doc/plugins/check_acp_ocp_node_avail.md) | Monitoring the availability of the cluster node              |
| [check_acp_ocp_node_perf](/doc/plugins/check_acp_ocp_node_perf.md) | Monitoring the performance of the cluster node               |
| [check_acp_ocp_pod](/doc/plugins/check_acp_ocp_pod.md)       | Monitoring the availability and performance of the application container |
