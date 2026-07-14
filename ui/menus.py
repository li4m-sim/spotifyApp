from typing import List, Optional, Tuple, TYPE_CHECKING
import questionary
from questionary import Style
from spotify.client import TIME_RANGE_LABELS

if TYPE_CHECKING:
    import spotipy
    from spotify.models import Artist

# Custom questionary style to match Rich's color scheme
STYLE = Style([
    ("qmark", "fg:#00ff87 bold"),
    ("question", "bold"),
    ("answer", "fg:#00bfff bold"),
    ("pointer", "fg:#00ff87 bold"),
    ("highlighted", "fg:#00ff87 bold"),
    ("selected", "fg:#00bfff"),
    ("separator", "fg:#6c6c6c"),
    ("instruction", "fg:#6c6c6c"),
])

# Countries grouped by continent
CONTINENTS = {
    "Europe": {
        "AL": "Albania",
        "AD": "Andorra",
        "AT": "Austria",
        "BY": "Belarus",
        "BE": "Belgium",
        "BA": "Bosnia and Herzegovina",
        "BG": "Bulgaria",
        "HR": "Croatia",
        "CY": "Cyprus",
        "CZ": "Czech Republic",
        "DK": "Denmark",
        "EE": "Estonia",
        "FI": "Finland",
        "FR": "France",
        "DE": "Germany",
        "GR": "Greece",
        "HU": "Hungary",
        "IS": "Iceland",
        "IE": "Ireland",
        "IT": "Italy",
        "XK": "Kosovo",
        "LV": "Latvia",
        "LI": "Liechtenstein",
        "LT": "Lithuania",
        "LU": "Luxembourg",
        "MT": "Malta",
        "MD": "Moldova",
        "MC": "Monaco",
        "ME": "Montenegro",
        "NL": "Netherlands",
        "MK": "North Macedonia",
        "NO": "Norway",
        "PL": "Poland",
        "PT": "Portugal",
        "RO": "Romania",
        "RU": "Russia",
        "SM": "San Marino",
        "RS": "Serbia",
        "SK": "Slovakia",
        "SI": "Slovenia",
        "ES": "Spain",
        "SE": "Sweden",
        "CH": "Switzerland",
        "UA": "Ukraine",
        "GB": "United Kingdom",
    },
    "North America": {
        "CA": "Canada",
        "CR": "Costa Rica",
        "CU": "Cuba",
        "DO": "Dominican Republic",
        "GT": "Guatemala",
        "HN": "Honduras",
        "JM": "Jamaica",
        "MX": "Mexico",
        "PA": "Panama",
        "PR": "Puerto Rico",
        "TT": "Trinidad and Tobago",
        "US": "United States",
    },
    "South America": {
        "AR": "Argentina",
        "BO": "Bolivia",
        "BR": "Brazil",
        "CL": "Chile",
        "CO": "Colombia",
        "EC": "Ecuador",
        "PY": "Paraguay",
        "PE": "Peru",
        "UY": "Uruguay",
        "VE": "Venezuela",
    },
    "Asia": {
        "CN": "China",
        "HK": "Hong Kong",
        "IN": "India",
        "ID": "Indonesia",
        "JP": "Japan",
        "KZ": "Kazakhstan",
        "MY": "Malaysia",
        "MN": "Mongolia",
        "PH": "Philippines",
        "SG": "Singapore",
        "KR": "South Korea",
        "TW": "Taiwan",
        "TH": "Thailand",
        "VN": "Vietnam",
    },
    "Middle East": {
        "BH": "Bahrain",
        "IL": "Israel",
        "JO": "Jordan",
        "KW": "Kuwait",
        "LB": "Lebanon",
        "OM": "Oman",
        "QA": "Qatar",
        "SA": "Saudi Arabia",
        "TR": "Turkey",
        "AE": "United Arab Emirates",
    },
    "Oceania": {
        "AU": "Australia",
        "FJ": "Fiji",
        "NZ": "New Zealand",
    },
    "Africa": {
        "DZ": "Algeria",
        "EG": "Egypt",
        "ET": "Ethiopia",
        "GH": "Ghana",
        "KE": "Kenya",
        "MA": "Morocco",
        "NG": "Nigeria",
        "SN": "Senegal",
        "ZA": "South Africa",
        "TN": "Tunisia",
        "UG": "Uganda",
    },
}

# Flat dict of all countries for lookup elsewhere in the app
COUNTRIES = {
    code: name
    for region in CONTINENTS.values()
    for code, name in region.items()
}

