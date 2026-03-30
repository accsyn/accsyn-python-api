import logging
import os

import pytest

from accsyn_api.session import AccsynException

from conftest import (
    TestUtils,
    TEST_FILE,
    TEST_FILE2,
    SHARED_FOLDER,
    SHARED_FOLDER2,
    TEST_FOLDER3,
)

UPLOAD_SUBDIR = "UPLOAD"
DOWNLOAD_SUBDIR = "DOWNLOAD"
ADMIN_SUBDIR = "ADMIN"
UPLOAD_CHILD_SUBDIR = "TEST_SUBDIR"
RENAMED_FILE = "renamed_bad_buck_bunny.png"

SHARE_NAME_1 = "Shared Folder"
SHARE_NAME_2 = "Shared Folder 2"

EXPECTED_FOLDER_ATTRIBUTES = [
    "code",
    "created",
    "creator",
    "description",
    "email",
    "id",
    "metadata",
    "modified",
    "modifier",
    "name",
    "parent",
    "path",
    "queue",
    "status_hr",
    "status",
]

EXPECTED_ACL_ATTRIBUTES = [
    "acknowledged",
    "created",
    "creator",
    "description",
    "entity",
    "id",
    "path",
    "read",
    "role",
    "status",
    "target",
    "token",
    "write",
]

_state = {
    "default_volume_code": None,
    "share1": None,
    "share2": None,
}


def _list_result_names(ls_result):
    assert isinstance(ls_result, list)
    items = ls_result
    names = []
    for i in items:
        if isinstance(i, dict) and "filename" in i:
            names.append(i["filename"])
    return names


@pytest.mark.order(0)
def test_cleanup_filesharing(session_admin, entities):
    # Remove test folders recursively on default volume root
    for folder in [SHARED_FOLDER, SHARED_FOLDER2, TEST_FOLDER3]:
        try:
            session_admin.delete(folder, force=True)
        except Exception:
            pass

    # Remove employee user if it exists (invite tests rely on clean start)
    employee_user = session_admin.find_one(f"User WHERE code='{TestUtils.get_employee_ident()}'")
    if employee_user:
        session_admin.delete_one("User", employee_user["id"])
        entities.remove_from_cleanup(kind="user", entity_id=employee_user["id"])

    # Remove standard user if it exists (invite tests rely on clean start)
    standard_user = session_admin.find_one(f"User WHERE code='{TestUtils.get_standard_ident()}'")
    if standard_user:
        session_admin.delete_one("User", standard_user["id"])
        entities.remove_from_cleanup(kind="user", entity_id=standard_user["id"])

    # Remove shares if they exist
    for share_code in [SHARE_NAME_1, SHARE_NAME_2]:
        share = session_admin.find_one(f"Folder WHERE name='{share_code}'")
        if share:
            session_admin.delete_one("Folder", share["id"])
            entities.remove_from_cleanup(kind="folder", entity_id=share["id"])


@pytest.mark.order(1)
def test_create_folders(session_admin):
    session_admin.mkdir(SHARED_FOLDER)
    session_admin.mkdir(f"{SHARED_FOLDER}/{UPLOAD_SUBDIR}")
    session_admin.mkdir(f"{SHARED_FOLDER}/{DOWNLOAD_SUBDIR}")
    session_admin.mkdir(f"{SHARED_FOLDER}/{ADMIN_SUBDIR}")

    session_admin.mkdir(SHARED_FOLDER2)
    session_admin.mkdir(TEST_FOLDER3)


@pytest.mark.order(3)
def test_create_shared_folders_and_grant(session_admin, entities):
    default_volume = session_admin.find_one("Volume WHERE default=True")
    assert default_volume is not None

    share1 = session_admin.create(
        "Folder",
        {
            "parent": default_volume["id"],
            "path": SHARED_FOLDER,
            "name": SHARE_NAME_1,
        },
    )
    _state["share1"] = share1
    entities.remember(kind="folder", temp_name="folder1", entity_id=share1["id"])
    TestUtils.validate_response(share1, EXPECTED_FOLDER_ATTRIBUTES)

    acl = session_admin.grant(
        "User",
        TestUtils.get_standard_ident(),
        "Folder",
        share1["id"],
        {
            "path": DOWNLOAD_SUBDIR,
            "read": True,
            "write": False,
        },
    )
    TestUtils.validate_response(acl, EXPECTED_ACL_ATTRIBUTES)

    standard_users = session_admin.find("User WHERE role=standard")
    assert isinstance(standard_users, list)
    std = next((u for u in standard_users if u.get("code") == TestUtils.get_standard_ident()), None)
    assert std is not None, "Standard user should have been invited by grant call"
    entities.remember(kind="user", temp_name="u-s1", entity_id=std["id"])

    share2 = session_admin.create(
        "Folder",
        {
            "parent": default_volume["id"],
            "path": SHARED_FOLDER2,
            "name": SHARE_NAME_2,
        },
    )
    _state["share2"] = share2
    TestUtils.validate_response(share2, EXPECTED_FOLDER_ATTRIBUTES)


