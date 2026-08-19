import pytest
import logging
import time
import sys
from datetime import datetime, timedelta

from accsyn_api.session import AccsynException

from conftest import TestUtils, TEST_FILE


@pytest.mark.order(0)
def test_ensure_users(session_admin, entities):
    print(f"Ensure employee users exists.")
    employee = session_admin.find_one(f"User WHERE code='{TestUtils.get_employee_ident()}'")
    if not employee:
        employee = session_admin.create("User", {"code": TestUtils.get_employee_ident(), "role": "employee"})
        assert employee is not None
    entities.remember(kind="user", temp_name="e1", entity_id=employee["id"], cleanup=False)
    # Make sure employee has full access to default volume
    volume = session_admin.find_one(f"Volume WHERE default=true")
    acls = session_admin.access("Volume", volume["id"], entitytype="User", entityid=entities.get_id("user", "e1"))
    if not acls:
        print(f"Granting employee full access to default volume.")
        session_admin.grant("User", entities.get_id("user", "e1"), "Volume", volume["id"])
    standard_user = session_admin.find_one(f"User where code='{TestUtils.get_standard_ident()}'")
    if not standard_user:
        standard_user = session_admin.create("User", {"code": TestUtils.get_standard_ident(), "role": "standard"})
        assert standard_user is not None
        entities.remember(kind="user", temp_name="s1", entity_id=standard_user["id"], cleanup=False)

    # Temporary invite second employee
    employee2 = session_admin.create("User", {"code": TestUtils.get_employee_ident(2), "role": "employee"})
    assert employee2 is not None
    entities.remember(kind="user", temp_name="e2", entity_id=employee2["id"])

@pytest.mark.skipif(not sys.stdin.isatty(), reason="needs interactive terminal")
@pytest.mark.order(1)
def test_ensure_client(session_admin, session_employee, entities):
    print("Check if the employee has a client running")
    active_client = None
    while True:
        clients = session_employee.find(f"App WHERE user={entities.get_id('user', 'e1')}")
        if len(clients) > 0:
            for client in clients:
                if client["status"] == "online":
                    active_client = client
                    break
            if active_client:
                break
            print(f"Please launch the accsyn Desktop as {TestUtils.get_employee_ident()} and press Enter to continue...")
        else:
            print(
                f"No client found, please login to the accsyn Desktop as {TestUtils.get_employee_ident()} and press Enter to continue..."
            )
        input()
        time.sleep(2)
    entities.remember(kind="client", temp_name="c", entity_id=active_client["id"], cleanup=False)
    print(f"Got employee active client: {active_client['id']}")

# Test push and pull with no mapping

@pytest.mark.order(10)
def test_push_admin_should_fail(session_admin, entities):
    print("Push file to user local mapped share, should fail")
    with pytest.raises(AccsynException):
        session_admin.create(
            "Transfer",
            {
                "source": TEST_FILE, 
                "destination": f"client={entities.get_id('client', 'c')}",
                "test": True
            },
        )

@pytest.mark.order(11)
def test_push_employee_should_fail(session_employee2, entities):
    print("Push file to user local mapped share as other employee, should fail")
    with pytest.raises(AccsynException):
        session_employee2.create(
            "Transfer",
            {
                "source": TEST_FILE, 
                "destination": f"client={entities.get_id('client', 'c')}",
                "test": True
            },
        )

@pytest.mark.order(12)
def test_push_standard_should_fail(session_standard, entities):
    print("Push file to user local mapped share as standard user, should fail")
    with pytest.raises(AccsynException):
        session_standard.create(
            "Transfer",
            {
                "source": TEST_FILE, 
                "destination": f"client={entities.get_id('client', 'c')}",
                "test": True
            },
        )

@pytest.mark.order(4)
def test_pull_admin_should_fail(session_admin, entities):
    print("Pull file from user local mapped share, should fail")
    with pytest.raises(AccsynException):
        session_admin.create(
            "Transfer",
            {
                "source": f"client={entities.get_id('client', 'c')}:{TEST_FILE}",
                "destination": "hq",
                "test": True
            },
        )

