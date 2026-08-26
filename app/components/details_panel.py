import flet as ft
from app import config
from app.models.drive_item import DriveItem
from app.utils.drive_helpers import format_modified_time


def build_details_panel(
    item: DriveItem,
    path_display: str,
    on_open_in_drive,
    on_rename,
    on_move,
    on_trash,
) -> ft.Control:
    date_str = format_modified_time(item.modified_time)

    def section_label(text: str) -> ft.Text:
        return ft.Text(text, size=11, weight=ft.FontWeight.W_600, color=config.TEXT_SECONDARY_COLOR)

    def divider() -> ft.Divider:
        return ft.Divider(height=1, color=config.BORDER_COLOR)

    def action_row(icon, label: str, on_click, color=None, disabled=False) -> ft.Container:
        c = color or config.TEXT_COLOR
        return ft.Container(
            padding=ft.Padding.symmetric(horizontal=0, vertical=8),
            on_click=on_click if not disabled else None,
            content=ft.Row([
                ft.Icon(icon, size=15, color=c if not disabled else config.BORDER_COLOR),
                ft.Text(label, size=13, color=c if not disabled else config.BORDER_COLOR),
            ], spacing=10),
            disabled=disabled,
        )

    return ft.Container(
        width=260,
        bgcolor=config.SURFACE_COLOR,
        border=ft.Border.only(left=ft.BorderSide(1, config.BORDER_COLOR)),
        padding=ft.Padding.symmetric(horizontal=16, vertical=16),
        content=ft.Column(
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                # Item name
                ft.Row([
                    ft.Icon(
                        ft.Icons.FOLDER if item.is_folder else ft.Icons.INSERT_DRIVE_FILE,
                        color="#F9A825" if item.is_folder else config.TEXT_SECONDARY_COLOR,
                        size=18,
                    ),
                    ft.Text(
                        item.name,
                        size=14,
                        weight=ft.FontWeight.W_600,
                        color=config.TEXT_COLOR,
                        expand=True,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                ], spacing=8),

                divider(),

                # Type
                ft.Column([
                    section_label("TYPE"),
                    ft.Text(item.mime_label(), size=13, color=config.TEXT_COLOR),
                ], spacing=4),

                # Location
                ft.Column([
                    section_label("LOCATION"),
                    ft.Text(
                        path_display or "—",
                        size=13,
                        color=config.TEXT_COLOR,
                        overflow=ft.TextOverflow.ELLIPSIS,
                        max_lines=2,
                    ),
                ], spacing=4),

                # Modified
                ft.Column([
                    section_label("MODIFIED"),
                    ft.Text(date_str or "—", size=13, color=config.TEXT_COLOR),
                ], spacing=4),

                divider(),

                # Open in Drive
                action_row(
                    ft.Icons.OPEN_IN_NEW,
                    "Open in Drive",
                    lambda _: on_open_in_drive(item),
                    color=config.ACCENT_COLOR,
                    disabled=not item.web_view_link,
                ),

                divider(),

                # Edit actions
                action_row(
                    ft.Icons.EDIT_OUTLINED,
                    "Rename",
                    lambda _: on_rename(item),
                    disabled=not item.can_rename,
                ),
                action_row(
                    ft.Icons.DRIVE_FILE_MOVE_OUTLINED,
                    "Move",
                    lambda _: on_move(item),
                    disabled=not item.can_move_item_within_drive,
                ),

                divider(),

                action_row(
                    ft.Icons.DELETE_OUTLINE,
                    "Move to Trash",
                    lambda _: on_trash(item),
                    color=config.DANGER_COLOR,
                    disabled=not item.can_trash,
                ),
            ],
        ),
    )


def build_empty_details_panel() -> ft.Control:
    return ft.Container(
        width=260,
        bgcolor=config.SURFACE_COLOR,
        border=ft.Border.only(left=ft.BorderSide(1, config.BORDER_COLOR)),
        content=ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
            controls=[
                ft.Icon(ft.Icons.TOUCH_APP_OUTLINED, size=32, color=config.BORDER_COLOR),
                ft.Container(height=8),
                ft.Text("Select an item", size=13, color=config.TEXT_SECONDARY_COLOR),
            ],
        ),
    )