@pytest.mark.order(4)
def test_upload_files(session_admin, entities):
    share1 = _state["share1"]
    assert share1 is not None

    transfer1 = session_admin.create(
        "Transfer",
        {
            "source": TestUtils.get_data_path(TEST_FILE),
            "destination": f"folder={share1['code']}/{TEST_FILE}",
            "status": "waiting",
        },
    )
    entities.remember(kind="transfer", temp_name="fs-upload-root", entity_id=transfer1["id"])
    TestUtils.wait_transfer_done(session_admin, transfer1)

    transfer2 = session_admin.create(
        "Transfer",
        {
            "source": TestUtils.get_data_path(TEST_FILE2),
            "destination": f"folder={share1['code']}/{DOWNLOAD_SUBDIR}/{TEST_FILE2}",
            "status": "waiting",
        },
    )
    entities.remember(kind="transfer", temp_name="fs-upload-download", entity_id=transfer2["id"])
    TestUtils.wait_transfer_done(session_admin, transfer2)


@pytest.mark.order(5)
def test_list_shared_folders(session_admin):
    folders = session_admin.find("Folder")
    assert isinstance(folders, list)
    names = [f.get("name") for f in folders]
    assert SHARE_NAME_1 in names
    assert SHARE_NAME_2 in names


@pytest.mark.order(6)
def test_list_shared_folders_and_content(session_standard):
    share1 = _state["share1"]
    assert share1 is not None

    folders = session_standard.find("Folder")
    assert isinstance(folders, list)
    assert len([f for f in folders if f.get("name") == SHARE_NAME_1]) == 1
    assert len([f for f in folders if f.get("name") == SHARE_NAME_2]) == 0

    root_ls = session_standard.ls(f"folder={share1['code']}")
    root_names = _list_result_names(root_ls)
    assert DOWNLOAD_SUBDIR in root_names
    assert UPLOAD_SUBDIR not in root_names
    assert ADMIN_SUBDIR not in root_names
    assert TEST_FILE not in root_names

    download_ls = session_standard.ls(f"folder={share1['code']}/{DOWNLOAD_SUBDIR}")
    download_names = _list_result_names(download_ls)
    assert TEST_FILE2 in download_names


@pytest.mark.order(7)
def test_download_shared_content(session_standard, entities):
    share1 = _state["share1"]
    assert share1 is not None

    target_path = TestUtils.get_tmp_path(TEST_FILE2)
    os.makedirs(os.path.dirname(target_path), exist_ok=True)

    transfer = session_standard.create(
        "Transfer",
        {
            "source": f"folder={share1['code']}/{DOWNLOAD_SUBDIR}/{TEST_FILE2}",
            "destination": target_path,
            "status": "waiting",
        },
    )
    entities.remember(kind="transfer", temp_name="fs-download", entity_id=transfer["id"])
    TestUtils.wait_transfer_done(session_standard, transfer)
    assert os.path.exists(target_path)


@pytest.mark.order(8)
def test_upload_content_should_fail(session_standard):
    share1 = _state["share1"]
    assert share1 is not None
    with pytest.raises(AccsynException):
        session_standard.create(
            "Transfer",
            {
                "source": TestUtils.get_data_path(TEST_FILE),
                "destination": f"folder={share1['code']}/{DOWNLOAD_SUBDIR}/{TEST_FILE}",
                "status": "waiting",
            },
        )


@pytest.mark.order(9)
def test_grant_write_access(session_admin):
    share1 = _state["share1"]
    assert share1 is not None
    granted = session_admin.grant(
        "User",
        TestUtils.get_standard_ident(),
        "Folder",
        share1["id"],
        {
            "path": UPLOAD_SUBDIR,
            "read": False,
            "write": True,
        },
    )
    assert granted is True


