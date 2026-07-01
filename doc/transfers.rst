..
    :copyright: Copyright (c) 2026 accsyn

.. _transfers:

**************
File Transfers
**************

An accsyn file transfer job :sup:`1` defines a set of files and folders — tasks — to synchronise from one endpoint (client) to another using the ASC protocol or HTTPS (web transfer).

.. role:: small

:sup:`1` :small:`Job is a base entity in accsyn, covering transfers, deliveries, streams, compute jobs, and queues.`


Query
=====

To list all active transfers::

    transfers = session.find('Transfer')

This returns a list of active file transfer jobs, as dict objects, that the session has permission to read.


A dict is returned containing transfer job attributes::

    {
        "code": "README.txt",
        "created": "2026-01-22T08:35:59",
        "destination": "user:6676f3e9c7ef4e27da254e57",
        "destination_hr": "user:lisa@example.com[standard](6676f3e9c7ef4e27da254e57)",
        "etr": "",
        "finished": "2026-01-22T08:43:05",
        "id": "6971e16fceadd67b955b1995",
        "name": "README.txt",
        "progress": 0,
        "size": 0,
        "source": "workspace:6645fbca9f8c4d3e7a3b678d",
        "source_hr": "workspace:seagull(6645fbca9f8c4d3e7a3b678d)",
        "speed": -1.0,
        "status": "aborted",
        "user": "6676f3e9c7ef4e27da254e57",
        "user_hr": "user:lisa@example.com[standard](6676f3e9c7ef4e27da254e57)"
    }


Explanation of the returned attributes:

* ``code``: Same as ``name``. Transfers and jobs in general do not have unique API identifiers, and can only be uniquely identified by their ID.
* ``created``: Date of creation.
* ``destination``: The recipient, in the form ``<entitytype>:<id>``.
* ``destination_hr``: The recipient, in human-readable form.
* ``etr``: (Running transfers) Estimated time remaining.
* ``finished``: The date the job finished — completed or aborted.
* ``id``: The internal accsyn job ID. Use this when modifying the job later on.
* ``name``: The name of the job (identical to code). If no name is supplied, one is generated from the first source filename.
* ``progress``: The job total progress, an integer in the range 0 to 100.
* ``size``: The total size of job, in bytes.
* ``source``: The sender, in the form ``<entitytype>:<id>``.
* ``source_hr``: The sender, in human-readable form.
* ``speed``: The current transfer speed, in MB/s.
* ``status``: The job status.
* ``uri``: The job URI within queues, built from parent queue code attributes.
* ``metadata``: Job metadata dict, used to pass user data through workflows.
* ``parent``: The ID of the parent job queue.
* ``parent_hr``: The parent job queue, in human-readable form.
* ``user``: The ID of the user who created the job.
* ``user_hr``: The user who created the job, in human-readable form.
* ``modified``: Date of last modification.
* ``modifier``: The user who most recently modified the job.


Job statuses
************

Transfer job statuses:

.. list-table:: accsyn transfer job statuses
   :widths: 20 70 10
   :header-rows: 1

   * - Code:
     - Description:
     - Writable :sup:`1`:
   * - init
     - Job is newly created and is initialising, total file size is measured.
     -
   * - waiting
     - Job is blocked and waiting for resources to become available,
       for example jobs ahead in the queue, or a server/client coming online
       or being enabled.
     - YES
   * - running
     - Job is working, files are being transferred or compute tasks are executed.
     -
   * - paused
     - Job is put on hold.
     - YES
   * - failed
     - Job has failed and may retry automatically later. Check logs for details.
     -
   * - aborted
     - Job has been aborted.
     - YES
   * - done
     - Job has executed all tasks.
     - YES

.. role:: small

* :sup:`1` This status can be set with a modify call (see below)


Job queries
***********

Retrieve a job by name (code), using quotation marks for whitespace in the query::

    transfer = session.find_one('Transfer WHERE name="x and y.png"')


.. note::

    If no match is found, ``None`` is returned.

    Multiple jobs can share the same name — ensure names are unique or query by ID.



To pretty-print a job and its attributes, use :meth:`Session.dump`::

    print(session.dump(transfer))


To list all jobs spawned by a specific user::

    session.find('Transfer WHERE user=user@mail.com')


