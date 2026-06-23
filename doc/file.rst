..
    :copyright: Copyright (c) 2022 accsyn

.. _file:

***************
File operations
***************

Besides working with entities, the API supports file operations on volumes (admins, employees) or on a specific shared folder, home, or collection (admins, employees, and restricted users depending on ACLs).


List files on storage
=====================


To list files on the share "thefilm-DIT", subfolder TO_ACMEFILM::

   session.ls("share=thefilm-DIT/TO_ACMEFILM")

Optional arguments:

* ``recursive``: Recursive listing, ``True`` or ``False``. Default ``False`` (see below).
* ``maxdepth``: (Recursive listing) Limit depth, positive integer >= 1.
* ``directories_only``: Return only directories. Default ``False``.
* ``files_only``: Return only files. Default ``False``. Note: ``recursive=True`` has no effect with this flag.
* ``getsize``: Calculate and return directory sizes.
* ``include``: Filter expression (string or list) for inclusion: ``"word"`` (exact), ``"*word"`` (ends with), ``"word*"`` (starts with), ``"*word*"`` (contains), ``"start*end"`` (starts and ends with), ``"re('...')"`` (regular expression). Takes precedence over ``exclude``.
* ``exclude``: Filter expression (string or list) for exclusion, same syntax as ``include``.



On success, this returns a list of dictionaries, one per file::

    {
        "result": [
            {
                "type":1,
                "filename":"pitch.mov",
                "size":81632,
                "modified":datetime(..)
            }
        ]
    }



* ``Type``: File type; 0 = directory, 1 = file.
* ``Filename``: File or directory name.
* ``Size``: File or directory size.
* ``Modified``: Python ``datetime`` of last modification.


By default, subdirectories are not traversed. Pass ``recursive=True`` to return all visible files::

    session.ls("share=thefilm-DIT", recursive=True)

On success, nested files appear in a ``files`` list within each directory entry::

    {
        "result": [
            {
                "filename":"TO_ACMEFILM",
                ..,
                "files":[
                   {"filename":"A001_C001.mov",...},
                   {...},
                ]
            }
        ]
    }



To search a directory and subdirectories for a specific filename, use ``include``::

    session.ls("share=Documentation", include="FindMe.doc", recursive=True)


To exclude files matching a regular expression, use ``exclude``::

    session.ls("share=Documentation", exclude="re('_Draft.*')")

.. note::

    ``include`` and ``exclude`` can be combined; ``include`` takes precedence.

For case-insensitive matching::

    session.ls("share=thefilm-DIT/TO_ACMEFILM", exclude="re('_draft.*', 'I')")

List files in a collection by code::

    files = session.ls("collection=filecollection")

List files in a delivery::

    files = session.ls("delivery=69732302fd379c8fff1089d0")


Failure scenarios
*****************

* Permission denied; an exception is raised.
* Share/path does not exist; an exception is raised. Call ``session.get_last_message()`` for details.



Check if a file/directory exists
================================

To check if a file exists::

    session.exists("workarea=thefilm-DIT/TO_ACMEFILM/final.mov")


On success, returns ``true`` or ``false``::

    {
        "result": True
    }


Failure scenarios
*****************

 * Permission denied; no read access to the folder.
 * Server is down; no online server to perform the operation.
 * Share/path does not exist.


Get size on disk
================

Get total size of a file or all files beneath a directory (requires read access)::

    session.getsize("share=thefilm-DIT/TO_ACMEFILM")

Optional arguments:

 * ``maxdepth``: Limit depth, positive integer >= 1.


On success, returns the size in bytes::

    {
        "result": 10462211
    }


Failure scenarios
*****************

An exception is raised if the operation fails:

* Permission denied; no read access to the folder.
* Server is down; no online server to perform the operation.
* Share/path does not exist.


Create directory
================

To create directory ``__UPLOAD`` at share ``projects`` (requires write access)::

    session.mkdir("share=projects/__UPLOAD")

Returns ``{"result":true}`` on success. On failure, an exception is raised — call ``session.get_last_message()`` for details.

Failure scenarios
*****************

* Permission denied; no write access to the parent folder.
* Parent directory does not exist.
* Directory already exists.


Rename a file or directory
==========================

Rename ``share=thefilm-DIT/TO_ACMEFILM/pitch.mov`` to ``share=thefilm-DIT/TO_ACMEFILM/pitch_new.mov`` (requires write access)::

    session.rename("share=thefilm-DIT/TO_ACMEFILM/pitch.mov","share=thefilm-DIT/TO_ACMEFILM/pitch_new.mov")

Returns ``{"result":true}`` on success; otherwise an exception is raised.

Failure scenarios
*****************

* Permission denied; no read access to source or no write access to destination.
* Source file/directory does not exist.
* Destination parent directory does not exist.


Move a file or directory
========================

Move ``share=thefilm-DIT/TO_ACMEFILM/pitch.mov`` to ``share=thefilm-DIT/TO_ACMEFILM/QT/pitch.mov`` (requires write access)::

    session.mv("share=thefilm-DIT/TO_ACMEFILM/pitch.mov","share=thefilm-DIT/TO_ACMEFILM/QT/pitch.mov")

Returns ``{"result":true}`` on success; otherwise an exception is raised.


Failure scenarios
*****************

* Permission denied; no read access to source or no write access to destination.
* Source file/directory does not exist.
* Destination directory cannot be created or written.


Delete a file or directory
==========================

.. warning::

    Automating file removal through API calls can delete unintended directories. Safeguard and test/dry-run your calls before production use.

Remove directory ``share=thefilm-DIT/TO_ACMEFILM/QT`` (requires write access)::

    session.delete("share=thefilm-DIT/TO_ACMEFILM/QT")

Returns ``{"result":true}`` on success; otherwise an exception is raised — call ``session.get_last_message()`` for details.

Failure scenarios
*****************

* Permission denied; no write access to the target.
* If the target is a non-empty directory: ``{"message":"Cannot delete non-empty directory 'share=thefilm-DIT/TO_ACMEFILM/QT'!"}``. Pass ``force=True`` to delete anyway: ``session.delete("share=thefilm-DIT/TO_ACMEFILM/QT", force=True)``.
* Removal failed due to locked files or server-side permission issues. Contact your domain administrator.


Multiple file operations
========================

Multiple file operations can be batched in one call by supplying a list::

    session.ls(["share=thefilm-DIT/folder","share=other/folder2"], recursive=True)

On success, returns a list of result dictionaries per operation::

    {
        [
            {
                "path": "share=thefilm-DIT/folder",
                "result": [
                    {
                        "filename":"delivery",
                        ..
                    }
                ]
            }
        ,
            {
                "path": "share=other/folder2",
                "result": [
                    {
                        "filename":"test",
                        ..
                    }
                ]
            }
        ]
    }



.. note::

    Retrieve the most recent failure message with::

            session.get_last_message()
