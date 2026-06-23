..
    :copyright: Copyright (c) 2026 accsyn

.. _deliveries:

**********
Deliveries
**********

An accsyn file delivery is a persistent job that delivers one or more files to one or more recipients. It is similar to a shared collection of files, but streamlined so recipients can download and action the delivery in a standard web browser.

Documentation: `https://support.accsyn.com/delivery <https://support.accsyn.com/delivery>`_


A file delivery can be created as a temporary delivery (files uploaded and then submitted) or from existing files on accsyn storage and submitted immediately.

Deliveries cannot be dispatched until at least one file and one recipient have been added. Until then, the delivery remains in ``init`` state and must be submitted once files and recipients are in place.

.. note::
    A delivery is kept in the init state for at most 8 hours (default) until it expires and is deleted automatically.


Query deliveries
================

Fetch all outbound deliveries
-----------------------------
To fetch all deliveries, use the find API function::

    deliveries = session.find("Delivery")

This returns a list of deliveries.

To fetch finished deliveries, use the finished=True argument::

    deliveries = session.find("Delivery", finished=True)


Fetch a delivery by its ID
--------------------------

To fetch a delivery by its ID, use the get_entity API function::

    delivery = session.get_entity("Delivery", delivery_id)

Returns the delivery in the same form as a find query.


Find delivery by its name
--------------------------

To fetch a delivery by its name, use the find_one API function::

    delivery = session.find_one("Delivery WHERE name='Project references'")

Returns the delivery in the same form as a find query.



Create a temporary delivery
===========================

A temporary delivery stores uploaded files in a temp folder on the default accsyn storage volume. The folder is deleted after the delivery expires or is aborted.

To create a temporary delivery without recipients, supply the name::

    delivery = session.create("Delivery",{"name":"Project references"})

To create a pending temporary delivery with recipients, supply the name and recipients::

    delivery = session.create("Delivery",{"name":"Project references", "recipients":["lisa@example.com"]})

Returns the new delivery in the same form as a find query.

The delivery will be kept in the init state for at most 8 hours (default) until it expires and is deleted.


Upload files to a temporary delivery in init state
---------------------------------------------------

The accsyn API cannot upload files to a delivery directly. Use the API to create a transfer job targeting a client running the accsyn desktop app or a user server instance.

To upload the file(s) to the delivery::

    transfer = session.create("Transfer", {
        "parent": delivery["id"],
        "source": "/Volumes/projects/references/Concept_images.zip",
        "name": "Upload concept images to '{}'".format(delivery["name"])
    })

.. note::
    A client must be registered (desktop app or user server) by the same user as the API session.

    Ensure the client is online and enabled for the upload to start.

    If multiple clients are online, a random client is selected. Prepend the destination with a party identifier in the form ``client=<client_id>:`` to target a specific client.


Add a recipient to a delivery
-----------------------------

To add a recipient to a delivery, use the grant API function with either user id or email::

    retval = session.grant("User", "lisa@example.com", "Delivery", delivery["id"])

The return value depends on the state of the delivery:

    - If the delivery is not submitted yet (pending/init state), the return value will be True.
    - If the delivery is submitted, the return value will be a dictionary with same form as the access list query would return.

The user will receive an email with a link to the delivery and instructions on how to action it.

.. note::
    
    The user is invited to your workspace if they do not already exist. First-time users receive instructions for signing up. Pass ``{"invite": False}`` as the data argument to skip the invitation.


List recipients of a delivery
-----------------------------

To list recipients of a delivery, use the assignments API function::

    recipients = session.access("Delivery", delivery["id"])

Return value will be a list of dictionaries with recipient data:

    [{"actioned": True, "user": "6676f3e9c7ef4e27da254e57", "user_hr": "user:lisa@example.com[standard](6676f3e9c7ef4e27da254e57)"}]

``actioned`` is ``True`` if the recipient has actioned the delivery, ``False`` otherwise.

.. note::

    A recipient may have started but not completed a download. To get the full picture, inspect all transfers beneath the delivery.


Remove a recipient from a delivery
----------------------------------

To remove a recipient from a delivery, use the deassign API function::

    retval = session.revoke("User", "6676f3e9c7ef4e27da254e57", "Delivery", delivery["id"])


Returns ``True`` if the operation succeeded.

.. note::

    The user will not be notified of the removal, they will need to check their deliveries to see if they are still listed.


