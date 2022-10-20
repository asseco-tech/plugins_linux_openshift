## Description:

Plugin [check_acp_ocp_node_avail_`<prefix>`.py](/plugins/check_acp_ocp_node_avail) which monitors the availability of an OpenShift cluster node.

> ###### `<prefix>` 
>
> ###### Python version 2+
>
> ```
> check_acp_ocp_node_avail_p2.py
> ```
>
> ###### Python version 3+
>
> ```
> check_acp_ocp_node_avail_p3.py
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
> chmod 755 check_acp_ocp_node_avail_<prefix>.py
> ```

## Usage:

```
check_acp_ocp_node_avail_<prefix>.py --host <ocp_cluster>  --port <port> --token <file_with_token> --node <node>

optional arguments:
  -h, --help     show this help message and exit
  --host HOST    name or ip address of OCP cluster
  --port PORT    port of OCP cluster
  --token TOKEN  token file required to connect to the API server for the created service account with the privileges on the cluster-reader level
  --node NODE    name of OCP node
  --version      show program's version number and exit
```

## Example:

#### Check Command

```
object CheckCommand "check_ocp_node_avail" {
    import "plugin-check-command"
    command = [ PluginDir + "/check_acp_ocp_node_avail_<prefix>.py" ]
    arguments += {
        "--host" = {
            order = 1
            value = "$ocp_host$"
        }
        "--node" = {
            order = 6
            value = "$ocp_node$"
        }
        "--port" = {
            order = 2
            value = "$ocp_port$"
        }
        "--token" = {
            order = 5
            value = "$ocp_token_file$"
        }
    }
}
```

#### Service

![heck_acp_ocp_node_avail.png](/doc/images/check_acp_ocp_node_avail.png)
