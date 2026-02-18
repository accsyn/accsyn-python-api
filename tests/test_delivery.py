import pytest
import logging

from accsyn_api.session import AccsynException

from conftest import STANDARD_USER_EMAIL, STANDARD_EMPLOYEE_EMAIL

TEMP_DELIVERY_NAME = "Project references temp"
TEMP_DELIVERY_NAME_EMPLOYEE = "Project references temp (EMP)"
DELIVERY_NAME = "Project references"

@pytest.mark.base
@pytest.mark.order(1)
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
        session_admin.grant("User", STANDARD_USER_EMAIL, "Delivery", delivery["id"], {"invite": False})
    # Add unknown recipient to delivery
    session_admin.grant("User", STANDARD_USER_EMAIL, "Delivery", delivery["id"])
    # Submit now should fail
    with pytest.raises(AccsynException):
        session_admin.update("Delivery", delivery["id"], {"status": "pending"})
    # TODO: Upload file and wait for completion
    # TODO: Submit and verify delivery
    # Invite employee to workspace
    employee = session_admin.create("User",{
        "code":STANDARD_EMPLOYEE_EMAIL,
        "role":"employee"
    })
    entities.remember(kind="user", temp_name="e1", entity_id=employee["id"])


@pytest.mark.base
@pytest.mark.order(2)
def test_create_temp_delivery_as_employee(session_employee, entities):
    # Should fail as employee have no access to any volumes
    with pytest.raises(AccsynException):
        session_employee.create("Delivery",{
            "name":TEMP_DELIVERY_NAME_EMPLOYEE
        })

@pytest.mark.base
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

@pytest.mark.base
@pytest.mark.order(2)
def test_create_delivery_from_existing(session_admin, entities):
    # Create a pending delivery from an existing file
    delivery = session_admin.create("Delivery",{
        "name":"Project files",
        "tasks":["bad_buck_bunny.png"],
        "status":"init"
    })
    entities.remember(kind="delivery", temp_name="d1", entity_id=delivery["id"])
    assert delivery["name"] == "Project files"

def test_create_delivery_form_existing_standard_should_fail(session_standard):
    with pytest.raises(AccsynException):
        session_standard.create("Delivery", {
            "name": "Project files from standard user",
            "tasks": ["projects/references"],
            "recipients": ["demo.user@accsyn.com"]
        })

def test_create_from_temp(session_admin, entities):
    delivery = session_admin.create("Delivery",{
        "name":"Project references",
        "status":"init"
    })
    entities.remember(kind="delivery", temp_name="d1", entity_id=delivery["id"])
    assert delivery["name"] == "Project references"
"""