Submit delivery
---------------

To submit a delivery that is in the init state, update its status to pending:

    session.update("Delivery", delivery["id"], {"status": "pending"})

Deliveries calculate their size, then send emails to recipients with instructions for accessing the delivery.

.. note::

    A delivery cannot be submitted until at least one file and one recipient have been added.


Create from existing files at accsyn storage
============================================

To create and submit a file delivery with two files, supply the source files as a list of paths and a list of recipients::

    delivery = session.create("Delivery",{
        "name":"Project reference",
        "tasks":["myproject/reference.png", "logo.jpeg"],
        "recipients":["lisa@example.com"]
    })

Files are assumed to be on the default accsyn storage volume. To specify a different folder or volume::

    delivery = session.create("Delivery",{
        "name":"Project reference",
        "tasks":["folder=myproject/reference.png", "volume=assets/logo.jpeg"],
        "recipients":["lisa@example.com"]
    })

The delivery will be submitted and the user will receive an email with a link to the delivery. 
The files will be available for download for the default duration of one month.


List files and folders associated with a delivery
-------------------------------------------------

To list files and folders sent with a delivery::

    files = session.find(f"task WHERE job.id={delivery['id']}")

Returns a list of tasks.


List file transfers associated with a delivery
===============================================

To list file transfers beneath a delivery for a specific user::

    transfers = session.find("Transfer WHERE parent=69732302fd379c8fff1089d0 AND user=6676f3e9c7ef4e27da254e57")

This returns a list of active transfer jobs beneath the delivery. Pass ``finished=True`` to include finished transfers.


Download from delivery
======================

The accsyn API cannot download files from a delivery directly. Use the API to create a transfer job targeting a destination client running the accsyn desktop app or a user server instance.

First, query the delivery to get the delivery ID::

    delivery = session.find_one("Delivery")
    print(delivery["name"])

To download the file(s) from a delivery::

    transfer = session.create("Transfer", {
        "parent": delivery["id"],
        "destination": "/tmp",
        "name": "Download '{}'".format(delivery["name"])
    })

.. note::
    A client must be registered by the same user as the API session.

    Ensure the client is online and enabled for the download to start.

    If multiple clients are online, a random client is selected. Prepend the destination with ``client=<client_id>:`` to target a specific client.


Modifying a delivery
====================

Abort a delivery
----------------

To abort a delivery, update its status to aborted:

    delivery = session.update("Delivery", delivery["id"], {"status": "aborted"})


Finish up a delivery
--------------------

To finish up a delivery, update its status to finished:

    delivery = session.update("Delivery", delivery["id"], {"status": "done"})

Returns the updated delivery in the same form as a find query.

Users cannot download files from a finished delivery. For temporary deliveries, files are deleted after the default grace period of 4 hours.

Delete a delivery
-----------------

To delete a delivery that has not been submitted, use the delete API function::

    retval = session.delete_one("Delivery", delivery["id"])

Returns ``True`` if the operation succeeded.

.. note::

    If it is a temporary delivery - the files will be deleted after the default grace of 4 hours.


Working with upload requests
============================

An upload request is a reverse delivery. It can be temporary (files stored in a temp folder on the default accsyn storage volume and deleted on expiration) or point to a folder on accsyn storage and be submitted immediately.

Requests follow the same workflow as deliveries for adding recipients and submitting.

Create a temporary upload request
---------------------------------

To create a temporary upload request, supply the name and the init status::

    upload_request = session.create("Request",{
        "name":"Project material",
        "recipients":["lisa@example.com"]
    })

Returns the created upload request in the same form as a find query. The request is
submitted immediately and the user will receive an email with a link to the request.

To create a temp request that will be submitted later::

    upload_request = session.create("Request",{
        "name":"Project material",
        "status":"init"
    })

The request will be kept in the init state for 8 hours (default) until it expires and is deleted.

Add at least one recipient, then submit the request by setting status to ``pending`` (see above).

Create upload request to a storage folder
-----------------------------------------

To create an upload request to a folder on the default volume, supply the folder path and recipients::

    upload_request = session.create("Request",{
        "name":"Provide project material",
        "destination":"share=(default)/source/from_client",
        "recipients":["lisa@example.com"]
    })

Returns the created upload request in the same form as a find query. The request is
submitted immediately and the user will receive an email with a link to the request.

To create a request that will be submitted later, supply with the 'init' status (see above)