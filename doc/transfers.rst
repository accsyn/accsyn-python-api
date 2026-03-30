..
    :copyright: Copyright (c) 2026 accsyn

.. _transfers:

**************
File Transfers
**************

An accsyn file transfer job :sup:`1` defines a set of file(s) and/or folder(s) to be transferred from one point(client) to another, either ny the ASC protocol or HTTPS (web transfer).

.. role:: small

:sup:`1` :small:`Job is a generic term within accsyn, covering transfers, deliveries, compute, etc.`


Query
=====

To list all activate transfers::

    transfers = session.find('Transfer')

This will return a list all active file transfer jobs, as dict objects, session has permission to read. 


A dict will be returned containing transfer job attributes::

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


Explaination of the returned attributes:

* ``code``: Same as name, transfers and jobs in general do not have unique API identifiers.
* ``created``: Date of creation.
* ``destination``: The recipient part, on the form <entitytype>:<id>.
* ``destination_hr``: The recipient part, on human readable form.
* ``etr``: (Running transfers) Estimated time remaining.
* ``finished``: The date job finished - completed or were aborted.
* ``id``: The internal accsyn job id, use this when modifying the job later on.
* ``name``; The name of the job, if no name supplied a name will be generated from the first source filename. 
* ``progress``: The job total progress, an integer in the range 0 to 100.
* ``size``: The total size of job, in bytes.
* ``source``: The sending part, on the form <entitytype>:<id>.
* ``source_hr``: The sending part, on human readable form.
* ``speed``: The current transfer speed, in MB/s.
* ``status``: The status of job.
* ``uri``: The of job within queues, build up with parent queue code attributes.
* ``metadata``: Job metadata dict, used to pass user data through workflows.
* ``parent``: The id of the parent job queue.
* ``parent_hr``: The parent job queue on human readable format.
* ``user``: The id of the user that created the job.
* ``user_hr``: The user that created the job, on human readable form.
* ``modified``: Date of last modification.
* ``modifier``: The user that most recently modified the job.


Job statuses
************

Here follow a listing of transfer job statuses:

.. list-table:: accsyn transfer job statuses
   :widths: 20 70 10
   :header-rows: 1

   * - Code:
     - Description:
     - Writeable :sup:`1`:
   * - init
     - Job is newly created and is initialising, total file size is measured.
     -
   * - waiting
     - Job is blocked and waiting for resources to become available,
       for example jobs ahead in queue or a server/client coming online /
       getting enabled.
     - YES
   * - running
     - Job is working, files are being transferred or compute tasks are executed.
     -
   * - paused
     - Job is put on hold.
     - YES
   * - failed
     - Job has failed for some reason and might retry automatically at a later point, check logs for clues.
     -
   * - aborted
     - Job has been aborted.
     - YES
   * - done
     - Job is done executing all its tasks.
     - YES

.. role:: small

* :sup:`1` This status can be set with a modify call (see below)


Job queries
***********

Retreive a job by it's name (code), using quation marks to support whitespaces in query::

    transfer = session.find_one('Transfer WHERE name="x and y.png"')


.. note::

    If no match for query is found, None will be returned.

    Multiple jobs can have the same name, either make sure job names are unique of query by unique ID.



To pretty print a job and its attribute, use the built in meth:`Session.str` function::

    print(session.dump(transfer))


To list all jobs spawned by a certain user::

    session.find_one('Transfer WHERE user=user@mail.com')


Or jobs having a certain destination (<user>, <site>)::

    session.find_one('Transfer WHERE destination=stockholm')


List all downloads - jobs having main site "hq" (default code) as source::

    session.find_one('Transfer WHERE source=hq')



Finished transfers
******************

When a transfer is finished or aborted, it is not live anymore and will not be returned by standard queries. 
To retrieve finished jobs, supply the 'finished' attribute::


    session.find('Transfer WHERE status=aborted', finished=True)


After default two weeks/14 days, inactive jobs are purged and archived. To retrieve jobs from the archive, 
supply the 'archived' attribute, recall that this operation may take long time to execute::

    session.find('Transfer WHERE status=done', archived=True)

To return a single job, regardless if it is finished or archived, use the get_entity function::

    transfer = session.get_entity("Transfer", transfer_id)


Create
======

When creating a file transfer, the source and destination must be specified with full paths.

Example of submitting a transfer job, on its simplest form, were a user downloads a file from a shared folder to their local computer::

    transfer = session.create("Transfer",{
        "source":"share=myproject/delivery/TRAILER_screening_v003.mov",
        "destination":"/Volumes/EDIT/from_client",
        "status":"paused"
    })

If successful, a list with transfer job data is returned on the same form as returned by a query.

.. note::

    The term "share" is a generic identifier for the following entities: "volume", "folder" (shared folder), "collection" or "home". 
    
    This example assumes the user only have one online accsyn client (desktop app or user server), if the user has multiple clients they
    would need to specify which one, e.g.: "destination":"client=664f53b16aa9149860da9d9c:/Volumes/EDIT/from_client".

For a complete set of job submit examples, see: `https://support.accsyn.com/job-specification <https://support.accsyn.com/job-specification>`_.


Modify
======

To resume a transfer and how to abort it::

    session.update("Transfer", '614d660de50d45bb027c9bdd', {'status':"waiting"})
    session.update("Transfer", '614d660de50d45bb027c9bdd', {'status':"aborted"})



