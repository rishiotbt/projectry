import flet as ft
from app import config
from app.models.drive_item import DriveItem


def _dialog_btn(text: str, on_click, primary: bool = False, danger: bool = False) -> ft.TextButton:
    if danger:
        color = config.DANGER_COLOR
    elif primary:
        color = config.ACCENT_COLOR
    else:
        color = config.TEXT_SECONDARY_COLOR
    return ft.TextButton(
        content=ft.Text(text, color=color),
        on_click=on_click,
    )


def show_create_folder_dialog(page: ft.Page, parent_name: str, on_create) -> None:
    name_field = ft.TextField(
        label="Folder name",
        autofocus=True,
        border_color=config.BORDER_COLOR,
        focused_border_color=config.ACCENT_COLOR,
        text_size=14,
    )
    error_text = ft.Text("", color=config.DANGER_COLOR, size=12, visible=False)

    def do_create(e):
        name = name_field.value.strip()
        if not name:
            error_text.value = "Please enter a folder name."
            error_text.visible = True
            error_text.update()
            return
        page.pop_dialog()
        on_create(name)

    name_field.on_submit = do_create

    dlg = ft.AlertDialog(
        modal=True,
        title=ft.Text("Create Folder", size=16, weight=ft.FontWeight.W_600, color=config.TEXT_COLOR),
        content=ft.Column(
            tight=True,
            spacing=8,
            controls=[
                name_field,
                ft.Row([
                    ft.Icon(ft.Icons.FOLDER_OPEN, size=14, color=config.TEXT_SECONDARY_COLOR),
                    ft.Text(f"Inside: {parent_name}", size=12, color=config.TEXT_SECONDARY_COLOR),
                ], spacing=4),
                error_text,
            ],
        ),
        actions=[
            _dialog_btn("Cancel", lambda _: page.pop_dialog()),
            _dialog_btn("Create", do_create, primary=True),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
        shape=ft.RoundedRectangleBorder(radius=8),
    )
    page.show_dialog(dlg)


def show_rename_dialog(page: ft.Page, item: DriveItem, on_rename) -> None:
    name_field = ft.TextField(
        value=item.name,
        autofocus=True,
        border_color=config.BORDER_COLOR,
        focused_border_color=config.ACCENT_COLOR,
        text_size=14,
        selection_color=config.ACCENT_LIGHT_COLOR,
    )
    error_text = ft.Text("", color=config.DANGER_COLOR, size=12, visible=False)

    def do_rename(e):
        name = name_field.value.strip()
        if not name:
            error_text.value = "Name cannot be empty."
            error_text.visible = True
            error_text.update()
            return
        if name == item.name:
            page.pop_dialog()
            return
        page.pop_dialog()
        on_rename(name)

    name_field.on_submit = do_rename

    dlg = ft.AlertDialog(
        modal=True,
        title=ft.Text("Rename", size=16, weight=ft.FontWeight.W_600, color=config.TEXT_COLOR),
        content=ft.Column(
            tight=True,
            spacing=8,
            controls=[name_field, error_text],
        ),
        actions=[
            _dialog_btn("Cancel", lambda _: page.pop_dialog()),
            _dialog_btn("Rename", do_rename, primary=True),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
        shape=ft.RoundedRectangleBorder(radius=8),
    )
    page.show_dialog(dlg)


def show_trash_dialog(page: ft.Page, item, on_confirm, label: str | None = None) -> None:
    msg = label or (f'"{item.name}" will be moved to Google Drive Trash.' if item else "")
    dlg = ft.AlertDialog(
        modal=True,
        title=ft.Text("Move to Trash?", size=16, weight=ft.FontWeight.W_600, color=config.TEXT_COLOR),
        content=ft.Column(
            tight=True,
            controls=[
                ft.Text(msg, size=14, color=config.TEXT_SECONDARY_COLOR),
            ],
        ),
        actions=[
            _dialog_btn("Cancel", lambda _: page.pop_dialog()),
            _dialog_btn("Move to Trash", lambda _: (page.pop_dialog(), on_confirm()), danger=True),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
        shape=ft.RoundedRectangleBorder(radius=8),
    )
    page.show_dialog(dlg)


def show_move_dialog(page: ft.Page, item: DriveItem, folder_options: list[DriveItem], on_move) -> None:
    selected_folder_id: list[str] = []
    items_col = ft.Column(spacing=2, scroll=ft.ScrollMode.AUTO, height=240)

    def select_folder(folder_id: str, folder_name: str) -> None:
        selected_folder_id.clear()
        selected_folder_id.append(folder_id)
        for row in items_col.controls:
            if hasattr(row, "data"):
                row.bgcolor = config.SELECTED_BG_COLOR if row.data == folder_id else "transparent"
        items_col.update()

    for folder in folder_options:
        if folder.id == item.id:
            continue
        row = ft.Container(
            data=folder.id,
            padding=ft.Padding.symmetric(horizontal=12, vertical=8),
            border_radius=6,
            bgcolor="transparent",
            on_click=lambda e, fid=folder.id, fn=folder.name: select_folder(fid, fn),
            content=ft.Row([
                ft.Icon(ft.Icons.FOLDER, color="#F9A825", size=16),
                ft.Text(folder.name, size=13, color=config.TEXT_COLOR),
            ], spacing=8),
        )
        items_col.controls.append(row)

    def do_move(e):
        if not selected_folder_id:
            return
        page.pop_dialog()
        on_move(selected_folder_id[0])

    dlg = ft.AlertDialog(
        modal=True,
        title=ft.Text(f'Move "{item.name}"', size=16, weight=ft.FontWeight.W_600, color=config.TEXT_COLOR),
        content=ft.Column(
            tight=True,
            spacing=8,
            controls=[
                ft.Text("Select destination folder:", size=13, color=config.TEXT_SECONDARY_COLOR),
                ft.Container(
                    content=items_col,
                    border=ft.Border.all(1, config.BORDER_COLOR),
                    border_radius=6,
                    height=240,
                ),
            ],
        ),
        actions=[
            _dialog_btn("Cancel", lambda _: page.pop_dialog()),
            _dialog_btn("Move", do_move, primary=True),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
        shape=ft.RoundedRectangleBorder(radius=8),
    )
    page.show_dialog(dlg)


def show_add_product_dialog(page: ft.Page, on_create_new, on_use_existing) -> None:
    dlg = ft.AlertDialog(
        modal=True,
        title=ft.Text("Add Project", size=16, weight=ft.FontWeight.W_600, color=config.TEXT_COLOR),
        content=ft.Column(
            tight=True,
            spacing=8,
            width=320,
            controls=[
                ft.Text("How would you like to add a product?", size=13, color=config.TEXT_SECONDARY_COLOR),
                ft.Container(height=4),
                ft.Container(
                    padding=ft.Padding.all(14),
                    border=ft.Border.all(1, config.BORDER_COLOR),
                    border_radius=8,
                    on_click=lambda _: (page.pop_dialog(), on_create_new()),
                    ink=True,
                    content=ft.Row([
                        ft.Icon(ft.Icons.CREATE_NEW_FOLDER, color=config.ACCENT_COLOR, size=20),
                        ft.Column([
                            ft.Text("Create New Project Folder", size=13, weight=ft.FontWeight.W_500, color=config.TEXT_COLOR),
                            ft.Text("Creates a new folder in Google Drive", size=11, color=config.TEXT_SECONDARY_COLOR),
                        ], spacing=2),
                    ], spacing=12),
                ),
                ft.Container(
                    padding=ft.Padding.all(14),
                    border=ft.Border.all(1, config.BORDER_COLOR),
                    border_radius=8,
                    on_click=lambda _: (page.pop_dialog(), on_use_existing()),
                    ink=True,
                    content=ft.Row([
                        ft.Icon(ft.Icons.FOLDER_OPEN, color=config.ACCENT_COLOR, size=20),
                        ft.Column([
                            ft.Text("Use Existing Drive Folder", size=13, weight=ft.FontWeight.W_500, color=config.TEXT_COLOR),
                            ft.Text("Select a folder already in your Drive", size=11, color=config.TEXT_SECONDARY_COLOR),
                        ], spacing=2),
                    ], spacing=12),
                ),
            ],
        ),
        actions=[
            _dialog_btn("Cancel", lambda _: page.pop_dialog()),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
        shape=ft.RoundedRectangleBorder(radius=8),
    )
    page.show_dialog(dlg)


def show_create_product_dialog(page: ft.Page, on_create) -> None:
    name_field = ft.TextField(
        label="Product name",
        hint_text="e.g. Kozmo",
        autofocus=True,
        border_color=config.BORDER_COLOR,
        focused_border_color=config.ACCENT_COLOR,
        text_size=14,
    )
    error_text = ft.Text("", color=config.DANGER_COLOR, size=12, visible=False)

    def do_create(e):
        name = name_field.value.strip()
        if not name:
            error_text.value = "Please enter a product name."
            error_text.visible = True
            error_text.update()
            return
        page.pop_dialog()
        on_create(name)

    name_field.on_submit = do_create

    dlg = ft.AlertDialog(
        modal=True,
        title=ft.Text("Create New Project Folder", size=16, weight=ft.FontWeight.W_600, color=config.TEXT_COLOR),
        content=ft.Column(
            tight=True,
            spacing=8,
            controls=[
                name_field,
                ft.Row([
                    ft.Icon(ft.Icons.CLOUD, size=14, color=config.TEXT_SECONDARY_COLOR),
                    ft.Text("Location: My Drive (root)", size=12, color=config.TEXT_SECONDARY_COLOR),
                ], spacing=4),
                error_text,
            ],
        ),
        actions=[
            _dialog_btn("Cancel", lambda _: page.pop_dialog()),
            _dialog_btn("Create", do_create, primary=True),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
        shape=ft.RoundedRectangleBorder(radius=8),
    )
    page.show_dialog(dlg)


def show_select_product_dialog(page: ft.Page, folders: list[DriveItem], existing_ids: set[str], on_select) -> None:
    selected_id: list[str] = []
    items_col = ft.Column(spacing=2, scroll=ft.ScrollMode.AUTO, height=280)
    search_field = ft.TextField(
        hint_text="Search folders...",
        border_color=config.BORDER_COLOR,
        focused_border_color=config.ACCENT_COLOR,
        text_size=13,
        prefix_icon=ft.Icons.SEARCH,
        height=40,
    )

    all_folders = [f for f in folders if f.id not in existing_ids]

    def render_folders(filter_text: str = "") -> None:
        items_col.controls.clear()
        filtered = [f for f in all_folders if filter_text.lower() in f.name.lower()] if filter_text else all_folders
        for folder in filtered:
            is_sel = folder.id in selected_id
            row = ft.Container(
                data=folder.id,
                padding=ft.Padding.symmetric(horizontal=12, vertical=8),
                border_radius=6,
                bgcolor=config.SELECTED_BG_COLOR if is_sel else "transparent",
                on_click=lambda e, fid=folder.id: select_folder(fid),
                content=ft.Row([
                    ft.Icon(ft.Icons.FOLDER, color="#F9A825", size=16),
                    ft.Text(folder.name, size=13, color=config.TEXT_COLOR),
                ], spacing=8),
            )
            items_col.controls.append(row)
        try:
            items_col.update()
        except Exception:
            pass

    def select_folder(folder_id: str) -> None:
        selected_id.clear()
        selected_id.append(folder_id)
        render_folders(search_field.value or "")

    def on_search(e):
        render_folders(e.control.value or "")

    search_field.on_change = on_search
    render_folders()

    def do_select(e):
        if not selected_id:
            return
        folder = next((f for f in folders if f.id == selected_id[0]), None)
        if folder:
            page.pop_dialog()
            on_select(folder)

    dlg = ft.AlertDialog(
        modal=True,
        title=ft.Text("Select Product Folder", size=16, weight=ft.FontWeight.W_600, color=config.TEXT_COLOR),
        content=ft.Column(
            tight=True,
            spacing=8,
            width=360,
            controls=[
                search_field,
                ft.Container(
                    content=items_col,
                    border=ft.Border.all(1, config.BORDER_COLOR),
                    border_radius=6,
                    height=280,
                ),
            ],
        ),
        actions=[
            _dialog_btn("Cancel", lambda _: page.pop_dialog()),
            _dialog_btn("Select", do_select, primary=True),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
        shape=ft.RoundedRectangleBorder(radius=8),
    )
    page.show_dialog(dlg)
