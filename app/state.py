from dataclasses import dataclass, field
from app.models.drive_item import DriveItem
from app.models.product import ProductReference


@dataclass
class AppState:
    authenticated: bool = False

    user_id: str | None = None
    user_name: str | None = None
    user_email: str | None = None
    user_avatar: str | None = None
    access_token: str | None = None

    products: list[ProductReference] = field(default_factory=list)
    current_product_id: str | None = None

    selected_item_id: str | None = None

    current_view: str = "tree"

    expanded_ids: set[str] = field(default_factory=set)
    children_cache: dict[str, list[DriveItem]] = field(default_factory=dict)

    loading: bool = False
    error: str | None = None

    def get_current_product(self) -> ProductReference | None:
        if not self.current_product_id:
            return None
        return next((p for p in self.products if p.folder_id == self.current_product_id), None)

    def get_cached_item(self, item_id: str) -> DriveItem | None:
        for children in self.children_cache.values():
            for item in children:
                if item.id == item_id:
                    return item
        return None

    def remove_item_from_cache(self, item_id: str) -> None:
        for parent_id, children in self.children_cache.items():
            self.children_cache[parent_id] = [c for c in children if c.id != item_id]

    def update_item_in_cache(self, updated_item: DriveItem) -> None:
        for parent_id, children in self.children_cache.items():
            for i, item in enumerate(children):
                if item.id == updated_item.id:
                    self.children_cache[parent_id][i] = updated_item
                    return

    def find_parent_id(self, item_id: str) -> str | None:
        for parent_id, children in self.children_cache.items():
            for item in children:
                if item.id == item_id:
                    return parent_id
        return None

    def clear_workspace(self) -> None:
        self.current_product_id = None
        self.selected_item_id = None
        self.expanded_ids.clear()
        self.children_cache.clear()
        self.error = None
        self.loading = False
