..
    :copyright: Copyright (c) 2026 accsyn

.. _deliveries:

**********
Deliveries
**********

A an accsyn file delivery is a persistent job that delivers one or more files to one or more recipients and 
is similar to a shared collection of files, but streamlined to make it simple for the recipient to 
download and action the delivery using a standard web browser.

Documentation: `https://support.accsyn.com/delivery <https://support.accsyn.com/delivery>`_


A file delivery can either be created as a temporary delivery that will 
have files uploaded to it and then be submitted, or be created
from existing files on an accsyn storage volume/share and submitted immediately.



Create a temporary delivery
===========================

A pending delivery will have its files uploaded to a temp folder on default accsyn storage volume,
 that will be deleted after the delivery is done (expired) or aborted.

To create a temporary delivery, supply the name and the init status::

    delivery = session.create("Delivery",{
        "name":"Project references",
        "status":"init"
    })

This will return the created delivery, as would have been returned by a delivery find query.

The delivery will be kept in the init state for 8 hours (default) until it expires and is deleted.


Upload files to a temporary delivery
------------------------------------

The accsyn API is not able to upload files to a delivery, 
you need to use the accsyn desktop app and then use the API to create a transfer job for the files.

To upload the file(s) to the delivery::

    transfer = session.create("Transfer", {
        "parent": delivery["id"],
        "source": "/Volumes/projects/references/Concept_images.zip",
        "name": "Upload concept images to '{}'".format(delivery["name"])
    })

.. note::
    A client must be registered, by the same user as the API session.

    Make sure your client is online and enabled to have upload start.

    If multiple clients are online, a random client will be resolved. 
    Prepend the destination with "client=<client_id>:" to target a specific client.


Add a recipient to a delivery
-----------------------------

To add a recipient to a delivery, use the assign API function::

    retval = session.grant("User", "6676f3e9c7ef4e27da254e57", "Delivery", delivery["id"])

Return value will a dictionary with same form as the access list query would return. 
The user will receive an email with a link to the delivery and instructions on how to action it.

.. note::
    
    The user will be invited to your workspace if it does not exist. First time users will be given clear instructions on how to sign up their personal accsyn account.


List recipients of a delivery
-----------------------------

To list recipients of a delivery, use the assignments API function::

    recipients = session.access("Delivery", delivery["id"])

Return value will be a list of dictionaries with recipient data:

    [{'actioned': True, 'user': '6676f3e9c7ef4e27da254e57', 'user_hr': 'demo.user@accsyn.com'}]

Actioned is True if the recipient has already actioned the delivery, False if not.

.. note::

    The user might have tried downloading the delivery but interrupted or failed, to get the full story you will need to load and inspect all transfers beneath delivery.


Remove a recipient from a delivery
----------------------------------

To remove a recipient from a delivery, use the deassign API function::

    retval = session.revoke("User", "6676f3e9c7ef4e27da254e57", "Delivery", delivery["id"])


This will return True if operation was successful.

.. note::

    The user will not be notified of the removal, they will need to check their deliveries to see if they are still listed.


Submit delivery
---------------

To submit a delivery, update its status to pending:

    delivery = session.update("Delivery", delivery["id"], {"status": "pending"})

This will return the updated delivery, as would have been returned by a delivery find query.


.. note::

    A delivery can not be submitted until at least one file and one recipient has been added.


Create from existing files
==========================

To create and submit a file delivery with two files, supply the source files as a list of paths and a list of recipients::

    delivery = session.create("Delivery",{
        "name":"Project reference",
        "tasks":["project/reference.png", "project/description.txt"],
        "recipients":["demo.user@accsyn.com"]
    })

The delivery will be submitted and the user will receive an email with a link to the delivery. 
The files will be available for download for the default duration of one month.

List files and folders associated with a delivery
-------------------------------------------------

To list files and folders that has been sent with a delivery::

    files = session.find(f"task where job.id={delivery['id']}")

This will return a list of tasks.


List file transfers associated with a delivery
===============================================

To list file transfers beneath a delivery for a specific user::

    transfers = session.find("Transfer where parent=69732302fd379c8fff1089d0 and user=6676f3e9c7ef4e27da254e57")

This will return a list of all active transfer jobs beneath the delivery, to fetch all finished transfer you need to supply finished=True argument.


Download from delivery
======================

The accsyn API is not able to download files files from a delivery, 
you need to use the accsyn desktop app and then use the API to create a transfer job for the files.

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
    A client must be registered, by the same user as the API session.

    Make sure your client is online and enabled to have download start.

    If multiple clients are online, a random client will be selected to download the files. Prepend the destination with "client=<client_id>:" to target a specific client.


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

This will return the updated delivery, as would have been returned by a delivery find query.

User's will not be able to download files from a delivery after it has been finished, if it is 
a temporary delivery - the files will be deleted after the default grace of 4 hours.

Delete a delivery
-----------------

To delete a delivery that has not been submitted, use the delete API function::

    retval = session.delete_one("Delivery", delivery["id"])

This will return True if operation was successful.

.. note::

    Tf it is a temporary delivery - the files will be deleted after the default grace of 4 hours.


Working with upload requests
============================

An upload request can either be a temporary request that will have files stored in a temp folder on default accsyn storage 
volume and then deleted on expiration, or be created pointing to an folder on and accsyn storage volume/share and submitted immediately.

A request is similar to a delivery when it comes to adding recipients and submitting the request.

Create a temporary upload request
---------------------------------

To create a temporary upload request, supply the name and the init status::

    upload_request = session.create("Request",{
        "name":"Project material",
        "recipients":["demo.user@accsyn.com"]
    })

This will return the created upload request, as would have been returned by a request find query. The request will be 
submitted immediately and the user will receive an email with a link to the request.

To create a temp request that will be submitted later::

    upload_request = session.create("Request",{
        "name":"Project material",
        "status":"init"
    })

The request will be kept in the init state for 8 hours (default) until it expires and is deleted.

Add at least one recipient and then submit the request by setting the status to pending (see above)

Create upload reqest to a storage folder
----------------------------------------

To create an upload request to a folder on the the default volume supply the path to the folder and the recipients::

    upload_request = session.create("Request",{
        "name":"Provide project material",
        "destination":"share=(default)/source/from_client",
        "recipients":["demo.user@accsyn.com"]
    })

This will return the created upload request, as would have been returned by a request find query. The request will be 
submitted immediately and the user will receive an email with a link to the request.

To create a request that will be submitted later, supply with the 'init' status (see above)