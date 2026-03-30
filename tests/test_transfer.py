import pytest
import logging
import time
import sys
from datetime import datetime, timedelta

from accsyn_api.session import AccsynException

from conftest import TestUtils, TEST_FILE, TEST_FILE2

TEMP_TRANSFER_NAME = "Jönssonligan dyker upp igen"


@pytest.mark.order(0)
def test_prepare_transfer(session_admin, entities):
    # Prepare tests, remove file at storage
    for filename in [TEST_FILE, TEST_FILE2, TEST_FILE2]:
        if not session_admin.exists(filename):
            continue
        logging.info(f"Deleting existing file at test storage: {filename}")
        session_admin.delete(filename)
        assert session_admin.exists(filename) is False


@pytest.mark.order(1)
def test_upload_should_fail(session_admin, entities):
    # Test upload if no client, should fail as no source client exists
    if session_admin.find_one("App"):
        logging.info("A client exists, skipping upload failure test")
        return
    with pytest.raises(AccsynException):
        session_admin.create(
            "Transfer",
            {"source": TestUtils.get_data_path(TEST_FILE), "destination": TEST_FILE, "name": TEMP_TRANSFER_NAME},
        )


@pytest.mark.skipif(not sys.stdin.isatty(), reason="needs interactive terminal")
@pytest.mark.order(2)
def test_check_client(session_admin, entities):
    # Check the admin has a client running
    while True:
        clients = session_admin.find("App")
        if len(clients) > 0:
            break
        input(f"Please login to the accsyn Desktop as {TestUtils.get_admin_ident()} and press Enter to continue...")
        time.sleep(1)


@pytest.mark.order(3)
def test_upload(session_admin, entities):
    # Test upload to root at default volume
    transfer = session_admin.create(
        "Transfer",
        {
            "source": TestUtils.get_data_path(TEST_FILE),
            "destination": TEST_FILE,
            "name": TEMP_TRANSFER_NAME,
            "status": "paused",
        },
    )
    assert transfer is not None
    entities.remember(kind="transfer", temp_name="t1", entity_id=transfer["id"])
    logging.info(f"Waiting for upload {transfer['name']}({transfer['id']}) to get size")
    while transfer["size"] is None or transfer["size"] <= 0:
        time.sleep(1)
        transfer = session_admin.find_one(f"Transfer WHERE id={transfer['id']}")
        if transfer is None:
            raise AccsynException(f"{transfer['name']} disappeared!")
        logging.info(f"Transfer {transfer['name']} is {transfer['status']}")
        if transfer["status"] not in ["paused"]:
            raise AccsynException(f"{transfer['name']} derailed (status: {transfer['status']})!")


@pytest.mark.order(4)
def test_resume_upload(session_admin, entities):
    # Test resume and finish upload
    transfer_id = entities.get_id("transfer", "t1")
    transfer = session_admin.get_entity("Transfer", transfer_id)
    assert transfer is not None
    transfer = session_admin.update("Transfer", transfer_id, {"status": "waiting"})
    assert transfer["status"] == "waiting"
    logging.info(f"Resumed upload {transfer['name']}({transfer_id}), waiting for completion")
    TestUtils.wait_transfer_done(session_admin, transfer)


@pytest.mark.order(5)
def test_append_to_upload(session_admin, entities):
    transfer_id = entities.get_id("transfer", "t1")
    transfer = session_admin.get_entity("Transfer", transfer_id)  # Need to use get_entity to get the finished job
    assert transfer is not None
    logging.info(f"Appendeding file upload to {transfer['name']}({transfer_id}), waiting for completion")
    result = session_admin.create(
        "Job", {"source": TestUtils.get_data_path(TEST_FILE2), "destination": TEST_FILE2, "append": True}
    )
    assert result['id'] == transfer_id  # Should be same job
    assert result['status'] != "done"  # Job should be revived

    TestUtils.wait_transfer_done(session_admin, result)


@pytest.mark.order(6)
def test_create_nonexistent_upload_task(session_admin, entities):
    transfer_id = entities.get_id("transfer", "t1")
    transfer = session_admin.get_entity("Transfer", transfer_id)
    assert transfer is not None
    result = session_admin.create(
        "Task",
        {
            "source": TestUtils.get_data_path("nonexistent.txt"),
            "destination": "nonexistent.txt",
        },
        entityid=transfer_id,
    )
    logging.info(f"Nonexistent task create result: {result}")
    # Will return a list of tasks
    assert isinstance(result, dict)
    task = result
    # Make sure only

    # Check job status
    transfer = session_admin.get_entity("Transfer", transfer_id)
    assert transfer['status'] == "waiting"

    logging.info(f"Waiting for upload {transfer['name']} to fail")
    date_timeout = datetime.now() + timedelta(seconds=10)
    while transfer["status"] != "failed":
        time.sleep(1)
        transfer = session_admin.find_one(f"Transfer WHERE id={transfer['id']}")
        if transfer is None:
            raise AccsynException(f"{transfer['name']} finished when it should have failed!")
        logging.info(f"Transfer {transfer['name']} is {transfer['status']}")
        if transfer["status"] not in ["waiting", "running", "failed"]:
            raise AccsynException(f"{transfer['name']} derailed!")
        if datetime.now() > date_timeout:
            raise AccsynException(f"Upload {transfer['name']} task update timed out!")

    # Query tasks and do some basic validation
    tasks = session_admin.find("Task", entityid=transfer_id)
    logging.info(f"Task query result: {tasks}")
    assert isinstance(tasks, list)
    assert len(tasks) == 3


@pytest.mark.order(7)
def test_modify_task(session_admin, entities):
    # Set the failing task to onhold
    transfer_id = entities.get_id("transfer", "t1")
    transfer = session_admin.get_entity("Transfer", transfer_id)
    assert transfer is not None
    result = session_admin.update_many("Task", transfer["id"], [{"uri": "2", "status": "onhold"}])
    assert result is not None
    assert isinstance(result, list)
    assert len(result) == 1
    task = result[0]
    assert task['uri'] == "2"
    assert task['status'] == "onhold"

    logging.info(f"Waiting for upload {transfer['name']} to pause")
    date_timeout = datetime.now() + timedelta(seconds=10)
    while transfer["status"] != "paused":
        time.sleep(1)
        transfer = session_admin.find_one(f"Transfer WHERE id={transfer['id']}")
        if transfer is None:
            raise AccsynException(f"{transfer['name']} finished when it should have failed!")
        logging.info(f"Transfer {transfer['name']} is {transfer['status']}")
        if transfer["status"] not in ["failed", "paused"]:
            raise AccsynException(f"{transfer['name']} derailed!")
        if datetime.now() > date_timeout:
            raise AccsynException(f"Upload {transfer['name']} task update timed out!")


@pytest.mark.order(20)
def test_download_task(session_admin, entities):
    # Set the failing task to onhold
    pass
