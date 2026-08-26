import pytest
from app.models.drive_item import DriveItem, FOLDER_MIME
from app.state import AppState
from app.services.tree_layout import TreeLayoutService, NODE_WIDTH, NODE_HEIGHT


def make_folder(id: str, name: str) -> DriveItem:
    return DriveItem(id=id, name=name, mime_type=FOLDER_MIME, parents=[], is_folder=True)


def build_state_with_tree() -> tuple[AppState, DriveItem]:
    """
    root
     ├── a
     │   ├── a1
     │   └── a2
     └── b
    """
    state = AppState()
    state.current_product_id = "root"

    root = make_folder("root", "Product")
    folder_a = make_folder("a", "A")
    folder_b = make_folder("b", "B")
    folder_a1 = make_folder("a1", "A1")
    folder_a2 = make_folder("a2", "A2")

    state.children_cache["root"] = [folder_a, folder_b]
    state.children_cache["a"] = [folder_a1, folder_a2]
    state.children_cache["b"] = []
    state.children_cache["a1"] = []
    state.children_cache["a2"] = []

    return state, root


def test_root_node_has_children():
    state, root = build_state_with_tree()
    service = TreeLayoutService(state)
    layout = service.layout(root)
    assert len(layout.children) == 2


def test_root_node_dimensions():
    state, root = build_state_with_tree()
    service = TreeLayoutService(state)
    layout = service.layout(root)
    assert layout.width == NODE_WIDTH
    assert layout.height == NODE_HEIGHT


def test_children_placed_below_parent():
    state, root = build_state_with_tree()
    service = TreeLayoutService(state)
    layout = service.layout(root)
    for child in layout.children:
        assert child.y > layout.y


def test_children_have_correct_ids():
    state, root = build_state_with_tree()
    service = TreeLayoutService(state)
    layout = service.layout(root)
    child_ids = {c.item.id for c in layout.children}
    assert child_ids == {"a", "b"}


def test_grandchildren_placed_below_children():
    state, root = build_state_with_tree()
    service = TreeLayoutService(state)
    layout = service.layout(root)
    a_node = next(c for c in layout.children if c.item.id == "a")
    assert len(a_node.children) == 2
    for gc in a_node.children:
        assert gc.y > a_node.y


def test_total_bounds_larger_than_root():
    state, root = build_state_with_tree()
    service = TreeLayoutService(state)
    layout = service.layout(root)
    min_x, min_y, max_x, max_y = service.total_bounds(layout)
    assert max_y > layout.y + layout.height
    assert (max_x - min_x) >= NODE_WIDTH


def test_single_node_no_children():
    state = AppState()
    root = make_folder("r", "Root")
    state.children_cache["r"] = []
    service = TreeLayoutService(state)
    layout = service.layout(root)
    assert len(layout.children) == 0
    assert layout.width == NODE_WIDTH
    assert layout.height == NODE_HEIGHT