@pytest.mark.order(10)
def test_upload_content(session_standard, entities):
    share1 = _state["share1"]
    assert share1 is not None
    transfer = session_standard.create(
        "Transfer",
        {
            "source": TestUtils.get_data_path(TEST_FILE2),
            "destination": f"folder={share1['code']}/{UPLOAD_SUBDIR}/{TEST_FILE2}",
            "status": "waiting",
        },
    )
    entities.remember(kind="transfer", temp_name="fs-upload-write-only", entity_id=transfer["id"])
    TestUtils.wait_transfer_done(session_standard, transfer)


@pytest.mark.order(11)
def test_read_upload_should_fail(session_standard):
    share1 = _state["share1"]
    assert share1 is not None
    with pytest.raises(AccsynException):
        session_standard.ls(f"folder={share1['code']}/{UPLOAD_SUBDIR}")


@pytest.mark.order(12)
def test_move_content_should_fail(session_standard):
    share1 = _state["share1"]
    assert share1 is not None
    with pytest.raises(AccsynException):
        session_standard.mv(
            f"folder={share1['code']}/{UPLOAD_SUBDIR}/{TEST_FILE2}",
            f"folder={share1['code']}/{TEST_FILE2}",
        )


@pytest.mark.order(13)
def test_modify_content(session_standard):
    share1 = _state["share1"]
    assert share1 is not None

    source_path = f"folder={share1['code']}/{UPLOAD_SUBDIR}/{TEST_FILE2}"
    renamed_path = f"folder={share1['code']}/{UPLOAD_SUBDIR}/{RENAMED_FILE}"
    child_dir_path = f"folder={share1['code']}/{UPLOAD_SUBDIR}/{UPLOAD_CHILD_SUBDIR}"
    moved_path = f"folder={share1['code']}/{UPLOAD_SUBDIR}/{UPLOAD_CHILD_SUBDIR}/{RENAMED_FILE}"

    session_standard.rename(source_path, renamed_path)
    session_standard.mkdir(child_dir_path)
    session_standard.mv(renamed_path, moved_path)
    session_standard.delete(moved_path)


@pytest.mark.order(14)
def test_modify_download_content_should_fail(session_standard):
    share1 = _state["share1"]
    assert share1 is not None

    source_path = f"folder={share1['code']}/{DOWNLOAD_SUBDIR}/{TEST_FILE2}"
    renamed_path = f"folder={share1['code']}/{DOWNLOAD_SUBDIR}/{RENAMED_FILE}"
    child_dir_path = f"folder={share1['code']}/{DOWNLOAD_SUBDIR}/{UPLOAD_CHILD_SUBDIR}"
    moved_path = f"folder={share1['code']}/{DOWNLOAD_SUBDIR}/{UPLOAD_CHILD_SUBDIR}/{RENAMED_FILE}"

    with pytest.raises(AccsynException):
        session_standard.rename(source_path, renamed_path)

    with pytest.raises(AccsynException):
        session_standard.mkdir(child_dir_path)

    with pytest.raises(AccsynException):
        session_standard.mv(source_path, moved_path)

    with pytest.raises(AccsynException):
        session_standard.delete(source_path)


@pytest.mark.order(15)
def test_standard_share_test_folder3_should_fail(session_admin, session_standard):
    default_volume = session_admin.find_one("Volume WHERE default=True")
    assert default_volume is not None

    with pytest.raises(AccsynException):
        session_standard.create(
            "Folder",
            {
                "parent": default_volume["id"],
                "path": TEST_FOLDER3,
                "name": "Standard should fail share",
            },
        )


@pytest.mark.order(16)
def test_admin_modify_deactivate_activate_delete_share2(session_admin):
    share = _state["share1"]
    assert share is not None

    # Rename share
    renamed_name = f"{SHARE_NAME_1} Renamed"
    updated = session_admin.update("Folder", share["id"], {"name": renamed_name})
    assert updated is not None
    assert updated["name"] == renamed_name

    # Disable share
    updated = session_admin.update("Folder", share["id"], {"status": "disabled"})
    assert updated is not None
    assert updated["status"] == "disabled"

    # Inactivate share
    deactivated = session_admin.deactivate_one("Folder", share["id"])
    assert deactivated is True

    # Should not be returned by active query anymore
    assert session_admin.find_one(f"Folder WHERE id={share['id']}") is None

    # Reactivate
    activated = session_admin.activate_one("Folder", share["id"])
    assert activated is True
    assert session_admin.find_one(f"Folder WHERE id={share['id']}") is not None

    # Verify ACLs were also re-activated
    acls = session_admin.access("Folder", share["id"])
    assert isinstance(acls, list)
    assert len(acls) == 1
