import pytest
import logging

from accsyn_api.session import AccsynException

from conftest import TEST_ADMIN_EMAIL, TEST_EMPLOYEE_EMAIL, TEST_USER_EMAIL

TEMP_DELIVERY_NAME = "Project references temp"
TEMP_DELIVERY_NAME_EMPLOYEE = "Project references temp (EMP)"
TEMP_DELIVERY_NAME_STANDARD = "Project references temp (STA)"
DELIVERY_NAME = "Project references"
DELIVERY_NAME_EMPLOYEE = "Project references (EMP)"
DELIVERY_NAME_STANDARD = "Project references (STA)"

@pytest.mark.order(1)
def test_prepare_deliveries(session_admin, entities):
    # Prepare tests, remove employee and standard user if they exist
    admin_user = session_admin.find_one(f"User WHERE code='{TEST_ADMIN_EMAIL}'")
    employee_user = session_admin.find_one(f"User WHERE code='{TEST_EMPLOYEE_EMAIL}'")
    if employee_user:
        session_admin.delete_one("User", employee_user["id"])
        entities.remove_from_cleanup(kind="e1", entity_id=employee_user["id"])
    standard_user = session_admin.find_one(f"User WHERE code='{TEST_USER_EMAIL}'")
    if standard_user:
        session_admin.delete_one("User", standard_user["id"])
        entities.remove_from_cleanup(kind="s1", entity_id=standard_user["id"])
    # Make sure server is running
    server = session_admin.find_one(f"Server WHERE roles CONTAINS storage")
    assert server is not None, "No storage server found"
    assert server.status == "online", "Storage server is not online"
    # Make sure admin has a client running, app or user server type
    client = session_admin.find_one(f"Client WHERE user={admin_user['id']} AND type in 0,2")
    assert client is not None, "No client found for admin, please login app or setup a user server"
    assert client.status == "online", "Client is not online"

# Create temp

@pytest.mark.order(2)
def test_create_temp_delivery(session_admin, entities):
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
        session_admin.grant("User", TEST_USER_EMAIL, "Delivery", delivery["id"], {"invite": False})
    # Add unknown recipient to delivery, should be invited
    session_admin.grant("User", TEST_USER_EMAIL, "Delivery", delivery["id"])
    # Submit now should fail - have no files uploaded yet
    with pytest.raises(AccsynException):
        session_admin.update("Delivery", delivery["id"], {"status": "pending"})
    # TODO: Upload file and wait for completion
    # TODO: Submit and verify delivery
    # Invite employee to workspace
    employee = session_admin.create("User",{
        "code":TEST_EMPLOYEE_EMAIL,
        "role":"employee"
    })
    entities.remember(kind="user", temp_name="e1", entity_id=employee["id"])

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

# Upload
@pytest.mark.order(5)
def test_upload_file_to_temp_delivery(session_admin, entities):
    # Assume 
    delivery_id = entities.get_id("delivery", "d1")
    delivery = session_admin.get_entity("Delivery", delivery_id)
    assert delivery is not None
    

#@pytest.mark.extended
@pytest.mark.order(99)
def test_delete_temp_delivery(session_admin, entities):
    # Delete delivery
    delivery_id = entities.get_id("delivery", "d1")
    delivery = session_admin.get_entity("Delivery", delivery_id)
    assert delivery is not None
    result = session_admin.delete_one("Delivery", delivery["id"])
    assert result is True
    # Remove from cache
    entities.remove_from_cleanup(kind="delivery", entity_id=delivery["id"])

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