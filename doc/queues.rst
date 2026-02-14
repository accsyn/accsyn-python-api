..
    :copyright: Copyright (c) 2021 accsyn

.. _queues:

******
Queues
******

A queue is an ordered list of jobs (transfers, compute jobs, deliveries, requests, streams) with a given priority set. As jobs do not have priorities
, they inherit the priority from queue, which enables job management. Internally in accsyn, a queue is of same entity type as jobs ("job") and share common attributes.

A priority is an integer between 0 (lowest) and 1000 (highest), and decidees which jobs are executed first.

Query
=====

To list queues::

    queues = session.find("Queue")

To list all transfers in a queue::

    queue_transfers = session.find("Transfer where parent=6989982945131d8f16277b71")


Create
======

To create a queue::

    queue = session.create("Queue",{
        "name":"Panic",
        "priority":1000,
        "description":"Queue for panic deliveries superseeding high prio jobs."
    })


A dict will be returned containing queue attributes::

    {
        "code": "panic",
        "compute_default": false,
        "created": "2026-02-09T09:17:45+01:00",
        "creator": "demo.admin@accsyn.com",
        "default": false,
        "description": "Queue for panic deliveries superseeding high prio jobs.",
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

* ``code``: The unique API identifier of the queue, is auto generated from name if not provided. Can be used when referring to the queue in API calls, must be unique across all queues in the workspace.
* ``compute_default``: If True, this queue will be the default queue for compute jobs.
* ``created``: Date of creation.
* ``creator``: The user who created the queue, 'accsyn' means it is created by the backend.
* ``default``: If default or not, the default queue is were new jobs are put id not explicitly set.
* ``description``: Description of the queue.
* ``id``: The internal accsyn user id, use this when modifying the queue later on.
* ``metadata``: Queue metadata dict.
* ``modified``: Date of last modification.
* ``modifier``: The user that most recently modified the queue.
* ``name``: The name of the queue.
* ``priority``: The priority value, from 0 (lowest) to 1000 (highest).
* ``status``: The status of queue, can be "waiting" (enabled) or "paused" (disabled) - all jobs within queue are put on hold.
* ``uri``: The URI of queue, used for nested queues. Always starts with the default workspace queue having the same name as the workspace.


Modify
======

To disable a queue::

    session.update("Queue", "6989982945131d8f16277b71", {"status" :"paused"})

A dict will be returned containing same attributes as when queried.

To enable a queue again::

    session.update("Queue", "6989982945131d8f16277b71", {"status" :"waiting"})

A dict will be returned containing same attributes as when queried.

.. note::

    Queue settings has to be modified throught the admin pages `https://accsyn.io/admin/queues <https://accsyn.io/admin/queues>`_.


Delete
======

To delete a queue::

    session.delete_one("Queue", "6989982945131d8f16277b71")

.. note::

    * If you delete a queue, all associated jobs are moved to the default queue.
    * The default queue cannot be deleted, assign another queue as default before deleting.