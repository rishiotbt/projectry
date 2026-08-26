from datetime import datetime, timezone
from app.state import AppState
from app.models.drive_item import DriveItem


def format_modified_time(iso_string: str | None) -> str:
    if not iso_string:
        return ""
    try:
        dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
        return f"{dt.day} {dt.strftime('%b')} {dt.year}"
    except Exception:
        return iso_string[:10] if iso_string else ""


def validate_move(
    state: AppState,
    source_id: str,
    target_id: str,
) -> tuple[bool, str]:
    if source_id == target_id:
        return False, "Cannot move an item into itself."

    if state.current_product_id and source_id == state.current_product_id:
        return False, "Cannot move the product root folder."

    target = state.get_cached_item(target_id)
    if target and not target.is_folder:
        return False, "Target must be a folder."

    if _is_descendant(state, target_id, source_id):
        return False, "Cannot move a folder into one of its own subfolders."

    return True, ""


def _is_descendant(state: AppState, potential_desc_id: str, ancestor_id: str) -> bool:
    children = state.children_cache.get(ancestor_id, [])
    for child in children:
        if child.id == potential_desc_id:
            return True
        if _is_descendant(state, potential_desc_id, child.id):
            return True
    return False


def find_item_path_display(state: AppState, item_id: str, product_name: str) -> str:
    """Returns a breadcrumb string like 'Kozmo / Product Specs / Chat'."""
    parts: list[str] = []
    current_id = item_id
    visited: set[str] = set()

    while current_id and current_id not in visited:
        visited.add(current_id)
        parent_id = state.find_parent_id(current_id)
        if parent_id is None:
            break
        item = state.get_cached_item(current_id)
        if item:
            parts.insert(0, item.name)
        current_id = parent_id

    if not parts:
        return product_name
    return " / ".join(parts[:-1]) if len(parts) > 1 else product_name


def get_create_folder_parent(state: AppState) -> str | None:
    """Determines parent for new folder based on current selection."""
    if not state.selected_item_id:
        return state.current_product_id

    selected = state.get_cached_item(state.selected_item_id)
    if selected is None:
        return state.current_product_id

    if selected.is_folder:
        return selected.id
    else:
        return state.find_parent_id(state.selected_item_id) or state.current_product_id
