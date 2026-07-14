import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from config import (
    SPOTIFY_CLIENT_ID,
    SPOTIFY_CLIENT_SECRET,
    SPOTIFY_REDIRECT_URI,
    SPOTIFY_CACHE_PATH,
    SPOTIFY_SCOPES,
)


def create_spotify_client() -> spotipy.Spotify:
    """
    Create and return an authenticated Spotipy client.
    Uses Authorization Code flow with token caching.
    On first run, opens a browser for user login.
    Subsequent runs reuse the cached token automatically.
    """
    auth_manager = SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope=" ".join(SPOTIFY_SCOPES),
        cache_path=SPOTIFY_CACHE_PATH,
        open_browser=True,
        show_dialog=False,
    )

    return spotipy.Spotify(auth_manager=auth_manager)


def get_current_user(sp: spotipy.Spotify) -> dict:
    """Return the current user's profile."""
    return sp.current_user()


def logout() -> bool:
    """
    Delete the cached Spotify token, forcing a fresh browser login on next auth.
    Returns True if a cache file was found and deleted, False if there was nothing to delete.
    """
    if os.path.exists(SPOTIFY_CACHE_PATH):
        os.remove(SPOTIFY_CACHE_PATH)
        return True
    return False
