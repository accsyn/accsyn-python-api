..
    :copyright: Copyright (c) 2022 accsyn

.. _misc:

****************************
Miscellaneous API operations
****************************

Reading logs
============

Use ``logs`` to fetch backend disk logs for a scope/entity. The return value is the raw backend response dict and currently includes at least ``{"result": [...]}``.

.. code-block:: python

    # Workspace logs
    logs_response = session.logs("workspace")
    entries = logs_response.get("result", [])

    # Filtered and sorted logs with optional pagination controls
    logs_response = session.logs(
        "workspace",
        search="error",
        sort="date",
        sort_reverse=True,
        pagination_page=1,
        pagination_limit=50,
    )


App and daemon status
=====================

Check if the accsyn app or daemon (user server) is running on the same machine and same user ID::

    session.app_is_running()

    session.daemon_is_running()

Will return True if GUI/Server is running, False if offline, None if not installed/detected.



