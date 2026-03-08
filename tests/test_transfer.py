import pytest
import logging
import time

from accsyn_api.session import AccsynException

from conftest import TestUtils, TEST_FILE, TEST_FILE2

TEMP_TRANSFER_NAME = "Jönssonligan dyker upp igen"

@pytest.mark.order(0)
def test_prepare_transfer(session_admin, entities):
    # Prepare tests, remove file at storage
    for filename in [TEST_FILE, TEST_FILE2, TEST_FILE2]:
        if not session_admin.exists(filename):
            continue
        session_admin.delete(filename)
        assert session_admin.exists(filename) is False

@pytest.mark.order(2)
def test_upload(session_admin, entities):
    # Test upload to root at default volume 
    transfer = session_admin.create("Transfer", {
        "source": TestUtils.get_data_path(TEST_FILE),
        "destination":TEST_FILE,
        "name":TEMP_TRANSFER_NAME,
        "status":"paused"
    })
    assert transfer is not None
    entities.remember(kind="transfer", temp_name="t1", entity_id=transfer["id"])

@pytest.mark.order(2)
def test_resume_upload(session_admin, entities):
    # Test resume and finish upload
    transfer_id = entities.get_id("transfer", "t1")
    transfer = session_admin.get_entity("Transfer", transfer_id)
    assert transfer is not None
    transfer = session_admin.update("Transfer", transfer_id, {"status":"waiting"})
    assert transfer["status"] == "waiting"

    logging.info(f"Waiting for upload {transfer['name']} to complete")
    while transfer["status"] != "done":
        time.sleep(1)
        t = session_admin.find_one(f"Transfer WHERE id={transfer['id']}")
        if t is None:
            break # Job done
        logging.info(f"Transfer {t['name']} is {t['status']}")
        if t["status"] in ["failed"]:
            raise AccsynException(f"{t['name']} derailed!")

@pytest.mark.order(3)
def test_append_to_upload(session_admin, entities):
    transfer_id = entities.get_id("transfer", "t1")
    transfer = session_admin.get_entity("Transfer", transfer_id) # Need to use get_entity to get the finished job    
    assert transfer is not None
    result = session_admin.create("Job", {
        "source": TestUtils.get_data_path(TEST_FILE2),
        "destination":TEST_FILE2,
        "append":True
    })
    assert result['id'] == transfer_id # Should be same job
    assert result['status'] != "done" # Job should be revived

    logging.info(f"Waiting for upload {transfer['name']} to complete")
    while transfer["status"] != "done":
        time.sleep(1)
        t = session_admin.find_one(f"Transfer WHERE id={transfer['id']}")
        if t is None:
            break # Job done
        logging.info(f"Transfer {t['name']} is {t['status']}")
        if t["status"] in ["failed"]:
            raise AccsynException(f"{t['name']} derailed!")

@pytest.mark.order(4)
def test_create_nonexistent_upload_task(session_admin, entities):
    transfer_id = entities.get_id("transfer", "t1")
    transfer = session_admin.get_entity("Transfer", transfer_id)   
    assert transfer is not None
    result = session_admin.create("Task", {
        "source": TestUtils.get_data_path("nonexistent.txt"),
        "destination":"nonexistent.txt",
    }, entityid=transfer_id)
    logging.info(f"Nonexistent task create result: {result}")
    # Will return a list of tasks
    assert isinstance(result, dict)
    task = result
    # Make sure only 

    # Check job status
    transfer = session_admin.get_entity("Transfer", transfer_id)  
    assert result['status'] == "waiting"

    logging.info(f"Waiting for upload {transfer['name']} to fail")
    while transfer["status"] != "failed":
        time.sleep(1)
        t = session_admin.find_one(f"Transfer WHERE id={transfer['id']}")
        if t is None:
             raise AccsynException(f"{t['name']} finished when it should have failed!")
        logging.info(f"Transfer {t['name']} is {t['status']}")
        if t["status"] not in ["waiting","running","failed"]:
            raise AccsynException(f"{t['name']} derailed!")

    # Query tasks and do some basic validation
    tasks = session_admin.find("Task", entityid=transfer_id)
    logging.info(f"Task query result: {tasks}")
    assert isinstance(tasks, list)
    assert len(tasks) == 3


@pytest.mark.order(5)
def test_modify_task(session_admin, entities):
    # Set the failing task to onhold
    transfer_id = entities.get_id("transfer", "t1")
    transfer = session_admin.get_entity("Transfer", transfer_id)   
    assert transfer is not None
    result = session_admin.update_many("Task", transfer["id"], [{
        "uri":"2",
        "status":"onhold"
    }])
    assert result is not None
    assert isinstance(result, list)
    assert len(result) == 1
    task = result[0]
    assert task['uri'] == "2"
    assert task['status'] == "onhold"

    logging.info(f"Waiting for upload {transfer['name']} to pause")
    while transfer["status"] != "paused":
        time.sleep(1)
        t = session_admin.find_one(f"Transfer WHERE id={transfer['id']}")
        if t is None:
             raise AccsynException(f"{t['name']} finished when it should have failed!")
        logging.info(f"Transfer {t['name']} is {t['status']}")
        if t["status"] not in ["failed","paused"]:
            raise AccsynException(f"{t['name']} derailed!")

@pytest.mark.order(20)
def test_download_task(session_admin, entities):
    # Set the failing task to onhold
    pass
