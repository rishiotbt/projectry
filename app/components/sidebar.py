import flet as ft
from app import config
from app.state import AppState
from app.models.product import ProductReference


def build_sidebar(
    state: AppState,
    on_select_product,
    on_add_product,
    on_delete_product,
    on_open_drive,
) -> ft.Control:
    product_items: list[ft.Control] = []
    for product in state.products:
        is_active = product.folder_id == state.current_product_id
        product_items.append(
            ft.Container(
                padding=ft.Padding.symmetric(horizontal=12, vertical=7),
                border_radius=6,
                bgcolor=config.SELECTED_BG_COLOR if is_active else "transparent",
                on_click=lambda e, pid=product.folder_id: on_select_product(pid),
                ink=True,
                content=ft.Row([
                    ft.Container(
                        width=3,
                        height=16,
                        bgcolor=config.ACCENT_COLOR if is_active else "transparent",
                        border_radius=2,
                    ),
                    ft.Text(
                        product.name,
                        size=13,
                        weight=ft.FontWeight.W_500 if is_active else ft.FontWeight.W_400,
                        color=config.ACCENT_COLOR if is_active else config.TEXT_COLOR,
                        overflow=ft.TextOverflow.ELLIPSIS,
                        expand=True,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.DELETE_OUTLINE,
                        icon_size=14,
                        icon_color=config.DANGER_COLOR,
                        tooltip="Delete project",
                        on_click=lambda e, p=product: (e.stop_propagation() if hasattr(e, 'stop_propagation') else None, on_delete_product(p))[-1],
                        style=ft.ButtonStyle(padding=ft.Padding.all(2), overlay_color="transparent"),
                        visible=is_active,
                    ),
                ], spacing=8),
            )
        )

    return ft.Container(
        width=210,
        bgcolor=config.SIDEBAR_BG_COLOR,
        border=ft.Border.only(right=ft.BorderSide(1, config.BORDER_COLOR)),
        padding=ft.Padding.only(top=12, bottom=12),
        content=ft.Column(
            spacing=0,
            expand=True,
            controls=[
                # Projects label
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=16, vertical=4),
                    content=ft.Text(
                        "PROJECTS",
                        size=10,
                        weight=ft.FontWeight.W_700,
                        color=config.TEXT_SECONDARY_COLOR,
                    ),
                ),
                ft.Container(height=4),
                # Product list
                ft.Column(controls=product_items, spacing=2),
                ft.Container(height=8),
                # Add product button
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=12, vertical=7),
                    border_radius=6,
                    on_click=lambda _: on_add_product(),
                    ink=True,
                    content=ft.Row([
                        ft.Icon(ft.Icons.ADD, size=14, color=config.ACCENT_COLOR),
                        ft.Text("Add Project", size=13, color=config.ACCENT_COLOR),
                    ], spacing=6),
                ),
                # Spacer
                ft.Container(expand=True),
                ft.Divider(height=1, color=config.BORDER_COLOR),
                ft.Container(height=8),
                # Drive link
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=12, vertical=7),
                    border_radius=6,
                    on_click=lambda _: on_open_drive(),
                    ink=True,
                    content=ft.Row([
                        ft.Icon(ft.Icons.CLOUD_OUTLINED, size=14, color=config.TEXT_SECONDARY_COLOR),
                        ft.Text("Google Drive", size=13, color=config.TEXT_SECONDARY_COLOR),
                    ], spacing=6),
                ),
            ],
        ),
    )
