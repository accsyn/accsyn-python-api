import os
import pytest
import uuid
import logging
import tempfile

# Ensure INFO messages from this module go to the log file (pytest often sets root to WARNING).
# Use line-buffered stream so teardown logs are written before pytest exits.
_logpath = os.path.join(tempfile.gettempdir(), "accsyn-python-api-pytest.log")
_logstream = open(_logpath, "a", encoding="utf-8", buffering=1)
_handler = logging.StreamHandler(_logstream)
_handler.setLevel(logging.INFO)
_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(_handler)

from dataclasses import dataclass, field
from typing import Any, Callable

TEST_ADMIN_EMAIL = "byos.tester@accsyn.com"
TEST_USER_EMAIL = "test.user@accsyn.com"
TEST_EMPLOYEE_EMAIL = "test.employee@accsyn.com"

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
        logger.info(f"(Remember) Remembering {ce.kind} entity {ce.id} ({temp_name})")
        return entity_id

    def get_id(self, kind: str, temp_name: str) -> str:
        return self._by_key[(kind, temp_name)].id

    def remove_from_cleanup(self, kind: str, entity_id: str) -> None:
        """Remove an entity from the cleanup stack so it will not be deleted during teardown."""
        key_to_remove = None
        for key, ce in self._by_key.items():
            if ce.kind == kind and ce.id == entity_id:
                key_to_remove = key
                break
        if key_to_remove is not None:
            ce = self._by_key.pop(key_to_remove)
            self._created_stack.remove(ce)

    def cleanup(self) -> None:
        # Best effort: delete everything we created, even if some deletes fail.
        logger.info("Cleaning up %s entities", len(self._created_stack))
        for h in logger.handlers:
            h.flush()
        errors: list[Exception] = []
        while self._created_stack:
            ce = self._created_stack.pop()
            deleter = self._deleters.get(ce.kind)
            if not deleter:
                continue
            try:
                deleter(ce.id)
                logger.info(f"(Clean up) Deleted {ce.kind} entity {ce.id}")
            except Exception as e:
                errors.append(e)
                logger.warning(f"(Clean up) Error deleting {ce.kind} entity {ce.id}: {e}")
        for h in logger.handlers:
            h.flush()
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
        "user": lambda _id: session.delete_one("User", _id),
    }
    return EntityRegistry(run_id=run_id, deleters=deleters)


@pytest.fixture(scope="session")
def entities(run_id, session_admin):
    """
    Shared entity registry for all roles (admin, employee, standard).
    Cleanup is performed with the admin session so all created entities can be deleted.

    Usage:
        entities.remember(kind="delivery", temp_name="d1", entity_id="...")
        entities.get_id("delivery", "d1")
        entities.temp("d1") -> namespaced name safe for shared workspaces
    """
    reg = _make_entities_registry(session_admin, run_id)
    try:
        yield reg
    finally:
        reg.cleanup()