Or jobs with a specific destination (``<user>`` or ``<site>``)::

    session.find_one('Transfer WHERE destination=stockholm')


List downloads where the main site ``hq`` (default main site code) is the source::

    session.find_one('Transfer WHERE source=hq')



Finished transfers
******************

When a transfer is finished or aborted, it is no longer live and is not returned by standard queries. This improves query performance and reduces clutter.
To retrieve finished jobs, pass the ``finished`` attribute::


    session.find('Transfer WHERE status=aborted', finished=True)


After the default retention period of two weeks (14 days), inactive jobs are purged and archived. To retrieve jobs from the archive,
pass the ``archived`` attribute. This operation may take a long time to execute::

    session.find('Transfer WHERE status=done', archived=True)

To return a single job, regardless of whether it is finished or archived, use :meth:`Session.get_entity`::

    transfer = session.get_entity("Transfer", transfer_id)

The :meth:`Session.find_one` function also considers finished or archived jobs::

    transfer = session.find_one('Transfer WHERE id=614d660de50d45bb027c9bdd')


Create
======

When creating a file transfer, specify the source and destination, including the sending and receiving endpoints and full paths.

Example: submit a transfer where a user downloads a file from a shared folder to their local machine::

    transfer = session.create("Transfer",{
        "source":"share=myproject/delivery/TRAILER_screening_v003.mov",
        "destination":"/Volumes/EDIT/from_client"
    })

If successful, transfer job data is returned in the same form as a query.


Source and destination notation
********************************

An accsyn source/destination is a combination of a party and a path similar to standard rsync and scp notation, using this template::
  
    <party definition>:<accsyn path|absolute path>

If a party is not specified, accsyn attempts to resolve the party from the path. In the example above, accsyn resolves the source party as the workspace because accsyn path notation is used. 
The destination is specified as an absolute path and no party is specified, so it is resolved as the invoking user party.


Party resolution
****************

The following parties are supported:

* ``<workspace code|ID>``: The explicit accsyn workspace party — the main(default) site and server. For example: ``myworkspace:<accsyn path>``, where ``myworkspace`` is the unique API code/domain of the workspace.
* ``<user email|ID>``: An accsyn user party. For example: ``emma@example.com:/path/to/file``, where ``emma@example.com`` is the user's email address.
* ``<site=site code|ID>``: A site party — a site server. For example: ``site=my_site:<accsyn path>``, where ``my_site`` is the unique API code/domain of the site.
* ``<client=client id>``: A client party — a desktop app or user server. For example: ``client=664f53b16aa9149860da9d9c:/path/to/file``, where ``664f53b16aa9149860da9d9c`` is the unique client ID. Code (hostname) can also be used instead of the ID, but may be ambiguous.

.. note::

  The workspace party is technically the same as the main site party. By default the main site API code is ``hq``, meaning that "myworkspace:..." notation is the same as "site=hq:..." notation.


The accsyn path notation
************************

accsyn path notation points to a file or directory on a share, so callers can use the relative path to the share instead of the full absolute path.

When targeting a file on accsyn storage cloud/hq or a site, use accsyn path notation.

.. note::

  accsyn can still interpret absolute paths, such as paths defined for a volume, but accsyn path notation is recommended for clarity and consistency.

An accsyn path is defined by this pattern::

  <share_type>=<share_code_or_entityid>/<relative_path>

Share types:

* ``volume``: An accsyn volume — the base folder on a server exposed to accsyn and addressable by admins and employees with explicit access.
* ``folder``: A shared folder beneath a volume, intended to be shared with standard users.
* ``collection``: A set of arbitrary files and/or folders intended to be shared with standard users.
* ``home``: A home folder — a shared folder dedicated to be a user's personal workspace.
* ``share``: A generic entity type identifier for ``volume``, ``folder`` (shared folder), ``collection``, or ``home``.

Mirror path concept
*******************

When an accsyn path is used as the source, and the destination has the volume and/or share defined, mirror paths can be configured for the whole job or for individual tasks.

With mirror paths, the full destination path is not required. accsyn resolves it at runtime from the source path and mirror path.
For example, the file can be written to the same folder as the source file, preserving the folder structure.

If no destination path is defined, mirror paths are assumed and enabled by default.

