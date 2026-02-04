..
    :copyright: Copyright (c) 2021 accsyn

.. _filesharing:

************
File Sharing
************

Files and folders residing on accsyn storage volumes can be shared with other users, either through a delivery or through the accsyn file sharing engine.

Documentation: `https://support.accsyn.com/file-sharing <https://support.accsyn.com/file-sharing>`_


An accsyn 'share' is the base entity used to describe the following storage entities avaiable through the API:

* **Volume**; The base directory, were accsyn has access and files can be shared/delivered from or to. Users having the default 'employee' role has full access to volumes beeing granted access to, restricted users have not.

* **Folder**; A shared folder beneath a volume, at a relative path, from which restricted users can be given access through ACLs (access control lists). 

* **Home**; A shared folder designated to a user, providing an initial default area for file access. Home folders are not mandatory for operation, but accsyn can be configured to automatically create a home folder for each user upon user activation.

* **Collection**; A virtual shared folder containing one or more files and/or folders to be granted access through ACLs to one or more standard users.


Working with volumes
====================

List volumes
------------

To list all volumes::

    volumes = session.find('Volume')


A list of dictionaries will be returned containing volume attributes::

    {
        "code": "projects",
        "created": "2024-05-20T17:34:14",
        "creator": "demo.admin@accsyn.com",
        "default": true,
        "description": "Huvudvolym f\u00f6r projekt.",
        "email": "",
        "id": "664b6d76e43eb396e5e55419",
        "licensed": true,
        "metadata": {},
        "modified": "2026-02-02T07:13:12",
        "modifier": "backend@accsyn.com",
        "name": "Projects",
        "path": "/Volumes/projects",
        "paths": {
            "linux": "/projects",
            "mac": "/Volumes/projects",
            "windows": "P:"
        },
        "queue": null,
        "status": "enabled",
        "type": "volume"
    }


Explanation of the returned attributes:

* ``code``: The unique API name of the share.
* ``created``: Date of creation.
* ``creator``: The user that created the share.
* ``default``: true if this is the default (main) volume, that will harbor temp deliveries and home shares. Only one main volume can be defined, if not given it will default to true if not other volume exist.
* ``description``: Volume description.
* ``email``: Additional email addresses to deliver notifications to.
* ``id``: The internal accsyn job id, use this when modifying the share later on.
* ``licensed``: (Internal) true if the volume is licensed, false if not.
* ``metadata``: Volume metadata dict, used to transport data with workflows.
* ``modified``: Date of last modification.
* ``modifier``: The user that most recently modified the share.'
* ``name``: The name of the volume.
* ``path``: When served by a server, this will be the resolved absolute path on storage for this volume.
* ``paths``: Dict containing path definitions, for each operating system accsyn supports (windows, linux and mac). Also may contain VPN paths, allowing accsyn desktop app to proper identify remote source/destination and download/upload mode.
* ``type``: The share type, always "volume".
* ``status``; The status of share, see below.


Volume statuses
***************

Here follow a listing of volume statuses:

.. list-table:: accsyn volume statuses
   :widths: 20 70 10
   :header-rows: 1

   * - Code:
     - Description:
     - Writeable :sup:`1`:
   * - enabled
     - Normal state - volume is enabled and functioning.
     - YES
   * - disabled
     - Volume is disabled - all related jobs are put on hold.
     - YES
   * - offline
     - Volume is enabled but unavailable - not served or folder on server are missing. Related jobs are put on hold.
     -
   * - disabled-offline
     - Volume is offline and disabled. Related jobs are put on hold.
     -

* :sup:`1` This status can be set with a volume modify call (see below)


Create a volume
---------------

To create a volume, supply its name, server ID and paths (admin role required)::

    volume = session.create("Volume",{
        "name":"Assets",
        "code":"assets",
        "paths":{
            "windows":"A:",
            "windows_vpn":"\\192.168.0.1\assets",
            "linux":"/assets",
            "linux_vpn":"/192.168.0.1/assets",
            "mac":"/Volumes/assets",
            "mac_vpn":"/net/192.168.0.1/assets",
        },
        "server": "664b5db8ed9dc749a06f9bd6",
        "siteservers": ["6751d72886f229f292b4f2d4"]
    })

.. note::

    * The API identifier "code" must be unique with the workspace among all shares.
    * The path corresponding to the operating system server is running must be supplied.
    * The siteservers list of IDs are optional.


Modifying a volume
------------------

Rename a volume
***************

To rename a volume::

    session.update("Volume", "61779c54b80099ea066b0604", {"name":"Assets 2"})

