..
    :copyright: Copyright (c) 2021 accsyn

.. _jobs:

****
Jobs
****

An accsyn job is a file transfer:sup:`1` from one point(client) to another, and contains one ore more tasks(files).


Query
=====


The find and find_one functions provide query functionality within the API.


To list all activate jobs::

    jobs = session.find('Job')

This will return a list all active jobs, as dict objects, session has permission to read. 


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


Expressions
***********

The accsyn query syntax is not as evolved as for example SQL. The accsyn API currently support nested AND/OR operations using the = or !=/<>. An example of a query in its most complex form::

    session.find('job WHERE (user=5bfeb0381da7ee4095fa217e AND source=hq) OR status<>failed')


Limit
*****

To return only a limited set of attributes::

    session.find_one('Job where id=614d660de50d45bb027c9bdd', attributes=['source','destination'])


To run a paginated query, that skips 100 jobs and only returns a maximum of 50::

    session.find('Job', skip=100, limit=50)




Inactive jobs
*************

When a job is finished or aborted, it becomes inactive and unloaded from memory after one hour. To retrieve inactive jobs, supply the 'finished' attribute::


    session.find('Job where status=aborted', finished=True)


After two weeks/14 days, inactive jobs are purged and archived. To retreive jobs from the archive, supply the 'archive' attribute, recall that this operation may take long time to execute::

    session.find('Job where status=done', archive=True)

.. role:: small

* :sup:`1` :small:`Can also be compute jobs with the Compute feature enabled.`





Create
======


To create any entity, supply the scope and the data as a dict payload on this generic form::

    session.create('<entity>', <payload as dict>)


Example of creating a transfer job, on its simplest form, sending a file from a share to a user::

    job = session.create("job",{
        "source":"share=projects/thefilm/latest_edit.mov",
        "destination":"lars@edit.com",
        "status":"paused"
    })


A dict will be returned containing job attributes::

    {
        'id': '614d660de50d45bb027c9bdd', 
        'code': 'latest_edit.mov', 
        'uri': 'acmevfx/medium', 
        'status': 'init', 
        'created': datetime.datetime(2021, 9, 24, 7, 45, 49), 
        'source': 'organization:5a4f71ef1da7ee15c5d43ae3', 
        'source_hr': 'organization:acmevfx', 
        'destination': 'user:5d91b33ac71c12871d1fc3c2', 
        'destination_hr': 'user:lars@edit.com(user)', 
        'etr': '', 
        'metadata': {}, 
        'parent': '5a4f72111da7ee15c5d43af4', 
        'parent_hr': 'job:acmevfx/medium(5a4f72111da7ee15c5d43af4)', 
        'progress': 0, 
        'size': -1, 
        'speed': 0.0, 
        'user': '5d91b33ac71c12871d1fc3c2', 
        'user_hr': 'user:employee@acmevfx.com(employee)'
        'finished': datetime.datetime(1970, 1, 1, 1, 0), 
    }


Explaination of the returned attributes:

* id; The internal accsyn job id, use this when modifying the job later on.
* code; The name of the job, if no name supplied a name will be generated from the first source filename.
* uri; The queue location of job, in stripped human readable form.
* source; The sending part, on the form <scope>:<id>.
* source_hr; The sending part, on human readable form.
* destination; The recipient part, on the form <scope>:<id>.
* destination_hr; The recipient part, on human readable form.
* etr; Time left of current transfer, on the form 'Hh{ours}:Mm{inutes}:Ss{econds}'.
* metadata; Job metadata dict.
* parent; The id of the parent job queue.
* parent_hr; The parent job queue on human readable format.
* progress; The job total progress, an integer in the range 0 to 100.
* size; The total size of job, in bytes.
* speed; The current transfer speed, in MB/s.
* created; Date of creation.
* user; The id of the user that created the job.
* user_hr; The user that created the job, on human readable form.
* finished; The date job finished - completed or were aborted.


Job statuses
************

Here follow a listing of job statuses:

.. list-table:: accsyn job statuses
   :widths: 20 80
   :header-rows: 1

   * - Code:
     - Description:
   * - init
     - Job is newly created and is initialising, total file size is measured.
   * - pending
     - Job is waiting for a destinition to be set, e.g. a download location for a sent package.
   * - waiting
     - Job is blocked and waiting for resources to become available, 
       for example jobs ahead in queue or a server/client coming online / getting enabled.
   * - running
     - Job is working, files are being transferred or compute tasks are executed.
   * - paused
     - Job is put on hold.
   * - failed
     - Job has failed for some reason, check logs for clues.
   * - aborted
     - Job has been aborted.
   * - done
     - Job is done executing all its tasks.

Modify
======


To modify an entity, supply the scope, id and data payload::

    session.update_one(<scope>, <id>, <data>)


To pause a job, resume it and abort it::

    session.update_one('job', '614d660de50d45bb027c9bdd', {'status':"paused"})
    session.update_one('job', '614d660de50d45bb027c9bdd', {'status':"waiting"})
    session.update_one('job', '614d660de50d45bb027c9bdd', {'status':"aborted"})

To resend a package - reset destination::

    session.update_one('job', '614d660de50d45bb027c9bdd', {'status':"pending"})

An additional function is provided to update multiple tasks, within a job::

    session.update_many('task', <job id>, <list of tasks>)


As an example, to exclude a task from a job::

    session.update_many('task', '614d660de50d45bb027c9bdd', [{'id':'b8401ce0-9c6c-4c32-98c6-61d18db01f07', 'status':'excluded'}])



Delete
======

To delete an entity, supply the scope and id::

    session.delete_one(<scope>, <id>)


To delete a job::

    session.delete_one('job', '614d660de50d45bb027c9bdd')


