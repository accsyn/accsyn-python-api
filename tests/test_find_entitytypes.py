import pytest

from conftest import TEST_EMPLOYEE_EMAIL, TEST_USER_EMAIL

def _list_contains_code(value: list) -> bool:
    for item in value:
        if isinstance(item, str) and item.lower() == "code":
            return True
        if isinstance(item, dict):
            # Be resilient if backend returns attribute objects rather than strings
            if any(isinstance(k, str) and k.lower() == "code" for k in item.keys()):
                return True
            if any(isinstance(v, str) and v.lower() == "code" for v in item.values()):
                return True
    return False

@pytest.mark.order(1)
def test_find_entitytypes_as_admin(session_admin):
    """
    Test finding entitytypes as admin role.
    """
    entitytypes = session_admin.find("entitytypes")
    assert isinstance(entitytypes, list)
    assert len(entitytypes) > 2
    assert "user" in {str(x).lower() for x in entitytypes}

@pytest.mark.order(2)
def test_find_attributes_delivery_contains_code_as_admin(session_admin):
    """
    Test finding delivery attributes as admin role.
    """
    attributes = session_admin.find("attributes WHERE entitytype=delivery")
    assert isinstance(attributes, list)
    assert _list_contains_code(attributes)


@pytest.mark.order(3)
def test_create_users(session_admin, entities):
    # Invate employee and standard user if they don't exist
    employee = session_admin.find_one(f"User where code='{TEST_EMPLOYEE_EMAIL}'")
    if not employee:
        employee = session_admin.create("User",{
            "code":TEST_EMPLOYEE_EMAIL,
            "role":"employee"
        })
        assert employee is not None
        entities.remember(kind="user", temp_name="e1", entity_id=employee["id"])
    standard = session_admin.find_one(f"User where code='{TEST_USER_EMAIL}'")
    if not standard:
        standard = session_admin.create("User",{
            "code":TEST_USER_EMAIL,
            "role":"standard"
        })
        assert standard is not None
        entities.remember(kind="user", temp_name="s1", entity_id=standard["id"])

@pytest.mark.order(4)
def test_find_attributes_delivery_contains_code(session_standard):
    attributes = session_standard.find("attributes WHERE entitytype=delivery")
    assert isinstance(attributes, list)
    assert _list_contains_code(attributes)

@pytest.mark.order(5)
def test_find_entitytypes_as_employee(session_employee):
    """
    Test finding entitytypes as employee role.
    """
    entitytypes = session_employee.find("entitytypes")
    assert isinstance(entitytypes, list)
    assert len(entitytypes) > 2
    assert "user" in {str(x).lower() for x in entitytypes}

@pytest.mark.order(6)
def test_find_entitytypes_as_standard(session_standard):
    """
    Test finding entitytypes as standard (restricted end user) role.
    """
    entitytypes = session_standard.find("entitytypes")
    assert isinstance(entitytypes, list)
    assert len(entitytypes) > 2
    assert "user" in {str(x).lower() for x in entitytypes}

@pytest.mark.order(7)
def test_find_attributes_delivery_contains_code_as_employee(session_employee):
    """
    Test finding delivery attributes as employee role.
    """
    attributes = session_employee.find("attributes WHERE entitytype=delivery")
    assert isinstance(attributes, list)
    assert _list_contains_code(attributes)

@pytest.mark.order(8)
def test_find_attributes_delivery_contains_code_as_standard(session_standard):
    """
    Test finding delivery attributes as standard (restricted end user) role.
    """
    attributes = session_standard.find("attributes WHERE entitytype=delivery")
    assert isinstance(attributes, list)
    assert _list_contains_code(attributes)
