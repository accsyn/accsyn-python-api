..
    :copyright: Copyright (c) 2021 accsyn

.. _users:

*****
Users
*****

An user identifies a physical person that interacts with accsyn, and access is role based with three base roles/clearance levels:

* **Administrator**; Have full access to everything, this include transfer files and administrate accsyn.

* **Employee**; Have full access to transfer files, and view configuration.

* **User**; (Standard) Have access to download file packages sent to them, and to shares given explicit access through ACLs (Access Control Lists).

Users are managed centralised, with all users having their unique ID across all workspaces and one authentication method (accsyn / Google etc)


Query
=====


To list all users::

    users = session.find("User")


List only employees::

    employees = session.find("User WHERE role=employee")


Create
======

To invite a new default role (standard) user::

    user = session.create("User",{
        "code":"lisa@example.com",
    })


A dict will be returned containing user attributes::

    {
        "code": "demo.user3@accsyn.com",
        "created": "2026-02-08T11:20:05",
        "creator": "lisa@example.com",
        "description": "",
        "id": "69887165f643db8cd731b31a",
        "logged_in": null,
        "metadata": {},
        "modified": "2026-02-08T11:35:11",
        "modifier": "",
        "name": "demo.user3@accsyn.com",
        "queue": null,
        "role": "standard",
        "status": "enabled"
    }


Explanation of the returned attributes:

* ``code``: The unique email user Email address.
* ``created``: Date of creation.
* ``creator``: The user that created the user.
* ``description``: Description of user.
* ``id``: The internal accsyn user id, use this when modifying the user later on.
* ``logged_in``: The last time user login.
* ``metadata``: User metadata dict.
* ``modified``: Date of last modification.
* ``modifier``: The user that most recently modified the user.
* ``name``: The name that user entered during registration phase.
* ``queue``: The queue (ID or code) to put jobs in, when involving this user. Will have no effect if queue already defined with job.
* ``role``: The role user has.
* ``status``: The status of user, can be "enabled" or "disabled" - cannot login and all jobs put on hold.

Additinal payload attributes that can be supplied:

* ``create_home_share``: If True, the user will be given a home share in the workspace. Supply fals to prevent creation of home share, even if configured to do so.
* ``give_all_volumes_access``: If True, the user will be given full read and write access to all volumes in the workspace.
* ``give_default_volume_access``: If True, the user will be given full read and write access to the default volume in the workspace.
* ``volumes``: A list of volume IDs to give full read and write access to.
* ``message``: An invitation message to the user, will be supplied in the email sent.
* ``mail``: If False, no email will be sent to the user.


Modify
======

To disable a user::

    session.update("User", "69887165f643db8cd731b31a", {"status" :"disabled"})


To change user clearance/role::

    session.update("User", "69887165f643db8cd731b31a", {"role" :"employee"})

.. note::
    * Only administrators can change user roles.
    * Be careful when changing user roles, as it will affect what the user can do in the workspace. Changing role will cause all access to be revoked and need to be granted again.


Offline
=======

An user can be deactivated, which means it will be removed from accsyn but still eglible
for audit & restore if you again create/invite a user with the same identification (code)::

    session.deactivate_one("User", "69887165f643db8cd731b31a")

.. note::

    * Offlining a user also causes user home share to be put offline together with ACLs.
    * No jobs that involves the user can be active.
    * Offline users have the attribute inactive set to True.


Re-activate a user
==================

To re-activate a user, supply the user email address(code) or ID::

    session.activate_one("User", "69887165f643db8cd731b31a")

Delete
======

To delete a user::

    session.delete_one("User", "69887165f643db8cd731b31a")

.. note::

    * If you delete a user, all associated jobs are aborted.
    * Related user home share will also be deleted.
    * The user will be removed from your workspace, but kept centrally in accsyn platform as user might have access to other workspaces.
    * accsyn user account information are ontouched.