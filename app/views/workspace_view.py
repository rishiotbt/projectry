import flet as ft
import json
from typing import Callable

from app import config
from app.state import AppState
from app.models.product import ProductReference
from app.models.drive_item import DriveItem
from app.services.google_drive import GoogleDriveService, DriveAPIError
from app.services.tree_layout import TreeLayoutService
from app.utils.drive_helpers import validate_move, get_create_folder_parent, find_item_path_display
from app.components.header import build_header
from app.components.sidebar import build_sidebar
from app.components.details_panel import build_details_panel, build_empty_details_panel
from app.components.error_banner import ErrorBanner
from app.components import dialogs
from app.views.tree_view import build_tree_view
from app.views.map_view import build_map_view


class WorkspaceView:
    def __init__(
        self,
        page: ft.Page,
        state: AppState,
        save_products: Callable,
        on_session_expired: Callable | None = None,
    ):
        self.page = page
        self.state = state
        self._save_products = save_products
        self._on_session_expired = on_session_expired

        self._header_ref = ft.Ref[ft.Container]()
        self._sidebar_ref = ft.Ref[ft.Container]()
        self._content_ref = ft.Ref[ft.Container]()
        self._details_ref = ft.Ref[ft.Container]()

        self._error_banner = ErrorBanner(on_dismiss=self._clear_error)

        self._header_container = ft.Container(ref=self._header_ref)
        self._sidebar_container = ft.Container(ref=self._sidebar_ref)
        self._content_container = ft.Container(ref=self._content_ref, expand=True)
        self._details_container = ft.Container(ref=self._details_ref)

        self._upload_parent_id: str | None = None

    # ─────────────────────────── Drive service ────────────────────────────

    def _drive(self) -> GoogleDriveService:
        return GoogleDriveService(self.state.access_token)

    # ─────────────────────────── Build layout ─────────────────────────────

    def build(self) -> ft.Control:
        self._refresh_header()
        self._refresh_sidebar()
        self._refresh_content()
        self._refresh_details()

        return ft.Column(
            expand=True,
            spacing=0,
            controls=[
                self._header_container,
                self._error_banner.build(),
                ft.Row(
                    expand=True,
                    spacing=0,
                    controls=[
                        self._sidebar_container,
                        self._content_container,
                        self._details_container,
                    ],
                ),
            ],
        )

    # ─────────────────────────── Refresh helpers ──────────────────────────

    def _refresh_header(self) -> None:
        self._header_container.content = build_header(
            state=self.state,
            on_create_folder=self._on_create_folder,
            on_import_files=self._on_import_files,
            on_refresh=self._on_refresh,
            on_expand_all=self._on_expand_all,
            on_collapse_all=self._on_collapse_all,
            on_logout=self._on_logout,
            on_open_drive=lambda: self.page.launch_url("https://drive.google.com", web_popup_window_name="_blank"),
            on_switch_view=self._on_switch_view,
        )
        try:
            self._header_container.update()
        except Exception:
            pass

    def _refresh_sidebar(self) -> None:
        self._sidebar_container.content = build_sidebar(
            state=self.state,
            on_select_product=self._on_select_product,
            on_add_product=self._on_add_product,
            on_delete_product=self._on_delete_product,
            on_open_drive=lambda: self.page.launch_url("https://drive.google.com", web_popup_window_name="_blank"),
        )
        try:
            self._sidebar_container.update()
        except Exception:
            pass

    def _refresh_content(self) -> None:
        if self.state.current_view == "map":
            content = build_map_view(
                state=self.state,
                on_select=self._on_select_item,
                on_drop=self._handle_drop,
            )
        else:
            content = build_tree_view(
                state=self.state,
                on_select=self._on_select_item,
                on_toggle_expand=self._on_toggle_expand,
                on_rename=self._on_rename_item,
                on_move=self._on_move_item,
                on_trash=self._on_trash_item,
                on_open_in_drive=self._open_in_drive,
                on_drop=self._handle_drop,
                on_create_subfolder=self._on_create_subfolder_in,
                on_import_files=self._on_import_files,
            )
        self._content_container.content = content
        try:
            self._content_container.update()
        except Exception:
            pass

    def _refresh_details(self) -> None:
        if self.state.selected_item_id:
            item = self.state.get_cached_item(self.state.selected_item_id)
            if item:
                product = self.state.get_current_product()
                path = find_item_path_display(
                    self.state, self.state.selected_item_id,
                    product.name if product else ""
                )
                panel = build_details_panel(
                    item=item,
                    path_display=path,
                    on_open_in_drive=self._open_in_drive,
                    on_rename=self._on_rename_item,
                    on_move=self._on_move_item,
                    on_trash=self._on_trash_item,
                )
            else:
                panel = build_empty_details_panel()
        else:
            panel = build_empty_details_panel()

        self._details_container.content = panel
        try:
            self._details_container.update()
        except Exception:
            pass

    def _refresh_all(self) -> None:
        self._refresh_header()
        self._refresh_sidebar()
        self._refresh_content()
        self._refresh_details()

    # ─────────────────────────── Error handling ───────────────────────────

    def _show_error(self, message: str) -> None:
        if "401" in str(message) and self._on_session_expired:
            self._on_session_expired()
            return
        self.state.error = message
        self._error_banner.show(message)

    def _clear_error(self) -> None:
        self.state.error = None

    def _snack(self, message: str, color: str = config.TEXT_COLOR) -> None:
        self.page.show_dialog(ft.SnackBar(
            content=ft.Text(message, color="white"),
            bgcolor=color,
            duration=3000,
            open=True,
        ))

    # ─────────────────────────── Product management ───────────────────────

    def _on_add_product(self) -> None:
        dialogs.show_add_product_dialog(
            self.page,
            on_create_new=self._create_new_product,
            on_use_existing=self._use_existing_product,
        )

    def _create_new_product(self) -> None:
        dialogs.show_create_product_dialog(
            self.page,
            on_create=lambda name: self.page.run_task(self._do_create_product, name),
        )

    async def _do_create_product(self, name: str) -> None:
        try:
            folder = await self._drive().create_folder(name, "root")
            product = ProductReference(folder_id=folder.id, name=folder.name)
            self.state.products.append(product)
            self._save_products(self.state.user_id, self.state.products)
            self._refresh_sidebar()
            await self._load_product(folder.id)
        except DriveAPIError as e:
            self._show_error(f"Could not create product folder: {e.message}")
        except Exception as e:
            self._show_error(f"Unexpected error: {e}")

    def _use_existing_product(self) -> None:
        self.page.run_task(self._fetch_and_show_folders)

    async def _fetch_and_show_folders(self) -> None:
        try:
            folders = await self._drive().list_root_folders()
            existing_ids = {p.folder_id for p in self.state.products}
            dialogs.show_select_product_dialog(
                self.page,
                folders=folders,
                existing_ids=existing_ids,
                on_select=self._on_folder_selected,
            )
        except DriveAPIError as e:
            self._show_error(f"Could not load Drive folders: {e.message}")
        except Exception as e:
            self._show_error(f"Unexpected error: {e}")

    def _on_folder_selected(self, folder: DriveItem) -> None:
        product = ProductReference(folder_id=folder.id, name=folder.name)
        if not any(p.folder_id == folder.id for p in self.state.products):
            self.state.products.append(product)
            self._save_products(self.state.user_id, self.state.products)
            self._refresh_sidebar()
        self.page.run_task(self._load_product, folder.id)

    def _on_delete_product(self, product) -> None:
        dialogs.show_trash_dialog(
            self.page,
            item=None,
            label=f'Delete project "{product.name}"? This will move the folder to Drive Trash.',
            on_confirm=lambda: self.page.run_task(self._do_delete_product, product),
        )

    async def _do_delete_product(self, product) -> None:
        try:
            await self._drive().trash_item(product.folder_id)
            self.state.products = [p for p in self.state.products if p.folder_id != product.folder_id]
            self._save_products(self.state.user_id, self.state.products)
            if self.state.current_product_id == product.folder_id:
                self.state.clear_workspace()
            self._snack(f'Project "{product.name}" moved to Drive Trash.')
        except Exception as e:
            self._show_error(f"Could not delete project: {e}")
        self._refresh_all()

    def _on_select_product(self, product_id: str) -> None:
        if product_id == self.state.current_product_id:
            return
        self.state.clear_workspace()
        self.state.current_product_id = product_id
        self._refresh_all()
        self.page.run_task(self._load_product, product_id)

    async def _load_product(self, product_id: str) -> None:
        self.state.current_product_id = product_id
        self.state.loading = True
        self._refresh_content()
        try:
            children = await self._drive().list_children(product_id)
            self.state.children_cache[product_id] = children
        except DriveAPIError as e:
            self._show_error(f"Could not load product: {e.message}")
        except Exception as e:
            self._show_error(f"Unexpected error: {e}")
        finally:
            self.state.loading = False
        self._refresh_header()
        self._refresh_content()

    # ─────────────────────────── Tree interactions ────────────────────────

    def _on_select_item(self, item_id: str) -> None:
        if self.state.selected_item_id == item_id:
            self.state.selected_item_id = None
        else:
            self.state.selected_item_id = item_id
        self._refresh_content()
        self._refresh_details()

    def _on_toggle_expand(self, folder_id: str) -> None:
        if folder_id in self.state.expanded_ids:
            self.state.expanded_ids.discard(folder_id)
            self._refresh_content()
        else:
            self.state.expanded_ids.add(folder_id)
            self._refresh_content()
            if folder_id not in self.state.children_cache:
                self.page.run_task(self._load_folder_children, folder_id)

    async def _load_folder_children(self, folder_id: str) -> None:
        try:
            children = await self._drive().list_children(folder_id)
            self.state.children_cache[folder_id] = children
        except DriveAPIError as e:
            self._show_error(f"Could not load folder: {e.message}")
        except Exception as e:
            self._show_error(f"Error loading folder: {e}")
        self._refresh_content()

    # ─────────────────────────── View switching ───────────────────────────

    def _on_switch_view(self, view: str) -> None:
        self.state.current_view = view
        self._refresh_header()
        self._refresh_content()

    # ─────────────────────────── Expand / Collapse all ───────────────────

    def _on_expand_all(self) -> None:
        self.page.run_task(self._do_expand_all)

    async def _do_expand_all(self) -> None:
        if not self.state.current_product_id:
            return
        # BFS through all known folders, fetching children for any not yet loaded
        queue = [self.state.current_product_id]
        visited: set[str] = set()
        while queue:
            folder_id = queue.pop(0)
            if folder_id in visited:
                continue
            visited.add(folder_id)
            if folder_id not in self.state.children_cache:
                try:
                    children = await self._drive().list_children(folder_id)
                    self.state.children_cache[folder_id] = children
                except Exception:
                    continue
            for item in self.state.children_cache.get(folder_id, []):
                if item.is_folder:
                    self.state.expanded_ids.add(item.id)
                    queue.append(item.id)
        self._refresh_content()

    def _on_collapse_all(self) -> None:
        self.state.expanded_ids.clear()
        self._refresh_content()

    # ─────────────────────────── Refresh ─────────────────────────────────

    def _on_refresh(self) -> None:
        if not self.state.current_product_id:
            return
        product_id = self.state.current_product_id
        prev_expanded = set(self.state.expanded_ids)
        prev_selected = self.state.selected_item_id

        self.state.children_cache.clear()
        self.state.expanded_ids.clear()
        self.state.selected_item_id = None

        self.page.run_task(self._do_refresh, product_id, prev_expanded, prev_selected)

    async def _do_refresh(self, product_id: str, prev_expanded: set, prev_selected: str | None) -> None:
        self.state.loading = True
        self._refresh_content()
        try:
            children = await self._drive().list_children(product_id)
            self.state.children_cache[product_id] = children

            # Reload previously expanded folders
            for folder_id in prev_expanded:
                try:
                    sub_children = await self._drive().list_children(folder_id)
                    self.state.children_cache[folder_id] = sub_children
                    self.state.expanded_ids.add(folder_id)
                except Exception:
                    pass

            # Restore selection if still present
            if prev_selected and self.state.get_cached_item(prev_selected):
                self.state.selected_item_id = prev_selected

        except DriveAPIError as e:
            self._show_error(f"Could not refresh: {e.message}")
        except Exception as e:
            self._show_error(f"Error refreshing: {e}")
        finally:
            self.state.loading = False
        self._refresh_content()
        self._refresh_details()

    # ─────────────────────────── Drive mutations ──────────────────────────

    def _on_create_subfolder_in(self, parent_id: str) -> None:
        parent_item = self.state.get_cached_item(parent_id)
        parent_name = parent_item.name if parent_item else "folder"
        dialogs.show_create_folder_dialog(
            self.page,
            parent_name=parent_name,
            on_create=lambda name: self.page.run_task(self._do_create_folder, name, parent_id),
        )

    def _on_create_folder(self) -> None:
        parent_id = get_create_folder_parent(self.state)
        if not parent_id:
            return
        parent_item = self.state.get_cached_item(parent_id)
        parent_name = parent_item.name if parent_item else (
            self.state.get_current_product().name if self.state.get_current_product() else "Product"
        )
        dialogs.show_create_folder_dialog(
            self.page,
            parent_name=parent_name,
            on_create=lambda name: self.page.run_task(self._do_create_folder, name, parent_id),
        )

    async def _do_create_folder(self, name: str, parent_id: str) -> None:
        try:
            new_folder = await self._drive().create_folder(name, parent_id)
            # Insert into cache
            if parent_id not in self.state.children_cache:
                self.state.children_cache[parent_id] = []
            self.state.children_cache[parent_id].append(new_folder)
            # Expand parent and select new folder
            self.state.expanded_ids.add(parent_id)
            self.state.selected_item_id = new_folder.id
            self._snack(f'Folder "{name}" created.')
        except DriveAPIError as e:
            self._show_error(f"Could not create folder: {e.message}")
        except Exception as e:
            self._show_error(f"Unexpected error: {e}")
        self._refresh_content()
        self._refresh_details()

    def _on_rename_item(self, item: DriveItem) -> None:
        dialogs.show_rename_dialog(
            self.page,
            item=item,
            on_rename=lambda name: self.page.run_task(self._do_rename, item.id, name),
        )

    async def _do_rename(self, item_id: str, new_name: str) -> None:
        try:
            updated = await self._drive().rename_item(item_id, new_name)
            self.state.update_item_in_cache(updated)
            # If this is a product, update product name
            for product in self.state.products:
                if product.folder_id == item_id:
                    product.name = new_name
                    self._save_products(self.state.user_id, self.state.products)
                    break
            self._snack(f'Renamed to "{new_name}".')
        except DriveAPIError as e:
            self._show_error(f"Could not rename: {e.message}")
        except Exception as e:
            self._show_error(f"Unexpected error: {e}")
        self._refresh_header()
        self._refresh_sidebar()
        self._refresh_content()
        self._refresh_details()

    def _on_move_item(self, item: DriveItem) -> None:
        # Collect all folders from cache as move targets
        all_folders: list[DriveItem] = []
        for children in self.state.children_cache.values():
            for child in children:
                if child.is_folder and child.id != item.id:
                    all_folders.append(child)

        # Include the product root as option
        if self.state.current_product_id:
            product = self.state.get_current_product()
            if product:
                root_item = DriveItem(
                    id=self.state.current_product_id,
                    name=product.name,
                    mime_type="application/vnd.google-apps.folder",
                    parents=[],
                    is_folder=True,
                )
                all_folders.insert(0, root_item)

        dialogs.show_move_dialog(
            self.page,
            item=item,
            folder_options=all_folders,
            on_move=lambda target_id: self.page.run_task(self._do_move, item.id, target_id),
        )

    async def _do_move(self, item_id: str, target_id: str) -> None:
        valid, reason = validate_move(self.state, item_id, target_id)
        if not valid:
            self._show_error(reason)
            return
        try:
            updated = await self._drive().move_item(item_id, target_id)
            # Remove from old parent in cache
            self.state.remove_item_from_cache(item_id)
            # Insert into new parent cache
            if target_id not in self.state.children_cache:
                self.state.children_cache[target_id] = []
            self.state.children_cache[target_id].append(updated)
            self.state.expanded_ids.add(target_id)
            self._snack("Item moved.")
        except DriveAPIError as e:
            self._show_error(f"Could not move item: {e.message}")
        except Exception as e:
            self._show_error(f"Unexpected error: {e}")
        self._refresh_content()
        self._refresh_details()

    def _on_trash_item(self, item: DriveItem) -> None:
        dialogs.show_trash_dialog(
            self.page,
            item=item,
            on_confirm=lambda: self.page.run_task(self._do_trash, item.id),
        )

    async def _do_trash(self, item_id: str) -> None:
        try:
            await self._drive().trash_item(item_id)
            self.state.remove_item_from_cache(item_id)
            self.state.expanded_ids.discard(item_id)
            self.state.children_cache.pop(item_id, None)
            if self.state.selected_item_id == item_id:
                self.state.selected_item_id = None
            self._snack("Moved to Trash.")
        except DriveAPIError as e:
            self._show_error(f"Could not move to Trash: {e.message}")
        except Exception as e:
            self._show_error(f"Unexpected error: {e}")
        self._refresh_content()
        self._refresh_details()

    # ─────────────────────────── Drag & drop ─────────────────────────────

    def _handle_drop(self, source_id: str, target_id: str) -> None:
        valid, reason = validate_move(self.state, source_id, target_id)
        if not valid:
            self._show_error(reason)
            return
        self.page.run_task(self._do_move, source_id, target_id)

    # ─────────────────────────── Misc ────────────────────────────────────

    def _open_in_drive(self, item: DriveItem) -> None:
        if item.web_view_link:
            self.page.launch_url(item.web_view_link, web_popup_window_name="_blank")
        else:
            self._show_error("No Drive link available for this item.")

    def _on_import_files(self, parent_id: str | None = None) -> None:
        # FilePicker not supported in Flet web mode — open Drive folder directly
        target_id = parent_id or self.state.current_product_id
        if target_id:
            self.page.launch_url(
                f"https://drive.google.com/drive/folders/{target_id}",
                web_popup_window_name="_blank",
            )
        else:
            self.page.launch_url("https://drive.google.com", web_popup_window_name="_blank")

    def _on_logout(self) -> None:
        self.page.logout()
