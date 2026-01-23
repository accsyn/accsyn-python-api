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

A file delivery can either be created from existing files on an accsyn storage volume or as a temporary delivery that will 
have files uploaded to it at a later stage and then submitted.

Create from existing files
==========================

To create and submit a file delivery with two files, supply the source files as a list of paths and a list of recipients::

    delivery = session.create("Delivery",{
        "name":"Project reference",
        "tasks":["project/reference.png", "project/description.txt"],
        "recipients":["demo.user@accsyn.com"]
    })

The user will receive an email with a link to the delivery, and the files will be available for download for the default duration of one month.


Create a pending delivery
=========================

A pending delivery will have its files uploaded to a temp folder on default accsyn storage volume, that will be deleted after the delivery is done (expired) or aborted.

To create a pending delivery, supply the source files as a list of paths and a list of recipients::

    delivery = session.create("Delivery",{
        "name":"Project references",
        "status":"init"
    })


Download from delivery
======================

The accsyn API is not able to download files from a delivery, you need to use the accsyn desktop app or user server to download files from a delivery.

First, query the delivery to get the delivery ID::

    delivery = session.find_one("Delivery")
    print(delivery["name"])

To download the file(s) from a delivery, make sure your client is online::

    transfer = session.create("Transfer", {
        "parent": delivery["id"],
        "destination": "/tmp",
        "name": "Download '{}'".format(delivery["name"])
    })

