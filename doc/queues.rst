..
    :copyright: Copyright (c) 2021 accsyn

.. _queues:

******
Queues
******

A queue is an ordered list of jobs (transfers, compute jobs, deliveries, requests, streams) with a given priority. Jobs inherit queue priority rather than defining their own, which enables centralised job management. Internally, a queue shares the same entity type as jobs (``job``) and common attributes.

Priority is an integer from 0 (lowest) to 1000 (highest) and determines execution order.

Query
=====

To list queues::

    queues = session.find("Queue")

To list all transfers in a queue::

    queue_transfers = session.find("Transfer WHERE parent=6989982945131d8f16277b71")


Create
======

To create a queue::

    queue = session.create("Queue",{
        "name":"Panic",
        "priority":1000,
        "description":"Queue for panic deliveries superseding high-priority jobs."
    })


A dict is returned containing queue attributes::

    {
        "code": "panic",
        "compute_default": false,
        "created": "2026-02-09T09:17:45+01:00",
        "creator": "demo.admin@accsyn.com",
        "default": false,
        "description": "Queue for panic deliveries superseding high prio jobs.",
        "id": "6989982945131d8f16277b71",
        "metadata": {},
        "modified": "2026-02-09T09:17:45+01:00",
        "modifier": "",
        "name": "Panic",
        "priority": 1000,
        "status": "waiting",
        "uri": "Acme Post"
    }



Explanation of the returned attributes:

* ``code``: Unique API identifier, auto-generated from name if not provided. Must be unique across queues in the workspace.
* ``compute_default``: If ``True``, this is the default queue for compute jobs.
* ``created``: Date of creation.
* ``creator``: User who created the queue. ``accsyn`` means the backend created it.
* ``default``: Whether this is the default queue where new jobs land if not explicitly assigned.
* ``description``: Queue description.
* ``id``: Internal accsyn queue ID. Use this when modifying the queue.
* ``metadata``: Queue metadata dict.
* ``modified``: Date of last modification.
* ``modifier``: User who last modified the queue.
* ``name``: Queue name.
* ``priority``: Priority value, 0 (lowest) to 1000 (highest).
* ``status``: ``waiting`` (enabled) or ``paused`` (disabled). Paused queues put all contained jobs on hold.
* ``uri``: Queue URI for nested queues. Always starts with the default workspace queue named after the workspace.


Modify
======

To disable a queue::

    session.update("Queue", "6989982945131d8f16277b71", {"status" :"paused"})

A dict is returned with the same attributes as a query.

To enable a queue again::

    session.update("Queue", "6989982945131d8f16277b71", {"status" :"waiting"})

A dict is returned with the same attributes as a query.

.. note::

    Additional queue settings are managed through the admin pages: `https://accsyn.io/admin/queues <https://accsyn.io/admin/queues>`_.


Delete
======

To delete a queue::

    session.delete_one("Queue", "6989982945131d8f16277b71")

.. note::

    * Deleting a queue moves associated jobs to the default queue.
    * The default queue cannot be deleted. Assign another queue as default first.