A dictionary will be returned on the same format as a volume query would return.

To change the API code identifier::

    session.update("Volume", "61779c54b80099ea066b0604", {"code":"assets2"})

To update the paths::

    session.update("Volume", "61779c54b80099ea066b0604", {"paths":{"windows":"B:","linux":"/assets2","mac":"/Volumes/assets2"}})



List servers
************

To list which servers are serving a volume::

    retval = session.assignments("Volume", "61779c54b80099ea066b0604")

Return value will be a list of dictionaries with assignment data.



Assign server
*************


To change which server is serving a volume on the main site (hq) (admin role required)::  

    retval = session.assign("Volume", "server", {
        "volume":"61779c54b80099ea066b0604",
        "server": "66867188e8b00e18156bcf51"
    })

Return value will be True if operation was successful. Ongoing jobs will not be affected by this change, only new jobs.


.. note::

    * The server has to be authenticated with and admin user account to be able to serve volumes.
    * All file transfer endpoints are called 'clients' within accsyn, server is a role which a client can have and means it will be the party listening for the incoming TCP connection from remote p2p client.


To assign a site server, e.g. a server that will serve a volume locally at a remote office/cloud location::

    retval = session.assign("Volume", "server", {
        "volume":"61779c54b80099ea066b0604",
        "server": "66867188e8b00e18156bcf51"
    })

Return value will be True if operation was successful. Ongoing jobs will not be affected by this change, only new jobs.

.. note::

    The server must be configured to be at this site before this command can succeed.


De-assign server
****************

To stop a server from serving a volume, call the 'deassign' API function (admin role required)::

    retval = session.deassign("Volume", "server", {
        "volume":"61779c54b80099ea066b0604",
        "server": "66867188e8b00e18156bcf51",
    })

Return value will be True if operation was successful. Ongoing jobs will not be affected by this change, new jobs will
not be able to be submitted until a new server is assigned for the volume.

.. note::

    * If the server is at main site (hq) and it is the default volume, accsyn delivery and home shares might stop functioning until a new server is assigned.


Granting access to a volume
---------------------------

User having the role "employee" has no default access to a volume, access must be granted through ACLs (Access Control Lists). 


.. note::

    The backend acl entity is not directly exposed through the API, these are among other things is also used to bind users to deliveries internally within accsyn.


To grant access to an employee, use the session assign function::

    acl = session.grant("User", "61779c54b80099ea066b0604", "Volume", "664b6d76e43eb396e5e55419")

Return value will be a dictionary with same form as the access list query would return. 


List volume access
------------------

To list ACLs for a volume::

    acl = session.access("Volume", "664b6d76e43eb396e5e55419")

Return value will be a list of dictionaries containing selected ACL attributes.


Revoke access to a volume
--------------------------

To revoke access to a volume::

    acl = session.revoke("User", "61779c54b80099ea066b0604", "Volume", "664b6d76e43eb396e5e55419")

Return value will be true if operation was successful. False will be returned if the user did not have access to the volume.


Delete a volume
---------------

To delete a volume::

    session.delete_one("Volume", "61779c54b80099ea066b0604")

Return value will be True if operation was successful.

.. note::
    * If you delete a volume, all associated jobs are aborted.
    * All associated shared folders and homes will be deleted.
    * All associated ACLs will be deleted.
    * No files or folders on disk will be touched.


Working with shared folders and homes
=====================================

List folders
------------

To query shared folders::

    shared_folders = session.find('Folder')

A home is very similar to a share folder, with the difference that it is bound to a user and 
can be set to be created automatically upon user activation. To query homes::

    homes = session.find('Home')

A dict will be returned containing share attributes::

    {
        "code": "theproject",
        "created": "2024-11-19T16:49:33",
        "creator": "demo.employee@accsyn.com",
        "description": "",
        "email": "",
        "id": "673cb38dea344d0d17969018",
        "metadata": {},
        "modified": "2026-02-04T13:10:25",
        "modifier": "demo.admin@accsyn.com",
        "name": "TheProject",
        "parent": "664b6d76e43eb396e5e55419",
        "parent_hr": "share:Projects[volume](664b6d76e43eb396e5e55419)",
        "path": "projects/TheProject",
        "queue": null,
        "status": "enabled"
    }


Explanation of the returned attributes:

