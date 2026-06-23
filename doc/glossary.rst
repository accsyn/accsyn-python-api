..
    :copyright: Copyright (c) 2021 accsyn/HDR

********
Glossary
********

.. glossary::

    api
        Application programming interface.

    python
        A programming language for automation and systems integration. See http://www.python.org

    domain
        The accsyn backend instance orchestrating file transfers and compute jobs across servers and clients. Identified by the workspace ``code`` attribute.

    user
        A user entity identifying a person interacting with accsyn. See :ref:`users`.

    role
        User access level defining base permissions, overridable for global API keys. Three roles exist: Admin, Employee, and Standard (restricted, default). See :ref:`users`.

    volume
        Base folder entity on a server from which accsyn serves files. See :ref:`filesharing`.

    folder
        Folder beneath a volume where standard/restricted users receive access through a :term:`acl`. See :ref:`filesharing`.

    home
        Dedicated user folder beneath a volume, with access granted through a :term:`acl`. See :ref:`filesharing`.

    collection
        Collection of files and/or folders across one or more volumes, with access granted through a :term:`acl`. See :ref:`filesharing`.

    acl
        Access Control List entity defining share (or directory) access for a standard/restricted user.

    transfer
        Job entity holding tasks — files and/or directories synchronised between two network endpoints (P2P), or a compute job. See :ref:`transfers`.

    compute
        Job entity defining long-running compute-intensive tasks. Also called a "render job". See :ref:`compute`.

    delivery
        Job entity defining files and/or directories delivered to one or more recipients. See :ref:`deliveries`.

    request
        Job entity defining files and/or directories requested (uploaded) from one or more senders. See :ref:`deliveries`.

    task
        File and/or directory synchronised between two network endpoints (P2P), or a compute task. See :ref:`transfers`.

    queue
        Container entity for jobs with its own dispatch priority. See :ref:`queues`.

    site
        Remote physical location with a unique name. New servers default to on-prem site ``hq``; desktop clients and user servers use ``roaming``, with effective site determined by WAN IP. During compute submit, the site determines whether dependency sync is required.

    desktop application
        accsyn desktop GUI for receiving, submitting, and monitoring jobs. Represents a :term:`client` that connects to a remote :term:`server` during transfer.

    server
        accsyn server daemon for unattended data transmission and computation. Runs a :term:`client` configured to serve one or more volumes (see :ref:`filesharing`), listening for connections from another :term:`client` — desktop app, web browser, :term:`site server`, or :term:`user server`.

    site server
        Server type managing file transfer to and from a main :term:`server` at a remote site for one or more volumes.

    user server
        Server type running in user space for unattended file transfers to and from locally mapped shares/volumes.

    client
        Instance of the accsyn desktop application or background daemon capable of file transfers or compute execution.

    engine
        Entity defining a compute (render) engine and its Python wrapper script. See :ref:`compute`.

    metadata
        Custom JSON data bound to an entity, split into internal (hidden from standard users) and external (visible to all). Supplied to hooks during execution for workflow purposes.