# Reverse lookup: lowercase name -> code
_NAME_TO_CODE = {name.lower(): code for code, name in COUNTRIES.items()}


# ---------------------------------------------------------------------------
# Artist source selection
# ---------------------------------------------------------------------------

def ask_artist_sources() -> List[str]:
    """
    Multi-select: which sources should be included?
    Returns a list of selected source keys: 'top', 'followed', 'searched'
    """
    choices = [
        questionary.Choice("My top played artists", value="top"),
        questionary.Choice("My followed artists", value="followed"),
        questionary.Choice("Search for specific artists", value="searched"),
    ]
    selected = questionary.checkbox(
        "Which artist sources do you want to include? (space to select, enter to confirm)",
        choices=choices,
        style=STYLE,
    ).ask()
    return selected or []


def ask_time_range() -> str:
    """Ask which Spotify time range to use for top artists."""
    choices = [
        questionary.Choice(label, value=key)
        for key, label in TIME_RANGE_LABELS.items()
    ]
    return questionary.select(
        "Which time period for your top artists?",
        choices=choices,
        style=STYLE,
    ).ask()


def ask_specific_artists(sp: "spotipy.Spotify") -> List["Artist"]:
    """
    Autocomplete artist search loop using the Spotify search API.
    User types a query, picks from results, optionally adds more.
    Returns a list of Artist objects with source='searched'.
    """
    from spotify.client import search_artists

    selected: List["Artist"] = []

    while True:
        selected_names = [a.name for a in selected]
        if selected_names:
            prompt = f"Search for another artist (selected: {', '.join(selected_names)}):"
        else:
            prompt = "Search for an artist:"

        query = questionary.text(
            prompt,
            style=STYLE,
        ).ask()

        if not query or not query.strip():
            break

        results = search_artists(sp, query.strip())
        if not results:
            print("  No results found, try again.")
            continue

        # Let user pick from search results
        already_ids = {a.id for a in selected}
        choices = [
            questionary.Choice(
                f"{a.name}" + (f" — {', '.join(a.genres[:2])}" if a.genres else ""),
                value=a,
            )
            for a in results
            if a.id not in already_ids
        ]
        choices.append(questionary.Choice("[ Cancel / skip this search ]", value=None))

        pick = questionary.select(
            "Select an artist:",
            choices=choices,
            style=STYLE,
        ).ask()

        if pick is not None:
            selected.append(pick)

        add_more = questionary.confirm(
            "Search for another artist?",
            default=True,
            style=STYLE,
        ).ask()

        if not add_more:
            break

    return selected


# ---------------------------------------------------------------------------
# Artist review / editing
# ---------------------------------------------------------------------------

def ask_review_artists(artists: List["Artist"]) -> str:
    """
    Show a summary of the current artist list and ask what to do next.
    Returns: 'continue', 'remove', 'add', 'restart'
    """
    count = len(artists)
    return questionary.select(
        f"Your artist list has {count} artist(s). What would you like to do?",
        choices=[
            questionary.Choice("Continue with these artists", value="continue"),
            questionary.Choice("Remove specific artists", value="remove"),
            questionary.Choice("Add more artists (search)", value="add"),
            questionary.Choice("Start over", value="restart"),
        ],
        style=STYLE,
    ).ask()


def ask_remove_artists(artists: List["Artist"]) -> List["Artist"]:
    """
    Let the user remove artists from the current list.
    - If <=20 artists: straight to checkbox.
    - If >20: offer checkbox or search-to-remove.
    Returns the updated list of artists to KEEP.
    """
    if len(artists) > 20:
        method = questionary.select(
            "How would you like to remove artists?",
            choices=[
                questionary.Choice("Uncheck from full list", value="checkbox"),
                questionary.Choice("Search by name", value="search"),
            ],
            style=STYLE,
        ).ask()
    else:
        method = "checkbox"

    if method == "checkbox":
        choices = [
            questionary.Choice(
                f"{a.name}  [{a.source}]",
                value=a,
                checked=True,  # all checked (kept) by default
            )
            for a in artists
        ]
        keep = questionary.checkbox(
            "Uncheck artists to remove them (enter to confirm):",
            choices=choices,
            style=STYLE,
        ).ask()
        return keep if keep is not None else artists

    else:
        # Search-to-remove loop
        remaining = list(artists)
        while True:
            query = questionary.text(
                "Type artist name to remove (leave blank to finish):",
                style=STYLE,
            ).ask()

            if not query or not query.strip():
                break

            query_lower = query.strip().lower()
            matches = [a for a in remaining if query_lower in a.name.lower()]

            if not matches:
                print("  No matching artists found.")
                continue

            choices = [
                questionary.Choice(f"{a.name}  [{a.source}]", value=a)
                for a in matches
            ]
            choices.append(questionary.Choice("[ Cancel ]", value=None))

            to_remove = questionary.select(
                "Select artist to remove:",
                choices=choices,
                style=STYLE,
            ).ask()

            if to_remove is not None:
                remaining = [a for a in remaining if a.id != to_remove.id]
                print(f"  Removed: {to_remove.name}")

            cont = questionary.confirm(
                "Remove another artist?",
                default=True,
                style=STYLE,
            ).ask()
            if not cont:
                break

        return remaining