* ``code``: The unique API identifier of the share. Used in accsyn path notation: "share=<code>/some/path".
* ``created``: Date of creation.
* ``creator``: The user that created the share.
* ``description``: Share description.
* ``email``: Additional email addresses to deliver notifications to.
* ``id``: The internal accsyn share id, use this when modifying the share later on.
* ``metadata``: Share metadata dict.
* ``modified``: Date of last modification.
* ``modifier``: The user that most recently modified the share.'
* ``name``: The name of the share.
* ``parent``: The ID of the parent volume.
* ``parent_hr``: Human readable parent volume entry.
* ``path``: The relative path share has beneath parent volume.
* ``queue``: The queue (ID or code) to put jobs in, when involving this share. Will have no effect if queue already defined for job.
* ``status``; The status of share, see below.


Shared folder/home states
*************************

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
     - Share is enabled but the volume is offline - no server, missing or have other issues.
     -
   * - disabled-offline
     - Share is online but disabled - all related file transfers are put on hold.
     -


* :sup:`1` This status can be set with a modify call (see below)


Create a shared folder
----------------------

To share a folder beneath a volume, provide the parent (volume) ID, the relative path to 
the folder and the name of the share (employee clearance required)::

    share = session.create("Folder",{
        "parent": "664b6d76e43eb396e5e55419",
        "path":"projects/theproject",
        "name":"Shared project assets",
    })

In both cases, if creation was successful, a dictionary will be returned on the same format as a share query would return.

Create a home
-------------

To create a home, you just need to supply the user email address(code) or ID::

    home = session.create("Home", {
        "user": "693bf3168d4e0d0c2afe1d53",
    })

A dictionary will be returned containing home attributes on the same format as a folder query would return.


Granting access to a shared folder/home
----------------------------------------

A shared folder or home is not automatically accessible to any user, access must be granted through ACLs 
(Access Control Lists).

To grant access to a user, use the session assign function::

    acl = session.grant("User", "61779c54b80099ea066b0604", "Folder", "673cb38dea344d0d17969018", {
        "path": "FROM_VENDORS/acmevfx",
        "read": True,
        "write": True,
        "notify": True,
        "message": "Please upload your files here.",
    })

Return value will be a dictionary containing ACL attributes.

.. note::
    * The path is the relative path to the shared folder/home. It is optional, of not given the entire folder is granted access (equivalent to path: "/").
    * Either read and or write access must be granted. Both can not be false.
    * The notify flag is optional, and defaults to True. If set to False, no email will be sent to the user when the ACL is granted.
    * The message is optional, and will be sent as a notification to the user when access is granted.


List ACLs
---------

To list ACLs for a shared folder::

    acls = session.access("Folder", "673cb38dea344d0d17969018")

Return value will be a list of dictionaries containing ACL attributes.


Revoke access to a shared folder/home
-------------------------------------

To remove an ACL, use the session deassign function::

    acl = session.revoke("User", "61779c54b80099ea066b0604", "Folder", "673cb38dea344d0d17969018")

Return value will be True if operation was successful, false if the user did not have access to the folder.


Modify a shared folder/home
---------------------------

To disable a share::

    session.update("Folder", "614d660de50d45bb027c9bdd", {"status" :"disabled"})

Configuring a queue which will become default for new jobs using share::

    session.update("Folder", "614d660de50d45bb027c9bdd", {"queue" :"5ac60a8b1da7ee7eb4d146cf"})


Working with collections
========================

A collection is a virtual shared folder containing one or more files and/or folders to be granted access through ACLs to one or more standard users.
The files can stem from multiple source volumes, folders and/or homes.

To create a collection, you need to supply the source volumes, folders and/or homes IDs::

    collection = session.create("Collection", {
        "name": "Project assets",
        "files": ["volume=(default)/projects/theproject/assets", "folder=theproject/deliverables/specs.doc"],
    })

Offline
=======

A share (volume, folder, home, collection) can be deactivated, which means it will be removed from accsyn
but still eglible for audit & restore if you again create a share with the same name::

    session.deactivate_one("Volume", "61779c54b80099ea066b0604")

.. note::

    * Offline a volume also causes all descendant shares to be archived.
    * No jobs that uses the share can be active.
    * ACLs are offlined with share.
    * Offline shares have the attribute inactive set to True.



Re-activate a share
===================

To re-activate a share, supply the user email address(code) or ID::

    session.activate_one("Volume", "61779c54b80099ea066b0604")


Delete
======

To delete a shared folder/home::

    session.delete_one("Folder", "61779c54b80099ea066b0604")


.. note::

    * If you delete a share, all associated jobs are aborted. Deleting a volume also causes all related shares to be deleted.
    * For audit/security reasons, deleted shares with associated data (acls) are kept in the archive for query.