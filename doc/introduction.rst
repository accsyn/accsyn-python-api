..
    :copyright: Copyright (c) 2026 accsyn

.. _introduction:

************
Introduction
************

The accsyn Python API allows for easy integration into Python (v3.7+) enabled third party applications or tooling, enabling
direct encrypted communication with accsyn via the low level REST :term:`API` over https.

With the API you can for example:

- Create automated file transfer or render farm workflows where jobs can be created programmatically.
- Fetch and display accsyn a :term:`transfer` in your own user interface, also enabling control in terms of pause, resume and abort.
- Manage shares programmatically, allowing expose of project dedicated file areas with one or more external users, upon an event in your production systems.


Limitations:
============

- The result of a request is static dictionaries, meaning that API will not attempt to dynamically updated any returned objects after they have been retrieved or harbor and local caching of any kind This means that for example continous monitor of job progress requires polling.

- The API also do not support multi-operation transactions, meaning that any create, update or delete operation will commit instantly.

- The Python API are not able to send files and act as a :term:`client`, it can only tell accsyn backend to spawn a transfer between a server (typically identified by a domain, share and path) and a client (typically identified by a user name/E-mail and/or client ID/hostname). This means that the API will work independent of a locally installed file transfer client.

- The API only support file transfer/compute and file sharing related operations, Media Vault operations are not supported.


Other resources:
================

This documentation the most common use cases, syntax of API calls are also shown within the accsyn webapp/admin pages @ https://accsyn.io, at the bottom of each page.

Our tutorials covers how to setup accsyn to achieve a certain functionality and many of them come with complete source code, find the tutorials here: 

`https://support.accsyn.com <https://support.accsyn.com>`_.

Find source code samples using the API at our public GitHub:

`https://github.com/accsyn/accsyn-python-api <https://github.com/accsyn/accsyn-python-api>`_
