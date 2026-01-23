import os
import pytest
import uuid
import logging

from dataclasses import dataclass, field
from typing import Any, Callable

# Session fixtures for different roles

@pytest.fixture(scope="session")
def session_admin():
    """
    Integration test session with admin role.
    
    Requires .env file: .env.admin
    """
    import accsyn_api
    
    if not os.path.exists(".env.admin"):
        pytest.skip("Missing required .env file: .env.admin")
    
    return accsyn_api.Session(path_envfile=".env.admin", connect_timeout=10, timeout=30)


@pytest.fixture(scope="session")
def session_employee():
    """
    Integration test session with employee role.
    
    Requires .env file: .env.employee
    """
    import accsyn_api
    
    if not os.path.exists(".env.employee"):
        pytest.skip("Missing required .env file: .env.employee")
    
    return accsyn_api.Session(path_envfile=".env.employee", connect_timeout=10, timeout=30)


@pytest.fixture(scope="session")
def session_standard():
    """
    Integration test session with standard (restricted end user) role.
    
    Requires .env file: .env.standard
    """
    import accsyn_api
    
    if not os.path.exists(".env.standard"):
        pytest.skip("Missing required .env file: .env.standard")
    
    return accsyn_api.Session(path_envfile=".env.standard", connect_timeout=10, timeout=30)


# Temp entity storage

@dataclass
class CreatedEntity:
    kind: str
    id: str
    meta: dict[str, Any] = field(default_factory=dict)

class EntityRegistry:
    """
    Stores entities by (kind, temp_name) -> id and keeps a LIFO list for cleanup.
    """
    def __init__(self, run_id: str, deleters: dict[str, Callable[[str], None]]):
        self.run_id = run_id
        self._deleters = deleters
        self._by_key: dict[tuple[str, str], CreatedEntity] = {}
        self._created_stack: list[CreatedEntity] = []

    def temp(self, name: str) -> str:
        """Namespace temp names so we can safely operate in an existing workspace."""
        return f"pytest-{self.run_id}-{name}"

    def remember(self, *, kind: str, temp_name: str, entity_id: str, **meta: Any) -> str:
        ce = CreatedEntity(kind=kind, id=entity_id, meta=meta)
        self._by_key[(kind, temp_name)] = ce
        self._created_stack.append(ce)  # LIFO cleanup helps with dependencies
        return entity_id

    def get_id(self, kind: str, temp_name: str) -> str:
        return self._by_key[(kind, temp_name)].id

    def cleanup(self) -> None:
        # Best effort: delete everything we created, even if some deletes fail.
        print(f"Cleaning up {len(self._created_stack)} entities")
        errors: list[Exception] = []
        while self._created_stack:
            ce = self._created_stack.pop()
            deleter = self._deleters.get(ce.kind)
            if not deleter:
                continue
            try:
                deleter(ce.id)
            except Exception as e:
                errors.append(e)

        if errors:
            # Optionally re-raise one error to make it visible,
            # or just log; depends on how strict you want teardown to be.
            raise RuntimeError(f"Cleanup had {len(errors)} errors, first: {errors[0]}") from errors[0]

@pytest.fixture(scope="session")
def run_id() -> str:
    # stable per-test run id for namespacing; could also be session-level
    return uuid.uuid4().hex[:10]


def _make_entities_registry(session: Any, run_id: str) -> EntityRegistry:
    """
    Factory function to create an EntityRegistry for a given session.
    
    :param session: The session object (admin, employee, or standard)
    :param run_id: Unique run ID for namespacing
    :return: EntityRegistry instance
    """
    # Map "kind" -> delete function
    deleters = {
        "delivery": lambda _id: session.delete_one("Delivery", _id),
    }
    return EntityRegistry(run_id=run_id, deleters=deleters)


@pytest.fixture(scope="session")
def entities_admin(run_id, session_admin):
    """
    Entity registry for admin session.
    
    Usage:
        entities_admin.remember(kind="delivery", temp_name="d1", entity_id="...")
        entities_admin.get_id("delivery", "d1")
        entities_admin.temp("d1") -> namespaced name safe for shared workspaces
    """
    reg = _make_entities_registry(session_admin, run_id)
    try:
        yield reg
    finally:
        # always runs, even if test fails or asserts
        reg.cleanup()


@pytest.fixture(scope="session")
def entities_employee(run_id, session_employee):
    """
    Entity registry for employee session.
    
    Usage:
        entities_employee.remember(kind="delivery", temp_name="d1", entity_id="...")
        entities_employee.get_id("delivery", "d1")
        entities_employee.temp("d1") -> namespaced name safe for shared workspaces
    """
    reg = _make_entities_registry(session_employee, run_id)
    try:
        yield reg
    finally:
        # always runs, even if test fails or asserts
        reg.cleanup()


@pytest.fixture(scope="session")
def entities_standard(run_id, session_standard):
    """
    Entity registry for standard session.
    
    Usage:
        entities_standard.remember(kind="delivery", temp_name="d1", entity_id="...")
        entities_standard.get_id("delivery", "d1")
        entities_standard.temp("d1") -> namespaced name safe for shared workspaces
    """
    reg = _make_entities_registry(session_standard, run_id)
    try:
        yield reg
    finally:
        # always runs, even if test fails or asserts
        reg.cleanup()
