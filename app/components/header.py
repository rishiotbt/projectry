import flet as ft
from app import config
from app.state import AppState


def build_header(
    state: AppState,
    on_create_folder,
    on_import_files,
    on_refresh,
    on_expand_all,
    on_collapse_all,
    on_logout,
    on_open_drive,
    on_switch_view,
) -> ft.Control:
    product = state.get_current_product()
    product_name = product.name if product else "Product Tree"

    # View toggle buttons
    tree_active = state.current_view == "tree"
    map_active = state.current_view == "map"

    def view_btn(label: str, view: str, active: bool) -> ft.Container:
        return ft.Container(
            padding=ft.Padding.symmetric(horizontal=10, vertical=4),
            border_radius=5,
            bgcolor=config.SELECTED_BG_COLOR if active else "transparent",
            on_click=lambda _: on_switch_view(view),
            ink=True,
            content=ft.Text(
                label,
                size=12,
                weight=ft.FontWeight.W_500 if active else ft.FontWeight.W_400,
                color=config.ACCENT_COLOR if active else config.TEXT_SECONDARY_COLOR,
            ),
        )

    user_menu = ft.PopupMenuButton(
        content=ft.Row(
            spacing=6,
            controls=[
                ft.CircleAvatar(
                    foreground_image_src=state.user_avatar,
                    content=ft.Text(
                        (state.user_name or "U")[0].upper(),
                        size=12,
                        color="white",
                    ),
                    radius=14,
                    bgcolor=config.ACCENT_COLOR,
                ),
                ft.Icon(ft.Icons.ARROW_DROP_DOWN, size=16, color=config.TEXT_SECONDARY_COLOR),
            ],
        ),
        items=[
            ft.PopupMenuItem(
                content=ft.Column([
                    ft.Text(state.user_name or "", size=13, weight=ft.FontWeight.W_500, color=config.TEXT_COLOR),
                    ft.Text(state.user_email or "", size=11, color=config.TEXT_SECONDARY_COLOR),
                ], spacing=2),
                disabled=True,
            ),
            ft.PopupMenuItem(),
            ft.PopupMenuItem(
                content=ft.Row([
                    ft.Icon(ft.Icons.CHECK_CIRCLE, size=16, color=config.ACCENT_COLOR),
                    ft.Text("Connected to Google Drive", size=13, color=config.TEXT_COLOR),
                ], spacing=8),
                disabled=True,
            ),
            ft.PopupMenuItem(
                content=ft.Row([
                    ft.Icon(ft.Icons.OPEN_IN_NEW, size=16, color=config.TEXT_COLOR),
                    ft.Text("Open Google Drive", size=13, color=config.TEXT_COLOR),
                ], spacing=8),
                on_click=lambda _: on_open_drive(),
            ),
            ft.PopupMenuItem(),
            ft.PopupMenuItem(
                content=ft.Row([
                    ft.Icon(ft.Icons.LOGOUT, size=16, color=config.TEXT_COLOR),
                    ft.Text("Logout", size=13, color=config.TEXT_COLOR),
                ], spacing=8),
                on_click=lambda _: on_logout(),
            ),
        ],
    )

    return ft.Container(
        height=52,
        bgcolor=config.SURFACE_COLOR,
        border=ft.Border.only(bottom=ft.BorderSide(1, config.BORDER_COLOR)),
        padding=ft.Padding.symmetric(horizontal=16),
        content=ft.Row(
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                # Product name
                ft.Text(
                    product_name,
                    size=14,
                    weight=ft.FontWeight.W_600,
                    color=config.TEXT_COLOR,
                ),
                ft.Container(width=16),
                # View toggle
                ft.Container(
                    bgcolor=config.BG_COLOR,
                    border_radius=6,
                    border=ft.Border.all(1, config.BORDER_COLOR),
                    padding=ft.Padding.all(2),
                    content=ft.Row([
                        view_btn("Tree", "tree", tree_active),
                        view_btn("Map", "map", map_active),
                    ], spacing=2),
                ),
                # Spacer
                ft.Container(expand=True),
                # + Folder button
                ft.TextButton(
                    content=ft.Row([
                        ft.Icon(ft.Icons.CREATE_NEW_FOLDER_OUTLINED, size=15, color=config.ACCENT_COLOR),
                        ft.Text("Folder", size=13, color=config.ACCENT_COLOR),
                    ], spacing=5),
                    on_click=lambda _: on_create_folder(),
                    style=ft.ButtonStyle(
                        padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                        overlay_color=config.ACCENT_LIGHT_COLOR,
                    ),
                    disabled=state.current_product_id is None,
                ),
                # Upload files button (opens Drive folder)
                ft.TextButton(
                    content=ft.Row([
                        ft.Icon(ft.Icons.UPLOAD_FILE, size=15, color=config.ACCENT_COLOR),
                        ft.Text("Upload", size=13, color=config.ACCENT_COLOR),
                    ], spacing=5),
                    tooltip="Upload files via Google Drive",
                    on_click=lambda _: on_import_files(),
                    style=ft.ButtonStyle(
                        padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                        overlay_color=config.ACCENT_LIGHT_COLOR,
                    ),
                    disabled=state.current_product_id is None,
                ),
                # Expand / Collapse all
                ft.IconButton(
                    icon=ft.Icons.UNFOLD_MORE,
                    icon_size=18,
                    icon_color=config.TEXT_SECONDARY_COLOR,
                    tooltip="Expand all folders",
                    on_click=lambda _: on_expand_all(),
                    disabled=state.current_product_id is None,
                ),
                ft.IconButton(
                    icon=ft.Icons.UNFOLD_LESS,
                    icon_size=18,
                    icon_color=config.TEXT_SECONDARY_COLOR,
                    tooltip="Collapse all folders",
                    on_click=lambda _: on_collapse_all(),
                    disabled=state.current_product_id is None,
                ),
                # Refresh
                ft.IconButton(
                    icon=ft.Icons.REFRESH,
                    icon_size=18,
                    icon_color=config.TEXT_SECONDARY_COLOR,
                    tooltip="Refresh",
                    on_click=lambda _: on_refresh(),
                    disabled=state.current_product_id is None,
                ),
                ft.Container(width=4),
                # User menu
                user_menu,
            ],
        ),
    )
