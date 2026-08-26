import flet as ft
from flet.auth.providers import GoogleOAuthProvider
import httpx
import json
import os
import time

from app import config
from app.state import AppState
from app.models.product import ProductReference
from app.views.login_view import build_login_view
from app.views.workspace_view import WorkspaceView

# Server-side storage file for product preferences
_STORAGE_FILE = os.path.join(os.path.dirname(__file__), "..", "user_products.json")

SESSION_KEY = "pt_session_v1"
SESSION_TIMEOUT = 8 * 3600  # 8 hours


def _read_storage() -> dict:
    try:
        with open(_STORAGE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _write_storage(data: dict) -> None:
    try:
        with open(_STORAGE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def _load_products(user_id: str) -> list[ProductReference]:
    data = _read_storage()
    products = data.get(user_id, [])
    return [ProductReference(**p) for p in products]


def _save_products(user_id: str | None, products: list[ProductReference]) -> None:
    if not user_id:
        return
    data = _read_storage()
    data[user_id] = [{"folder_id": p.folder_id, "name": p.name} for p in products]
    _write_storage(data)


async def _fetch_user_info(access_token: str) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        resp.raise_for_status()
        return resp.json()


def main(page: ft.Page) -> None:
    page.title = "Product Tree"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = config.BG_COLOR
    page.padding = 0
    page.spacing = 0

    state = AppState()

    print(f"[AUTH] redirect_url = {config.GOOGLE_REDIRECT_URL}")
    print(f"[AUTH] client_id    = {config.GOOGLE_CLIENT_ID}")
    provider = GoogleOAuthProvider(
        client_id=config.GOOGLE_CLIENT_ID,
        client_secret=config.GOOGLE_CLIENT_SECRET,
        redirect_url=config.GOOGLE_REDIRECT_URL,
    )

    workspace: list[WorkspaceView] = []

    def _show_login(error: str | None = None) -> None:
        page.controls.clear()
        page.add(build_login_view(on_login_click=_on_login_click))
        if error:
            page.show_dialog(ft.SnackBar(
                content=ft.Text(error, color="white"),
                bgcolor=config.DANGER_COLOR,
                duration=5000,
                open=True,
            ))
        page.update()

    def _show_workspace() -> None:
        ws = WorkspaceView(page=page, state=state, save_products=_save_products, on_session_expired=_on_session_expired)
        workspace.clear()
        workspace.append(ws)
        page.controls.clear()
        page.add(ws.build())
        page.update()

    async def _save_session() -> None:
        try:
            data = json.dumps({
                "user_id": state.user_id,
                "user_name": state.user_name,
                "user_email": state.user_email,
                "user_avatar": state.user_avatar,
                "access_token": state.access_token,
                "expiry": time.time() + SESSION_TIMEOUT,
            })
            await page.client_storage.set_async(SESSION_KEY, data)
        except Exception:
            pass

    async def _clear_session() -> None:
        try:
            await page.client_storage.remove_async(SESSION_KEY)
        except Exception:
            pass

    async def _restore_session() -> bool:
        try:
            raw = await page.client_storage.get_async(SESSION_KEY)
            if not raw:
                return False
            data = json.loads(raw)
            if time.time() > data.get("expiry", 0):
                await _clear_session()
                return False
            state.user_id = data.get("user_id")
            state.user_name = data.get("user_name")
            state.user_email = data.get("user_email")
            state.user_avatar = data.get("user_avatar")
            state.access_token = data.get("access_token")
            state.authenticated = True
            if state.user_id:
                state.products = _load_products(state.user_id)
            return True
        except Exception:
            return False

    async def _init() -> None:
        restored = await _restore_session()
        if restored:
            _show_workspace()
        else:
            _show_login()

    async def _on_login(e: ft.LoginEvent) -> None:
        if e.error:
            _show_login(error=f"Login failed: {e.error}")
            return

        try:
            token = await page.auth.get_token()
            access_token = token.access_token

            user = page.auth.user
            if user and user.id:
                state.user_id = user.id
                state.user_name = user.get("name") or user.get("given_name", "")
                state.user_email = user.get("email", "")
                state.user_avatar = user.get("picture")
            else:
                user_info = await _fetch_user_info(access_token)
                state.user_id = user_info.get("id") or user_info.get("sub", "")
                state.user_name = user_info.get("name", "")
                state.user_email = user_info.get("email", "")
                state.user_avatar = user_info.get("picture")

            state.access_token = access_token
            state.authenticated = True

            if state.user_id:
                state.products = _load_products(state.user_id)

            await _save_session()
            _show_workspace()

        except Exception as ex:
            import traceback
            traceback.print_exc()
            _show_login(error=f"Login error: {type(ex).__name__}: {ex}")

    def _on_session_expired() -> None:
        page.run_task(_do_logout)

    async def _do_logout() -> None:
        await _clear_session()
        state.authenticated = False
        state.access_token = None
        state.user_id = None
        state.user_name = None
        state.user_email = None
        state.user_avatar = None
        state.products = []
        state.clear_workspace()
        workspace.clear()
        _show_login(error="Session expired. Please log in again.")

    def _on_logout(e) -> None:
        page.run_task(_do_logout)

    async def _on_login_click(e) -> None:
        await page.login(provider, scope=config.DRIVE_SCOPES)

    page.on_login = _on_login
    page.on_logout = _on_logout

    # Check for existing session before showing login
    page.run_task(_init)


if __name__ == "__main__":
    ft.run(
        main,
        host="0.0.0.0",
        port=config.PORT,
        view=ft.AppView.WEB_BROWSER,
    )
