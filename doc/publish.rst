..
    :copyright: Copyright (c) 2022 accsyn

.. _publish:

*******
Publish
*******

The accsyn publish workflow is an extended upload mechanism allowing you to check the files before upload, decide where the should be written and allow user to input metadata. It is described in detail in this tutorial:


`https://support.accsyn.com/tutorial-publish-workflow <https://support.accsyn.com/tutorial-publish-workflow>`_.


The Python API supports the publish workflow and can be used for building your own client-side tools.


Pre publish
===========

Supply the list of file-/directory names that should be checked at server end, supplying an unique ID and
sub files-/directories as necessary.  The ID should be a uuid4 and is required for accsyn to relate each
publish entry with each task on job submit later on::

    pre_publish_response = session.publish([
       {
          "id":"33d59998-c980-4b82-9f6d-06ce27201d26",
          "filename":"first_file",
          "size":10240,
          "is_dir":false
       },
       {
          "id":"dda32b0f-36e5-4a5f-9379-fdfabfd482e1",
          "filename":"proj_task001_v001",
          "is_dir":true,
          "files":[{
             "filename":"file.0001.exr",
             "filename":"file.0002.exr",
             "size":1000000
          }]
       }
    ])


Which will return back the same list with additional entries appended by your pre-publish hook::

     {
        "files":[
            {
              "id":"33d59998-c980-4b82-9f6d-06ce27201d26",
              "filename":"first_file",
              "size":10240,
              "is_dir":false,
              "warning":"Will be uploaded but not published",
              "can_upload":true,
            },
            {
              "id":"dda32b0f-36e5-4a5f-9379-fdfabfd482e1",
              "filename":"proj_task001_v001",
              "is_dir":true,
              "files":[{
                 "filename":"file.0001.exr",
                 "filename":"file.0002.exr",
                 "size":1000000
              }],
              "ident":"abcd1234",
              "can_publish":true,
              "info":"Verified publish, please enter comment and time report"
           }
       ],
       "time_report":true,
       "comment":true,
       "guidelines":"..",
       "tasks":["proj_task001_v001","proj2_sq0010_sh0010_lighting_v0002"],
    }



 or throw an exception if something went wrong.

Then submit job as you would normally, with this publish data supplied as a hook
and corresponding ID:s supplied to tasks as well::

    jobs = session.create("job", {
        "code":"abcd1234_publish",
        "tasks":[
            {
                "id":"33d59998-c980-4b82-9f6d-06ce27201d26",
                "source":"/Volumes/NAS01/first_file",
            },
            {
                "id":"dda32b0f-36e5-4a5f-9379-fdfabfd482e1",
                "source":"/Volumes/NAS01/proj_task001_v001",
            }
        ],
        "hooks":[
            {
               "when":"hook-job-publish-server",
               "data":{"files":pre_publish_response['files']}
            }
        ]
    })

This will cause hook to be run after files has been transferred to the correct location at server, as supplied by pre publish hooks.