Delete
======


To delete a Transfer::

    session.delete_one("Transfer", "614d660de50d45bb027c9bdd")



Tasks
=====

A task is a file/directory to execute within a job. Task access through API is restricted, for example
deleting task is not possible neither changing their path. Instead of deleting a task, they can be excluded.

Query tasks
***********

Job tasks are a sub entity of job, and not a true accsyn entity. To query tasks, supply the parent job ID separately from query::

    tasks = session.find("Task", entityid="5a7325f8b7ef72f5f9d74bf4")

Find all tasks that have a certain status::

    tasks = session.find("Task WHERE status=onhold", entityid="5a7325f8b7ef72f5f9d74bf4")

A list if tasks is returned as dictionaries::

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
            "v": "5c5bf52a1da7ee0165105b85",
            "user": "5d91b33ac71c12871d1fc3c2"
        },
        "status": "queued",
        "time": 110239,
        "uri": "0",
    }

* ``created``: The date of task creation.
* ``destination``: Dictionary containing information about the destination file/directory party.
* ``finished``: The date task finished execution.
* ``id``: The internal accsyn ID of task.
* ``job``: The ID of the parent job.
* ``job_hr``: The parent job on human readable form.
* ``priority``: The task priority, see job priority.
* ``size``: The size of source file/directory.
* ``source``: Dictionary containing information about the source file/directory (or compute client) party.
* ``status``: The status of task, see below. can be "pending"(waiting for user to choose download location),"queued", "booting","executing","failed","done,"onhold","excluded".
* ``time``: The time it took the execute this task.
* ``uri``: The uri - unique name/code of task, usually sequential number "0", "1" and so on (string format).

The contents of ``source`` and ``destination`` parties varies depending on sender and receiver - site(Server) or user(Desktop app/User server):

* ``client``: The ID of the client.
* ``path``: The file path, either absolute if no share is involved or relative share (folder, collection, volume etc.)
* ``path_abs_final``: The final evaluated path, when a share is involved. This is set on transfer execution, as client might have dynamic path resolvers that apply in runtime.
* ``v``: ID of the volume.
* ``s``: ID of the share, if a share is involved.
* ``user``: ID of the user, if party is a user.
* ``site``: ID of the site, if party is a site.

.. note::

    * If no user or site is involved, the party is the workspace main site and server (hq).
    * ``source`` and ``destination`` cannot be modified.
    * ``time`` is the time it took to execute the entire bucket (group) of task as dispatched, not the individual time for the single task.


.. list-table:: accsyn task statuses
   :widths: 20 70 10
   :header-rows: 1

   * - Code:
     - Description:
     - Writeable :sup:`1`:
   * - pending
     - Task(job) is newly created and waiting for receiving user to select a
       download path.
     -
   * - queued
     - Task is waiting to be dispatched.
     - YES
   * - booting
     - Task transfer/execution is being initialized on involved parties.
     -
   * - executing
     - File/directory is being transferred or task is being executed(compute)
     -
   * - failed
     - The task has failed for some reason, check job log and/or task log for
       clues.
     - YES
   * - onhold
     - Task if put on hold.
     - YES
   * - excluded
     - Task is excluded from execution.
     - YES
   * - done
     - File/directory has successfully been transfered / compute task has
       successfully executed.
     - YES

.. role:: small

* :sup:`1` This status can be set with a modify call (see below)


Create tasks
************

Add a file(task) to an existing job, mirroring paths to same destination as rest of job::

   session.create("Task", {"tasks":["/Volumes/projects/creatures_showreel_2018.mov"]}, job["id"]))

Returns {"success":True} if everything goes well, exception thrown otherwise. If another task exists with the same source and destination,
no task will be added and instead the existing task will be retried. To have Accsyn reject duplicate tasks,
supply attribute allow_duplicates=False to create call.

.. note::

    Tasks without no destination provided can only be created with jobs sending files with mirrored paths.

Add a single task to a download job::

    session.create("Task", {
      "tasks":{
        "source":"_REF/creatures_showreel_2018.mov",
        "destination":"/Users/johndoe/Downloads/creatures_showreel_2018.mov"
      }
    }, entityid=transfer["id"])

The single task will be returned as a dictionary, providing task ID, status and other attributes. If adding
multiple tasks, a list of tasks will be returned.

.. note::

    * Only users themselves own the right to add files from/to their local harddrive/storage for upload/download.
    * Operation will fail if another task exists with same source and destination path
    * Ongoing executing tasks will not be interrupted when new tasks are added.


Modifying tasks
***************

Only the ``status``, ``priority`` or ``metadata`` attributes of a task can currently be modified.

Tasks are always updated in group with values supplied as a list of dicts instead of a single dict::

    transfer = session.find('Transfer where id=5a7325f8b7ef72f5f9d74bf4')

    updated_tasks = session.update_many("Task", transfer["id"], [{
        "id":"cc5f2afa-9ae4-46e0-9273-82ac802b20ff",
        "status":"onhold"
    }])

Will return the updated tasks, as would have been returned by a task find query.


Delete task
***********

Tasks cannot be deleted, of audit/security reasons. Set task status to excluded instead to have it ignored during transfer/execution.

