import pytest


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



def test_find_attributes_delivery_contains_code(session_standard):
    attributes = session_standard.find("attributes WHERE entitytype=delivery")
    assert isinstance(attributes, list)
    assert _list_contains_code(attributes)


# Role-based tests
def test_find_entitytypes_as_admin(session_admin):
    """
    Test finding entitytypes as admin role.
    """
    entitytypes = session_admin.find("entitytypes")
    assert isinstance(entitytypes, list)
    assert len(entitytypes) > 2
    assert "user" in {str(x).lower() for x in entitytypes}


def test_find_entitytypes_as_employee(session_employee):
    """
    Test finding entitytypes as employee role.
    """
    entitytypes = session_employee.find("entitytypes")
    assert isinstance(entitytypes, list)
    assert len(entitytypes) > 2
    assert "user" in {str(x).lower() for x in entitytypes}


def test_find_entitytypes_as_standard(session_standard):
    """
    Test finding entitytypes as standard (restricted end user) role.
    """
    entitytypes = session_standard.find("entitytypes")
    assert isinstance(entitytypes, list)
    assert len(entitytypes) > 2
    assert "user" in {str(x).lower() for x in entitytypes}


def test_find_attributes_delivery_contains_code_as_admin(session_admin):
    """
    Test finding delivery attributes as admin role.
    """
    attributes = session_admin.find("attributes WHERE entitytype=delivery")
    assert isinstance(attributes, list)
    assert _list_contains_code(attributes)


def test_find_attributes_delivery_contains_code_as_employee(session_employee):
    """
    Test finding delivery attributes as employee role.
    """
    attributes = session_employee.find("attributes WHERE entitytype=delivery")
    assert isinstance(attributes, list)
    assert _list_contains_code(attributes)


def test_find_attributes_delivery_contains_code_as_standard(session_standard):
    """
    Test finding delivery attributes as standard (restricted end user) role.
    """
    attributes = session_standard.find("attributes WHERE entitytype=delivery")
    assert isinstance(attributes, list)
    assert _list_contains_code(attributes)
