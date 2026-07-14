from typing import List, Optional
from datetime import date
import requests
from bandsintown.models import Concert
from config import BANDSINTOWN_APP_ID
from ui.menus import COUNTRIES

BASE_URL = "https://rest.bandsintown.com"


def get_artist_events(
    artist_name: str,
    country_codes: Optional[List[str]] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    debug: bool = False,
) -> List[Concert]:
    """
    Fetch upcoming events for an artist from the Bandsintown API.

    Filters locally by country code and date range.

    Args:
        artist_name: Name of the artist
        country_codes: ISO country codes to filter by. Pass [] or None for all locations.
        date_from: Optional start date filter (inclusive)
        date_to: Optional end date filter (inclusive)
        debug: If True, print API errors and filter stats to the terminal

    Returns:
        List of Concert objects
    """
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

        # Country filter — skip if empty (all locations)
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

        # Date range filter
        if date_from:
            filtered = [c for c in filtered if c.date >= str(date_from)]
        if date_to:
            filtered = [c for c in filtered if c.date <= str(date_to)]

        if debug:
            country_names = (
                [_country_code_to_name(c) for c in country_codes]
                if country_codes
                else ["all locations"]
            )
            display.print_debug_info(
                artist_name=artist_name,
                total_events=len(all_concerts),
                filtered_events=len(filtered),
                country_names=country_names,
            )

        return filtered

    except requests.exceptions.ConnectionError:
        if debug:
            display.print_api_error(
                artist_name=artist_name,
                status_code=0,
                detail="Connection error — check your internet connection.",
                app_id=BANDSINTOWN_APP_ID,
            )
        return []
    except requests.exceptions.Timeout:
        if debug:
            display.print_api_error(
                artist_name=artist_name,
                status_code=0,
                detail="Request timed out after 10 seconds.",
                app_id=BANDSINTOWN_APP_ID,
            )
        return []
    except requests.exceptions.RequestException as e:
        if debug:
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
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    debug: bool = False,
) -> List[Concert]:
    """
    Search for concerts for an artist, filtered by countries, date range, and optionally city.

    Args:
        artist_name: Artist name to search
        country_codes: ISO country codes to include. Empty list = all locations.
        city: Optional city name to filter by (substring match)
        date_from: Optional start date filter (inclusive)
        date_to: Optional end date filter (inclusive)
        debug: If True, surface API errors and filter stats

    Returns:
        Filtered, sorted list of Concert objects
    """
    concerts = get_artist_events(
        artist_name,
        country_codes=country_codes,
        date_from=date_from,
        date_to=date_to,
        debug=debug,
    )

    # Optional city filter (case-insensitive substring match)
    if city:
        city_lower = city.lower()
        concerts = [c for c in concerts if city_lower in c.city.lower()]

    concerts.sort(key=lambda c: c.date)
    return concerts


def _country_code_to_name(code: str) -> str:
    return COUNTRIES.get(code.upper(), code)
