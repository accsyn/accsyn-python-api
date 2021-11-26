..
    :copyright: Copyright (c) 2021 accsyn

.. _shares:

******
Shares
******

An accsyn share defines a physical location on storage, from which files are allowed to be served. There are two main types of shares:

* **Root share**; The base directory, were accsyn has access and were shares can live. Users having the default 'employee' role has full access to root shares, restricted users have not.

* **Share**; A directory beneath a root share, at a relative path, from which restricted users can be given access through ACLs (access control lists). There are **Standard** shares and the **User** (a.k.a Home share) which is always created upon user activation, providing an initial default area for file access.



Query
=====


To list all root shares, standard shares and home shares::

    root_shares = session.find('Share where type=root')
    standard_shares = session.find('Share where type=standard')
    users_shares = session.find('Share where type=user')


Create
======


Create a root share, admin role required::

    root_share = session.create("share",{
        "type":"root",
        "code":"assets",
        "paths":{
            "windows":"A:",
            "windows_vpn":"\\192.168.0.1\assets",
            "linux":"/assets",
            "linux_vpn":"/192.168.0.1/assets",
            "mac":"/Volumes/assets",
            "mac_vpn":"/net/192.168.0.1/assets",
        }
    })


A dict will be returned containing root share attributes::

    {
        "id": "61779c54b80099ea066b0604",
        "code": "assets",
        "default": false,
        "type": "root"
        "status": "enabled",
        "paths":{
            "windows":"A:",
            "windows_vpn":"\\192.168.0.1\assets",
            "linux":"/assets",
            "linux_vpn":"/192.168.0.1/assets",
            "mac":"/Volumes/assets",
            "mac_vpn":"/net/192.168.0.1/assets",
        },
        "path": "",
        "modified": "2021-10-26T08:12:36",
        "created": "2021-10-26T08:12:36",
        "creator": "admin@acmevfx.com",
    }


Explaination of the returned attributes:

* id; The internal accsyn job id, use this when modifying the share later on.
* code; The unique name of the share.
* uri; The queue location of job, in stripped human readable form.
* default; true if this is the default (main) root share, that will harbor home shares. Only one root share can be the main share, if not given it will default to true if not other shares exist.
* type; The share type, can have the values "root", "standard" or "user.
* status;
* paths; Dict containing path definitions, for each operating system accsyn supports (windows, linux and mac). Also may contain VPN paths, allowing accsyn desktop app to proper identify remote source/destination and download/upload mode.
* path; When assigned a server, and a path on the server's operating system, this will be the absolute path on disk for root share.
* created; Date of creation.
* creator: The user that created the share.
* modified; Date of last modification.
* modifier: The user that most recently modified the share.


Create a standard share, beneath a root share::


    root_share = session.create("share",{
        "type":"standard",
        "parent": "61779c54b80099ea066b0604",
        "code":"shared_assets",
        "path":"_SHARED_ASSETS",
    })


A dict will be returned containing root share attributes::

    {
        "id": "61779c54b80099ea066b0604",
        "code": "assets",
        "default": false,
        "type": "root"
        "status": "enabled",
        "path": "",
        "paths":{
            "windows":"A:",
            "windows_vpn":"\\192.168.0.1\assets",
            "linux":"/assets",
            "linux_vpn":"/192.168.0.1/assets",
            "mac":"/Volumes/assets",
            "mac_vpn":"/net/192.168.0.1/assets",
        },
        "modified": "2021-10-26T08:12:36",
        "created": "2021-10-26T08:12:36",
        "creator": "admin@acmevfx.com",
    }


Explaination of the returned attributes:

* id; The internal accsyn job id, use this when modifying the share later on.
* code; The unique name of the share.
* uri; The queue location of job, in stripped human readable form.
* default; true if this is the default (main) root share, that will harbor home shares. Only one root share can be the main share. 
* type; The share type, can have the values "root", "standard" or "user.
* email; (Standard & home shares) Additional email addresses to deliver notifications to.
* path; (Root sh.
* etr; Time left of current transfer, on the form 'Hh{ours}:Mm{inutes}:Ss{econds}'.
* created; Date of creation.
* creator: The user that created the share.
* modified; Date of last modification.
* modifier: The user that most recently modified the share.


Assign server
*************

Upon creation, a root share is not served by a client yet. This is required to be able to perform file transfers.

To assign a server to a root share::

    retval = session.assign("share", "server", {
        "share":"standard",
        "client": "61779c54b80099ea066b0604",
    })

Return value will be True if operation was successful. Ongoing jobs will not be affected by this change, only new jobs.


.. note::

    All file transfer endpoints are called 'clients' within accsyn, server is a role which a client can have and means it will be the party listening for the incoming TCP connection from remote p2p client.


De-assign server
****************

To stop a server from serving a root share, call the 'deassign' API function::

    retval = session.deassign("share", "server", {
        "share":"standard",
        "client": "61779c54b80099ea066b0604",
    })

Return value will be True if operation was successful. Ongoing jobs will not be affected by this change, new jobs will not be able to be submitted until a new server is assigned.


Modify
======

To disable a share::

    session.update_one('share', '614d660de50d45bb027c9bdd', {'status':"disabled"})


Delete
======

To delete a share::

    session.delete_one('share', '61779c54b80099ea066b0604')


.. note::

    If you delete a share, all associated jobs are aborted. Deleting a root share also causes all related shares to be deleted.