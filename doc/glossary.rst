..
    :copyright: Copyright (c) 2021 accsyn/HDR

********
Glossary
********

.. glossary::

    api
        Application programming interface.

    python
        A programming language that lets you work more quickly and integrate
        your systems more effectively and create automisations. Visit
        the language website at http://www.python.org

    domain
        The accsyn backend instance orchestrating file transfers/compute jobs across servers and clients.

    user
        A user entity, identifying a human interacting with accsyn. See :ref:`users`.

    role
        The user access level defining the base permissions, which can be overridden for
        global API keys. Three different roles currently exist: Admin, Employee and Standard/restricted(default) user.
        See :ref:`users`.

    root share
        The base folder entity, on a server, that accsyn can server files from. See :ref:`shares`.

    share
        A sub folder entity, beneath a root share, were standard/restricted users can be
        given access to by a :term:`acl`. See :ref:`shares`.

    acl
        Access Control List entity, normally defining a share (or a directory) beneath
        a share were a standard/restricted user have download (and upload) access.

    job
        A entity which holds a set of tasks - files and/or directories to be synchronized between two network
        endpoints (P2P), or a compute job for processing data. See :ref:`jobs`.

    task
        A file and/or directory to be synchronized between two network
        endpoints (P2P), or a compute task for processing data. See :ref:`jobs`.

    queue
        A container entity for jobs, having it's own priority in which jobs are dispatched in queue order. See :ref:`queues`.

    site
        A remote physical location, given an unique name. New servers are assigned the on-prem default "hq" site,
        desktop clients and user servers are always assigned the "roaming" site, which means the effective site will
        be detected by analysing the WAN IP of client. During compute job submit, the site is used to determine if
        synchronization of dependencies are required.

    desktop application
        The accsyn desktop GUI application, designed for receiving, submitting and monitoring jobs. Represents a :term:`client`
        which connects to a remote :term:`server` during transfer process.

    server
        The accsyn server background daemon designed for unattended transmission of data and computations. Represents a
        :term:`client` which, in case configured to serve a :term:`root share`, listens for incoming connections from another
        :term:`app`, :term:`site server` or :term:`user server`.

    site server
        A special type of server, responsible for managing file transfer to and from a main :term:`server` at a remote site, for one or more root shares.

    user server
        A special type of server, running in user space, for unattended file transfers to and from locally mapped shares/root shares.

    client
        An instance of the accsyn desktop application, or background daemon capable of perform file transfers or executing computations.

    app
        An entity defining a compute app and its Python wrapper script.

    metadata
        Custom data bound to an entity, in JSON format, divided into an internal (invisible to standard users) and external (visible to all users). Can be used for workflow purposes - are supplied to hooks during execution.

