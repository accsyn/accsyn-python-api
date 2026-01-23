import pytest

from accsyn_api.session import AccsynException

@pytest.mark.order(1)
def test_create_delivery_from_existing(session_admin, entities_admin):
    delivery = session_admin.create("Delivery",{
        "name":"Project files",
        "tasks":["projects/references"],
        "recipients":["demo.user@accsyn.com"]
    })
    entities_admin.remember(kind="delivery", temp_name="d1", entity_id=delivery["id"])
    assert delivery["name"] == "Project files"

def test_create_delivery_form_existing_standard_should_fail(session_standard):
    with pytest.raises(AccsynException):
        session_standard.create("Delivery", {
            "name": "Project files from standard user",
            "tasks": ["projects/references"],
            "recipients": ["demo.user@accsyn.com"]
        })

#def test_create_from_temp(session_admin, entities):
#    delivery = session_admin.create("Delivery",{
#        "name":"Project references",
#        "status":"init"
#    })
#    entities.remember(kind="delivery", temp_name="d1", entity_id=delivery["id"])
#    assert delivery["name"] == "Project references"