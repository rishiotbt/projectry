import flet as ft
from app import config
from app.models.drive_item import DriveItem
from app.services.tree_layout import PositionedNode, NODE_WIDTH, NODE_HEIGHT


def build_map_node(
    node: PositionedNode,
    selected_id: str | None,
    offset_x: float,
    offset_y: float,
    on_select,
    on_drop,
) -> list[ft.Control]:
    """Returns a list of Stack controls (node + connector lines to children)."""
    controls: list[ft.Control] = []
    item = node.item
    is_selected = item.id == selected_id

    node_content = ft.Container(
        width=NODE_WIDTH,
        height=NODE_HEIGHT,
        bgcolor=config.SELECTED_BG_COLOR if is_selected else config.SURFACE_COLOR,
        border=ft.Border.all(
            2 if is_selected else 1,
            config.ACCENT_COLOR if is_selected else config.BORDER_COLOR,
        ),
        border_radius=6,
        on_click=lambda _: on_select(item.id),
        content=ft.Row(
            spacing=6,
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Icon(
                    ft.Icons.FOLDER if item.is_folder else ft.Icons.INSERT_DRIVE_FILE,
                    size=14,
                    color="#F9A825" if item.is_folder else config.TEXT_SECONDARY_COLOR,
                ),
                ft.Text(
                    item.name,
                    size=11,
                    color=config.TEXT_COLOR,
                    overflow=ft.TextOverflow.ELLIPSIS,
                    max_lines=1,
                    expand=True,
                ),
            ],
        ),
    )

    ghost = ft.Container(
        width=NODE_WIDTH,
        height=NODE_HEIGHT,
        bgcolor=config.ACCENT_LIGHT_COLOR,
        border=ft.Border.all(1, config.ACCENT_COLOR),
        border_radius=6,
        opacity=0.6,
    )

    draggable_node = ft.Draggable(
        group="drive_items",
        data=item.id,
        content=node_content,
        content_when_dragging=ghost,
    )

    if item.is_folder:
        inner = ft.DragTarget(
            group="drive_items",
            content=draggable_node,
            on_accept=lambda e: on_drop(e.data, item.id),
        )
    else:
        inner = draggable_node

    # Wrap in a positioned container as direct Stack child
    positioned = ft.Container(
        left=node.x + offset_x,
        top=node.y + offset_y,
        width=NODE_WIDTH,
        height=NODE_HEIGHT,
        content=inner,
    )
    controls.append(positioned)

    # Draw connector lines to children
    parent_cx = node.x + offset_x + NODE_WIDTH / 2
    parent_bottom_y = node.y + offset_y + NODE_HEIGHT

    for child in node.children:
        child_cx = child.x + offset_x + NODE_WIDTH / 2
        child_top_y = child.y + offset_y

        mid_y = (parent_bottom_y + child_top_y) / 2

        # Vertical line from parent bottom to midpoint
        controls.append(ft.Container(
            left=parent_cx - 1,
            top=parent_bottom_y,
            width=2,
            height=mid_y - parent_bottom_y,
            bgcolor=config.BORDER_COLOR,
        ))

        # Horizontal line at midpoint
        x1 = min(parent_cx, child_cx)
        x2 = max(parent_cx, child_cx)
        if abs(x2 - x1) > 1:
            controls.append(ft.Container(
                left=x1,
                top=mid_y - 1,
                width=x2 - x1,
                height=2,
                bgcolor=config.BORDER_COLOR,
            ))

        # Vertical line from midpoint to child top
        controls.append(ft.Container(
            left=child_cx - 1,
            top=mid_y,
            width=2,
            height=child_top_y - mid_y,
            bgcolor=config.BORDER_COLOR,
        ))

        # Recurse for child's children
        child_controls = build_map_node(
            child, selected_id, offset_x, offset_y, on_select, on_drop
        )
        controls.extend(child_controls)

    return controls
