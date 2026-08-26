from dataclasses import dataclass, field

FOLDER_MIME = "application/vnd.google-apps.folder"


@dataclass
class DriveItem:
    id: str
    name: str
    mime_type: str
    parents: list[str]
    modified_time: str | None = None
    web_view_link: str | None = None
    is_folder: bool = False
    capabilities: dict = field(default_factory=dict)
    children_loaded: bool = False

    @property
    def can_edit(self) -> bool:
        return self.capabilities.get("canEdit", True)

    @property
    def can_move_item_within_drive(self) -> bool:
        return self.capabilities.get("canMoveItemWithinDrive", True)

    @property
    def can_rename(self) -> bool:
        return self.capabilities.get("canRename", True)

    @property
    def can_trash(self) -> bool:
        return self.capabilities.get("canTrash", True)

    def mime_label(self) -> str:
        labels = {
            "application/vnd.google-apps.folder": "Folder",
            "application/vnd.google-apps.document": "Google Doc",
            "application/vnd.google-apps.spreadsheet": "Google Sheet",
            "application/vnd.google-apps.presentation": "Google Slides",
            "application/vnd.google-apps.form": "Google Form",
            "application/pdf": "PDF",
            "image/png": "Image",
            "image/jpeg": "Image",
            "text/plain": "Text File",
        }
        return labels.get(self.mime_type, "File")
