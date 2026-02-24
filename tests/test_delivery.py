import pytest
import logging
import time

from accsyn_api.session import AccsynException

from conftest import TestUtils

TEMP_DELIVERY_NAME = "Project references temp"
TEMP_DELIVERY_NAME_EMPLOYEE = "Project references temp (EMP)"
TEMP_DELIVERY_NAME_STANDARD = "Project references temp (STA)"
DELIVERY_NAME = "Project references"
DELIVERY_NAME_EMPLOYEE = "Project references (EMP)"
DELIVERY_NAME_STANDARD = "Project references (STA)"

@pytest.mark.order(1)
def test_prepare_deliveries(session_admin, entities):
    # Prepare tests, remove employee and standard user if they exist
    admin_user = session_admin.find_one(f"User WHERE code='{TestUtils.get_admin_ident()}'")
    employee_user = session_admin.find_one(f"User WHERE code='{TestUtils.get_employee_ident()}'")
    if employee_user:
        session_admin.delete_one("User", employee_user["id"])
        entities.remove_from_cleanup(kind="e1", entity_id=employee_user["id"])
    standard_user = session_admin.find_one(f"User WHERE code='{TestUtils.get_standard_ident()}'")
    if standard_user:
        session_admin.delete_one("User", standard_user["id"])
        entities.remove_from_cleanup(kind="s1", entity_id=standard_user["id"])
    # Make sure server is running
    server = session_admin.find_one(f"Server WHERE roles CONTAINS storage")
    assert server is not None, "No storage server found"
    assert server["status"] == "online", "Storage server is not online"
    # Make sure admin has a client running, app or user server type
    client = session_admin.find_one(f"Client WHERE user={admin_user['id']} AND type in 0,2")
    assert client is not None, "No client found for admin, please login app or setup a user server"
    assert client["status"] == "online", "Client is not online"
    # Invite employee to workspace
    employee = session_admin.create("User",{
        "code":TestUtils.get_employee_ident(),
        "role":"employee"
    })
    entities.remember(kind="user", temp_name="e1", entity_id=employee["id"])

# Create temp delivery
@pytest.mark.order(2)
def test_create_temp_delivery_as_admin(session_admin, entities):
    # Create a pending delivery living in a temp folder on default volume
    delivery = session_admin.create("Delivery",{
        "name":TEMP_DELIVERY_NAME
    })
    entities.remember(kind="delivery", temp_name="d1", entity_id=delivery["id"])
    assert delivery["name"] == TEMP_DELIVERY_NAME
    # Submit delivery now should fail
    with pytest.raises(AccsynException):
        session_admin.update("Delivery", delivery["id"], {"status": "pending"})
    # Add unknown recipient to delivery, with invitation not allowed should fail
    with pytest.raises(AccsynException):
        session_admin.grant("User", TestUtils.get_standard_ident(), "Delivery", delivery["id"], {"invite": False})
    # Submit now should fail - have no files or recipients yet
    with pytest.raises(AccsynException):
        session_admin.update("Delivery", delivery["id"], {"status": "pending"})

@pytest.mark.order(3)
def test_create_temp_delivery_as_employee(session_employee, entities):
    # Should fail as employee have no access to any volumes
    with pytest.raises(AccsynException):
        session_employee.create("Delivery",{
            "name":TEMP_DELIVERY_NAME_EMPLOYEE
        })

@pytest.mark.order(4)
def test_create_temp_delivery_as_standard(session_standard, entities):
    # Should fail as standard user have no access to create deliveries
    with pytest.raises(AccsynException):
        session_standard.create("Delivery",{
            "name":TEMP_DELIVERY_NAME_STANDARD
        })

@pytest.mark.order(5)
def test_read_temp_delivery_as_admin(session_admin, entities):
    delivery_id = entities.get_id("delivery", "d1")
    delivery = session_admin.get_entity("Delivery", delivery_id)
    assert delivery is not None
    TestUtils.validate_response(delivery, ["name", "status", "public", "user"], 
    should_exclude=["data","config","tasks"])

@pytest.mark.order(6)
def test_read_temp_delivery_as_employee(session_employee, entities):
    # Should fail as employee have no access to any volumes
    delivery_id = entities.get_id("delivery", "d1")
    delivery = session_employee.get_entity("Delivery", delivery_id)
    assert delivery is None

@pytest.mark.order(7)
def test_read_temp_delivery_as_standard(session_standard, entities):
    # Should fail as standard user have no access to delivery
    delivery_id = entities.get_id("delivery", "d1")
    delivery = session_standard.get_entity("Delivery", delivery_id)
    assert delivery is None

@pytest.mark.order(8)
def test_add_recipient_to_temp_delivery_as_admin(session_admin, entities):
    delivery_id = entities.get_id("delivery", "d1")
    result = session_admin.grant("User", TestUtils.get_standard_ident(), "Delivery", delivery_id)
    assert result is True
    # Verify recipient is added
    recipients = session_admin.access("Delivery", delivery_id)
    assert len(recipients) == 1
    assert recipients[0]["user_hr"] == TestUtils.get_standard_ident()
    # Test submit, should fail - have no files uploaded yet
    with pytest.raises(AccsynException):
        session_admin.update("Delivery", delivery_id, {"status": "pending"})

@pytest.mark.order(9)
def test_add_recipient_to_temp_delivery_as_employee(session_employee, entities):
    # Should fail as employee has no access to volume related to delivery
    delivery_id = entities.get_id("delivery", "d1")
    with pytest.raises(AccsynException):
        session_employee.grant("User", TestUtils.get_standard_ident(), "Delivery", delivery_id)

