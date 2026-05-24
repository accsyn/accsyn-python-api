import pytest

@pytest.mark.order(0)
def test_queue_compute_avoid_setting_crud(session_admin, entities):
    queues = session_admin.find("Queue WHERE name='medium'")
    assert isinstance(queues, list)
    assert len(queues) == 1

    queue = queues[0]
    queue_id = queue["id"]

    # Set
    set_ok = session_admin.set_setting(
        entitytype="job",
        entityid=queue_id,
        name="compute_avoid",
        value="disable",
    )
    assert set_ok is True

    # Verify present
    settings_after_set = session_admin.get_settings(
        entitytype="job",
        entityid=queue_id,
        upstream=False,
        omit_defaults=False,
    )
    assert isinstance(settings_after_set, dict)
    assert "compute_avoid" in str(settings_after_set)

    # Delete
    delete_ok = session_admin.delete_setting(
        entitytype="job",
        entityid=queue_id,
        name="compute_avoid",
    )
    assert delete_ok is True

    # Verify absent
    settings_after_delete = session_admin.get_settings(
        entitytype="job",
        entityid=queue_id,
        upstream=False,
        omit_defaults=False,
    )
    assert isinstance(settings_after_delete, dict)
    assert "compute_avoid" not in str(settings_after_delete)
