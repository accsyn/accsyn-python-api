..
    :copyright: Copyright (c) 2022 accsyn

.. _jobs:

****
Jobs
****

An accsyn job is a file transfer :sup:`1` from one point(client) to another, and contains one ore more tasks(files).

.. role:: small

* :sup:`1` :small:`Can also be compute jobs with the Compute feature enabled.`


Query
=====

To list all activate jobs::

    jobs = session.find('Job')

This will return a list all active jobs, as dict objects, session has permission to read. 


A dict will be returned containing job attributes::

    {
        "id": "614d660de50d45bb027c9bdd",
        "code": "latest_edit.mov",
        "uri": "acmevfx/medium",
        "status": "init",
        "created": datetime.datetime(2021, 9, 24, 7, 45, 49),
        "source": "organization:5a4f71ef1da7ee15c5d43ae3",
        "source_hr": "organization:acmevfx",
        "destination": "user:5d91b33ac71c12871d1fc3c2",
        "destination_hr": "user:lars@edit.com(user)",
        "etr": ",
        "metadata": {},
        "parent": "5a4f72111da7ee15c5d43af4",
        "parent_hr": "job:acmevfx/medium(5a4f72111da7ee15c5d43af4)",
        "progress": 0,
        "size": -1,
        "speed": 0.0,
        "user": "5d91b33ac71c12871d1fc3c2",
        "user_hr": "user:employee@acmevfx.com(employee)"
        "finished": datetime.datetime(1970, 1, 1, 1, 0),
        "modified": "2021-10-26T08:12:36",
        "modifier": "61bf395c46ed6081a2b2afc0",
    }


Explaination of the returned attributes:

* ``id``: The internal accsyn job id, use this when modifying the job later on.
* ``code``: The name of the job, if no name supplied a name will be generated from the first source filename.
* ``uri``: The queue location of job, in stripped human readable form.
* ``source``: The sending part, on the form <scope>:<id>.
* ``source_hr``: The sending part, on human readable form.
* ``destination``: The recipient part, on the form <scope>:<id>.
* ``destination_hr``: The recipient part, on human readable form.
* ``etr``: Time left of current transfer, on the form 'Hh{ours}:Mm{inutes}:Ss{econds}'.
* ``metadata``: Job metadata dict.
* ``parent``: The id of the parent job queue.
* ``parent_hr``: The parent job queue on human readable format.
* ``progress``: The job total progress, an integer in the range 0 to 100.
* ``size``: The total size of job, in bytes.
* ``speed``: The current transfer speed, in MB/s.
* ``created``: Date of creation.
* ``user``: The id of the user that created the job.
* ``user_hr``: The user that created the job, on human readable form.
* ``finished``: The date job finished - completed or were aborted.
* ``modified``: Date of last modification.
* ``modifier``: The user that most recently modified the share.

Job statuses
************

Here follow a listing of job statuses:

.. list-table:: accsyn job statuses
   :widths: 20 70 10
   :header-rows: 1

   * - Code:
     - Description:
     - Writeable :sup:`1`:
   * - init
     - Job is newly created and is initialising, total file size is measured.
     -
   * - pending
     - Job is waiting for a destinition to be set, e.g. a download location for
       a sent package. Setting this status on
       an existing job.
     - YES
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
     - Job has failed for some reason, check logs for clues.
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

    job = session.find_one('Job where code="x and y.png"')


.. note::

    If no match for query is found, None will be returned.

    See below for explaination of the returned dict contents.



To pretty print a job and its attribute, use the built in meth:`Session.str` function::

    print(session.str(job))


To list all jobs spawned by a certain user::

    session.find_one('Job where user=user@mail.com')


Or jobs having a certain destination (<user>, <site>)::

    session.find_one('Job where destination="stockholm"')


List all downloads - jobs having main site "hq" (default) as source::

    session.find_one('Job where source=hq')



Inactive jobs
*************

When a job is finished or aborted, it becomes inactive and unloaded from memory after one hour. To retrieve inactive jobs, supply the 'finished' attribute::


    session.find('Job where status=aborted', finished=True)


After two weeks/14 days, inactive jobs are purged and archived. To retrieve jobs from the archive, supply the 'archive' attribute, recall that this operation may take long time to execute::

    session.find('Job where status=done', archived=True)


Create
======

Example of submitting a transfer job, on its simplest form, sending a file from a share to a user::

    job = session.create("Job",{
        "source":"share=projects/thefilm/latest_edit.mov",
        "destination":"lars@edit.com",
        "status":"paused"
    })

If successful, a list of dictionaries is returned on the same form as returned by a query.

.. note::

    For more examples of the accsyn jobmit syntax, see: `https://https://support.accsyn.com/job-specification <https://support.accsyn.com/job-specification>`_.

Modify
======