@pytest.mark.order(10)
def test_add_recipient_to_temp_delivery_as_standard(session_standard, entities):
    # Should fail as standard user has no access to deliveries
    delivery_id = entities.get_id("delivery", "d1")
    with pytest.raises(AccsynException):
        session_standard.grant("User", TestUtils.get_standard_ident(), "Delivery", delivery_id)


# Upload and submit
@pytest.mark.order(20)
def test_upload_file_to_temp_delivery(session_admin, entities):
    # Assume delivery is created and ready to receive files
    delivery_id = entities.get_id("delivery", "d1")
    delivery = session_admin.get_entity("Delivery", delivery_id)
    assert delivery is not None
    transfer = session_admin.create("Transfer", {
        "parent": delivery["id"],
        "source": TestUtils.get_data_path("bad_buck_bunny.png")
    })
    assert transfer is not None
    # Wait for transfer to complete (move to finished)
    logging.info(f"Waiting for upload {transfer['name']} to complete")
    while transfer["status"] != "done":
        time.sleep(1)
        t = session_admin.get_entity("Transfer", transfer["id"])
        if t is None:
            break
        logging.info(f"Transfer {t['name']} is {t['status']}")
        if t["status"] in ["failed"]:
            raise AccsynException(f"{t['name']} derailed!")
    logging.info(f"Upload {transfer['name']} completed")
    entities.remember(kind="transfer", temp_name="t1", entity_id=transfer["id"])

@pytest.mark.order(21)
def test_upload_file_to_temp_delivery_as_employee(session_employee, entities):
    # Should fail as employee have no access to any volumes
    delivery_id = entities.get_id("delivery", "d1")
    with pytest.raises(AccsynException):
        session_employee.create("Transfer", {
            "parent": delivery_id,
            "source": TestUtils.get_data_path("bad_buck_bunny.png")
        })

@pytest.mark.order(22)
def test_upload_file_to_temp_delivery_as_standard(session_standard, entities):
    # Should fail as standard user have no access to deliveries
    delivery_id = entities.get_id("delivery", "d1")
    with pytest.raises(AccsynException):
        session_standard.create("Transfer", {
            "parent": delivery_id,
            "source": TestUtils.get_data_path("bad_buck_bunny.png")
        })

@pytest.mark.order(23)
def test_submit_temp_delivery(session_admin, entities):
    delivery_id = entities.get_id("delivery", "d1")
    delivery = session_admin.update("Delivery", delivery_id, {"status": "pending"})
    # Make sure it is on the move
    assert delivery["status"] != "init"
    # Wait for delivery to enter waiting state
    while delivery["status"] in ["pending"]:
        time.sleep(1)
        delivery = session_admin.get_entity("Delivery", delivery_id)
        logging.info(f"Delivery {delivery['name']} is {delivery['status']}")
    assert delivery["status"] == "waiting"


@pytest.mark.order(24)
def test_abort_temp_delivery_as_employee(session_employee, entities):
    delivery_id = entities.get_id("delivery", "d1")
    with pytest.raises(AccsynException):
        session_employee.update("Delivery", delivery_id, {"status": "aborted"})

@pytest.mark.order(25)
def test_pause_temp_delivery_as_standard(session_standard, entities):
    # Should fail as standard user have no access to deliveries
    delivery_id = entities.get_id("delivery", "d1")
    with pytest.raises(AccsynException):
        session_standard.update("Delivery", delivery_id, {"status": "aborted"})

@pytest.mark.order(26)
def test_abort_temp_delivery_as_admin(session_admin, entities):
    delivery_id = entities.get_id("delivery", "d1")
    delivery = session_admin.update("Delivery", delivery_id, {"status": "aborted"})
    assert delivery["status"] == "aborted"

@pytest.mark.order(97)
def test_delete_temp_delivery_as_employee(session_employee, entities):
    # Should fail as employee have no access to any volumes
    delivery_id = entities.get_id("delivery", "d1")
    with pytest.raises(AccsynException):
        session_employee.delete_one("Delivery", delivery_id)

@pytest.mark.order(98)
def test_delete_temp_delivery_as_standard(session_standard, entities):
    # Should fail as standard user have no access to deliveries
    delivery_id = entities.get_id("delivery", "d1")
    with pytest.raises(AccsynException):
        session_standard.delete_one("Delivery", delivery_id)

#@pytest.mark.extended
@pytest.mark.order(99)
def test_delete_temp_delivery(session_admin, entities):
    # Delete delivery
    delivery_id = entities.get_id("delivery", "d1")
    result = session_admin.delete_one("Delivery", delivery_id)
    assert result is True
    # Remove from cache
    entities.remove_from_cleanup("delivery", delivery_id)

"""

@pytest.mark.order(100)
def test_create_delivery(session_admin, entities):
    # Create a pending delivery from an existing file
    delivery = session_admin.create("Delivery",{
        "name":DELIVERY_NAME,
        "tasks":["bad_buck_bunny.png"],
        "status":"init",
    })
    entities.remember(kind="delivery", temp_name="d2", entity_id=delivery["id"])
    assert delivery["name"] == DELIVERY_NAME


def test_create_delivery_form_existing_standard_should_fail(session_standard):
    with pytest.raises(AccsynException):
        session_standard.create("Delivery", {
            "name": "Project files from standard user",
            "tasks": ["projects/references"],
            "recipients": [TEST_USER_EMAIL]
        })

"""