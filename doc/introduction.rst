..
    :copyright: Copyright (c) 2026 accsyn

.. _introduction:

************
Introduction
************

The accsyn Python API integrates into Python 3.7+ applications and tooling, providing direct encrypted communication with accsyn over the REST :term:`API` via HTTPS.

Example use cases:
==================

- Automate file transfer and render-farm workflows by creating jobs programmatically.
- Fetch and display an accsyn :term:`transfer` in your own UI, with control over pause, resume, and abort.
- Create delivery packages or upload requests to receive material from customers or deliver final deliverables.
- Manage shared folders and collections programmatically — expose project-specific file areas to external users in response to events in your production systems.


Limitations:
============

- Request results are static dictionaries. The API does not update returned objects after retrieval or provide local caching. Monitoring job progress, for example, requires polling.

- The API does not support multi-operation transactions. Each create, update, or delete commits immediately.

- The Python API cannot send files or act as a :term:`client` entity. It instructs the accsyn backend to spawn a transfer between a server (typically identified by domain, share, and path) and a client (typically identified by username/email and/or client ID/hostname). The API works without a locally installed file transfer client.

- accsyn Media Vault operations are not supported — for example, creating or managing titles or media entities.


Other resources:
================

For broader accsyn development documentation, visit the Developer Hub:

`https://support.accsyn.com/developer <https://support.accsyn.com/developer>`_

Our tutorials cover how to configure accsyn for specific workflows. Many include complete source code:

`https://support.accsyn.com <https://support.accsyn.com>`_

Source code samples using the API are available on GitHub:

`https://github.com/accsyn/accsyn-python-api <https://github.com/accsyn/accsyn-python-api>`_