Mirror path example: synchronise a project folder to a backup site, deleting destination files that do not exist at the source::

    transfer = session.create("Transfer",{
        "source":"PROJECTS/PRJ054",
        "destination":"site=backup",
        "settings":{"transfer_mode":"onewaysync"}
    })

Some observations on the example:

* Mirror paths are ideal for backup jobs where the folder structure should be preserved.
* Relaxed source definition — the default volume is assumed and the source path is relative to that volume.
* Relaxed destination definition — a site is the destination. Because the volume is mapped, mirror paths can be applied.
* For more information on what settings are available, see: `https://support.accsyn.com/settings <https://support.accsyn.com/settings>`_.

In general, files cannot be transferred to a user with mirrored paths. However, users can configure local share mappings,
which allows accsyn path notation when transferring files to and from a user (client).
Combined with a user server setup, this enables unattended 24/7 push and pull of files to and from a remote user endpoint.

User mirror path example: synchronise a project folder to a user (user server or online desktop app instance)::

    transfer = session.create("Transfer",{
        "source":"share=prj054/ASSETS/LidarScans_260629",
        "destination":"emma@example.com"
    })

The transfer is submitted if Emma has mapped the share ``prj054`` on a machine, and the invoking user has write access.

For more information on how to configure local share mappings, see: `https://support.accsyn.com/admin/hosts <https://support.accsyn.com/admin/hosts>`_.

Client resolution
*****************

When accsyn has a valid party and path, it resolves the most suitable client to use as the transfer source or destination:

* Workspace parties (cloud/hq or site); there is no ambiguity about which client to use, as only one server can serve a volume and its shared folders/files on a site.
* User parties; the most recently online client is used unless an explicit client is specified.


.. note::

  Clients are resolved at submit time. If a client goes offline after submit and another client comes online,
  the transfer remains bound to the client resolved at submit time. Submit a new job to use the new client.

accsyn paths, on the other hand, are resolved at runtime and the absolute final path is stored in the task. 
his allows dynamic path resolvers to be applied, such as the user's home folder or preferred download location as configured on the host or by locally mapped shares.


Further job specification examples
**********************************

For a complete set of job submit examples, see: `https://support.accsyn.com/job-specification <https://support.accsyn.com/job-specification>`_.


Modify
======

To resume or abort a transfer::

    session.update("Transfer", '614d660de50d45bb027c9bdd', {'status':"waiting"})
    session.update("Transfer", '614d660de50d45bb027c9bdd', {'status':"aborted"})



Delete
======


To purge a transfer from accsyn::

    session.delete_one("Transfer", "614d660de50d45bb027c9bdd")



Tasks
=====

A task is a file or directory to transfer within a Transfer job, or a compute task to execute on a farm server.

Task access through the API is restricted — for example, deleting tasks or changing their paths is not supported. To skip a task, set its status to ``excluded``.

Query tasks
***********

Job tasks are a sub-entity of a job, not a standalone accsyn entity. To query tasks, supply the parent job ID separately from the query::

    tasks = session.find("Task", entityid="5a7325f8b7ef72f5f9d74bf4")

Find all tasks that have a certain status::

    tasks = session.find("Task WHERE status=onhold", entityid="5a7325f8b7ef72f5f9d74bf4")

A list of tasks is returned as dictionaries::

    {
        "created": "2020-08-04T09:52:27",
        "destination": {
            "client": "5da09b9ae1b3c330746529ec",
            "path": "/Users/tommy/Downloads/A001_C011_09187Ia.mov",
            "path_abs_final": "/Users/tommy/Downloads/A001_C011_09187Ia.mov",
            "user": "5d91b33ac71c12871d1fc3c2"
        },
        "finished": "2020-08-04T10:12:26",
        "id": "26468234-c9ee-48d6-8d28-e900b5957129",
        "job": "69732302fd379c8fff1089d0",
        "job_hr": "README.txt[7](6971e16fceadd67b955b1995)",
        "priority": 1,
        "size": 128868496,
        "source": {
            "client": "5da08873b0eb10fade60b3f7",
            "path": "A001_C011_09187Ia.mov",
            "path_abs_final": "X:\A001_C011_09187Ia.mov",
            "volume": "5c5bf52a1da7ee0165105b85",
            "user": "5d91b33ac71c12871d1fc3c2"
        },
        "status": "queued",
        "time": 110239,
        "uri": "0",
    }

