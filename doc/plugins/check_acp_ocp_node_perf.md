## Description:

Plugin [check_acp_ocp_node_perf_`<prefix>`.py](https://github.com/asseco-tech/plugins_linux_openshift/tree/master/plugins/check_acp_ocp_node_perf) which monitors the performance of an OpenShift cluster node.

> ###### `<prefix>` 
>
> ###### Python version 2+
>
> ```
> check_acp_ocp_node_perf_p2.py
> ```
>
> ###### Python version 3+
>
> ```
> check_acp_ocp_node_perf_p3.py
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
> chmod 755 check_acp_ocp_node_perf_<prefix>.py
> ```

## Usage:

    check_acp_ocp_node_perf_<prefix>.py --ohost <host_ocp> --oport <port_ocp> --phost <host_prometheus> --pport <port_prometheus> --token <file_with_token> --node <node> --ipnode <address IP>
    
    optional arguments:
      -h, --help       show this help message and exit
      --ohost OHOST    name or ip address of OCP cluster
      --oport OPORT    port of OCP cluster
      --phost PHOST    name or ip address of Prometheus on OCP
      --pport PPORT    port of Prometheus
      --token TOKEN    token file required to connect to the API server for the created service account with the privileges on the cluster-reader level
      --node NODE      name of OCP node
      --ipnode IPNODE  IP node
      --version        show program's version number and exit

## Example:

#### Check Command

    object CheckCommand "check_ocp_node_perf" {
        import "plugin-check-command"
        command = [ PluginDir + "/check_acp_ocp_node_perf_<prefix>.py" ]
        arguments += {
            "--ipnode" = {
                order = 7
                value = "$ipnode$"
            }
            "--node" = {
                order = 6
                value = "$ocp_node$"
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
            "--pport" = {
                order = 4
                value = "$prometheus_port$"
            }
            "--token" = {
                order = 5
                value = "$ocp_token_file$"
            }
        }
    }

#### Service

![heck_acp_ocp_node_perf.png](https://github.com/asseco-tech/plugins_linux_openshift/blob/master/doc/images/check_acp_ocp_node_perf.png)
