..
    :copyright: Copyright (c) 2026 accsyn

.. _using:


.. currentmodule:: accsyn_api.session

*****
Using
*****

.. highlight:: python

In a Python session, import the accsyn Python API to start using it::

    import accsyn_api


Create a session
================

The session is the object used to communicate with the accsyn workspace backend. Valid API credentials are required at creation::

    session = accsyn_api.Session(workspace='acmefilm',username='john@user.com', api_key='BlrPCfxLIRZEdhL6LXotwXRmDWbPRsPgLYcpa7ubyu97gxpqSC4130Adfh968Low')



The following environment variables are read from the parent Python process and override arguments passed to the Session constructor:

.. list-table:: env mappings
   :widths: 100 100
   :header-rows: 1

   * - Environment:
     - Parameter:
   * - ACCSYN_WORKSPACE
     - workspace
   * - ACCSYN_API_USER
     - username
   * - ACCSYN_API_KEY
     - api_key


.. note::

    accsyn communicates over TCP port 443 (HTTPS-wrapped CRUD REST calls). Allow outgoing traffic to your workspace backend (``https://your-workspace.accsyn.com``), where ``your-workspace`` is your unique workspace API code.

    Obtain your API key at `https://accsyn.io/developer <https://accsyn.io/developer>`_ or from the desktop app under Settings > API.

    Treat the API key as a secret — it grants access to list and modify files on your accsyn shared storage.

    Pass ``verbose=True`` at session creation to enable verbose debug output.

    Pass ``path_logfile=/path/to/my.log.file`` to redirect stdout to a log file.


Testing the session
===================

To verify the API is working, test the session::

    print(session.find_one("User"))

Should output your user profile::

    {
       "id":"5b0faf03304bfd4810dbd5fc",
       "code":"john@user.com",
       "modified":datetime("2018-06-04 07:06:41.028619")
    }



Query
=====

The ``find`` and ``find_one`` functions provide query functionality.

To get a list of all entities of a certain entity type::

   entities = session.find('<entitytype>')

Where ``<entitytype>`` is the entity type — for example ``transfer``, ``delivery``, ``user``, or ``share``.

Return a single entity of a certain entity type::

   job = session.find_one('<entitytype> WHERE id=<id>')

Where ``<id>`` is the internal accsyn entity ID.


Expressions
***********

The accsyn API uses a query language that is based on a simplified SQL syntax::

    session.find('Transfer WHERE source=myworkspace')

Returns a list of all download jobs (workspace code/domain is "myworkspace").

.. note::

    The syntax is simpler than SQL. The accsyn API supports nested AND/OR operations with ``=``, ``!=``, and ``<>``.

    Queries are case-insensitive — for example, ``transfer`` and ``Transfer`` are equivalent, as are ``WHERE`` and ``where``. Throughout this documentation, we use uppercase for WHERE and operators for readability.

Example of a nested complex query::

    session.find('transfer WHERE ((user=lisa@example.com AND destination=hq) OR status<>failed) AND code="* backup"')

This query returns transfers where the user is lisa@example.com and the destination is site hq, or the status is not failed, and the code (name) ends with `` backup`` (``*`` is a wildcard).


Operators
*********

The accsyn API supports the following operators:

.. list-table:: accsyn query operators
   :widths: 20 100
   :header-rows: 1

   * - Operator:
     - Description:
   * - =
     - Equal to the value on the right hand side.
   * - !=
     - Not equal to the value on the right hand side.
   * - <>
     - Not equal to the value on the right hand side.
   * - <
     - Less than the value on the right hand side.
   * - >
     - Greater than the value on the right hand side.
   * - <=
     - Less than or equal to the value on the right hand side.
   * - >=
     - Greater than or equal to the value on the right hand side.
   * - in
     - Matches one of the values in the comma(,) separated list on the right hand side string expression.
   * - not in
     - Does not match any of the values in the comma(,) separated list on the right hand side string expression.
   * - contains
     - Attribute (string) contains the given substring on the right hand side.
   * - not contains
     - Attribute (string) does not contain the given substring on the right hand side.
   * - matches
     - Attribute (string) matches the regular expression on the right hand side
   * - not matches
     - Attribute (string) does not match the regular expression on the right hand side.

Example of substring match::

    session.find('Transfer WHERE name CONTAINS "backup"')

Example of regular expression match::

    session.find('Transfer WHERE name matches "backup.*\\.zip"')

.. note::

    All comparisons are case insensitive.
    If string value contains whitespace, it must be enclosed in quotes(').
    The attribute to compare must be on the left hand side of the operator, and the value to compare must be on the right hand side. For example, "name=X" is valid, but "X=name" is not.
    Regular expression syntax is that of the accsyn backend (commonly Python-style).



Limit
*****

To return only a limited set of attributes::

    session.find_one('Transfer WHERE id=614d660de50d45bb027c9bdd', attributes=['source','destination'])


To run a paginated query, that skips 100 jobs and only returns a maximum of 50::

    session.find('Transfer', skip=100, limit=50)


Create
======

To create an entity, supply the entity type (string) and data as a dictionary payload::

    session.create(<entitytype>, <data>)


Modify
======

To modify an entity, supply the entity type (string), entity ID (string), and data as a dictionary payload::

    session.update(<entitytype>, <id>, <data>)


Delete
======

To delete an entity, supply the entity type (string) and entity ID (string)::

    session.delete_one(<entitytype>, <id>)


Example of obtaining and modifying an accsyn file transfer
==========================================================

Get a job named "my_transfer"::

    transfer = session.find_one('Transfer WHERE name="my_transfer"')


Change its status::

    session.update('Transfer', transfer['id'], {"status":"aborted"}) 


Delete (archive) the transfer::

    session.delete_one('Transfer', transfer['id'])



From here, see :ref:`datatypes` or the sections below for details on users, jobs, queues, and other entities.


Error handling
==============

If an error occurs, an exception is raised. Retrieve the message with::

    print(session.get_last_message())

If the workspace backend or reverse proxy is throttling your client IP, you may receive HTTP **429 Too Many Requests**. See :ref:`rate_limits` for limit details and recommended backoff behaviour.


Network proxy support
=====================

If your network does not have direct Internet access, the Python API can use a SOCKS (v4/v5) proxy or an accsyn daemon acting as a proxy (see the accsyn admin manual for proxy setup).

Using a SOCKS proxy
*******************

Supply ``proxy="socks:<hostname or IP>:<port>"`` when creating the session, or set the ``ACCSYN_PROXY`` environment variable.

Using an accsyn network proxy
*****************************

Supply ``proxy="accsyn:<hostname or IP>:<port>"`` when creating the session, or set the ``ACCSYN_PROXY`` environment variable.



.. _rate_limits:

Rate limits
===========

accsyn protects workspace backends against abuse with rate limits at the reverse proxy and in the backend layer.
Python API clients should treat throttling as a normal operational condition and back off when requests are delayed or rejected.


Overview
********

Protection is applied in two layers:

1. **Edge (nginx)** — limits request rate and concurrent connections per client IP before traffic reaches the backend.
2. **Backend Service** — applies additional per-IP throttling on sensitive REST endpoints (for example authentication and unauthenticated probes), using logarithmic delays and a hard HTTP 429 cutoff for sustained abuse.

These limits apply per public client IP. Traffic from many users behind the same NAT or corporate egress may share one IP and therefore share one limit bucket.


Edge limits (nginx)
*******************

Hosted workspace nodes terminate HTTPS in nginx and proxy to the local REST (API/clients/CLI) and GraphQL (Web/App) services. Typical limits per client IP:

.. list-table:: nginx rate limits
   :widths: 30 20 20 30
   :header-rows: 1

   * - Path prefix
     - Sustained rate
     - Burst
     - Notes
   * - ``/api``
     - 30 requests/s
     - 60
     - REST API (used by the Python API)
   * - ``/graphql``
     - 20 requests/s
     - 40
     - GraphQL API
   * - ``/proxy``, ``/u``, ``/d``
     - 20 requests/s
     - 40
     - Download/proxy routes
   * - All HTTPS locations
     - —
     - 100 concurrent connections
     - Per-IP connection cap

When nginx rejects a request, the response status is **429 Too Many Requests**.


Application limits (REST)
*************************

The REST backend tracks repeated requests per IP in a short sliding window (approximately five minutes). Behaviour:

- The **first** request in a window is not delayed.
- Further requests from the same IP incur a **logarithmic delay** (up to about 10 seconds) before the backend processes the call.
- After **50 recorded hits** in the window, the backend responds with **429** and a ``Retry-After`` header instead of sleeping further.

Application throttling is especially relevant for:

- ``/api/v3/api/auth`` (API key authentication)
- Unauthenticated or lightly authenticated endpoints
- Repeated failed authentication attempts

Successful, well-spaced API calls from a single integration are unlikely to hit these limits under normal use.


HTTP 429 responses
******************

A throttled response may look like:

.. code-block:: json

    {
        "message": "Too many requests, please try again later.",
        "retry_after": 120
    }

The ``Retry-After`` response header (seconds) indicates how long to wait before retrying.


Recommendations for Python API clients
**************************************

- **Use exponential backoff** when you receive HTTP 429 or notice increasing latency on auth or REST calls.
- **Respect ``Retry-After``** when present; do not retry immediately in a tight loop.
- **Cache sessions** — create one ``Session`` and reuse it; avoid re-authenticating on every ``find`` or ``update`` call.
- **Poll responsibly** — when monitoring job progress, use intervals of several seconds (or longer) rather than sub-second polling.
- **Serialise bulk operations** — batch creates/updates with short pauses if you are driving large automated workflows.
- **Handle shared egress** — if many services exit through one IP, coordinate request volume or stagger jobs.

Example backoff after a failed request:

.. code-block:: python

    import time

    def call_with_backoff(session, entitytype, query, max_attempts=5):
        delay = 1.0
        for attempt in range(max_attempts):
            try:
                return session.find_one(f"{entitytype} WHERE {query}")
            except Exception:
                if attempt == max_attempts - 1:
                    raise
                time.sleep(delay)
                delay = min(delay * 2, 60)


.. note::

    The Python API does not currently retry throttled requests automatically. Unattended integrations should catch errors, inspect ``session.get_last_message()``, and apply backoff as shown above.


