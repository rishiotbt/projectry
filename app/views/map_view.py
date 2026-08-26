import flet as ft
from app import config
from app.state import AppState
from app.models.drive_item import DriveItem
from app.services.tree_layout import TreeLayoutService, PositionedNode, NODE_WIDTH, NODE_HEIGHT
from app.components.map_node import build_map_node


def build_map_view(
    state: AppState,
    on_select,
    on_drop,
) -> ft.Control:
    if not state.current_product_id:
        return ft.Container(
            expand=True,
            bgcolor=config.SURFACE_COLOR,
            content=ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
                controls=[
                    ft.Icon(ft.Icons.ACCOUNT_TREE, size=48, color=config.BORDER_COLOR),
                    ft.Container(height=12),
                    ft.Text("Select a product to see the map view", size=14, color=config.TEXT_SECONDARY_COLOR),
                ],
            ),
        )

    root_id = state.current_product_id
    root_children = state.children_cache.get(root_id, [])

    if not root_children:
        return ft.Container(
            expand=True,
            bgcolor=config.SURFACE_COLOR,
            content=ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
                controls=[
                    ft.Icon(ft.Icons.ACCOUNT_TREE, size=48, color=config.BORDER_COLOR),
                    ft.Container(height=12),
                    ft.Text("No items to display in map view.", size=14, color=config.TEXT_SECONDARY_COLOR),
                ],
            ),
        )

    # Get the product root item
    product_item = DriveItem(
        id=root_id,
        name=state.get_current_product().name if state.get_current_product() else "Product",
        mime_type="application/vnd.google-apps.folder",
        parents=[],
        is_folder=True,
    )

    layout_service = TreeLayoutService(state)
    root_node = layout_service.layout(product_item)
    min_x, min_y, max_x, max_y = layout_service.total_bounds(root_node)

    # Shift everything so min_x/min_y become (PADDING, PADDING)
    PADDING = 40.0
    offset_x = -min_x + PADDING
    offset_y = -min_y + PADDING

    total_w = max_x - min_x + PADDING * 2
    total_h = max_y - min_y + PADDING * 2

    stack_controls = build_map_node(
        node=root_node,
        selected_id=state.selected_item_id,
        offset_x=offset_x,
        offset_y=offset_y,
        on_select=on_select,
        on_drop=on_drop,
    )

    return ft.Container(
        expand=True,
        bgcolor=config.BG_COLOR,
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            controls=[
                ft.Row(
                    scroll=ft.ScrollMode.AUTO,
                    controls=[
                        ft.Stack(
                            controls=stack_controls,
                            width=max(total_w, 800),
                            height=max(total_h, 500),
                        )
                    ],
                )
            ],
        ),
    )
