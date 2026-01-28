..
    :copyright: Copyright (c) 2026 accsyn

.. _deliveries:

***************
File Deliveries
***************

A an accsyn file delivery is a persistent job that delivers one or more files to one or more recipients.

Documentation: `https://support.accsyn.com/delivery`


Create
======

A file delivery can either be created as a temporary delivery that will 
have files uploaded to it at a later stage and then submitted, or existing files on an accsyn storage volume and submitted immediately.


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


Create a pending delivery
=========================

A pending delivery will have its files uploaded to a temp folder on default accsyn storage volume, that will be deleted after the delivery is done (expired) or aborted.

To create a pending delivery, supply the source files as a list of paths and a list of recipients::

    delivery = session.create("Delivery",{
        "name":"Project references",
        "status":"init"
    })


Add a recipient to a delivery
=============================

To add a recipient to a delivery, use the assign API function::

    retval = session.assign("Delivery", "user", {
        "delivery":"69732302fd379c8fff1089d0",
        "user": "6676f3e9c7ef4e27da254e57",
    })

Return value will be True if operation was successful. The user will receive an email with a link to the delivery and instructions on how to action it.

.. note::
    
    The user will be invited to your workspace if it does not exist. First time users will be given clear instructions on how to sign up their personal accsyn account.


List recipients of a delivery
=============================

To list recipients of a delivery, use the assignments API function::

    recipients = session.assignments("Delivery", "69732302fd379c8fff1089d0")

Return value will be a list of dictionaries with recipient data:

    [{'actioned': True, 'user': '6676f3e9c7ef4e27da254e57', 'user_hr': 'demo.user@accsyn.com'}]

Actioned is True if the recipient has already actioned the delivery, False if not.

.. note::

    The user might have tried downloading the delivery but interrupted or failed, to get the full story you will need to load and inspect all transfers beneath delivery.


List file transfers beneath a delivery
======================================

To list file transfers beneath a delivery for a specific user::

    transfers = session.find("Transfer where parent=69732302fd379c8fff1089d0 and user=6676f3e9c7ef4e27da254e57")

This will return a list of transfer jobs beneath the delivery.


Remove a recipient from a delivery
==================================

To remove a recipient from a delivery, use the deassign API function::

    retval = session.deassign("Delivery", "user", {
        "delivery":"69732302fd379c8fff1089d0",
        "user": "6676f3e9c7ef4e27da254e57",
    })

This will return True if operation was successful.

.. note::

    The user will not be notified of the removal, they will need to check their deliveries to see if they are still listed.


Download from delivery
======================

The accsyn API is not able to download files from a delivery, you need to use the accsyn desktop app or user server to download files from a delivery.

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



