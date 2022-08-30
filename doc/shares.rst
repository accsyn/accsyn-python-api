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

To list all root shares::

    root_shares = session.find('Share where type=root')


A list of dictionaries will be returned containing root share attributes::

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
        "description": "",
        "created": "2021-10-26T08:12:36",
        "creator": "admin@acmevfx.com",
        "modified": "2021-10-26T08:12:36",
        "modifier": "61bf395c46ed6081a2b2afc0",
    }


Explanation of the returned attributes:

* ``id``: The internal accsyn job id, use this when modifying the share later on.
* ``code``: The unique name of the share.
* ``uri``: The queue location of job, in stripped human readable form.
* ``default``: true if this is the default (main) root share, that will harbor home shares. Only one root share can be the main share, if not given it will default to true if not other shares exist.
* ``type``: The share type, can have the values "root", "standard" or "user.
* ``status``; The status of share, see below.
* ``paths``: Dict containing path definitions, for each operating system accsyn supports (windows, linux and mac). Also may contain VPN paths, allowing accsyn desktop app to proper identify remote source/destination and download/upload mode.
* ``path``: When assigned a server, and a path on the server's operating system, this will be the absolute path on disk for root share.
* ``description``: Share description.
* ``created``: Date of creation.
* ``creator``: The user that created the share.
* ``modified``: Date of last modification.
* ``modifier``: The user that most recently modified the share.'

To query standard/user shares::

    standard_shares = session.find('Share where type=standard')
    users_shares = session.find('Share where type=user')


A dict will be returned containing share attributes::

    {
        "id": "5db17f9f7384eff8e7065322",
        "code": "shared_assets",
        "default": false,
        "type": "standard"
        "status": "enabled",
        "path": "_SHARED_ASSETS",
        "email": "",
        "queue": "",
        "description": "",
        "modified": "2021-10-26T08:12:36",
        "created": "2021-10-26T08:12:36",
        "creator": "admin@acmevfx.com",
    }


Explanation of the returned attributes:

* ``id``: The internal accsyn share id, use this when modifying the share later on.
* ``code``: The unique name of the share.
* ``type``: The share type, can have the values "standard" or "user.
* ``status``; The status of share, see below.
* ``path``: The relative path share has beneath root share.
* ``email``: Additional email addresses to deliver notifications to.
* ``queue``: The queue (ID or code) to put jobs in, when involving this share. Will have no effect if queue already defined for job.
* ``description``: Share description.
* ``created``: Date of creation.
* ``creator``: The user that created the share.
* ``modified``: Date of last modification.
* ``modifier``: The user that most recently modified the share.'


Share states
************

Here follow a listing of share statuses:

.. list-table:: accsyn share statuses
   :widths: 20 70 10
   :header-rows: 1

   * - Code:
     - Description:
     - Writeable :sup:`1`:
   * - enabled
     - Normal state - share is enabled and functioning.
     - YES
   * - disabled
     - Share is offline and disabled - all related file transfers are put on hold.
     - YES
   * - offline
     - Share is enabled but the root share is offline - not server, missing or have other issues.
     -
   * - disabled-offline
     - Share is online but disabled - all related file transfers are put on hold.
     -


* :sup:`1` This status can be set with a modify call (see below)


Create
======


Create a root share (admin role required)::

    root_share = session.create("Share",{
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



Create a standard share, beneath a root share (employee clearance allowed)::


    root_share = session.create("Share",{
        "type":"standard",
        "parent": "61779c54b80099ea066b0604",
        "code":"shared_assets",
        "path":"_SHARED_ASSETS",
    })

In both cases, if creation was successful, a dictionary will be returned on the same format as a query would return.

Assign server
*************

Upon creation, a root share is not served by a client yet. This is required to be able to perform file transfers.

To assign a server to a root share (admin role required)::

    retval = session.assign("Share", "server", {
        "share":"61779c54b80099ea066b0604",
        "client": "61779c54b80099ea066b0604",
        "main":True
    })

Return value will be True if operation was successful. Ongoing jobs will not be affected by this change, only new jobs.


.. note::

    * The server has to be authenticated with and admin user account to be able to serve root shares.
    * All file transfer endpoints are called 'clients' within accsyn, server is a role which a client can have and means it will be the party listening for the incoming TCP connection from remote p2p client.



To assign a site server, e.g. a server that will serve a proxy of a root share on a remote office/cloud location::

    retval = session.assign("Share", "server", {
        "share":"61779c54b80099ea066b0604",
        "client": "61779c54b80099ea066b0604",
        "site":True
    })

Return value will be True if operation was successful. Ongoing jobs will not be affected by this change, only new jobs.

.. note::

    The site server have to be configured to be present at the site before this command can succeed.

List servers
************

To list which servers are serving a root share::

    retval = session.assignments("Share", "61779c54b80099ea066b0604")

Return value will be a list of dictionaries with assignment data.


De-assign server
****************

To stop a server from serving a root share, call the 'deassign' API function (admin role required)::

    retval = session.deassign("Share", "server", {
        "share":"standard",
        "client": "61779c54b80099ea066b0604",
        "main":True
    })

Return value will be True if operation was successful. Ongoing jobs will not be affected by this change, new jobs will
not be able to be submitted until a new server is assigned.


Modify
======

To disable a share::

    session.update('Share', '614d660de50d45bb027c9bdd', {'status':"disabled"})

Configuring a queue which will become default for new jobs using share::

    session.update('Share', '614d660de50d45bb027c9bdd', {'queue':"5ac60a8b1da7ee7eb4d146cf"})


Offline
=======

A share can be offlined, which means it will be removed from accsyn but still eglible for restore if you again create a share with the same name::

    session.offline_one('Share', '61779c54b80099ea066b0604')

.. note::

    * Offline a root share also causes all descendant shares to be archived.
    * No jobs that uses the share can be active.
    * ACLs are offlined with share.


Delete
======

To delete a share::

    session.delete_one('Share', '61779c54b80099ea066b0604')


.. note::

    * If you delete a share, all associated jobs are aborted. Deleting a root share also causes all related shares to be deleted.
    * For audit/security reasons, deleted shares with associated data (acls) are kept in the archive for query.