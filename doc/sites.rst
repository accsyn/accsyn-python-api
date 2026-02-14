..
    :copyright: Copyright (c) 2026 accsyn

.. _sites:

*****
Sites
*****

A site is a physical or cloud location where accsyn can be deployed by installing an accsyn server, enabling site to site file transfers and compute jobs.


Query
=====

To list sites::

    sites = session.find("Site")

This will return a list of all sites, including built-in sites, with their attributes.

Create
======

To create a site::

    site = session.create("Site",{
        "name":"Stockholm",
        "description":"Stockholm office"
    })


A dict will be returned containing queue attributes::

    {
        "accsyn": false,
        "code": "stockholm",
        "created": "2026-02-12T11:25:43",
        "creator": "demo.admin@accsyn.com",
        "description": "Stockholm office",
        "id": "698db8b7aa985445979d473d",
        "main": false,
        "name": "Stockholm",
        "status": "enabled"
    }


Explanation of the returned attributes:

* ``accsyn``: If True, this site is the built-in accsyn hosting site. This is the default site for cloud (non BYOS) workspaces.
* ``code``: The unique API identifier of the site, is auto generated from name if not provided. Can be used when referring to the site in API calls with the accsyn path notation: "site=<code>:share=<share_code>/path/to/file".
* ``created``: Date of creation.
* ``creator``: The user who created the queue, 'accsyn' means it is created by the backend.
* ``main``: If True, this site is the main on-premise site for the workspace. New servers are assigned the main site by default.
* ``description``: Description of the site.
* ``id``: The internal accsyn site id, use this when modifying the site later on.
* ``metadata``: Site metadata dict.
* ``modified``: Date of last modification.
* ``modifier``: The user that most recently modified the site.
* ``name``: The name of the site.
* ``status``: The status of site, can be "enabled" or "disabled".


Modify
======

To disable a site::

    session.update("Site", "698db8b7aa985445979d473d", {"status" :"disabled"})

A dict will be returned containing same attributes as when queried.

To enable the site again::

    session.update("Site", "698db8b7aa985445979d473d", {"status" :"enabled"})


.. note::

    Site settings has to be modified throught the admin pages `https://accsyn.io/admin/sites <https://accsyn.io/admin/sites>`_.


Delete
======

To delete a site::

    session.delete_one("Site", "698db8b7aa985445979d473d")

.. note::

    * No servers can be assigned to the site, move these servers to another site before deleting.
    * No transfers can be active involving the site, abort these transfers before deleting.
    * The main site cannot be deleted, assign another site as main before deleting.