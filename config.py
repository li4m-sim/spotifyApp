import os
from dotenv import load_dotenv

load_dotenv()

# Spotify
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", "http://localhost:8888/callback")
SPOTIFY_CACHE_PATH = os.path.join(os.path.expanduser("~"), ".spotifyapp_cache")
#SPOTIFY_CACHE_PATH = os.path.expanduser("~/.cache/spotifyapp")

SPOTIFY_SCOPES = [
    "user-top-read",
    "user-follow-read",
]

# Bandsintown — no registration required, just pick a name for your app
BANDSINTOWN_APP_ID = os.getenv("BANDSINTOWN_APP_ID", "spotifyconcertfinder")

# App defaults
DEFAULT_TOP_ARTISTS_LIMIT = 20
DEFAULT_FOLLOWED_ARTISTS_LIMIT = 50

# Developer mode password — set this in your .env file
DEV_PASSWORD = os.getenv("DEV_PASSWORD", "")

# Runtime flag — set to True at startup when user selects Developer mode.
# Modules should import this and check it at call time, not at import time.
DEBUG_MODE: bool = False
