import pytest
import logging
import time
import sys
from datetime import datetime, timedelta

from accsyn_api.session import AccsynException

from conftest import TestUtils, TEST_FILE


@pytest.mark.skipif(not sys.stdin.isatty(), reason="needs interactive terminal")
@pytest.mark.order(0)
def test_ensure_client(session_admin, entities):
    print("Check if the admin has a client running")
    active_client = None
    while True:
        clients = session_admin.find("App")
        if len(clients) > 0:
            for client in clients:
                if client["status"] == "online":
                    active_client = client
                    break
            if active_client:
                break
            print(f"Please launch the accsyn Desktop as {TestUtils.get_admin_ident()} and press Enter to continue...")
        else:
            print(
                f"No client found, please login to the accsyn Desktop as {TestUtils.get_admin_ident()} and press Enter to continue..."
            )
        input()
        time.sleep(2)
    entities.remember(kind="client", temp_name="c", entity_id=active_client["id"], cleanup=False)
    print(f"Please remove all local share mappings on client {active_client['code']} and press Enter to continue...")
    input()

@pytest.mark.order(1)
def test_download_from_share_should_fail(session_admin, entities):
    print("Download file from share with mirror paths, should fail")
    active_client = session_admin.get_entity("Client", entities.get_id("client", "c"))
    with pytest.raises(AccsynException):
        session_admin.create(
            "Transfer",
            {
                "source": TestUtils.get_data_path(TEST_FILE), 
                "destination": f"client={active_client['id']}",
                "test": True
            },
        )
