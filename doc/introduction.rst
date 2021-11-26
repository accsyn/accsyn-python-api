..
    :copyright: Copyright (c) 2021 accsyn

.. _introduction:

************
Introduction
************

The accsyn Python API allows for easy integration into Python (v2.7 & v3.4+) enabled third party applications, enabling
direct communication with accsyn via the low level REST :term:`API` over https.

With the API you can for example:

- Create automated workflows that reacts on an event and then dispatches data (files/metadata) across the globe, in a safe and controlled environment.
- Fetch and display accsyn a transfer :term:`job` in your own user interface, also enabling control in terms of pause, resume and abort.
- Handle shares automatically, allowing expose of project dedicated file areas with one or more external users, upon an event in your production systems.


.. note::

    The result of a request is static dictionaries, meaning that API will not attempt to dynamically updated any returned objects after they have been retrieved or harbor and local caching of any kind This means that for example continous monitor of job progress requires polling.


.. note::

    The API also do not support multi-operation transactions, meaning that any create, update or delete operation will
    commit instantly.


.. note::

    The Python API are not able to send files and act as a :term:`client`, it can only tell accsyn backend to spawn a
    transfer between a server (typically identified by a domain, share and path) and a client (typically identified by
    a user name/E-mail and/or client ID/hostname). This means that the API will work independent of a locally installed
    file transfer client.


Other resources:
================

This documentation the most common use cases, syntax of API calls are also shown within the accsyn webapp/admin pages @ https://<yourdomain>.accsyn.com, at the bottom of each page.

Our tutorials covers how to setup accsyn to achieve a certain functionality and many of them come with complete source code, find the tutorials here: 

`https://support.accsyn.com <https://support.accsyn.com>`_.

Find source code samples using the API at our public GitHub:

`https://github.com/accsyn/accsyn-python-api <https://github.com/accsyn/accsyn-python-api>`_
