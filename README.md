# accsyn-python-api
Official AccSyn fast film delivery Python API

Complete Python API reference can be found [here](https://support.accsyn.com/python-api).


Changelog:
----------
v1.3-4
  * (task query) Fixed bug where additional expression were not detected.
  * New function 'get_session_key' that returns the current session key retreived at authentication, and can be used for subsequent authentications throughout the lifetime of key.
  * New argument 'session_key' to Session(..) construct, will make API to attempt authenticate using the session key instead of API key. The session key are bound to the IP and device detected upon creation.
  * PEP-8 compliant.

v1.3-1
  * (ls) Now supports getsize attribute. If true, sizes will be calculated and returned for folders within file listings. Have no effect if 'files_only' attribute is set.

v1.2-7

  * (Session init) Support for logging to file.
  * (Session init) Tell Accsyn to log JSON indentented in verbose mode.
  * (find attributes) Choose which type of attributes to query: find(default), create (allowed when creating an antity) and update (allowed when updating).

v1.2-5

  * b4; Create task; If another tasks exists with same source and destination, it is retried instead of added as dupliace. If argument 'allow_duplicates' is supplied as False, an exception will be thrown.

v1.2-4

  FEATURES
  * b1; Pre-publish support.
  * b2; Query and update job tasks support.
  * b3; Bug fixes.

v1.2-2

   BUG FIXES
   * b1; Fixed bug in rename.

v1.2-1

  FEATURES 
  (b=build)
  * b1; Renamed from FilmHUB.

  BUG FIXES
  * b2; Fixed bug in rename.


v1.1-4
   
   FEATURES 
   (b=build)
   * b2; Python 3 support.

   BUG FIXES
   * b2; Not retrying twice if timeout, could cause for example two jobs to be created.


Henrik Norin, HDR AB, 2020
Accsyn(r) - secure data delivery and workflow sync
https://accsyn.com 
https://support.accsyn.com

