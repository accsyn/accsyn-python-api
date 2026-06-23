..
    :copyright: Copyright (c) 2026 accsyn

.. _sites:

*****
Sites
*****

A site is a physical or cloud location where accsyn is deployed by installing an accsyn server, enabling site-to-site file transfers and compute jobs.


Query
=====

To list sites::

    sites = session.find("Site")

This returns all sites, including built-in sites, with their attributes.

Create
======

To create a site::

    site = session.create("Site",{
        "name":"Stockholm",
        "description":"Stockholm office"
    })


A dict is returned containing site attributes::

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

* ``accsyn``: If ``True``, this is the built-in accsyn hosting site — the default for cloud (non-BYOS) workspaces.
* ``code``: Unique API identifier, auto-generated from name if not provided. Used in accsyn path notation: ``site=<code>:share=<share_code>/path/to/file``.
* ``created``: Date of creation.
* ``creator``: User who created the site. ``accsyn`` means the backend created it.
* ``main``: If ``True``, this is the main on-premise site. New servers are assigned to the main site by default.
* ``description``: Site description.
* ``id``: Internal accsyn site ID. Use this when modifying the site.
* ``metadata``: Site metadata dict.
* ``modified``: Date of last modification.
* ``modifier``: User who last modified the site.
* ``name``: Site name.
* ``status``: ``enabled`` or ``disabled``.


Modify
======

To disable a site::

    session.update("Site", "698db8b7aa985445979d473d", {"status" :"disabled"})

A dict is returned with the same attributes as a query.

To enable the site again::

    session.update("Site", "698db8b7aa985445979d473d", {"status" :"enabled"})


.. note::

    Additional site settings are managed through the admin pages: `https://accsyn.io/admin/sites <https://accsyn.io/admin/sites>`_.


Delete
======

To delete a site::

    session.delete_one("Site", "698db8b7aa985445979d473d")

.. note::

    * No servers may be assigned to the site. Move them to another site first.
    * No active transfers may involve the site. Abort them first.
    * The main site cannot be deleted. Assign another site as main first.
