import secrets
import time
import json
import os
import urllib.parse

import httpx
import flet as ft
import flet.fastapi as flet_fastapi
import uvicorn
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app import config
from app.state import AppState
from app.models.product import ProductReference
from app.views.login_view import build_login_view
from app.views.workspace_view import WorkspaceView

# ── Server-side storage ───────────────────────────────────────────────────────

_STORAGE_FILE = os.path.join(os.path.dirname(__file__), "..", "user_products.json")
SESSION_KEY = "pt_session_v1"
SESSION_TIMEOUT = 8 * 3600  # 8 hours

# In-memory pending auth store: state -> auth payload
# (single-process on Render free tier, so this is safe)
_pending_auth: dict[str, dict] = {}


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
    return [ProductReference(**p) for p in data.get(user_id, [])]


def _save_products(user_id: str | None, products: list[ProductReference]) -> None:
    if not user_id:
        return
    data = _read_storage()
    data[user_id] = [{"folder_id": p.folder_id, "name": p.name} for p in products]
    _write_storage(data)


def _build_oauth_url(state: str) -> str:
    params = {
        "client_id": config.GOOGLE_CLIENT_ID,
        "redirect_uri": config.GOOGLE_REDIRECT_URL,
        "response_type": "code",
        "scope": " ".join(config.DRIVE_SCOPES),
        "state": state,
        "access_type": "online",
        "prompt": "select_account",
    }
    return "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)


# ── Flet app ──────────────────────────────────────────────────────────────────

def main(page: ft.Page) -> None:
    page.title = "Product Tree"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = config.BG_COLOR
    page.padding = 0
    page.spacing = 0

    state = AppState()
    workspace: list[WorkspaceView] = []

    # ── UI helpers ────────────────────────────────────────────────────────────

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
        ws = WorkspaceView(
            page=page,
            state=state,
            save_products=_save_products,
            on_session_expired=_on_session_expired,
        )
        workspace.clear()
        workspace.append(ws)
        page.controls.clear()
        page.add(ws.build())
        page.update()

    # ── Session persistence ───────────────────────────────────────────────────

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

    # ── Init: check route or restore session ─────────────────────────────────

    async def _init() -> None:
        route = page.route or ""

        # OAuth just completed — route is /auth_{state}
        if route.startswith("/auth_"):
            auth_state = route[6:]
            auth_data = _pending_auth.pop(auth_state, None)
            if auth_data and time.time() - auth_data.get("timestamp", 0) < 300:
                state.access_token = auth_data["access_token"]
                state.user_id = auth_data["user_id"]
                state.user_name = auth_data["user_name"]
                state.user_email = auth_data["user_email"]
                state.user_avatar = auth_data["user_avatar"]
                state.authenticated = True
                if state.user_id:
                    state.products = _load_products(state.user_id)
                await _save_session()
                _show_workspace()
                return
            else:
                _show_login(error="Login failed or expired. Please try again.")
                return

        if route == "/auth_error":
            _show_login(error="Google login failed. Please try again.")
            return

        # Try restoring existing session
        restored = await _restore_session()
        if restored:
            _show_workspace()
        else:
            _show_login()

    # ── Login / Logout ────────────────────────────────────────────────────────

    def _on_login_click(e) -> None:
        auth_state = secrets.token_urlsafe(16)
        oauth_url = _build_oauth_url(auth_state)
        page.launch_url(oauth_url, web_popup_window_name="_self")

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

    page.on_logout = lambda e: page.run_task(_do_logout)

    page.run_task(_init)


# ── FastAPI app ───────────────────────────────────────────────────────────────

app = FastAPI()


@app.get("/oauth/callback")
async def oauth_callback(
    code: str = None,
    state: str = None,
    error: str = None,
    **kwargs,
):
    if error or not code or not state:
        return RedirectResponse("/#/auth_error")

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            # Exchange code for access token
            token_resp = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": config.GOOGLE_CLIENT_ID,
                    "client_secret": config.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": config.GOOGLE_REDIRECT_URL,
                    "grant_type": "authorization_code",
                },
            )
            token_resp.raise_for_status()
            token_data = token_resp.json()
            access_token = token_data["access_token"]

            # Fetch user info
            user_resp = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            user_resp.raise_for_status()
            user_info = user_resp.json()

        _pending_auth[state] = {
            "access_token": access_token,
            "user_id": user_info.get("id") or user_info.get("sub", ""),
            "user_name": user_info.get("name", ""),
            "user_email": user_info.get("email", ""),
            "user_avatar": user_info.get("picture"),
            "timestamp": time.time(),
        }

        return RedirectResponse(f"/#/auth_{state}")

    except Exception as ex:
        print(f"[OAuth] Token exchange error: {ex}")
        return RedirectResponse("/#/auth_error")


# Mount Flet under root
app.mount("/", flet_fastapi.app(main))


if __name__ == "__main__":
    print(f"[AUTH] redirect_url = {config.GOOGLE_REDIRECT_URL}")
    uvicorn.run(app, host="0.0.0.0", port=config.PORT)
