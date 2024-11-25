..
    :copyright: Copyright (c) 2022 accsyn

.. _misc:

****************************
Miscellaneous API operations
****************************


Retrieve session key::

    session.get_session_key()

Will return a string with your session key.

.. note::

    The session key can only be used by other API instances within the same device and should be treated as a secret password and not to be shared with other users as they would gain access to files on your shares. They will expire, typically within an hour and will need to be refreshed.



Check if the accsyn app or daemon (user server) is running on the same machine and same user ID::

    session.app_is_running()

    session.daemon_is_running()

Will return True if GUI/Server is running, False if offline, None if not installed/detected.



