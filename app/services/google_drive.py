import httpx
from app.models.drive_item import DriveItem, FOLDER_MIME

DRIVE_BASE = "https://www.googleapis.com/drive/v3"
ITEM_FIELDS = "id,name,mimeType,parents,modifiedTime,webViewLink,capabilities"
LIST_FIELDS = f"files({ITEM_FIELDS})"

COMMON_PARAMS = {
    "supportsAllDrives": "true",
    "includeItemsFromAllDrives": "true",
}


class DriveAPIError(Exception):
    def __init__(self, status: int, message: str):
        self.status = status
        self.message = message
        super().__init__(f"Drive API {status}: {message}")


class GoogleDriveService:
    def __init__(self, access_token: str):
        self._token = access_token

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/json",
        }

    def _json_headers(self) -> dict:
        return {**self._headers(), "Content-Type": "application/json"}

    @staticmethod
    def _parse_item(data: dict) -> DriveItem:
        mime = data.get("mimeType", "")
        return DriveItem(
            id=data["id"],
            name=data.get("name", "Untitled"),
            mime_type=mime,
            parents=data.get("parents", []),
            modified_time=data.get("modifiedTime"),
            web_view_link=data.get("webViewLink"),
            is_folder=mime == FOLDER_MIME,
            capabilities=data.get("capabilities", {}),
        )

    @staticmethod
    def _raise_for_status(resp: httpx.Response) -> None:
        if resp.is_error:
            try:
                body = resp.json()
                msg = body.get("error", {}).get("message", resp.text)
            except Exception:
                msg = resp.text
            raise DriveAPIError(resp.status_code, msg)

    async def list_children(self, parent_id: str) -> list[DriveItem]:
        query = f"'{parent_id}' in parents and trashed = false"
        params = {
            **COMMON_PARAMS,
            "q": query,
            "fields": LIST_FIELDS,
            "orderBy": "folder,name",
            "pageSize": "200",
        }
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(f"{DRIVE_BASE}/files", headers=self._headers(), params=params)
            self._raise_for_status(resp)
            return [self._parse_item(f) for f in resp.json().get("files", [])]

    async def get_item(self, file_id: str) -> DriveItem:
        params = {**COMMON_PARAMS, "fields": ITEM_FIELDS}
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(f"{DRIVE_BASE}/files/{file_id}", headers=self._headers(), params=params)
            self._raise_for_status(resp)
            return self._parse_item(resp.json())

    async def list_root_folders(self) -> list[DriveItem]:
        query = "'root' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        params = {
            **COMMON_PARAMS,
            "q": query,
            "fields": LIST_FIELDS,
            "orderBy": "name",
            "pageSize": "100",
        }
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(f"{DRIVE_BASE}/files", headers=self._headers(), params=params)
            self._raise_for_status(resp)
            return [self._parse_item(f) for f in resp.json().get("files", [])]

    async def create_folder(self, name: str, parent_id: str) -> DriveItem:
        body = {
            "name": name,
            "mimeType": FOLDER_MIME,
            "parents": [parent_id],
        }
        params = {**COMMON_PARAMS, "fields": ITEM_FIELDS}
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{DRIVE_BASE}/files",
                headers=self._json_headers(),
                json=body,
                params=params,
            )
            self._raise_for_status(resp)
            return self._parse_item(resp.json())

    async def rename_item(self, file_id: str, new_name: str) -> DriveItem:
        params = {**COMMON_PARAMS, "fields": ITEM_FIELDS}
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.patch(
                f"{DRIVE_BASE}/files/{file_id}",
                headers=self._json_headers(),
                json={"name": new_name},
                params=params,
            )
            self._raise_for_status(resp)
            return self._parse_item(resp.json())

    async def move_item(self, file_id: str, new_parent_id: str) -> DriveItem:
        current = await self.get_item(file_id)
        old_parents = ",".join(current.parents) if current.parents else ""
        params = {
            **COMMON_PARAMS,
            "addParents": new_parent_id,
            "removeParents": old_parents,
            "fields": ITEM_FIELDS,
        }
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.patch(
                f"{DRIVE_BASE}/files/{file_id}",
                headers=self._json_headers(),
                json={},
                params=params,
            )
            self._raise_for_status(resp)
            return self._parse_item(resp.json())

    async def trash_item(self, file_id: str) -> DriveItem:
        params = {**COMMON_PARAMS, "fields": ITEM_FIELDS}
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.patch(
                f"{DRIVE_BASE}/files/{file_id}",
                headers=self._json_headers(),
                json={"trashed": True},
                params=params,
            )
            self._raise_for_status(resp)
            return self._parse_item(resp.json())

    async def upload_file(self, name: str, parent_id: str, content: bytes, mime_type: str = "application/octet-stream") -> DriveItem:
        import json as _json
        metadata = _json.dumps({"name": name, "parents": [parent_id]}).encode()
        boundary = b"flet_upload_boundary"
        body = (
            b"--" + boundary + b"\r\n"
            b"Content-Type: application/json; charset=UTF-8\r\n\r\n" +
            metadata + b"\r\n"
            b"--" + boundary + b"\r\n"
            b"Content-Type: " + mime_type.encode() + b"\r\n\r\n" +
            content + b"\r\n"
            b"--" + boundary + b"--"
        )
        headers = {
            **self._headers(),
            "Content-Type": f"multipart/related; boundary={boundary.decode()}",
        }
        params = {**COMMON_PARAMS, "uploadType": "multipart", "fields": ITEM_FIELDS}
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                "https://www.googleapis.com/upload/drive/v3/files",
                headers=headers,
                content=body,
                params=params,
            )
            self._raise_for_status(resp)
            return self._parse_item(resp.json())

    async def get_path_names(self, file_id: str, product_root_id: str) -> list[str]:
        """Returns name segments from product root down to the item (exclusive of root name)."""
        path_parts: list[str] = []
        current_id = file_id
        visited: set[str] = set()

        while current_id and current_id not in visited and current_id != product_root_id:
            visited.add(current_id)
            try:
                item = await self.get_item(current_id)
                path_parts.insert(0, item.name)
                if item.parents:
                    current_id = item.parents[0]
                else:
                    break
            except Exception:
                break

        return path_parts
