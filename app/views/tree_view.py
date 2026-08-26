import flet as ft
from app import config
from app.state import AppState
from app.models.drive_item import DriveItem
from app.components.tree_row import build_tree_row


def build_skeleton_rows(count: int = 6) -> list[ft.Control]:
    rows = []
    widths = [220, 180, 160, 140, 200, 170]
    indents = [0, 18, 36, 36, 18, 36]
    for i in range(min(count, len(widths))):
        rows.append(ft.Container(
            height=32,
            padding=ft.Padding.only(left=indents[i % len(indents)] + 8, top=8, bottom=8),
            content=ft.Container(
                height=14,
                width=widths[i % len(widths)],
                bgcolor=config.SKELETON_COLOR,
                border_radius=4,
            ),
        ))
    return rows


def build_tree_view(
    state: AppState,
    on_select,
    on_toggle_expand,
    on_rename,
    on_move,
    on_trash,
    on_open_in_drive,
    on_drop,
    on_create_subfolder=None,
    on_import_files=None,
) -> ft.Control:
    if state.loading:
        return ft.Container(
            expand=True,
            bgcolor=config.SURFACE_COLOR,
            padding=ft.Padding.all(12),
            content=ft.Column(controls=build_skeleton_rows(), spacing=0),
        )

    if not state.current_product_id:
        return ft.Container(
            expand=True,
            bgcolor=config.SURFACE_COLOR,
            content=ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
                controls=[
                    ft.Icon(ft.Icons.FOLDER_OPEN, size=48, color=config.BORDER_COLOR),
                    ft.Container(height=12),
                    ft.Text("Select or create a product to get started", size=14, color=config.TEXT_SECONDARY_COLOR),
                ],
            ),
        )

    root_children = state.children_cache.get(state.current_product_id, [])
    if not root_children:
        return ft.Container(
            expand=True,
            bgcolor=config.SURFACE_COLOR,
            content=ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
                controls=[
                    ft.Icon(ft.Icons.FOLDER_OPEN, size=48, color=config.BORDER_COLOR),
                    ft.Container(height=12),
                    ft.Text("This product folder is empty.", size=14, color=config.TEXT_SECONDARY_COLOR),
                    ft.Text("Create a folder to get started.", size=13, color=config.TEXT_SECONDARY_COLOR),
                ],
            ),
        )

    rows = _build_rows(
        parent_id=state.current_product_id,
        depth=0,
        state=state,
        on_select=on_select,
        on_toggle_expand=on_toggle_expand,
        on_rename=on_rename,
        on_move=on_move,
        on_trash=on_trash,
        on_open_in_drive=on_open_in_drive,
        on_drop=on_drop,
        on_create_subfolder=on_create_subfolder,
        on_import_files=on_import_files,
    )

    return ft.Container(
        expand=True,
        bgcolor=config.SURFACE_COLOR,
        padding=ft.Padding.symmetric(horizontal=8, vertical=6),
        content=ft.Column(
            controls=rows,
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        ),
    )


def _build_rows(
    parent_id: str,
    depth: int,
    state: AppState,
    on_select,
    on_toggle_expand,
    on_rename,
    on_move,
    on_trash,
    on_open_in_drive,
    on_drop,
    on_create_subfolder=None,
    on_import_files=None,
) -> list[ft.Control]:
    rows: list[ft.Control] = []
    children = state.children_cache.get(parent_id, [])

    for item in children:
        is_selected = item.id == state.selected_item_id
        is_expanded = item.id in state.expanded_ids

        row = build_tree_row(
            item=item,
            depth=depth,
            is_selected=is_selected,
            is_expanded=is_expanded,
            on_select=on_select,
            on_toggle_expand=on_toggle_expand,
            on_rename=on_rename,
            on_move=on_move,
            on_trash=on_trash,
            on_open_in_drive=on_open_in_drive,
            on_drop=on_drop,
            on_create_subfolder=on_create_subfolder,
            on_import_files=on_import_files,
        )
        rows.append(row)

        if item.is_folder and is_expanded:
            child_rows = _build_rows(
                parent_id=item.id,
                depth=depth + 1,
                state=state,
                on_select=on_select,
                on_toggle_expand=on_toggle_expand,
                on_rename=on_rename,
                on_move=on_move,
                on_trash=on_trash,
                on_open_in_drive=on_open_in_drive,
                on_drop=on_drop,
                on_create_subfolder=on_create_subfolder,
                on_import_files=on_import_files,
            )
            rows.extend(child_rows)

            if item.id not in state.children_cache:
                rows.append(ft.Container(
                    height=24,
                    padding=ft.Padding.only(left=(depth + 1) * 18 + 28),
                    content=ft.Row([
                        ft.ProgressRing(width=12, height=12, stroke_width=2, color=config.ACCENT_COLOR),
                        ft.Text("Loading...", size=11, color=config.TEXT_SECONDARY_COLOR),
                    ], spacing=6),
                ))

    return rows
