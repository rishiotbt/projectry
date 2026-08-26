from dataclasses import dataclass, field
from app.models.drive_item import DriveItem
from app.state import AppState

NODE_WIDTH = 160.0
NODE_HEIGHT = 40.0
H_GAP = 24.0
V_GAP = 64.0


@dataclass
class PositionedNode:
    item: DriveItem
    x: float
    y: float
    width: float = NODE_WIDTH
    height: float = NODE_HEIGHT
    children: list["PositionedNode"] = field(default_factory=list)


class TreeLayoutService:
    def __init__(self, state: AppState):
        self.state = state

    def _subtree_width(self, item_id: str) -> float:
        children = self.state.children_cache.get(item_id, [])
        if not children:
            return NODE_WIDTH
        total = sum(self._subtree_width(c.id) for c in children)
        gaps = H_GAP * (len(children) - 1)
        return max(NODE_WIDTH, total + gaps)

    def _layout(self, item: DriveItem, center_x: float, top_y: float) -> PositionedNode:
        children_items = self.state.children_cache.get(item.id, [])
        child_nodes: list[PositionedNode] = []

        if children_items:
            child_y = top_y + NODE_HEIGHT + V_GAP
            total_w = sum(self._subtree_width(c.id) for c in children_items)
            total_w += H_GAP * (len(children_items) - 1)
            child_x = center_x - total_w / 2

            for child in children_items:
                cw = self._subtree_width(child.id)
                node = self._layout(child, child_x + cw / 2, child_y)
                child_nodes.append(node)
                child_x += cw + H_GAP

        return PositionedNode(
            item=item,
            x=center_x - NODE_WIDTH / 2,
            y=top_y,
            width=NODE_WIDTH,
            height=NODE_HEIGHT,
            children=child_nodes,
        )

    def layout(self, root: DriveItem) -> PositionedNode:
        return self._layout(root, 0.0, 0.0)

    def total_bounds(self, node: PositionedNode) -> tuple[float, float, float, float]:
        """Returns (min_x, min_y, max_x, max_y) for the entire subtree."""
        min_x = node.x
        min_y = node.y
        max_x = node.x + node.width
        max_y = node.y + node.height
        for child in node.children:
            cx1, cy1, cx2, cy2 = self.total_bounds(child)
            min_x = min(min_x, cx1)
            min_y = min(min_y, cy1)
            max_x = max(max_x, cx2)
            max_y = max(max_y, cy2)
        return min_x, min_y, max_x, max_y
