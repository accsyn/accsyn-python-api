..
    :copyright: Copyright (c) 2022 accsyn

.. _publish:

*******
Publish
*******

The accsyn publish workflow is an extended upload mechanism that lets you validate files before upload, control where they are written, and collect user metadata. See the tutorial for full details:

`https://support.accsyn.com/tutorial-publish-workflow <https://support.accsyn.com/tutorial-publish-workflow>`_.

The Python API supports the publish workflow for building client-side tools.


Pre publish
===========

Supply the list of file/directory names to validate at the server, with a unique ID and sub-files/directories as needed. The ID must be a uuid4 — accsyn uses it to relate each publish entry to its task on job submit::

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


This returns the same list with additional entries appended by your pre-publish hook::

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



Or raises an exception on failure.

Then submit the job as usual, passing publish data as a hook and matching IDs on tasks::

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

This runs the hook after files are transferred to the location determined by the pre-publish hooks.

