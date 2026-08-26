import flet as ft
from app import config
from app.models.drive_item import DriveItem
from app.utils.drive_helpers import format_modified_time


def _file_icon(item: DriveItem) -> ft.Icon:
    if item.is_folder:
        return ft.Icon(ft.Icons.FOLDER, color="#F9A825", size=16)
    mime = item.mime_type
    if "document" in mime:
        return ft.Icon(ft.Icons.DESCRIPTION, color="#4285F4", size=16)
    if "spreadsheet" in mime:
        return ft.Icon(ft.Icons.TABLE_CHART, color="#0F9D58", size=16)
    if "presentation" in mime:
        return ft.Icon(ft.Icons.SLIDESHOW, color="#F4B400", size=16)
    if "pdf" in mime:
        return ft.Icon(ft.Icons.PICTURE_AS_PDF, color="#EA4335", size=16)
    if "image" in mime:
        return ft.Icon(ft.Icons.IMAGE, color="#9C27B0", size=16)
    return ft.Icon(ft.Icons.INSERT_DRIVE_FILE, color=config.TEXT_SECONDARY_COLOR, size=16)


def build_tree_row(
    item: DriveItem,
    depth: int,
    is_selected: bool,
    is_expanded: bool,
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
    indent = depth * 18

    # Expand/collapse arrow (only for folders)
    if item.is_folder:
        arrow = ft.IconButton(
            icon=ft.Icons.KEYBOARD_ARROW_DOWN if is_expanded else ft.Icons.KEYBOARD_ARROW_RIGHT,
            icon_size=16,
            icon_color=config.TEXT_SECONDARY_COLOR,
            on_click=lambda e: on_toggle_expand(item.id),
            padding=ft.Padding.all(0),
            style=ft.ButtonStyle(
                padding=ft.Padding.all(2),
                overlay_color={"": "transparent"},
            ),
        )
    else:
        arrow = ft.Container(width=24)

    date_str = format_modified_time(item.modified_time)

    actions_menu = ft.PopupMenuButton(
        icon=ft.Icons.MORE_HORIZ,
        icon_size=16,
        icon_color=config.TEXT_SECONDARY_COLOR,
        style=ft.ButtonStyle(
            padding=ft.Padding.all(2),
            overlay_color={"": "transparent"},
        ),
        items=[
            ft.PopupMenuItem(
                content=ft.Row([ft.Icon(ft.Icons.OPEN_IN_NEW, size=16, color=config.TEXT_COLOR), ft.Text("Open in Drive", size=13, color=config.TEXT_COLOR)], spacing=8),
                on_click=lambda _: on_open_in_drive(item),
            ),
            *([
                ft.PopupMenuItem(),
                ft.PopupMenuItem(
                    content=ft.Row([ft.Icon(ft.Icons.CREATE_NEW_FOLDER_OUTLINED, size=16, color=config.TEXT_COLOR), ft.Text("New Subfolder", size=13, color=config.TEXT_COLOR)], spacing=8),
                    on_click=lambda _: on_create_subfolder(item.id) if on_create_subfolder else None,
                ),
                ft.PopupMenuItem(
                    content=ft.Row([ft.Icon(ft.Icons.UPLOAD_FILE, size=16, color=config.TEXT_COLOR), ft.Text("Upload Files Here", size=13, color=config.TEXT_COLOR)], spacing=8),
                    on_click=lambda _: on_import_files(item.id) if on_import_files else None,
                ),
            ] if item.is_folder else []),
            ft.PopupMenuItem(),
            ft.PopupMenuItem(
                content=ft.Row([ft.Icon(ft.Icons.EDIT, size=16, color=config.TEXT_COLOR), ft.Text("Rename", size=13, color=config.TEXT_COLOR)], spacing=8),
                on_click=lambda _: on_rename(item),
                disabled=not item.can_rename,
            ),
            ft.PopupMenuItem(
                content=ft.Row([ft.Icon(ft.Icons.DRIVE_FILE_MOVE, size=16, color=config.TEXT_COLOR), ft.Text("Move", size=13, color=config.TEXT_COLOR)], spacing=8),
                on_click=lambda _: on_move(item),
                disabled=not item.can_move_item_within_drive,
            ),
            ft.PopupMenuItem(),
            ft.PopupMenuItem(
                content=ft.Row([ft.Icon(ft.Icons.DELETE_OUTLINE, size=16, color=config.DANGER_COLOR), ft.Text("Move to Trash", size=13, color=config.DANGER_COLOR)], spacing=8),
                on_click=lambda _: on_trash(item),
                disabled=not item.can_trash,
            ),
        ],
    )

    row_content = ft.Container(
        height=32,
        bgcolor=config.SELECTED_BG_COLOR if is_selected else "transparent",
        border_radius=4,
        on_click=lambda _: on_select(item.id),
        on_hover=lambda e: _on_hover(e, is_selected),
        padding=ft.Padding.only(left=indent + 4, right=4),
        content=ft.Row(
            spacing=4,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                arrow,
                _file_icon(item),
                ft.Text(
                    item.name,
                    size=13,
                    color=config.TEXT_COLOR,
                    expand=True,
                    overflow=ft.TextOverflow.ELLIPSIS,
                    max_lines=1,
                ),
                ft.Text(
                    date_str,
                    size=11,
                    color=config.TEXT_SECONDARY_COLOR,
                    width=90,
                    text_align=ft.TextAlign.RIGHT,
                ),
                actions_menu,
            ],
        ),
    )

    def _on_hover(e: ft.HoverEvent, selected: bool) -> None:
        if not selected:
            e.control.bgcolor = config.HOVER_BG_COLOR if e.data == "true" else "transparent"
            e.control.update()

    # Wrap in Draggable; folders also act as DragTarget
    draggable = ft.Draggable(
        group="drive_items",
        content=row_content,
        content_when_dragging=ft.Container(
            height=32,
            bgcolor=config.ACCENT_LIGHT_COLOR,
            border_radius=4,
            opacity=0.6,
            padding=ft.Padding.only(left=indent + 4, right=4),
            content=ft.Row(
                spacing=4,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(width=24),
                    _file_icon(item),
                    ft.Text(item.name, size=13, color=config.ACCENT_COLOR),
                ],
            ),
        ),
        data=item.id,
    )

    if item.is_folder:
        return ft.DragTarget(
            group="drive_items",
            content=draggable,
            on_accept=lambda e: on_drop(e.data, item.id),
            on_will_accept=lambda e: _on_will_accept(e),
            on_leave=lambda e: _on_leave(e),
        )

    return draggable


def _on_will_accept(e: ft.DragTargetEvent) -> None:
    e.control.content.content.bgcolor = config.ACCENT_LIGHT_COLOR
    try:
        e.control.update()
    except Exception:
        pass


def _on_leave(e: ft.DragTargetEvent) -> None:
    e.control.content.content.bgcolor = "transparent"
    try:
        e.control.update()
    except Exception:
        pass
