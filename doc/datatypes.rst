..
    :copyright: Copyright (c) 2026 accsyn

.. _datatypes:


.. currentmodule:: accsyn_api.session


**********
Data types
**********

This section will explain the different type data that can be obtained by the API.


Roles
=====

Three built-in "roles" (permission/clearance) levels exists for accsyn users, the clearance dictates what entities and attributes can be read and write through the API:

* Administrators (**admin**); Are allowed to read and write all data – configure accsyn.

* Employees (**employee**); Managers that are allowed full access to jobs and data on volumes given access to.

* Standard users (**standard**); (i.e. remote/external users) Besides receiving deliveries, they are only allowed to access share's explicitly given access through ACLs (Access Control Lists).



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
     - Standard:
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
     - Users and their profile data
     - YES
     - YES
     - YES :sup:`1`
     - YES :sup:`1`
     - YES :sup:`2`
     - YES :sup:`2`
   * - Workspace
     - Global workspace settings
     - YES
     - YES
     - YES
     - no
     - no
     - no
   * - Queue
     - A queue of jobs (transfers, renders |br| (compute), deliveries, ...) to be executed
     - YES
     - YES
     - YES
     - no
     - no
     - no
   * - Transfer
     - A file transfer job with each task |br| being a file of folder to transfer (was formerly |br| known as "job")
     - YES
     - YES
     - YES
     - YES
     - YES :sup:`3`
     - YES :sup:`3`
   * - Delivery
     - A delivery package containing one |br| or more file(s) and/or folder(s) to be delivered |br| to one or more recipients
     - YES
     - YES
     - YES
     - YES
     - YES :sup:`4`
     - YES :sup:`4`
   * - Request
     - A request package containing one |br| or more file(s) and/or folder(s) to be requested |br| from one or more senders
     - YES
     - YES
     - YES
     - YES
     - YES :sup:`4`
     - YES :sup:`4`
   * - Stream
     - A video stream of one or more |br| files to be streamed and/or downloadable by one or |br| more recipients
     - YES
     - YES
     - YES
     - YES
     - YES :sup:`4`
     - YES :sup:`4`
   * - Task
     - A file/directory that should be |br| transferred within a job.
     - YES
     - YES
     - YES
     - YES
     - YES :sup:`3`
     - YES :sup:`3`
   * - Folder
     -  Defines a sub-directory beneath a |br| volume that should be granted access through ACLs |br| to one or more standard users.
     - YES
     - YES
     - YES
     - YES :sup:`5`
     - YES :sup:`6`
     - YES :sup:`6`
   * - Collection
     -  A virtual shared folder containing |br| one or more files and/or folders to be granted |br| access through ACLs to one or more standard users.
     - YES
     - YES
     - YES
     - YES :sup:`5`
     - YES :sup:`6`
     - YES :sup:`6`
   * - Home
     -  Defines the special home sub-directory |br| beneath a  volume that should be granted  |br| access through ACLs to a specific user.
     - YES
     - YES
     - YES
     - YES :sup:`5`
     - YES :sup:`6`
     - YES :sup:`6`
   * - Volume
     -  Defines a directory, typically on a |br| network volume, available |br| to accsyn and |br| granted access through ACLs to one ore more employees.
     - YES
     - YES
     - no
     - no
     - no
     - no
   * - Site
     - A physical or cloud location where accsyn |br| can be deployed
     - YES
     - YES
     - YES
     - no
     - no
     - no
   * - Server
     - A workspace file transfer endpoint or |br| compute node
     - YES
     - YES
     - YES
     - no
     - no
     - no
   * - User server
     - A server running remotely in user space |br| for unattended file deliveries and |br| globally mapped shares.
     - YES
     - YES
     - YES
     - YES
     - YES :sup:`1`
     - YES :sup:`1`
   * - Client
     - A user file transfer endpoint running in |br| app or web browser.
     - YES
     - YES
     - YES
     - YES
     - YES :sup:`1`
     - YES :sup:`1`
   * - ACL
     - Access control list defining what a user |br| has access to (workspace, folder, delivery etc.)
     - YES
     - YES
     - YES
     - YES
     - YES :sup:`1`
     - YES :sup:`1`

* :sup:`1` Their own and standard users.
* :sup:`2` Only their own.
* :sup:`3` If involved in job either as sending or receing part.
* :sup:`4` If an explicit recipient.
* :sup:`5` Except admin or other employee home shares.
* :sup:`6` Home share and share given explicit access through ACL.




To retrieve a list of all known entity types::

    session.find("entitytypes")

This will return a list of entity types as string, i.e. ["user","organization","job",..].


Attributes
==========

Each entity has its own attributes, such as “id” or “code”(an accsyn abbreviation for an unique “name”).

To retrieve a list of known attributes for an entity::

    session.find('attributes WHERE entitytype=delivery')

This will return a list of attributes an delivery entity can have, i.e. ["id","code","status",...]. 

.. note::
    
    The attributes available depends on the role/clearance level of the API user.



By default, all readable attributes are returned. To return attributes only allowed during creation and edit::

    session.find('attributes WHERE entitytype=folder', create=True)

    session.find('attributes WHERE entitytype=folder', update=True)






.. |br| raw:: html

      <br>

