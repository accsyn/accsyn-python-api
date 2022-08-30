..
    :copyright: Copyright (c) 2022 accsyn/HDR AB

.. _clients:

*******
Clients
*******

An accsyn client is an instance of the accsyn desktop application, or background daemon capable of perform file transfers or executing computations. Clients can have different types(roles):

 * App(type:0); The accsyn desktop application, that connects to a server during file transfers.
 * Server(type:1); The accsyn daemon installed by and admin to run in the background and launch with computer, receives connections from remote apps during file transfers. Servers can also act as compute nodes - executing tasks.
 * User server(type:2); The accsyn daemon installed as a user, either having rolve Employee or standard User. Enables unattended file transfers to locally configured proxy share locations.
 * Browser(type:3); A temporary web browser client spawned only during file transfer.
 * Compute lane (type:5); A virtual client used for parallelizing compute processes on the same client.

Query
=====

To list clients::

    all_clients = session.find('Client')
    servers = session.find('Client where type=1')

Each client entity will be a dict containing its attributes::

    {
        "id": "5da08873b0eb10fade60b3f7",
        "code": "WIN_SERVER",
        "user": "5d91b33ac71c12871d1fc3c2",
        "user_hr": "user:demo.admin@accsyn.com(admin)",
        "created": "2022-01-20T07:51:57",
        "type": 1,
        "site": "2374e137-ed06-4f40-9cb2-ce42965afec6",
        "site_hr": "hq",
        "description": "Main server",
        "host_id": "DE:A1:48:F1:01:22, 12:00:7C:18:F1:11",
        "last_checkin": "2022-01-21T07:51:57",
        "status": "online",
        "os": "mac",
        "type_hr": "server",
        "username": "root",
        "version": "1.4-4_27",
        "wan_ip": "123.123.123.123,
        "parent": null,
        "benchmark": null,
        "metrics": {
            "c": 16,
            "in": {
                "s": -1.0,
                "s_a": -1.0,
                "s_t": -1.0
            },
            "l": 23.134328358208954,
            "m": 76.0,
            "mpf": 7954137088,
            "mpt": 34359738368,
            "mvf": 1776025600,
            "mvt": 18253611008,
            "out": {
                "s": -1.0,
                "s_a": -1.0,
                "s_t": -1.0
            }
        },
        "metadata": {
            "external": {
                "location": "custom"
            },
            "internal": {
                "key": "hj39847tghenkls"
            }
        },
        "modified": "2022-01-21T07:51:57",
        "modifier": "5d91b33ac71c12871d1fc3c2"
    }



Explanation of the returned attributes:

* ``id``; The internal accsyn user id, use this when modifying the client later on.
* ``code``: The hostname of the client, does not need to be unique.
* ``user``: The ID of user that registered and owns the client.
* ``user_hr``: Human readable user entry.
* ``created``: Date of creation.
* ``type``: The type of client.
* ``type_hr``: Human readable client type.
* ``site``: The physical site client is located at.
* ``site_hr``: Human readable site type.
* ``description``: Description of the client.
* ``host_id``: Comma separated list of detected machine network interface MAC addresses.
* ``last_checkin:`` Last time client reported in.
* ``status:`` The status of client, see below.
* ``os``: The machine operating system, can be either "windows", "linux", "mac",  "raspbian", "solaris""
* ``username``: The operating system user name running the client executable.
* ``version``: The accsyn version of client.
* ``wan_ip``: The remote IP number, as seen from accsyn when client is reporting in.
* ``parent``: If a compute lane, this is the ID of the client lane belongs to.
* ``benchmark``: The compute benchmark (float), higher value means higher probability task will be dispatch to client/lane.
* ``metrics``: (Compute) The realtime metrics of client.
* ``metadata``: Client metadata dict.
* ``modified``: Date of last modification.
* ``modifier``: The user that most recently modified the user.


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
     - Client is online but disabled - cannot execute file transfers or compute tasks
     - YES :sup:`3`
   * - disabled-offline
     - Client is offline and disabled
     - NO

* :sup:`1` This status can be set with a modify call (see below)

* :sup:`2` Only disabled clients can be modified with this state, note that 'disabled-offline' clients will enter the 'offline' state if enabled.

* :sup:`3` Only non disabled clients can be modified with this state, note that 'offline' clients will enter the 'disabled-offline' state if disabled.


Create
======

Clients cannot be created through the API, it can only be installed and authenticated throught the accsyn Daemon or Desktop app installer.


Modify
======

To disable a client::

    session.update('Client', '61cd853e44b630d9e10cfb2e', {'status':"disabled"})


Delete
======

To delete a client::

    session.delete_one('Client', '61cd853e44b630d9e10cfb2e')

.. note::

    * Client have to be offline in order for deletion to succeed.
    * If client is serving and root shares, these assignments will also be removed.