To pause a job, resume it and abort it::

    session.update('job', '614d660de50d45bb027c9bdd', {'status':"paused"})
    session.update('job', '614d660de50d45bb027c9bdd', {'status':"waiting"})
    session.update('job', '614d660de50d45bb027c9bdd', {'status':"aborted"})

To resend a package - reset destination::

    session.update('job', '614d660de50d45bb027c9bdd', {'status':"pending"})

An additional function is provided to update multiple tasks, within a job::

    session.update_many('task', <job id>, <list of tasks>)


As an example, to exclude a task from a job::

    session.update_many('task', '614d660de50d45bb027c9bdd', [{'id':'b8401ce0-9c6c-4c32-98c6-61d18db01f07', 'status':'excluded'}])



Delete
======


To delete a job::

    session.delete_one('job', '614d660de50d45bb027c9bdd')


Tasks
=====

A task is a file/directory (or a compute item) to execute within a job. Task access through API is restricted, for example
deleting task is not possible neither changing their path. Instead of deleting a task, they can be excluide.

Query tasks
***********

Job tasks are fetched by supplying the job ID query merged with task query::

   session.find('task WHERE job.id=5a7325f8b7ef72f5f9d74bf4')
   session.find('task WHERE job.id=5a7325f8b7ef72f5f9d74bf4 AND status<>executing')

A list if tasks is returned as dictionaries::

    {
        "id": "26468234-c9ee-48d6-8d28-e900b5957129",
        "uri": "0"
        "status": "queued",
        "created": "2020-08-04T09:52:27",
        "source": {
            "client": "5da08873b0eb10fade60b3f7",
            "o": "5a4f71ef1da7ee15c5d43ae3",
            "path": "A001_C011_09187Ia.mov",
            "path_abs_final": "X:\A001_C011_09187Ia.mov",
            "r_s": "5c5bf52a1da7ee0165105b85",
            "slave": true,
            "user": "5d91b33ac71c12871d1fc3c2"
        },
        "destination": {
            "client": "5da09b9ae1b3c330746529ec",
            "master": true,
            "path": "/Users/tommy/Downloads/A001_C011_09187Ia.mov",
            "path_abs_final": "/Users/tommy/Downloads/A001_C011_09187Ia.mov",
            "user": "5d91b33ac71c12871d1fc3c2"
        },
        "priority": 1,
        "size": 128868496,
        "finished": "2020-08-04T10:12:26",
        "time": 110239,
    }

* ``id``: The internal accsyn ID of task.
* ``uri``: The uri - unique name/code of task, usually sequential number "0", "1" and so on (string format).
* ``status``: The status of task, see below. can be "pending"(waiting for user to choose download location),"queued", "booting","executing","failed","done,"onhold","excluded".
* ``created``: The date of task creation.
* ``source``: Dictionary containing information about the source file/directory (or compute client)
* ``destination``: (File transfers only) Dictionary containing information about the destination file/directory.
* ``priority``: The task priority, see job priority.
* ``size``: The size of source file/directory.
* ``finished``: The date task finished execution.
* ``time``: The time it took the execute this task.

.. note::

    * The contents of ``source`` and ``destination`` varies depending on sender and receiver - site(Server) or user(Desktop app/User server)
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

   session.create("task", {"tasks":["/Volumes/projects/creatures_showreel_2018.mov"]}, job["id"]))

Returns {"success":True} if everything goes well, exception thrown otherwise. If another task exists with the same source and destination,
no task will be added and instead the existing task will be retried. To have Accsyn reject duplicate tasks,
supply attribute allow_duplicates=False to create call.

.. note::

    tasks without destination can only be created for jobs sending files with mirrored paths.

Add with new destination path::

    session.create("task", {
        "tasks":[
            {
                "source":"share=projects/_REF/creatures_showreel_2018.mov",
                "destination":"share=projects/TMP/creatures_showreel_2018_tmp.mov"
            }
        ]
    }, job["id"])

.. note::

    * Only users themselves own the right to add files from/to their local harddrive/storage for upload/download.
    * Pending files (tasks without destination path:s) can not be added to a job that remote user already have started downloading.
    * Operation will fail if another task exists with same source and destination path
    * Ongoing executing tasks will not be interrupted when new tasks are added, to


Modifying tasks
***************

Only the ``status``, ``priority`` or ``metadata`` of a task can be modified.

Tasks are always updated in group with values supplied as a list of dicts instead of a single dict::

    job = session.find('job WHERE code="my_transfer"')

    updated_job = session.update_many("task", [{

        "id":"cc5f2afa-9ae4-46e0-9273-82ac802b20ff",

        "status":"onhold"

    }], entityid=job["id"])

Will return the updated tasks, as would have been returned by a task find query.


Delete task
***********

Tasks cannot be deleted, of audit/security reasons. Set task status to excluded instead to have it ignored during transfer/execution.

