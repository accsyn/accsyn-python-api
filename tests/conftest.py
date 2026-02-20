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
from typing import Any, Callable, List, Optional

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
        "transfer": lambda _id: session.delete_one("Transfer", _id, dict(force=True)),
        "delivery": lambda _id: session.delete_one("Delivery", _id, dict(force=True)),
        "user": lambda _id: session.delete_one("User", _id, dict(force=True)),
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


class TestUtils:
    """ Shared test utilities """
    
    @staticmethod
    def get_user_ident(role: str) -> str:
        """ Read the .env files and return the user ident for the given role """
        path_envfile = os.path.join(os.path.dirname(os.path.dirname(__file__)), f".env.{role}")
        assert os.path.exists(path_envfile), f"Missing test .env file: {path_envfile}"
        with open(path_envfile, "r") as f:
            for line in f:
                if line.startswith("ACCSYN_API_USER="):
                    return line.split("=")[1].strip()
        raise ValueError(f"Missing user ident for role: {role}")

    @staticmethod
    def get_admin_ident() -> str:
        return TestUtils.get_user_ident("admin")

    @staticmethod
    def get_employee_ident() -> str:
        return TestUtils.get_user_ident("employee")

    @staticmethod
    def get_standard_ident() -> str:
        return TestUtils.get_user_ident("standard")

    @staticmethod
    def get_data_path(file_name: str) -> str:
        return os.path.join(os.path.dirname(__file__), "data", file_name)

    @staticmethod
    def _extract_codes(value: Any) -> set:
        """Collect attribute codes (lowercase strings) from a dict or list of dicts/strings."""
        codes: set = set()
        if isinstance(value, dict):
            for k, v in value.items():
                if isinstance(k, str):
                    codes.add(k.lower())
                if isinstance(v, str):
                    codes.add(v.lower())
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    codes.add(item.lower())
                elif isinstance(item, dict):
                    codes.update(TestUtils._extract_codes(item))
        return codes

    @staticmethod
    def validate_response(
        value: Any,
        should_include: List[str],
        should_exclude: Optional[List[str]] = None,
    ) -> None:
        """
        Validate that response includes required codes and excludes forbidden ones.
        value: dict or list of dicts (e.g. find("attributes") response).
        If value is a list, every dict in the list is validated.
        Uses assert; do not use in assert, call as TestUtils.validate_response(...).
        """
        should_exclude = should_exclude or []
        if isinstance(value, list):
            dict_items = [item for item in value if isinstance(item, dict)]
            if dict_items:
                for item in dict_items:
                    TestUtils.validate_response(item, should_include, should_exclude)
            else:
                codes = TestUtils._extract_codes(value)
                for s in should_include:
                    assert s.lower() in codes, (
                        f"Expected attribute {s!r} in response, got codes: {sorted(codes)}"
                    )
                for s in should_exclude:
                    assert s.lower() not in codes, (
                        f"Expected attribute {s!r} not in response, got codes: {sorted(codes)}"
                    )
            return
        codes = TestUtils._extract_codes(value)
        for s in should_include:
            assert s.lower() in codes, (
                f"Expected attribute {s!r} in response, got codes: {sorted(codes)}"
            )
        for s in should_exclude:
            assert s.lower() not in codes, (
                f"Expected attribute {s!r} not in response, got codes: {sorted(codes)}"
            )