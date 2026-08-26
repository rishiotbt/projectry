import flet as ft
from app import config


def build_login_view(on_login_click=None) -> ft.Control:
    return ft.Container(
        bgcolor=config.BG_COLOR,
        expand=True,
        content=ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
            controls=[
                ft.Container(height=40),
                # Logo / icon area
                ft.Container(
                    width=48,
                    height=48,
                    bgcolor=config.ACCENT_COLOR,
                    border_radius=12,
                    content=ft.Icon(ft.Icons.FOLDER_OPEN, color="white", size=26),
                ),
                ft.Container(height=24),
                # Title
                ft.Text(
                    "Product Tree",
                    size=26,
                    weight=ft.FontWeight.W_700,
                    color=config.TEXT_COLOR,
                ),
                ft.Container(height=8),
                # Subtitle
                ft.Text(
                    "Your product workspace, powered by Drive.",
                    size=14,
                    color=config.TEXT_SECONDARY_COLOR,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=36),
                # Google login button
                ft.Container(
                    width=260,
                    height=44,
                    bgcolor=config.SURFACE_COLOR,
                    border_radius=8,
                    border=ft.Border.all(1, config.BORDER_COLOR),
                    url="/auth/login",
                    ink=True,
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=10,
                        controls=[
                            ft.Image(
                                src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg",
                                width=18,
                                height=18,
                                fit=ft.BoxFit.CONTAIN,
                            ),
                            ft.Text(
                                "Continue with Google",
                                size=14,
                                weight=ft.FontWeight.W_500,
                                color=config.TEXT_COLOR,
                            ),
                        ],
                    ),
                ),
                ft.Container(height=20),
                ft.Text(
                    "We only access Drive after you approve.",
                    size=12,
                    color=config.TEXT_SECONDARY_COLOR,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=8),
                ft.Text(
                    "This app requires Google Drive access to manage your product folders.",
                    size=11,
                    color="#AAAAAA",
                    text_align=ft.TextAlign.CENTER,
                    width=300,
                ),
            ],
        ),
    )
