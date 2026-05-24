import pytest


@pytest.mark.order(1)
def test_logs_workspace_as_admin(session_admin):
    """
    Test fetching workspace logs as admin role.
    """
    response = session_admin.logs("workspace")
    assert isinstance(response, dict)
    assert "result" in response
    assert isinstance(response["result"], list)
