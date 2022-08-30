..
    :copyright: Copyright (c) 2021 accsyn

.. _queues:

******
Queues
******

A queue is an ordered list of jobs with a given priority set. As jobs do not have priorities
by default, they inherit the priority from queue, which enables job management.

A priority is an integer between 0 (lowest) and 1000 (highest), and applies

Query
=====

To list queues::

    all_queues = session.find('Queue')


Create
======

To create a queue::

    queue = session.create("Queue",{
        "code":"high_prio",
        "priority":999
    })


A dict will be returned containing user attributes::

    {
        "id": "61cd853e44b630d9e10cfb2e",
        "code": "high_prio",
        "priority": 999,
        "status": "waiting",
        "default": false,
        "uri": "acmevfx/high_prio",
        "description": "",
        "metadata": {},
        "created": "2021-12-30T11:09:02",
        'user': '5d91b33ac71c12871d1fc3c2',
        'user_hr': 'user:employee@acmevfx.com(employee)',
        "modified": "2021-10-26T08:12:36",
        "modifier": "61bf395c46ed6081a2b2afc0"
    }



Explanation of the returned attributes:

* ``id``: The internal accsyn user id, use this when modifying the queue later on.
* ``code``: The unique name of the queue.
* ``priority``: The priority value, from 0 (lowest) to 1000 (highest).
* ``status``: The status of queue, can be "waiting" (enabled) or "disabled" - all jobs within queue are put on hold.
* ``default``: If default or not, the default queue is were new jobs are put id not explicitly set.
* ``uri``: The URI of queue, used for nested queues.
* ``description``: Description of the queue.
* ``metadata``: Queue metadata dict.
* ``created``: Date of creation.
* ``user``: The ID of user that created the queue.
* ``user_hr``: Human readable user entry.
* ``modified``: Date of last modification.
* ``modifier``: The user that most recently modified the user.


Modify
======

To disable a queue::

    session.update('Queue', '61cd853e44b630d9e10cfb2e', {'status':"disabled"})



Delete
======

To delete a queue::

    session.delete_one('Queue', '61cd853e44b630d9e10cfb2e')

.. note::

    * If you delete a queue, all associated jobs are moved to the
    * Related user home share will also be deleted.
    * accsyn user account information are still preserved, as user could be member of another accsyn domain.