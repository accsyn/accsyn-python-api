..
    :copyright: Copyright (c) 2021 accsyn

.. _datatypes:


.. currentmodule:: accsyn_api.session


**********
Data types
**********

This section will explain the different type data that can be obtained by the API.


Roles
=====

Three built-in "roles" (permission/clearance) levels exists for accsyn users, the clearance dictates what data can be read and write through the API:

* Admins; Are allowed to read and write all data – configure accsyn.

* Employees; Are allowed full access to jobs and data on all shares.

* Users; (i.e. remote freelancers/customers) Besides receiving packages, they are only allowed to access share's explicitly given access through ACLs (Access Control Lists). Restricted users automatically is given a share @ default location - <root share>/accsyn/<user id (email)>.



Entities
========

Data read from accsyn using the API arrives as JSON dictionaries, categorised by entity types:


.. list-table:: accsyn entitytypes and role permissions
   :widths: 10 40 8 8 8 8 8 8
   :header-rows: 2

   * - Entity type:
     - Description:
     - Admin:
     - 
     - Employee:
     - 
     - User (restricted):
     - 
   * -
     -
     - Read
     - Write
     - Read
     - Write
     - Read
     - Write
   * - User
     - User profile data
     - YES
     - YES
     - YES
     - YES :sup:`1`
     - YES :sup:`2`
     - YES :sup:`2`
   * - Organization
     - Global domain settings
     - YES
     - YES
     - YES
     - NO
     - NO
     - NO
   * - Job
     - A (transfer) job containing tasks
     - YES
     - YES
     - YES
     - YES
     - YES :sup:`3`
     - YES :sup:`3`
   * - Task
     - A file/directory that should be |br| transferred within a job.
     - YES
     - YES
     - YES
     - YES
     - YES :sup:`3`
     - YES :sup:`3`
   * - Share
     -  Defines a sub-directory beneath a |br| root share that should be made available |br| to users.
     - YES
     - YES
     - YES
     - YES :sup:`4`
     - YES :sup:`5`
     - YES :sup:`5`
   * - Root share
     -  Defines a directory, typically on a |br| network volume, that is to be made available |br| to accsyn for file transfers and other operations.
     - YES
     - YES
     - NO
     - NO
     - NO
     - NO

* :sup:`1` Their own and restricted users.

* :sup:`2` Only their own.

* :sup:`3` If involved in job either as sending or receing part.

* :sup:`4` Except admin or other employee home shares.

* :sup:`5` Home share and share given explicit access through ACL.




To retrieve a list of all known entity types::

    session.find("entitytypes")

This will return a list of entity types as string, i.e. ["user","organization","job",..].


Attributes
==========

Each entity has its own attributes, such as “id” or “code”(an accsyn abbreviation for an unique “name”).

To retrieve a list of known attributes for an entity::

    session.find('attributes WHERE entitytype=job')

This will return a list of attributes entities of that entity type can have, i.e. ["id","code","status",...]. 

.. note::
    
    Depending role/clearance, some attributes might be not visible if accessing the API as an restricted user.



By default, all readable attributes are returned. To return attributes only allowed during creation and edit::

    session.find('attributes WHERE entitytype=job', create=True)

    session.find('attributes WHERE entitytype=job', update=True)






.. |br| raw:: html

      <br>

