## Description:

Plugin [check_acp_ocp_cl_avail_` <prefix> `.py](https://github.com/asseco-tech/plugins_linux_openshift/tree/master/plugins/check_acp_ocp_cl_avail) which checks OpenShift cluster status.



> ###### `<prefix>` 
>
> ###### Python version 2+
>
> ```
> check_acp_ocp_cl_avail_p2.py
> ```
>
> ###### Python version 3+
>
> ```
> check_acp_ocp_cl_avail_p3.py
> ```


## Install:

1. Select a plugin for the appropriate version of Python
2. Move the file to the `plugins` directory
> ###### default `plugins`
>
> ```
> /usr/lib64/nagios/plugins
3. Set the file attributes `rwx/rw/rw`
> ###### example 
>
> ```
> chmod 755 check_acp_ocp_cl_avail_<prefix>.py

## Usage:

    check_acp_ocp_cl_avail_<prefix>.py --host <ocp_cluster> --port <ocp_port> --token <file_with_token>
    
    optional arguments:
      -h, --help     show this help message and exit
      --host HOST    name or ip address of OCP cluster
      --port PORT    port of OCP cluster
      --token TOKEN  token file required to connect to the API server for the created service account with the privileges on the cluster-reader level
      --version      show program's version number and exit

## Example:

#### Check Command

    object CheckCommand "check_ocp_cl_avail" {
        import "plugin-check-command"
        command = [ PluginDir + "/check_acp_ocp_cl_avail_<prefix>.py" ]
        arguments += {
            "--host" = {
                order = 1
                required = true
                value = "$ocp_host$"
            }
            "--port" = {
                order = 2
                required = true
                value = "$ocp_port$"
            }
            "--token" = {
                order = 3
                required = true
                value = "$ocp_token_file$"
            }
        }
    }

#### Service

![heck_acp_ocp_cl_avail.png](https://github.com/asseco-tech/plugins_linux_openshift/blob/master/doc/images/check_acp_ocp_cl_avail.png)
