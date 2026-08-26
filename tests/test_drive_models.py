import pytest
from app.models.drive_item import DriveItem, FOLDER_MIME


def make_folder(id="f1", name="Folder") -> DriveItem:
    return DriveItem(
        id=id,
        name=name,
        mime_type=FOLDER_MIME,
        parents=["root"],
        is_folder=True,
        capabilities={"canEdit": True, "canRename": True, "canTrash": True, "canMoveItemWithinDrive": True},
    )


def make_file(id="d1", name="Doc.gdoc") -> DriveItem:
    return DriveItem(
        id=id,
        name=name,
        mime_type="application/vnd.google-apps.document",
        parents=["f1"],
        is_folder=False,
    )


def test_folder_is_folder():
    folder = make_folder()
    assert folder.is_folder is True


def test_file_is_not_folder():
    f = make_file()
    assert f.is_folder is False


def test_folder_mime_label():
    folder = make_folder()
    assert folder.mime_label() == "Folder"


def test_doc_mime_label():
    f = make_file()
    assert f.mime_label() == "Google Doc"


def test_folder_capabilities():
    folder = make_folder()
    assert folder.can_edit is True
    assert folder.can_rename is True
    assert folder.can_trash is True
    assert folder.can_move_item_within_drive is True


def test_missing_capabilities_default_true():
    item = DriveItem(id="x", name="X", mime_type=FOLDER_MIME, parents=[], is_folder=True)
    assert item.can_edit is True
    assert item.can_rename is True
