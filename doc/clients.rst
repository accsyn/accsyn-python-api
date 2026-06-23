..
    :copyright: Copyright (c) 2022 accsyn/HDR AB

.. _clients:

*******
Clients
*******

The accsyn client is the base entity representing an instance that can run processes — as a file transfer endpoint, compute worker, or hook executor.
Clients are available through the API as these entity types:

 * **Client**; Base client entity type. All clients are of this type.
 * **App** (type:0); Spawned when launching the accsyn desktop application in the user context. Handles uploads, downloads, hook execution, and file sharing with locally mapped shares.
 * **Server** (type:1); Spawned in the workspace context on an accsyn daemon host running as a service.
 * **UserServer** (type:2); Spawned in the user context on an accsyn daemon host running as a server. Same features as App, plus unattended file deliveries.
 * **Browser** (type:3); Temporary web browser client during file transfer. Stored in a cookie and reused when possible.
 * **Lane** (type:5); Virtual server running multiple compute processes on the same machine.


Hosts
=====

A host is a running accsyn instance in a user context. Logging in to the desktop app as another user creates a separate host within that instance.

.. note::
    
    Servers currently support only one host; secondary hosts cannot be added.


Query
=====

To list App clients::

    apps = session.find("App")

To list Server clients::

    servers = session.find("Server")

A list of clients is returned, each as a dict::

    {
        "benchmark": -1,
        "code": "MacServer.local",
        "created": "2024-05-20T16:27:04",
        "description": "Lokal BYOS dev test server",
        "host_ident": "8E:74:1B:A9:66:2C, 96:C8:52:7A:1F:E4",
        "id": "664b5db8ed9dc749a06f9bd6",
        "last_checkin": "2026-02-12T13:28:16",
        "metrics": {..},
        "modified": "2026-02-12T13:28:15",
        "modifier": "demo.admin@accsyn.com",
        "os": "mac",
        "parent": null,
        "roles": "storage,compute",
        "site": "66fc222ebeabd25ad64f04ec",
        "site_hr": "hq(66fc222ebeabd25ad64f04ec)",
        "status": "online",
        "user": "661014984428048969323147",
        "user_hr": "user:demo.admin@accsyn.com[admin](661014984428048969323147)",
        "username": "henriknorin",
        "version": "3.5-2_3",
        "wan_ip": "127.0.0.1"
    }



Explanation of the returned attributes:

* ``benchmark``: Compute benchmark (float). Higher values increase the probability a task is dispatched to this client/lane.
* ``code``: Client hostname. Not necessarily unique.
* ``created``: Date of creation.
* ``description``: Client description.
* ``host_id``: Comma-separated list of detected network interface MAC addresses.
* ``id``; Internal accsyn client ID. Use this when modifying the client.
* ``last_checkin:`` Last check-in time.
* ``metadata``: Client metadata dict.
* ``metrics``: (Compute) Real-time client metrics.
* ``modified``: Date of last modification.
* ``modifier``: User who last modified the client.
* ``name``: Client name, same as ``code``.
* ``os``: Operating system — ``windows``, ``linux``, ``mac``, ``raspbian``, or ``solaris``.
* ``parent``: If a compute lane, the ID of the parent client.
* ``roles``: (Server) Comma-separated roles — ``storage`` (serves volumes at main site), ``compute`` (has lanes with engines assigned), ``site`` (serves volumes at a remote site), ``accsyn`` (hosted accsyn cloud server).
* ``site_hr``: Human-readable site.
* ``site``: Physical site where the client is located.
* ``status:`` Client status (see below).
* ``type_hr``: Human-readable client type.
* ``type``: Client type.
* ``user_hr``: Human-readable user entry.
* ``user``: ID of the user who registered and owns the client.
* ``username``: OS username running the client executable.
* ``version``: accsyn client version.
* ``wan_ip``: Remote IP as seen by accsyn when the client checks in.


Client states
-------------

.. list-table:: client states
   :widths: 20 60 10
   :header-rows: 1

   * - Status:
     - Description:
     - Writable :sup:`1`:
   * - online
     - Client is online and checking in regularly.
     - YES :sup:`2`
   * - offline
     - Client has not checked in and is considered offline (grace: 15 minutes).
     - NO
   * - disabled
     - Client is online but disabled — cannot execute processes.
     - YES :sup:`3`
   * - disabled-offline
     - Client is offline and disabled.
     - NO

* :sup:`1` This status can be set with a modify call (see below).

* :sup:`2` Only disabled clients can be set to this state. ``disabled-offline`` clients enter ``offline`` when enabled.

* :sup:`3` Only non-disabled clients can be set to this state. ``offline`` clients enter ``disabled-offline`` when disabled.


Create
======

Clients cannot be created through the API. They are spawned and authenticated through the accsyn daemon, desktop app, or web browser.

User servers are spawned from the `https://accsyn.io/hosts <https://accsyn.io/hosts>`_ page.

To adjust the number of lanes on a server, update the ``client_compute_lanes`` setting.


Modify
======

To disable a client::

    session.update("Lane", "664b5db8ed9dc749a06f9bd6", {"status" :"disabled"})

To enable a client::

    session.update("Lane", "664b5db8ed9dc749a06f9bd6", {"status" :"enabled"})


Delete
======

To delete a client::

    session.delete_one("App", "664b5db8ed9dc749a06f9bd6")

.. note::

    * Clients must be offline for deletion to succeed.
    * If a server serves volumes, those assignments are also removed.
    * Lanes cannot be deleted; adjust the lane count instead.
