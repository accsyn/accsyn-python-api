..
    :copyright: Copyright (c) 2022 accsyn

.. _file:

***************
File operations
***************

Besides working with entities, the API supports file operation on share level (admins, employees) or on a specific share (admins, employees and restricted users depending on ACLs).


List files on remote server
===========================


To list files on the share “thefilm-DIT”, subfolder TO_ACMEFILM::

   session.ls("share=thefilm-DIT/TO_ACMEFILM")

Optional arguments:

* ``recursive``: Do a recursive listing, True or False. Default False, see below.
* ``maxdepth``:  (Recursive listing)   Limit number of levels to descend, positive integer greater than or equal 1.
* ``directories_only``: Return only directories in listing, True or False. Default is False.
* ``files_only``: Return only files in listing, True or False. Default is False. Note: Providing recursive=True won't have any affect.
* ``getsize``: Calculate and return size of directories.



If succeeds, this will return a list of dictionaries, one for each file found::

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



* ``Type``: The type of file; 0 is directory/folder, 1 is a file.
* ``Filename``: The name of the file or directory.
* ``Size``: The size of the file or directory.
* ``Modified``: A Python datetime object holding the date file was last modified.


By default, it does not dig down into sub directories.  Add "recursive=True" to the call in order to have all (visible) files returned::

    session.ls("share=thefilm-DIT", recursive=True)

If succeeds, this will return a list of dictionaries, one for each file found, with further descendant files in a list::

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


Failure scenarios
*****************

* Permission denied; An exception will be thrown.
* Share/Path does not exists; An exception will be thrown, obtain the message by calling session.get_last_message().



Check if a file/directory exist
===============================

To check if a file exists::

    session.exists("workarea=thefilm-DIT/TO_ACMEFILM/final.mov")


If succeeds, this will return true or false::

    {
        "result": True
    }


Failure scenarios
*****************

 * Permission denied; you do not have read access to folder.
 * Server is down; server at organization is not online to perform the requested operation.
 * Share/Path does not exists;

Get size on disk
================

Get total size of file or all files beneath a directory::

    session.getsize("share=thefilm-DIT/TO_ACMEFILM")

Optional arguments:

 * ``maxdepth``:  Limit number of levels to descend, positive integer greater than or equal 1.


If succeeds, this will return the size of the file/directory::

    {
        "result": 10462211
    }


Failure scenarios
*****************

An exception will be thrown if listing fails. Possible reasons include:

* Permission denied; you do not have read access to folder.
* Server is down; server at organization is not online to perform the requested operation.
* Share/Path does not exists;

Create directory
================

To create directory “__UPLOAD” at the share “projects”::

    session.mkdir("share=projects/__UPLOAD")

Will return ; {"result":true} if successful, otherwise an exception to be thrown, obtain the message by calling session.get_last_message()):

Failure scenarios
*****************

* Permission denied; You do not have write access to the parent folder.
* Parent directory does not exist;
* Directory already exists;


Rename a file or directory
===============================

Rename file “share=thefilm-DIT/TO_ACMEFILM/pitch.mov” to “share=thefilm-DIT/TO_ACMEFILM/pitch_new.mov”::

    session.rename("share=thefilm-DIT/TO_ACMEFILM/pitch.mov","share=thefilm-DIT/TO_ACMEFILM/pitch_new.mov")

If rename went well  {“result”:true} will be returned, otherwise an exception to be thrown

Failure scenarios
*****************

* Permission denied; You do not have read access to the source file/folder or do not have write access to the destination file/folder.
* Source file/directory does not exist.
* Destination parent directory does not exist.


Move a file or directory
===============================

Move file “share=thefilm-DIT/TO_ACMEFILM/pitch.mov” to “share=thefilm-DIT/TO_ACMEFILM/QT/pitch.mov”::

    session.mv("share=thefilm-DIT/TO_ACMEFILM/pitch.mov","share=thefilm-DIT/TO_ACMEFILM/QT/pitch.mov")

If move went well  {“result”:true} will be returned, otherwise an exception to be thrown.


Failure scenarios
*****************

* Permission denied; You do not have read access to the source file/folder or do not have write access to the destination file/folder.
* Source file/directory does not exist.
* Destination directory cannot be created or written.


Delete a file or directory
==========================

.. warning::

    Automising file removal through API calls can cause unwanted directories to be deleted, always test/dry run your calls before you put  them into production!

Remove the directory “share=thefilm-DIT/TO_ACMEFILM/QT”::

    session.rm("share=thefilm-DIT/TO_ACMEFILM/QT")

Will return {“result”:true}  if  successful, otherwise an exception to be thrown, obtain the message by calling session.get_last_message()):

Failure scenarios
*****************

* Permission denied; You do not have write access to the file/folder that is to be deleted.
* If target is a directory and contains files, exception will say: {“message”:”Cannot delete non-empty directory 'share=thefilm-DIT/TO_ACMEFILM/QT'!”}. To have it deleted anyway, supply the force flag: session.delete("share=thefilm-DIT/TO_ACMEFILM/QT",force=True).
* The removal failed to to locked files or other permission problems on server. Contact domain adminstrator.


Multiple file operations
========================

Multiple file operations can be made with one call, to do that supply a list of operations::

    session.ls(["share=thefilm-DIT/folder","share=other/folder2"], recursive=True)

If succeeds, this will return a list of dictionaries with result for each operation::

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

    Obtain the most recent failure message by issuing::

            session.get_last_message()

