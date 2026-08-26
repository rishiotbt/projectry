import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URL = os.getenv("GOOGLE_REDIRECT_URL", "http://localhost:8550/oauth_callback")

DRIVE_SCOPES = [
    "openid",
    "email",
    "profile",
    "https://www.googleapis.com/auth/drive",
]

PORT = int(os.getenv("PORT", "8550"))

# Theme colors
BG_COLOR = "#F5F5F5"
SURFACE_COLOR = "#FFFFFF"
TEXT_COLOR = "#1A1A1A"
TEXT_SECONDARY_COLOR = "#6B6B6B"
BORDER_COLOR = "#E0E0E0"
ACCENT_COLOR = "#0088B0"
ACCENT_LIGHT_COLOR = "#E1F0F5"
DANGER_COLOR = "#D32F2F"
SELECTED_BG_COLOR = "#E1F0F5"
HOVER_BG_COLOR = "#F0F7FA"
SIDEBAR_BG_COLOR = "#FAFAFA"
SKELETON_COLOR = "#E0E0E0"
