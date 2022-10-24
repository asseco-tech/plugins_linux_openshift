## Description:

Plugin [check_acp_ocp_pod_`<prefix>`.py](https://github.com/asseco-tech/plugins_linux_openshift/tree/master/plugins/check_acp_ocp_pod) which monitors the availability and performance of the application container.

> ###### `<prefix>` 
>
> ###### Python version 2+
>
> ```
> check_acp_ocp_pod_p2.py
> ```
>
> ###### Python version 3+
>
> ```
> check_acp_ocp_pod_p3.py
> ```

## Install:

1. Select a plugin for the appropriate version of Python
2. Move the file to the `plugins` directory
> ###### default `plugins`
>
> ```
> /usr/lib64/nagios/plugins
> ```
3. Set the file attributes `rwx/rw/rw`
> ###### example
>
> ```
> chmod 755 check_acp_ocp_pod_<prefix>.py
> ```

## Usage:

    check_acp_ocp_pod_p2.py --ohost <ocp_cluster> --oport <ocp_port> --phost <host_prometheus> --pport <port_prometheus> --token <file_with_token> --namespace <namespace> --pod <pod_name> --memwarn <memory threshold - warning> --memcrit <memory threshold - critical> --restartwarn <pod restart threshold - warning> --restartcrit <pod restart threshold - critical>
    
    optional arguments:
      -h, --help                  show this help message and exit
      --ohost OHOST               name or ip address of OCP cluster
      --oport OPORT               port of OCP cluster
      --phost PHOST               name or ip address of Prometheus on OCP
      --pport PPORT               port of Prometheus
      --token TOKEN               token file required to connect to the API server for the created service account with the privileges on the cluster-reader level
      --namespace NAMESPACE       name of OCP namespace
      --pod POD                   name of OCP pod which is created in namespace
      --memwarn MEMWARN           memory threshold - warning
      --memcrit MEMCRIT           memory threshold - critical
      --restartwarn RESTARTWARN   pod restart threshold - warning
      --restartcrit RESTARTCRIT   pod restart threshold - critical
      --version                   show program's version number and exit

## Example:

#### Check Command

    object CheckCommand "check_ocp_pod" {
        import "plugin-check-command"
        command = [ PluginDir + "/check_acp_ocp_pod_<prefix>.py" ]
        arguments += {
            "--memcrit" = {
                order = 9
                value = "$mem_crit$"
            }
            "--memwarn" = {
                order = 8
                value = "$mem_warn$"
            }
            "--namespace" = {
                order = 6
                value = "$ocp_namespace$"
            }
            "--ohost" = {
                order = 1
                value = "$ocp_host$"
            }
            "--oport" = {
                order = 2
                value = "$ocp_port$"
            }
            "--phost" = {
                order = 3
                value = "$prometheus_host$"
            }
            "--pod" = {
                order = 7
                value = "$ocp_pod$"
            }
            "--pport" = {
                order = 4
                value = "$prometheus_port$"
            }
            "--restartcrit" = {
                order = 11
                value = "$restartcrit$"
            }
            "--restartwarn" = {
                order = 10
                value = "$restartwarn$"
            }
            "--token" = {
                order = 5
                value = "$ocp_token_file$"
            }
        }
    }

#### Service

![heck_acp_ocp_pod.png](https://github.com/asseco-tech/plugins_linux_openshift/blob/master/doc/images/check_acp_ocp_pod.png)

