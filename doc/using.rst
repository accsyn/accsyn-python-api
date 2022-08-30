..
    :copyright: Copyright (c) 2021 accsyn

.. _using:


.. currentmodule:: accsyn_api.session

***************************
Using the accsyn Python API
***************************

.. highlight:: python

In a Python session, import the accsyn Python API to start using it::

    import accsyn_api


Create a session
================

The session is the Python object used when communicating with accsyn, it requires valid credentials supplied::

    session = accsyn_api.Session(domain='acmefilm',username='john@user.com', api_key='f0a8b9a9-879f-4174-9d08-322eea196efc')

or::

    session = accsyn_api.Session(domain='acmefilm',username='john@user.com', pwd='password')

or::

    session = accsyn_api.Session(domain='acmefilm',username='john@user.com', session_key='6152693980700117321a5f8c')



The following environment variables are picked up if set by python parent process:

"ACCSYN_DOMAIN" => "domain".

"ACCSYN_API_USER" => "username".

"ACCSYN_API_KEY" => "api_key".



.. note::

    accsyn communicates over tcp port 443 (https wrapped CRUD REST calls), make sure to allow outgoing traffic towards accsyn backend (yourdomain.accsyn.com).

    Your API key can be obtained online or from desktop app @ Prefs>Setup API environment, or by running "accsyn user get_api_key" from your terminal/unix shell.

    Remember to treat the API key as a secret password as it will grant access to all data on your accsyn shared storage.

    Session authenticated with password will expire within 10h, make sure to design your application to check for "session_expired:true" being supplied when a error message is supplied. In that case you will need to re-create your session and retry operation.

    Add verbose=True to session creation if you want to see verbose debugging output.

    Add path_logfile=/path/to/my.log.file if you want all stdout should go to disk.


Testing the session
===================

To make sure you have permissions, you can test the obtained session::

    print(session.find_one("User"))

Should output your user profile::

    {
       "id":"5b0faf03304bfd4810dbd5fc",
       "code”:"john@user.com",
       "modified":datetime("2018-06-04 07:06:41.028619")
    }



Query
=====

The find and find_one functions provide query functionality within the API.

To get a list of all entities::

   jobs = session.find('<entity>')

Expressions
***********

The accsyn query syntax is not as evolved as for example SQL. The accsyn API currently support nested AND/OR operations using the = or !=/<>. An example of a query in its most complex form::

    session.find('job WHERE ((user=5bfeb0381da7ee4095fa217e AND source!=hq) OR status<>failed) AND code="Daily backup"')


Limit
*****

To return only a limited set of attributes::

    session.find_one('Job where id=614d660de50d45bb027c9bdd', attributes=['source','destination'])


To run a paginated query, that skips 100 jobs and only returns a maximum of 50::

    session.find('Job', skip=100, limit=50)


Create
======

To create any entity (string), supply the scope (string) and the data as a dictionary payload on this generic form::

    session.create(<entity>, <data>)


Modify
======

To modify an entity, supply the scope (string), entity id (string) and data as a dictionary payload::

    session.update(<scope>, <id>, <data>)


Delete
======

To delete an entity, supply the scope (string) and entity id (string)::

    session.delete_one(<scope>, <id>)


Example of obtaining and modifying an accsyn job
================================================

Get job named “my_transfer”::

    j = session.find_one('Job WHERE code="my_transfer"')


Change its status::

    session.update('Job', j['id'], {
        "status":"aborted"
    }) 


Delete(purge) the job::

    session.delete_one('Job', j['id']}) 



From here, learn more about :ref:`datatypes` and/or dig into the different sections for detailed information on how to work with users, jobs, queues and so on.


Error handling
==============

If an error occurs, an exception will be raised and the exception message can fetched afterwards by issuing::

    print(session.get_last_message())


Network proxy support
=====================

If you live on a network that does not have direct Internet access, the Python API can utilise a SOCKS (v4/v5) proxy of yours or an accsyn daemon acting as a proxy (refer to the Accsyn admin manual on how to setup such a proxy).

SOCKS proxy

Supply proxy="socks:<hostname or IP>:<port>" when creating session or set the ACCSYN_PROXY environment variable.

Using an accsyn network proxy:

Supply proxy="accsyn:<hostname or IP>:<port>" when creating session or set the ACCSYN_PROXY environment variable.