# ---------------------------------------------------------------------------
# Country selection
# ---------------------------------------------------------------------------

def ask_countries() -> List[str]:
    """
    2-step country selection:
    Step 1 — choose a continent, all countries, or pick specific ones.
    Step 2 — if picking specific: autocomplete search loop.
    """
    continent_choices = [
        questionary.Choice(f"All of {continent}", value=f"continent:{continent}")
        for continent in CONTINENTS.keys()
    ]
    continent_choices.append(questionary.Choice("Pick specific countries", value="specific"))
    continent_choices.append(questionary.Choice("Select all countries", value="all"))

    scope = questionary.select(
        "Which countries should we search for concerts in?",
        choices=continent_choices,
        style=STYLE,
    ).ask()

    if scope is None:
        return []

    if scope == "all":
        return list(COUNTRIES.keys())

    if scope.startswith("continent:"):
        continent_name = scope.split(":", 1)[1]
        return list(CONTINENTS[continent_name].keys())

    return _ask_specific_countries()


def _ask_specific_countries() -> List[str]:
    """
    Autocomplete loop — user types to search for a country,
    selects it, then optionally adds more.
    """
    all_options = sorted(
        [f"{name} ({code})" for code, name in COUNTRIES.items()],
        key=lambda x: x.lower(),
    )

    selected_codes = []
    selected_labels = []

    while True:
        if selected_labels:
            prompt = f"Add another country? (selected: {', '.join(selected_labels)})"
        else:
            prompt = "Type to search for a country:"

        answer = questionary.autocomplete(
            prompt,
            choices=all_options,
            style=STYLE,
            validate=lambda val: val in all_options or val == "" or "Type a country name to search",
            ignore_case=True,
        ).ask()

        if not answer:
            break

        if "(" in answer and answer.endswith(")"):
            code = answer.split("(")[-1].rstrip(")")
            name = answer.split(" (")[0]
            if code not in selected_codes:
                selected_codes.append(code)
                selected_labels.append(name)

        add_more = questionary.confirm(
            "Add another country?",
            default=True,
            style=STYLE,
        ).ask()

        if not add_more:
            break

    return selected_codes


# ---------------------------------------------------------------------------
# Radius / city search
# ---------------------------------------------------------------------------

def ask_radius_search() -> Tuple[Optional[str], Optional[int]]:
    """
    Optionally ask for a city + radius to narrow the search.
    Returns (city_name, radius_km) or (None, None) if skipped.
    """
    use_radius = questionary.confirm(
        "Also search within a radius of a specific city?",
        default=False,
        style=STYLE,
    ).ask()

    if not use_radius:
        return None, None

    city = questionary.text(
        "Enter city name:",
        style=STYLE,
    ).ask()

    radius_str = questionary.select(
        "Search radius:",
        choices=[
            questionary.Choice("25 km", value=25),
            questionary.Choice("50 km", value=50),
            questionary.Choice("100 km", value=100),
            questionary.Choice("200 km", value=200),
            questionary.Choice("500 km", value=500),
        ],
        style=STYLE,
    ).ask()

    return city, radius_str


# ---------------------------------------------------------------------------
# Main menu
# ---------------------------------------------------------------------------

def ask_main_menu() -> str:
    """Main menu after viewing results."""
    return questionary.select(
        "What would you like to do?",
        choices=[
            questionary.Choice("Search concerts for current artists", value="search"),
            questionary.Choice("Change artist selection", value="change_artists"),
            questionary.Choice("View my artists", value="artists"),
            questionary.Choice("Exit", value="exit"),
        ],
        style=STYLE,
    ).ask()


def ask_continue() -> bool:
    """Ask if the user wants to continue."""
    return questionary.confirm("Continue?", default=True, style=STYLE).ask()
