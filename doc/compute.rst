..
    :copyright: Copyright (c) 2022 accsyn

.. _compute:

***********
Render jobs
***********

The accsyn render (compute) feature submits CPU/GPU intensive tasks to accsyn for queued processing on a farm (cluster) across one or more sites.
accsyn supports site-to-site transfer of render dependencies when they are specified correctly and reside on a volume.


Submitting a render job
=======================

The Python API supports render job submission. Example: a Nuke 2D compositing job::

    jobs = session.create("Compute",{
        "name": "test_v002.nk render",
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
        "engine": "nuke-11",
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



* ``dependencies``: Files the input depends on and must be accessible during computation.
* ``engine``: Render app, by code or ID. Ensure it exists. Compute apps are managed at Admin/apps in the web admin. Open-source boilerplate scripts: https://github.com/accsyn/compute-scripts.
* ``envs``: Environment variables for the render process. Flat or nested under ``common``, ``linux``, ``mac``, and ``windows`` as in the example.
* ``filters``: Comma-separated filters (see below).
* ``input``: Path to the input file. Currently one file per job.
* ``name``: (Optional) Job name. Defaults to the input filename.
* ``output``: Folder where the render app writes results.
* ``parameters/arguments``: Additional command-line parameters.
* ``parameters/input_conversion``: Whether to parse and convert paths in the input file. Supported for ASCII formats. Values: ``always`` (always parse), ``platform`` (only on OS change, e.g. Windows to Mac), ``never`` (leave unchanged). Recommended: ``always`` unless paths in the input file match on-prem/render-farm paths exactly.
* ``parameters/mapped_share_paths``: (Optional, with ASCII input and conversion enabled) Local-to-share path mappings. Required when the input file contains local paths needing conversion. Use ``os`` for per-OS paths (``windows``, ``mac``, ``linux``). Picked by the common render app; extend the app to support additional OSes.
* ``parameters/remote_os``: (Optional) OS the submit originates from.
* ``parameters/site``: (Optional, since v2.0) Per-site setting overrides (see below).
* ``range``: (If the app supports frame splitting) Integer range. One or more entries: ``1-10`` (range), ``4`` (single), ``5-250x5`` (every 5th frame).
* ``settings``: Standard accsyn settings for all involved file transfers. See `https://support.accsyn.com <https://support.accsyn.com/admin-manual>`_.


Filters
*******

* ``ram``: RAM restriction. ``ram:<32g`` (less than 32 GB) or ``ram:>64g`` (more than 64 GB).
* ``hostname``: Include or exclude machines by hostname or ID. ``hostname:+myhostname`` (include only), ``hostname:-myhostname`` (exclude). Combine: ``hostname:-myhostname1-myhostname2``.
* ``site``: Restrict to a site. ``site:-mysite`` excludes site ``mysite``. See site-specific settings below.


Site settings
*************

Per-site settings under ``parameters``, editable after submit.

Provide settings by site name or ID with sub-key ``settings``:

* ``download``; Settings for downloads from main site to this site (typically render scripts and dependencies).
* ``upload``; Settings for uploads from this site back to main site.
* ``common``; Settings applied to both downloads and uploads.


The ``local`` site is reserved for the remote submitting machine and applies only when submitting from the ``roaming`` site. For ``local``, download and upload settings are swapped — upload settings govern dependency uploads to main site, download settings govern result downloads.

.. note::

    For settings that apply to all render job sync transfers, put them in the root ``settings`` dictionary.
