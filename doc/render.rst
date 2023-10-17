..
    :copyright: Copyright (c) 2022 accsyn

.. _render:

***********
Render jobs
***********

The accsyn render/compute feature allows submitting CPU intensive tasks to accsyn,
for queued processing on a cluster/farm of computers on one or more sites.
accsyn supports site-to-site transfer of render dependencies, as long as they are
specified properly and reside on a (root) share.


Submitting a render job
=======================

The Python accsyn API support submission of accsyn render jobs, here follows an example for rendering a Nuke 2D compositing job::

    jobs = session.create("job",{
        "code": "test_v002.nk render",
        "input": "C:\\projects\\nuke\\vfx\\test_v002.nk",
        "parameters": {
            "input_conversion": "always",
            "arguments": "-txV",
            "remote_os": "windows",
            "mapped_share_paths" : [
                {
                    "remote" : "C:\\projects",
                    "local" : "share=5c5bf52a1da7ee0165105b85"
                },
                {
                     "remote" : "E:\\tools",
                     "local" : "N:\\tools",
                     "os" : "windows"
                 },
            ],
            "site":{
                "local":{
                    "settings":{
                        "download":{
                            "enable": "false"
                        },
                        "upload":{
                            "task_bucketsize": "1"
                        },
                        "common":{
                            "transfer_speedlimit": "2"
                        }
                    }
                }
            }
        },
        "app": "nuke-11",
        "range": "1001-1100",
        "dependencies": [
            "C:\\projects\\nuke\\src\\vh_gridtest.0099.jpg"
        ],
        "filters": "ram:>32g,site:sthlm",
        "output": "C:\\projects\\nuke\\output",
        "settings": {
            "task_bucketsize": "5",
            "transfer_speedlimit": "-1"
        },
        "envs" : {
            "common": {
                "FOUNDRY_LICENSE_DEBUG": "true"
            },
            "linux": {
                "NUKE_PATH": "/projects/nuke/src"
            },
            "mac": {
                "NUKE_PATH": "/projects/nuke/src"
            },
            "windows": {
                "NUKE_PATH": "C:\\projects\\nuke\\src"
            }
        }
    })



* ``code``: (Optional) The name of the render job.
* ``input``: The path to the input file to process, currently accsyn only support on single file.
* ``parameters/input_conversion``: Tell wether input file should be parsed and have path's converted, only supported for ASCII format files. Possible values are: "always" - always attempt to parse  regardless of platform, "platform" - only if there is change in operating system platform (i.e. between windows and mac), "never" - do not touch the input file. It is recommended to leave this on "always" unless exactly the same paths are used within input file as on-prem / at render farm.
* ``parameters/arguments``: Additional parameters to pass on to the render process (command line options).
* ``parameters/remote_os``: (Optional)The operating system submit is made from.
* ``parameters/mapped_share_paths``: (Optional, if ASCII parsable input file and input conversions enabled) List of local paths mapped to on-prem shares. Required if the input file contains local paths that need conversion. If render servers are running different operating systems, "os" can be used to define different paths. Recognised values are "windows", "mac" and "linux", This is picked by the "common" render app only, it can be modified to support additional operating systems.
* ``parameters/site``: (Optional, since v2.0) Site specific setting overrides, see below.
* ``app``: The named render app to use, make sure it exists. Compute apps can be administered at Admin/apps page within accsyn web admin pages. Find open source render app boilerplate scripts  here: https://github.com/accsyn/compute-scripts.
* ``range``: (If app supports split into items/frames) The integer range to render. Can be on or more(space or comma separated list of) entries on the form "1-10"(range), "4"(single) or "5-250x5"(consider only every 5 item/frames).
* ``dependencies``: List of files that the input file depend on and must be able to access during the computation process.
* ``filters``: Comma separated list of filters to apply, see below.
* ``output``: Path to the folder where the render app should write back the resulting files.
* ``settings``: Standard accsyn settings to that will apply across all file involved file transfers, see https://support.accsyn.com/admin-manual.
* ``envs``: Environment variables to set on the render process, can either be given flat or as a dictionary with sub keys "common", "linux", "mac" and "windows" as in the example above.


Filters
*******

* ``ram``: Put a restriction on the RAM usage. On the form "ram:<32g" - less than 32GB or "ram:>64g" - more than 64GB.
* ``hostname``: Include or exclude machines by hostname or IDs. "hostname:+myhostname" - include this machine only, "hostname:-myhostname" - exclude this machine. Should be combine into one statement like: "hostname:-myhostname1-myhostname2".
* ``site``: Only execute on a particular site: "site:-mysite" - exclude the site "mysite". See below for Site specific settings.


Site settings
*************

Settings that is applied for each involved render site, available beneath ``parameters`` sub dictionary and can be edited after job has been submitted.

Proved settings as a dictionary by site name or ID, with sub key "settings":

* ``download``; Settings that will apply to all downloads from main site to this site, typically render scripts and dependencies. In the example above,
* ``upload``; Settings that will apply to all uploads from this site back to main site.
* ``common``; Settings that will apply to both downloads and uploads.


The ``local`` site is reserved and means the remote submitting computer and will only be considered when submitting from the remote "roaming" site. With the local site
download and upload are swapped settings wise, meaning that upload settings apply to the upload of render scripts and dependencies to main site and
download settings apply to the download of generated files.

.. note::

    To provide settings that should apply to all render job sync transfers, put them in ``settings`` dictionary in payload root.

