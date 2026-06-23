..
    :copyright: Copyright (c) 2021 accsyn

.. _users:

*****
Users
*****

A user identifies a person who interacts with accsyn. Access is role-based, with three clearance levels:

* **Administrator**; Full access to everything, including file transfers and workspace administration.

* **Employee**; Full access to transfer files and view configuration.

* **Standard**; Access to download file packages sent to them and to shares granted through explicit ACLs (Access Control Lists).

Users are managed centrally — each has a unique ID across workspaces and one authentication method (accsyn, Google, etc.).


Query
=====


To list all users::

    users = session.find("User")


List only employees::

    employees = session.find("User WHERE role=employee")


Create
======

To invite a new standard-role user::

    user = session.create("User",{
        "code":"lisa@example.com",
    })


A dict is returned containing user attributes::

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

* ``code``: The user's unique email address.
* ``created``: Date of creation.
* ``creator``: The user who created this user.
* ``description``: User description.
* ``id``: Internal accsyn user ID. Use this when modifying the user.
* ``logged_in``: Last login time.
* ``metadata``: User metadata dict.
* ``modified``: Date of last modification.
* ``modifier``: The user who last modified this user.
* ``name``: Name entered during registration.
* ``queue``: Queue (ID or code) for jobs involving this user. Has no effect if the job already defines a queue.
* ``role``: The user's role.
* ``status``: ``enabled`` or ``disabled``. Disabled users cannot log in and all jobs are put on hold.

Additional payload attributes:

* ``create_home_share``: If ``True``, create a home share in the workspace. Pass ``False`` to skip home share creation even when workspace policy would create one.
* ``give_all_volumes_access``: (Employees) If ``True``, grant full read/write access to all volumes.
* ``give_default_volume_access``: (Employees) If ``True``, grant full read/write access to the default volume.
* ``volumes``: List of volume IDs to grant full read/write access to.
* ``message``: Invitation message included in the email.
* ``mail``: If ``False``, do not send an email to the user.


Modify
======

To disable a user::

    session.update("User", "69887165f643db8cd731b31a", {"status" :"disabled"})


To change user base role::

    session.update("User", "69887165f643db8cd731b31a", {"role" :"employee"})

.. note::
    * Only administrators can change user roles.
    * Changing roles affects what the user can do. All access is revoked and must be re-granted.


Offline
=======

A user can be deactivated — removed from the workspace but eligible for audit and restore if you invite a user with the same identification (code) again::

    session.deactivate_one("User", "69887165f643db8cd731b31a")

.. note::

    * Deactivating a user also offlines their home share and ACLs.
    * No active jobs may involve the user.
    * Offline users have ``inactive`` set to ``True``.


Re-activate a user
==================

To re-activate a user, supply the email address (code) or ID::

    session.activate_one("User", "69887165f643db8cd731b31a")

Delete
======

To delete a user::

    session.delete_one("User", "69887165f643db8cd731b31a")

.. note::

    * Deleting a user aborts all associated jobs.
    * The related home share is also deleted.
    * The user is removed from your workspace but retained centrally if they have access to other workspaces.
    * Central accsyn account information is untouched.