* ``created``: The date of task creation.
* ``destination``: Dictionary containing information about the destination file/directory.
* ``finished``: The date the task finished execution.
* ``id``: The internal accsyn task ID.
* ``job``: The ID of the parent job.
* ``job_hr``: The parent job, in human-readable form.
* ``priority``: Task priority; see job priority.
* ``size``: The size of the source file/directory.
* ``source``: Dictionary containing information about the source file/directory (or compute client).
* ``status``: Task status (see below). Values include ``pending`` (waiting for user to choose download location), ``queued``, ``booting``, ``executing``, ``failed``, ``done``, ``onhold``, and ``excluded``.
* ``time``: Time taken to execute this task.
* ``uri``: The task URI — a unique name/code, usually a sequential number (``"0"``, ``"1"``, etc.) in string format.

The contents of ``source`` and ``destination`` vary depending on whether the party is a site (server) or user (desktop app/user server):

* ``client``: The ID of the client.
* ``path``: The file path, either absolute if no share is involved or relative to the share (folder, collection, volume, etc.).
* ``path_abs_final``: The final evaluated path when a share is involved. Set at transfer execution, as clients may apply dynamic path resolvers at runtime.
* ``volume``: ID of the volume.
* ``share``: ID of the share, if a share is involved.
* ``user``: ID of the user, if party is a user.
* ``site``: ID of the site, if party is a site.

.. note::

    * If no user or site is involved, the party is the workspace main site and server (hq).
    * ``source`` and ``destination`` cannot be modified.
    * ``time`` is the time to execute the entire bucket (group) of tasks as dispatched, not the individual task.


.. list-table:: accsyn task statuses
   :widths: 20 70 10
   :header-rows: 1

   * - Code:
     - Description:
     - Writable :sup:`1`:
   * - pending
     - Task (job) is newly created and waiting for the receiving user to select a
       download path.
     -
   * - queued
     - Task is waiting to be dispatched.
     - YES
   * - booting
     - Task transfer/execution is being initialised on involved parties.
     -
   * - executing
     - File/directory is being transferred or the task is being executed (compute).
     -
   * - failed
     - The task has failed. Check the job log and/or task log for
       clues.
     - YES
   * - onhold
     - Task is on hold.
     - YES
   * - excluded
     - Task is excluded from execution.
     - YES
   * - done
     - File/directory has been transferred, or the compute task has executed successfully.
     - YES

.. role:: small

* :sup:`1` This status can be set with a modify call (see below)


Create tasks
************

Add a file (task) to an existing job, with the same source and destination party as the rest of the job::

    session.create("Task", {"tasks":["/Volumes/projects/creatures_showreel_2018.mov"]}, entityid=job["id"])

Returns ``{"success": True}`` on success; otherwise an exception is raised. If another task exists with the same source and destination,
no task is added and the existing task is retried instead. To reject duplicate tasks, pass ``allow_duplicates=False`` to the create call.

.. note::

    Tasks without a destination can only be created on jobs that send files with mirrored paths.

Add a single task to a download job::

    session.create("Task", {
      "tasks":{
        "source":"_REF/creatures_showreel_2018.mov",
        "destination":"/Users/johndoe/Downloads/creatures_showreel_2018.mov"
      }
    }, entityid=transfer["id"])

The single task is returned as a dictionary with task ID, status, and other attributes. If adding
multiple tasks, a list of tasks is returned.

.. note::

    * Only users themselves can add files from/to their local hard drive/storage for upload/download, unless targeting a locally mapped share that has been granted access by the user.
    * The operation fails if another task exists with the same source and destination path.
    * Currently executing tasks are not interrupted when new tasks are added.


Modifying tasks
***************

Only the ``status``, ``priority``, or ``metadata`` attributes of a task can currently be modified.

Tasks are always updated in groups, with values supplied as a list of dicts instead of a single dict::

    transfer = session.find('Transfer where id=5a7325f8b7ef72f5f9d74bf4')

    updated_tasks = session.update_many("Task", transfer["id"], [{
        "id":"cc5f2afa-9ae4-46e0-9273-82ac802b20ff",
        "status":"onhold"
    }])

Returns the updated tasks in the same form as a task find query.


Delete task
***********

Tasks cannot be deleted for audit and security reasons. Set task status to ``excluded`` to skip it during transfer/execution.

