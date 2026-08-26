import flet as ft
from app import config


class ErrorBanner:
    def __init__(self, on_dismiss):
        self._on_dismiss = on_dismiss
        self.container = ft.Container(
            visible=False,
            bgcolor="#FFF3F3",
            border=ft.Border.all(1, "#FFCDD2"),
            border_radius=6,
            padding=ft.Padding.symmetric(horizontal=14, vertical=10),
            margin=ft.Margin.only(bottom=8),
        )

    def build(self) -> ft.Control:
        return self.container

    def show(self, message: str) -> None:
        self.container.content = ft.Row(
            controls=[
                ft.Icon(ft.Icons.ERROR_OUTLINE, color=config.DANGER_COLOR, size=16),
                ft.Text(message, color=config.DANGER_COLOR, size=13, expand=True),
                ft.IconButton(
                    icon=ft.Icons.CLOSE,
                    icon_size=14,
                    icon_color=config.DANGER_COLOR,
                    on_click=lambda _: self.hide(),
                    padding=ft.Padding.all(2),
                ),
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        self.container.visible = True
        try:
            self.container.update()
        except Exception:
            pass

    def hide(self) -> None:
        self.container.visible = False
        self._on_dismiss()
        try:
            self.container.update()
        except Exception:
            pass
