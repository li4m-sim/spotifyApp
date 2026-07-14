from typing import List, Optional
import requests
from bandsintown.models import Concert
from config import BANDSINTOWN_APP_ID
from ui.menus import COUNTRIES

BASE_URL = "https://rest.bandsintown.com"


def get_artist_events(
    artist_name: str,
    country_codes: Optional[List[str]] = None,
    debug: bool = False,
) -> List[Concert]:
    """
    Fetch upcoming events for an artist from the Bandsintown API.

    Bandsintown does not support server-side country filtering, so we fetch
    all upcoming events and filter locally by country code.

    Args:
        artist_name: Name of the artist
        country_codes: Optional list of ISO 3166-1 alpha-2 country codes to filter by
        debug: If True, print API errors and filter stats to the terminal

    Returns:
        List of Concert objects
    """
    # Import here to avoid circular import at module load time
    from ui import display

    try:
        resp = requests.get(
            f"{BASE_URL}/artists/{requests.utils.quote(artist_name)}/events",
            params={"app_id": BANDSINTOWN_APP_ID},
            timeout=10,
        )

        if not resp.ok:
            if debug:
                display.print_api_error(
                    artist_name=artist_name,
                    status_code=resp.status_code,
                    detail=resp.reason or "Unknown error",
                    app_id=BANDSINTOWN_APP_ID,
                )
            return []

        data = resp.json()

        # Bandsintown returns an error dict or a string "Not Found" on failure
        if not isinstance(data, list):
            if debug:
                display.print_api_error(
                    artist_name=artist_name,
                    status_code=resp.status_code,
                    detail=f"Unexpected response format: {str(data)[:120]}",
                    app_id=BANDSINTOWN_APP_ID,
                )
            return []

        all_concerts = [Concert.from_bandsintown(event, artist_name) for event in data]

        # Filter by country codes if provided
        if country_codes:
            allowed_names = {
                _country_code_to_name(code).lower()
                for code in country_codes
            }
            filtered = [
                c for c in all_concerts
                if c.country.lower() in allowed_names
            ]
        else:
            filtered = all_concerts

        if debug:
            country_names = [_country_code_to_name(c) for c in (country_codes or [])]
            display.print_debug_info(
                artist_name=artist_name,
                total_events=len(all_concerts),
                filtered_events=len(filtered),
                country_names=country_names,
            )

        return filtered

    except requests.exceptions.ConnectionError:
        if debug:
            from ui import display
            display.print_api_error(
                artist_name=artist_name,
                status_code=0,
                detail="Connection error — check your internet connection.",
                app_id=BANDSINTOWN_APP_ID,
            )
        return []
    except requests.exceptions.Timeout:
        if debug:
            from ui import display
            display.print_api_error(
                artist_name=artist_name,
                status_code=0,
                detail="Request timed out after 10 seconds.",
                app_id=BANDSINTOWN_APP_ID,
            )
        return []
    except requests.exceptions.RequestException as e:
        if debug:
            from ui import display
            display.print_api_error(
                artist_name=artist_name,
                status_code=0,
                detail=str(e),
                app_id=BANDSINTOWN_APP_ID,
            )
        return []


def search_concerts(
    artist_name: str,
    country_codes: List[str],
    city: Optional[str] = None,
    radius_km: Optional[int] = None,
    debug: bool = False,
) -> List[Concert]:
    """
    Search for concerts for an artist, filtered by countries and optionally city.

    Args:
        artist_name: Artist name to search
        country_codes: ISO country codes to include
        city: Optional city name to filter by (substring match)
        radius_km: Reserved for future use
        debug: If True, surface API errors and filter stats

    Returns:
        Filtered, sorted list of Concert objects
    """
    concerts = get_artist_events(artist_name, country_codes=country_codes, debug=debug)

    # Optional city filter (case-insensitive substring match)
    if city:
        city_lower = city.lower()
        concerts = [c for c in concerts if city_lower in c.city.lower()]

    concerts.sort(key=lambda c: c.date)
    return concerts


def _country_code_to_name(code: str) -> str:
    return COUNTRIES.get(code.upper(), code)
