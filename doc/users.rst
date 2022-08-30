..
    :copyright: Copyright (c) 2021 accsyn

.. _users:

*****
Users
*****

An user identifies a physical person that interacts with accsyn, and access is role based with three major roles/clearance levels:

* **Administrator**; Have full access to everything, this include transfer files and administrate accsyn.

* **Employee**; Have full access to transfer files, and view configuration.

* **User**; (Standard) Have access to download file packages sent to them, and to shares given explicit access through ACLs (Access Control Lists).



Query
=====


To list all users::

    all_users = session.find('User')


List only employees::

    all_users = session.find('User where role=employee')


Create
======

To invite a new user::

    user = session.create("User",{
        "code":"lisa@user.com",
    })


A dict will be returned containing user attributes::

    {
        "id": "61bf395c46ed6081a2b2afc0",
        "code": "lisa@user.com",
        "name": "",
        "role": "user",
        "description": "",
        "logged_in": "1970-01-01T01:00:00",
        "phase": "joined",
        "queue": "",
        "status": "enabled",
        "metadata": {},
        "created": "2021-12-19T14:53:31",
        "modified": "2022-01-19T18:56:16",
        "modifier": "61bf395c46ed6081a2b2afc0",
    }


Explanation of the returned attributes:

* ``id``: The internal accsyn user id, use this when modifying the user later on.
* ``code``: The unique email user Email address.
* ``role``: The role user has.
* ``name``: The name that user entered during registration phase.
* ``description``: Description of user.
* ``status``: The status of user, can be "enabled" or "disabled" - cannot login and all jobs put on hold.
* ``logged_in``: The last time user login.
* ``phase``: "activating": user has received an activation email and response is awaiting, "joining": user has requested to join, awaiting administrator to accept or deny request, "joined": Normal active status.
* ``creator``: The user that created the user.
* ``metadata``: Job metadata dict.
* ``created``: Date of creation.
* ``modified``: Date of last modification.
* ``modifier``: The user that most recently modified the user.


Modify
======

To disable a user::

    session.update('User', '61bf395c46ed6081a2b2afc0', {'status':"disabled"})


To change user clearance/role::

    session.update('User', '61bf395c46ed6081a2b2afc0', {'role':"disabled"})



Offline
=======

An user can be put offline, which means it will be removed from accsyn but still eglible
for restore if you again create a user with the same identification (code)::

    session.offline_one('User', '61bf395c46ed6081a2b2afc0')

.. note::

    * Offlining a user also causes user home share to be put offline together with ACLs.
    * No jobs that involves the user can be active.


Delete
======

To delete a user::

    session.delete_one('User', '61bf38d22650852bc50d5869')

.. note::

    * If you delete a user, all associated jobs are aborted.
    * Related user home share will also be deleted.
    * accsyn user account information are still preserved, as user could be member of another accsyn domain.