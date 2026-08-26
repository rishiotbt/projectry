# Kozmo Product Tree

A visual product workspace over Google Drive, built entirely in Python with Flet.

## What it does

- Sign in with Google and grant Drive access
- Create or select Product folders from your Drive
- Browse your Drive hierarchy as a Tree or Map
- Expand/collapse folders (lazy-loaded)
- Create, rename, move, and trash folders/files
- Drag and drop items to move them (reflects real Drive changes)
- All changes sync to Google Drive — Drive is the source of truth

---

## Setup

### 1. Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select an existing one)
3. Enable the **Google Drive API**
4. Go to **APIs & Services → OAuth consent screen**
   - Choose "External" user type
   - Fill in app name, support email, and developer email
   - Add scope: `https://www.googleapis.com/auth/drive`
   - Add your Google account as a test user
5. Go to **APIs & Services → Credentials → Create Credentials → OAuth Client ID**
   - Application type: **Web application**
   - Authorized redirect URIs: `http://localhost:8550/oauth_callback`
6. Copy your **Client ID** and **Client Secret**

### 2. Environment Variables

```bash
cp .env.example .env
```

Edit `.env`:

```env
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
GOOGLE_REDIRECT_URL=http://localhost:8550/oauth_callback
```

**Never commit `.env` to version control.**

### 3. Python Environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 4. Run

```bash
cd kozmo-product-tree
python -m app.main
```

Or with Flet CLI:

```bash
flet run --web app/main.py
```

The app opens at `http://localhost:8550`.

---

## Project Structure

```
app/
  main.py              Entry point
  config.py            Environment config + theme colors
  state.py             AppState dataclass

  models/
    drive_item.py      DriveItem dataclass
    product.py         ProductReference dataclass

  services/
    google_drive.py    Google Drive API v3 client
    tree_layout.py     Map view layout algorithm

  utils/
    drive_helpers.py   Move validation, formatting helpers

  views/
    login_view.py      Login screen
    workspace_view.py  Main workspace orchestrator
    tree_view.py       Tree view renderer
    map_view.py        Map view renderer

  components/
    header.py          Top header bar
    sidebar.py         Products sidebar
    tree_row.py        Single tree row (draggable + drop target)
    map_node.py        Map view node
    details_panel.py   Selected item details
    dialogs.py         All modal dialogs
    error_banner.py    Inline error display

tests/
  test_drive_models.py
  test_move_validation.py
  test_tree_layout.py
```

---

## Running Tests

```bash
pytest
```

---

## Technology

| Purpose        | Library                  |
|----------------|--------------------------|
| UI             | Flet                     |
| HTTP           | httpx                    |
| Config         | python-dotenv            |
| Auth           | Flet GoogleOAuthProvider |
| Drive API      | Google Drive REST API v3 |

---

## Security Notes

- Client secret lives only in `.env` — never in Python source
- Access tokens are never logged
- Drive is always the source of truth; no separate DB
- Destructive operations (trash) require confirmation
- All Drive API errors are caught and displayed inline
