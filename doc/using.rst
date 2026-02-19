..
    :copyright: Copyright (c) 2026 accsyn

.. _using:


.. currentmodule:: accsyn_api.session

*****
Using
*****

.. highlight:: python

In a Python session, import the accsyn Python API to start using it::

    import accsyn_api


Create a session
================

The session is the Python object used when communicating with the accsyn workspace backend, it requires valid API credentials 
supplied upon creation::

    session = accsyn_api.Session(workspace='acmefilm',username='john@user.com', api_key='BlrPCfxLIRZEdhL6LXotwXRmDWbPRsPgLYcpa7ubyu97gxpqSC4130Adfh968Low')



The following environment variables are picked up if set within python parent process, and not provided as arguments to the Session constructor:

.. list-table:: env mappings
   :widths: 100 100
   :header-rows: 1

   * - Environment:
     - Parameter:
   * - ACCSYN_WORKSPACE
     - workspace
   * - ACCSYN_API_USER
     - username
   * - ACCSYN_API_KEY
     - api_key


.. note::

    accsyn communicates over tcp port 443 (https wrapped CRUD REST calls), make sure to allow outgoing traffic towards accsyn backend (your-workspace.accsyn.com).

    Your API key can be obtained at `https://accsyn.io/developer <https://accsyn.io/developer>`_ or from desktop app @ Settings>API.

    Remember to treat the API key as a secret password as it will grant access to listing and modifying files on your accsyn shared storage.

    Add verbose=True to session creation if you want to see verbose debugging output.

    Add path_logfile=/path/to/my.log.file if you want all stdout should go to disk.


Testing the session
===================

To make sure the API is working, you can test the obtained session::

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

To get a list of all entities of a certain entity type::

   entities = session.find('<entitytype>')

Where <entitytype> is the entity type, i.e. "transfer", "delivery", "user", "share", etc.

Return a single entity of a certain entity type::

   job = session.find_one('<entitytype> WHERE id=<id>')

Where <entitytype> is the entity type, i.e. "transfer", "delivery", "user", "share", etc and <id> is the internal accsyn id of the entity.


Expressions
***********

The accsyn API uses a query language that is based on a simplified SQL syntax::

    session.find('Transfer WHERE source=myworkspace')

Returns a list of all download jobs (workspace code/domain is "myworkspace").

.. note::

    The  syntax is not as evolved as for example SQL. The accsyn API currently support nested AND/OR operations using the = or !=/<>.

    Queries are case insensitive, for example there is no difference between "transfer" and "Transfer" or supplying "WHERE" or "where". Throughout this documentation, we will have WHERE and operators in upper case for readability.

Example of a nested complex query::

    session.find('transfer WHERE ((user=lisa@example.com AND destination=hq) OR status<>failed) AND code="* backup"')

This query returns all transfers where the user is lisa@example.com and the destination is site hq, or the status is not failed, and the code(name) ends with " backup" (* is a wildcard).


Operators
*********

The accsyn API supports the following operators:

.. list-table:: accsyn query operators
   :widths: 20 100
   :header-rows: 1

   * - Operator:
     - Description:
   * - =
     - Equal to the value on the right hand side.
   * - !=
     - Not equal to the value on the right hand side.
   * - <>
     - Not equal to the value on the right hand side.
   * - <
     - Less than the value on the right hand side.
   * - >
     - Greater than the value on the right hand side.
   * - <=
     - Less than or equal to the value on the right hand side.
   * - >=
     - Greater than or equal to the value on the right hand side.
   * - in
     - Matches one of the values in the comma(,) separated list on the right hand side string expression.
   * - not in
     - Does not match any of the values in the comma(,) separated list on the right hand side string expression.
   * - contains
     - Attribute (string) contains the given substring on the right hand side.
   * - not contains
     - Attribute (string) does not contain the given substring on the right hand side.
   * - matches
     - Attribute (string) matches the regular expression on the right hand side
   * - not matches
     - Attribute (string) does not match the regular expression on the right hand side.

Example of substring match::

    session.find('Transfer WHERE name CONTAINS "backup"')

Example of regular expression match::

    session.find('Transfer WHERE name matches "backup.*\\.zip"')

.. note::

    All comparisons are case insensitive.
    If string value contains whitespace, it must be enclosed in quotes(').
    The attribute to compare must be on the left hand side of the operator, and the value to compare must be on the right hand side. For example, "name=X" is valid, but "X=name" is not.
    Regular expression syntax is that of the accsyn backend (commonly Python-style).



Limit
*****

To return only a limited set of attributes::

    session.find_one('Transfer where id=614d660de50d45bb027c9bdd', attributes=['source','destination'])


To run a paginated query, that skips 100 jobs and only returns a maximum of 50::

    session.find('Transfer', skip=100, limit=50)


Create
======

To create any entity (string), supply the scope (string) and the data as a dictionary payload on this generic form::

    session.create(<entitytype>, <data>)


Modify
======

To modify an entity, supply the scope (string), entity id (string) and data as a dictionary payload::

    session.update(<entitytype>, <id>, <data>)


Delete
======

To delete an entity, supply the scope (string) and entity id (string)::

    session.delete_one(<entitytype>, <id>)


Example of obtaining and modifying an accsyn file transfer
==========================================================

Get job named “my_transfer”::

    transfer = session.find_one('Transfer WHERE name="my_transfer"')


Change its status::

    session.update('Transfer', transfer['id'], {"status":"aborted"}) 


Delete(archive) the transfer::

    session.delete_one('Transfer', transfer['id']}) 



From here, learn more about :ref:`datatypes` and/or dig into the different sections for detailed information on how to work with users, jobs, queues and so on.


Error handling
==============

If an error occurs, an exception will be raised and the exception message can fetched afterwards by issuing::

    print(session.get_last_message())


Network proxy support
=====================

If you live on a network that does not have direct Internet access, the Python API can utilise a SOCKS (v4/v5) proxy of yours or an accsyn daemon acting as a proxy (refer to the Accsyn admin manual on how to setup such a proxy).

Using aSOCKS proxy
******************

Supply proxy="socks:<hostname or IP>:<port>" when creating session or set the ACCSYN_PROXY environment variable.

Using an accsyn network proxy
*****************************

Supply proxy="accsyn:<hostname or IP>:<port>" when creating session or set the ACCSYN_PROXY environment variable.




