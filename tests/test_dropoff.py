import pytest
import logging
import time
import sys
from datetime import datetime, timedelta

from accsyn_api.session import AccsynException

from conftest import TestUtils, TEST_FILE

TEMP_TRANSFER_NAME = "Jönssonligan dyker upp igen"


@pytest.mark.skipif(not sys.stdin.isatty(), reason="needs interactive terminal")
@pytest.mark.order(0)
def test_ensure_client(session_admin, entities):
    print("Check if the admin has a client running")
    while True:
        clients = session_admin.find("App")
        if len(clients) > 0:
            has_online = False
            for client in clients:
                if client["status"] == "online":
                    has_online = True
                    break
            if has_online:
                break
            print(f"Please launch the accsyn Desktop as {TestUtils.get_admin_ident()} and press Enter to continue...")
        else:
            print(
                f"No client found, please login to the accsyn Desktop as {TestUtils.get_admin_ident()} and press Enter to continue..."
            )
        input()
        time.sleep(2)

@pytest.mark.order(1)
def test_remove_home_share(session_admin, entities):
    print("Remove the admin's home share if exists")
    home_share = session_admin.find_one(f"Home WHERE code={TestUtils.get_admin_ident()}")
    if home_share:
        session_admin.delete_one("Home", home_share["id"])
        assert session_admin.find_one(f"Home WHERE code={TestUtils.get_admin_ident()}") is None, f"Home share {home_share['name']} still exists after deletion!"

@pytest.mark.order(2)
def test_upload_dropoff_should_fail(session_admin, entities):
    print("Test dropoff without home share, should fail")
    with pytest.raises(AccsynException):
        session_admin.create(
            "Transfer",
            {"source": TestUtils.get_data_path(TEST_FILE), "destination": f"~/{TEST_FILE}", "name": TEMP_TRANSFER_NAME},
        )

@pytest.mark.order(3)
def test_create_home_share(session_admin, entities):
    print("Creating a home share for admin")
    home_share = session_admin.create(
        "Home",
        {
            "code": TestUtils.get_admin_ident(),
            "description": f"Home share for {TestUtils.get_admin_ident()} used with automated tests",
        },
    )
    assert home_share is not None
    entities.remember(kind="home", temp_name="h1", entity_id=home_share["id"])

@pytest.mark.order(4)
def test_upload_dropoff(session_admin, entities):
    print("Test dropoff to home share")
    # First delete the file if it exists
    transfer = session_admin.create(
        "Transfer",
        {
            "source": TestUtils.get_data_path(TEST_FILE),
            "destination": "~",
            "name": f"Home dropoff: {TEMP_TRANSFER_NAME}"
        },
    )
    assert transfer is not None
    entities.remember(kind="transfer", temp_name="t1", entity_id=transfer["id"])
    logging.info(f"Waiting for upload {transfer['name']}({transfer['id']}) to finish..")
    while transfer["status"] not in ["done"]:
        time.sleep(2)
        transfer = session_admin.find_one(f"Transfer WHERE id={transfer['id']}")
        if transfer is None:
            raise AccsynException(f"{transfer['name']} disappeared!")
        logging.info(f"Transfer {transfer['name']} is {transfer['status']}")
        if transfer["status"] in ["failed","paused","aborted"]:
            raise AccsynException(f"{transfer['name']} derailed (status: {transfer['status']})!")

