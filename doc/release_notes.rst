..
    :copyright: Copyright (c) 2021 accsyn/HDR AB

.. _release_notes:

*************
Release Notes
*************

.. note::

    The accsyn overall changelog can be accessed here: 

    `https://support.accsyn.com <https://support.accsyn.com>`_.

.. release:: 3.0.2
    :date: 2024-11-18

    .. change:: fix

        * Replaced organization > workspace.

.. release:: 3.0.1
    :date: 2024-11-18

    .. change:: fix

        * Bug fixes.

.. release:: 3.0.0
    :date: 2024-11-17

    .. change:: feat

        * Compliance with new accsyn v3 workspaces.
        * Removed pwd and session key authentication, accsyn v3 only support API key basic auth.

.. release:: 2.2.0
    :date: 2023-11-09

    .. change:: feat

        * Include and exclude filter expressions to file 'ls' & 'getsize' operations.

.. release:: 2.1.4
    :date: 2023-10-17

    .. change:: fix

        * Documentation build fix.

.. release:: 2.1.3
    :date: 2023-10-03

    .. change:: new

        * Connect and read timeout argument added to session init.

.. release:: 2.1.0
    :date: 2022-12-02

    .. change:: new

        * Support for retrieving and applying settings for a scope, entity or integration.

    .. change:: new

        * Integration utility function (used by ftrack-accsyn-accessor)


.. release:: 2.0.3
    :date: 2021-10-04

    .. change:: fix

        * Fixed bug in PyPi source packaging


.. release:: 2.0.2
    :date: 2021-08-30

    .. change:: fix

        * Fixed bug in payload compression


    .. change:: change

        * Replaced update_one and update_many; Code sryle


.. release:: 2.0.1

    .. change:: new

        * (Share) Support for server assignment.
        * Support for offlining shares and users.
        * (Query) Support for listing offline entities.
        * Mew ``mkdir``,``rename``,``mv`` and ``rm`` file operations.

    .. change:: changed

        * Documentation moved from Google sites to readthedocs.io.
        * Code styling.


.. release:: 1.4.1
    :date: 2021-04-11

    .. change:: changed

        * ``Session.generate_session_key(liftime)`` - generates a new session key, with the given lifetime in seconds.
        * Now reads the ACCSYN_SESSION_KEY environment variable.

.. release:: 1.4.0-3
    :date: 2020-11-05

    .. change:: changed

        * Brought back ``Session.get_api_key()``, to be able enable this in future backend updates.

.. release:: 1.4.0-2
    :date: 2020-11-05

    .. change:: fixed

        * p3k bug fixes.

.. release:: 1.3.5
    :date: 2020-08-01

    .. change:: changed

        * (Create) Returns a list if multiple entities were created.
        * PEP-8 compliant.
        * b2; (py3k) removed 'long' usage.

    .. change:: fixed

        * b3; (py3k) fixed TypeError: a bytes-like object is required, not 'str'.

.. release:: 1.3.4
    :date: 2020-07-30

    .. change:: changed

        * New function ``get_session_key`` that returns the current session key retreived at authentication, and can be used for subsequent authentications throughout the lifetime of key.
        * New argument 'session_key' to Session(..) construct, will make API to attempt authenticate using the session key instead of API key. The session key are bound to the IP and device detected upon creation.

    .. change:: fixed

        * (task query) Fixed bug where additional expression were not detected.

.. release:: 1.3.1
    :date: 2020-07-22

    .. change:: new

        * File ``ls``; Now supports getsize attribute. If true, sizes will be calculated and returned for folders within file listings. Have no effect if 'files_only' attribute is set.

.. release:: 1.2.7
    :date: 2020-05-22

    .. change:: new

        * (Session init) Support for logging to file.
        * (Session init) Tell Accsyn to log JSON indented in verbose mode.
        * (find attributes) Choose which type of attributes to query: find(default), create (allowed when creating an antity) and update (allowed when updating).

.. release:: 1.2.5
    :date: 2020-04-01

    .. change:: changed

        * Create task; If another tasks exists with same source and destination, it is retried instead of added as duplicate. If argument 'allow_duplicates' is supplied as False, an exception will be thrown.

.. release:: 1.2.4
    :date: 2020-01-01

    .. change:: new

        * Pre-publish support.
        * Query and update job tasks support.
        * Bug fixes.

.. release::  1.2.2
    :date: 2019-10-10

    .. change:: fixed

        * Fixed bug in rename.

.. release:: 1.2.1
    :date: 2019-10-01

    .. change:: changed

        * Renamed from FilmHUB.

    .. change:: fixed

        * Fixed bug in rename.


.. release:: 1.1.4
    :date: 2019-08-25

    .. change:: changed

        * Python 3 support.

    .. change:: fixed

        * Not retrying twice if timeout, could cause for example two jobs to be created.