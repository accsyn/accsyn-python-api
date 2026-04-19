..
    :copyright: Copyright (c) 2026 accsyn

********
Settings
********

Use settings helpers to list, set, and delete configuration values on workspace and entity scopes.

Reading settings
================

.. code-block:: python

    from accsyn_api import Session

    session = Session()

    # Workspace settings
    workspace_settings = session.get_settings(
        "workspace",
        None,
    )

    # Queue settings, with inherited settings merged
    queue_settings = session.get_settings(
        "queue",
        "<queue_id>",
    )

    # Queue settings, with only the queue's own settings but filling in defaults
    queue_settings = session.get_settings(
        "queue",
        "<queue_id>",
        upstream=False,
    )

    # Queue settings, with only the queue's own settings and no defaults
    queue_settings = session.get_settings(
        "queue",
        "<queue_id>",
        upstream=False,
        omit_defaults=True,
    )


Setting a value
===============

.. code-block:: python

    ok = session.set_setting(
        "queue",

        "compute_avoid",
        "enable-clear-on-resume",
        entityid="<queue_id>",
    )
    assert ok is True

Deleting a value
================

.. code-block:: python

    ok = session.delete_setting(
        "job",
        "compute_avoid",
        entityid="<queue_id>",
    )
    assert ok is True
