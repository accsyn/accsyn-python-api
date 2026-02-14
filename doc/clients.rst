..
    :copyright: Copyright (c) 2022 accsyn/HDR AB

.. _clients:

*******
Clients
*******

The accsyn client is the underlaying entity type representing an instance that can run processes - act as a file transfer endpoint, execute compute jobs or hooks. 
Clients are availble through the api as these entity types:

 * App(type:0); The client that is spawned when launching the accsyn desktop application, in the user context. Provides uploads and downloads to and from a workspace as well as hook execution and file sharing with locally mapped shares.
 * Server(type:1); A client spawned in the workspace context, on an accsyn daemon host instance running as a service.
 * UserServer(type:2); A client spawned in the user context, on an accsyn daemon host instance running as a server. Facilitates the same features as an App, with additional features for unattended file deliveries.
 * Browser(type:3); A temporary web browser client spawned only during file transfer, stored with a cookie in the browser and re-used if possible.
 * Lane (type:5); A virtual server facilitating mulitple compute processes on the same machine.


Hosts
=====

A host is a running instance of accsyn, in the context of a user. When logging in to the accsyn desktop application as another user, another host is created within that instance. 

.. note::
    
    Servers can currently only have one host, there is no way to add a secondary host.


Query
=====

To list App clients::

    apps = session.find("App")

To list Server clients::

    servers = session.find("Server")

A list of clients will be returned, each client being a dict containing its attributes::

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

* ``benchmark``: The compute benchmark (float), higher value means higher probability task will be dispatch to client/lane.
* ``code``: The hostname of the client, not necessarily unique.
* ``created``: Date of creation.
* ``description``: Description of the client.
* ``host_id``: Comma separated list of detected machine network interface MAC addresses.
* ``id``; The internal accsyn user id, use this when modifying the client later on.
* ``last_checkin:`` Last time client reported in.
* ``metadata``: Client metadata dict.
* ``metrics``: (Compute) The realtime metrics of client.
* ``modified``: Date of last modification.
* ``modifier``: The user that most recently modified the user.
* ``name``: The name of the client, same as code.
* ``os``: The machine operating system, can be either "windows", "linux", "mac",  "raspbian", "solaris""
* ``parent``: If a compute lane, this is the ID of the client lane belongs to.
* ``roles``: (Server) Comma separated list of roles server has, can be "storage"(servers volumes at main site), "compute" (has lanes with engines assigned), "site" (serves volumes at a remote site), "accsyn" (hosted accsyn cloud server).
* ``site_hr``: Human readable site type.
* ``site``: The physical site client is located at.
* ``status:`` The status of client, see below.
* ``type_hr``: Human readable client type.
* ``type``: The type of client.
* ``user_hr``: Human readable user entry.
* ``user``: The ID of user that registered and owns the client.
* ``username``: The operating system user name running the client executable.
* ``version``: The accsyn version of client.
* ``wan_ip``: The remote IP number, as seen from accsyn when client is reporting in.


Client states
-------------

.. list-table:: client states
   :widths: 20 60 10
   :header-rows: 1

   * - Status:
     - Description:
     - Writeable:sup:`1`:
   * - online
     - Client is online and regularly checking in.
     - YES :sup:`2`
   * - offline
     - Client has not checked in and are considered offline (grace: 15 minutes)
     - NO
   * - disabled
     - Client is online but disabled - cannot execute processes
     - YES :sup:`3`
   * - disabled-offline
     - Client is offline and disabled
     - NO

* :sup:`1` This status can be set with a modify call (see below)

* :sup:`2` Only disabled clients can be modified with this state, note that 'disabled-offline' clients will enter the 'offline' state if enabled.

* :sup:`3` Only non disabled clients can be modified with this state, note that 'offline' clients will enter the 'disabled-offline' state if disabled.


Create
======

Clients cannot be created through the API, it can only be spawned and authenticated through the accsyn Daemon, desktop app or web browser.

User servers are spawned from `https://accsyn.io/hosts <https://accsyn.io/hosts>`_ page.

To adjust the number of lanes a server has, update server 'client_compute_lanes' setting.


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

    * Clients have to be offline in order for deletion to succeed.
    * If server is serving any volumes, these assignments will also be removed.
    * A lane can not be deleted, adjust the number of lanes instead.

