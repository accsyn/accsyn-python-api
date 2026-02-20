import pytest

from conftest import TestUtils


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
def test_find_and_validate_delivery_attributes_as_admin(session_admin):
    """
    Test finding delivery attributes as admin role.
    """
    attributes = session_admin.find("attributes WHERE entitytype=delivery")
    assert isinstance(attributes, list)
    TestUtils.validate_response(attributes, should_include=["code", "name", "public"], should_exclude=["data","config"])

@pytest.mark.order(3)
def test_create_users(session_admin, entities):
    # Invate employee and standard user if they don't exist
    employee = session_admin.find_one(f"User where code='{TestUtils.get_employee_ident()}'")
    if not employee:
        employee = session_admin.create("User",{
            "code":TestUtils.get_employee_ident(),
            "role":"employee"
        })
        assert employee is not None
        entities.remember(kind="user", temp_name="e1", entity_id=employee["id"])
    standard = session_admin.find_one(f"User where code='{TestUtils.get_standard_ident()}'")
    if not standard:
        standard = session_admin.create("User",{
            "code":TestUtils.get_standard_ident(),
            "role":"standard"
        })
        assert standard is not None
        entities.remember(kind="user", temp_name="s1", entity_id=standard["id"])

@pytest.mark.order(4)
def test_find_attributes_delivery_contains_code(session_standard):
    attributes = session_standard.find("attributes WHERE entitytype=delivery")
    assert isinstance(attributes, list)
    TestUtils.validate_response(attributes, should_include=["code"])

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
    TestUtils.validate_response(attributes, should_include=["code"])

@pytest.mark.order(8)
def test_find_attributes_delivery_contains_code_as_standard(session_standard):
    """
    Test finding delivery attributes as standard (restricted end user) role.
    """
    attributes = session_standard.find("attributes WHERE entitytype=delivery")
    assert isinstance(attributes, list)
    TestUtils.validate_response(attributes, should_include=["code"])
