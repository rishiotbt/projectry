import pytest
from app.models.drive_item import DriveItem, FOLDER_MIME
from app.state import AppState
from app.utils.drive_helpers import validate_move


def make_folder(id: str, name: str, parents: list[str] | None = None) -> DriveItem:
    return DriveItem(
        id=id,
        name=name,
        mime_type=FOLDER_MIME,
        parents=parents or ["root"],
        is_folder=True,
    )


def make_file(id: str, name: str, parents: list[str] | None = None) -> DriveItem:
    return DriveItem(
        id=id,
        name=name,
        mime_type="application/vnd.google-apps.document",
        parents=parents or ["root"],
        is_folder=False,
    )


def build_state() -> AppState:
    """
    Product root: p1
      ├── Folder A (a1)
      │   └── Folder B (b1)
      │       └── File X (x1)
      └── Folder C (c1)
    """
    state = AppState()
    state.current_product_id = "p1"

    folder_a = make_folder("a1", "Folder A", ["p1"])
    folder_b = make_folder("b1", "Folder B", ["a1"])
    folder_c = make_folder("c1", "Folder C", ["p1"])
    file_x = make_file("x1", "File X", ["b1"])

    state.children_cache["p1"] = [folder_a, folder_c]
    state.children_cache["a1"] = [folder_b]
    state.children_cache["b1"] = [file_x]
    state.children_cache["c1"] = []

    return state


def test_move_item_into_itself():
    state = build_state()
    ok, msg = validate_move(state, "a1", "a1")
    assert ok is False
    assert "itself" in msg.lower()


def test_move_product_root_blocked():
    state = build_state()
    ok, msg = validate_move(state, "p1", "c1")
    assert ok is False
    assert "product root" in msg.lower()


def test_move_into_descendant_blocked():
    state = build_state()
    # Moving a1 into b1 (b1 is a child of a1)
    ok, msg = validate_move(state, "a1", "b1")
    assert ok is False
    assert "descendant" in msg.lower() or "subfolder" in msg.lower()


def test_valid_move():
    state = build_state()
    # Moving x1 from b1 to c1
    ok, msg = validate_move(state, "x1", "c1")
    assert ok is True
    assert msg == ""


def test_move_folder_to_sibling():
    state = build_state()
    # Moving b1 from a1 to c1
    ok, msg = validate_move(state, "b1", "c1")
    assert ok is True


def test_move_deeply_nested_ancestor_blocked():
    state = build_state()
    # Moving a1 into x1's parent (b1) — b1 is descendant of a1
    ok, msg = validate_move(state, "a1", "b1")
    assert ok is False
