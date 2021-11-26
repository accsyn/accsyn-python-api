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
        your systems more effectively. Often used in creative industries. Visit
        the language website at http://www.python.org

    domain
        The accsyn backend instance orchestrating file transfers/compute jobs across servers and clients.

    user
        A user entity, identifying a human interacting with accsyn.

    role
        The user access level defining the base permissions, which can be overridden for
        global API keys. Three different roles currently exist: Admin, Employee and Standard/restricted(default) user.

    root share
        The base folder entity, on a server, that accsyn can server files from.

    share
        A sub folder entity, beneath a root share, were standard/restricted users can be
        given access to by a :term:`acl`.

    acl
        Access Control List entity, normally defining a share (or a directory) beneath
        a share were a standard/restricted user have download (and upload) access.

    job
        A entity which holds a set of tasks - files and/or directories to be synchronized between two network
        endpoints (P2P), or a compute job for processing data.

    task
        A file and/or directory to be synchronized between two network
        endpoints (P2P), or a compute task for processing data.

    queue
        A container entity for jobs, having it's own priority in which jobs are dispatched in queue order.

    app
        The accsyn desktop GUI application, designed for receiving, submitting and monitoring jobs. Represents a :term:`client`
        which connects to a remote :term:`server` during transfer process.

    server
        The accsyn server background daemon designed for unattended transmission of data and computations. Represents a
        :term:`client` which, in case configured to serve a :term:`root share`, listens for incoming connections from another
        :term:`app`, :term:`site server` or :term:`user server`.

    site server
        A special type of server, responsible for managing file transfer to and from a main :term:`server`, for one or more root shares.

    user server
        A special type of server, running in user space, for unattended file transfers to and from locally mapped shares/root shares.

    client
        An entity capable of perform file transfers or executing computations.

    app
        An entity defining



