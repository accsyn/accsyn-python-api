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


Read logs for a transfer:

.. code-block:: python

    # Jopb logs
    print(session.logs("Transfer", entityid="6aad45ce991535260e495da9")['result'])


Reading process logs
====================

Use ``processlogs`` to fetch the detailed process log (console output, e.g. the detailed transfer log) of a job. The
job is identified by ``entityid``, and the full backend response dict is returned. The log console output is in
``text_master`` for the master process and ``text_slave`` for the slave process, the returned try in ``try`` and the 
total number of tries in ``try_count``.

Without ``uri``, the backend picks the first task of the job that has been processed (has a log):

.. code-block:: python

    # Log for the first processed task of the job
    response = session.processlogs("6aad45ce991535260e495da9")
    print(response["text"])
    print("Tries: {}".format(response.get("try_count")))

With ``uri``, the log of that specific task is returned. Optionally supply ``try_num`` (zero-based) to read the log of
an earlier attempt, default is the latest:

.. code-block:: python

    # Log for a specific task
    response = session.processlogs("6aad45ce991535260e495da9", uri="<task uri>")
    print(response["text_master"])

    # Log for the first try of a specific task
    response = session.processlogs("6aad45ce991535260e495da9", uri="<task uri>", try_num=0)
    print(response["text_master"])

    # Fetch the slave (file server party) log instead, can only be done by operators and for transfer jobs
    response = session.processlogs("6aad45ce991535260e495da9", master=False, slave=True)
    print(response["text_slave"])


App and daemon status
=====================

Check whether the accsyn app or daemon (user server) is running on the same machine under the same user::

    session.app_is_running()

    session.daemon_is_running()

Returns ``True`` if the GUI/server is running, ``False`` if offline, ``None`` if not installed or detected.