@pytest.mark.order(5)
def test_pull_employee_should_fail(session_employee2, entities):
    print("Pull file from user local mapped share as other employee, should fail")
    with pytest.raises(AccsynException):
        session_employee2.create(
            "Transfer",
            {
                "source": f"client={entities.get_id('client', 'c')}:{TEST_FILE}",
                "destination": "hq",
                "test": True
            },
        )

@pytest.mark.order(6)
def test_pull_user_should_fail(session_standard, entities):
    print("Pull file from user local mapped share as standard user, should fail")
    with pytest.raises(AccsynException):
        session_standard.create(
            "Transfer",
            {
                "source": f"client={entities.get_id('client', 'c')}:{TEST_FILE}",
                "destination": "hq",
                "test": True
            },
        )

@pytest.mark.order(20)
def test_grant_read_access_to_share(session_admin, entities):
    print(f"Please map default volume locally and grant read only access, press Enter to continue...")
    input()

# Test push with no write access

@pytest.mark.order(21)
def test_push_to_read_only_share_admin_should_fail(session_admin, entities):
    print("Push file to user mapped share (read only) as admin, should fail")
    with pytest.raises(AccsynException):
        session_admin.create(
            "Transfer",
            {
                "source": TEST_FILE, 
                "destination": f"client={entities.get_id('client', 'c')}",
                "test": True
            },
        )


@pytest.mark.order(22)
def test_push_to_read_only_share_employee_should_fail(session_employee2, entities):
    print("Push file to user mapped share (read only) as otheremployee, should fail")
    with pytest.raises(AccsynException):
        session_employee2.create(
            "Transfer",
            {
                "source": TEST_FILE, 
                "destination": f"client={entities.get_id('client', 'c')}",
                "test": True
            },
        )

@pytest.mark.order(23)
def test_push_to_read_only_share_user_should_fail(session_standard, entities):
    print("Push file to user mapped share (read only) as user, should fail")
    with pytest.raises(AccsynException):
        session_standard.create(
            "Transfer",
            {
                "source": TEST_FILE, 
                "destination": f"client={entities.get_id('client', 'c')}",
                "test": True
            },
        )


@pytest.mark.order(30)
def test_grant_write_access_to_share(session_admin, entities):
    print(f"Please grant write access, press Enter to continue...")
    input()

# Test with write access

@pytest.mark.order(31)
def test_push_admin(session_admin, entities):
    print("Push file to user local mapped share as admin")
    session_admin.create(
        "Transfer",
        {
            "source": TEST_FILE, 
            "destination": f"client={entities.get_id('client', 'c')}",
            "test": True
        },
    )

@pytest.mark.order(32)
def test_push_employee(session_employee2, entities):
    print("Push file to user local mapped share as other employee")
    session_employee2.create(
        "Transfer",
        {
            "source": TEST_FILE, 
            "destination": f"client={entities.get_id('client', 'c')}",
            "test": True
        },
    )

@pytest.mark.order(33)
def test_push_user_should_fail(session_standard, entities):
    print("Push file to user local mapped share as standard user, should fail")
    with pytest.raises(AccsynException):
        session_standard.create(
            "Transfer",
            {
                "source": TEST_FILE, 
                "destination": f"client={entities.get_id('client', 'c')}",
                "test": True
            },
        )

# Pull tests

@pytest.mark.order(40) # Test pull file back to workspace as admin
def test_pull_admin(session_admin, entities):
    print("Pull file back to workspace as admin")
    session_admin.create(
        "Transfer",
        {
            "source": f"client={entities.get_id('client', 'c')}:{TEST_FILE}",
            "destination": "hq",
            "test": True
        },
    )

@pytest.mark.order(41)
def test_pull_employee(session_employee2, entities):
    print("Pull file back to workspace as employee")
    session_employee2.create(
        "Transfer",
        {
            "source": f"client={entities.get_id('client', 'c')}:{TEST_FILE}",
            "destination": "hq",
            "test": True
        }
    )

@pytest.mark.order(42)
def test_pull_user_should_fail(session_standard, entities):
    print("Pull file back to workspace as user")
    with pytest.raises(AccsynException):
        session_standard.create(
            "Transfer",
            {
                "source": f"client={entities.get_id('client', 'c')}:{TEST_FILE}",
                "destination": "hq",
                "test": True
            },
        )
        