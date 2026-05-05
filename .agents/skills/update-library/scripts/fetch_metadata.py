"""DEPRECATED: This script is no longer used.

The update-library skill now uses Playnite's rich metadata export directly.
Metadata enrichment from IGDB is no longer necessary since Playnite already
provides developers, genres, descriptions, tags, release dates, and scores.

See normalize_playnite_export.py for the current implementation.
"""

import json
import os
from pathlib import Path
import requests
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
DB_DIR = BASE_DIR / "database"
ENV_FILE = BASE_DIR / ".env"
NEEDS_METADATA_PATH = DB_DIR / "needs_metadata.json"
LIBRARY_PATH = DB_DIR / "library.json"

TWITCH_TOKEN_URL = "https://id.twitch.tv/oauth2/token"
IGDB_API_URL = "https://api.igdb.com/v4/games"

# Load environment variables
load_dotenv(ENV_FILE)


def load_config():
    """Load API credentials from environment variables."""
    config = {
        "TWITCH_CLIENT_ID": os.getenv("TWITCH_CLIENT_ID"),
        "TWITCH_CLIENT_SECRET": os.getenv("TWITCH_CLIENT_SECRET"),
    }
    return config


def get_twitch_bearer_token(client_id, client_secret):
    """Obtain a Bearer token from Twitch OAuth2."""
    params = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
    }
    
    try:
        response = requests.post(TWITCH_TOKEN_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get("access_token")
    except requests.exceptions.RequestException as e:
        print(f"Error obtaining Twitch Bearer token: {e}")
        raise SystemExit(1)


def load_needs_metadata():
    """Load the queue of games needing metadata."""
    if not NEEDS_METADATA_PATH.exists():
        print(f"Queue file not found at {NEEDS_METADATA_PATH}.")
        return []
    
    try:
        with NEEDS_METADATA_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, IOError):
        return []


def load_master_library():
    """Load the master library, or return empty list if it doesn't exist."""
    if not LIBRARY_PATH.exists():
        return []
    
    try:
        with LIBRARY_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, IOError):
        return []


def fetch_igdb_metadata(game_title, bearer_token, client_id):
    """Fetch metadata for a single game from IGDB."""
    headers = {
        "Client-ID": client_id,
        "Authorization": f"Bearer {bearer_token}",
    }
    
    query_body = f'search "{game_title}"; fields name, summary, genres.name, themes.name, game_modes.name, player_perspectives.name, keywords.name, total_rating, involved_companies.company.name; limit 1;'
    
    try:
        response = requests.post(
            IGDB_API_URL,
            headers=headers,
            data=query_body,
            timeout=30
        )
        response.raise_for_status()
        results = response.json()
        
        if not results:
            return None
        
        return results[0]
    except requests.exceptions.RequestException as e:
        print(f"\n  Error fetching IGDB metadata for '{game_title}': {e}")
        return None


def enrich_game(store_game, igdb_data):
    """Combine store data with IGDB metadata into a single object."""
    enriched = {
        "title": store_game.get("title"),
        "platform": store_game.get("platform"),
        "source_id": store_game.get("source_id"),
        "playtime_hours": store_game.get("playtime_hours"),
    }
    
    if igdb_data:
        enriched["igdb_id"] = igdb_data.get("id")
        enriched["summary"] = igdb_data.get("summary")
        enriched["genres"] = [g.get("name") for g in igdb_data.get("genres", [])]
        enriched["themes"] = [t.get("name") for t in igdb_data.get("themes", [])]
        enriched["game_modes"] = [m.get("name") for m in igdb_data.get("game_modes", [])]
        enriched["player_perspectives"] = [p.get("name") for p in igdb_data.get("player_perspectives", [])]
        enriched["keywords"] = [k.get("name") for k in igdb_data.get("keywords", [])]
        enriched["total_rating"] = igdb_data.get("total_rating")
        enriched["involved_companies"] = [c.get("company", {}).get("name") for c in igdb_data.get("involved_companies", [])]
    
    return enriched


def save_master_library(library):
    """Save the updated master library."""
    with LIBRARY_PATH.open("w", encoding="utf-8") as f:
        json.dump(library, f, indent=2, ensure_ascii=False)


def empty_queue():
    """Empty the needs_metadata.json file."""
    with NEEDS_METADATA_PATH.open("w", encoding="utf-8") as f:
        json.dump([], f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    # Load configuration
    config = load_config()
    client_id = config.get("TWITCH_CLIENT_ID")
    client_secret = config.get("TWITCH_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        print("Error: TWITCH_CLIENT_ID and TWITCH_CLIENT_SECRET must be set in .env file")
        raise SystemExit(1)
    
    # Get Twitch Bearer token
    print("Authenticating with Twitch OAuth2...")
    bearer_token = get_twitch_bearer_token(client_id, client_secret)
    print("✓ Bearer token obtained")
    
    # Load queue and library
    queue = load_needs_metadata()
    if not queue:
        print("Queue is empty. No games to enrich.")
        raise SystemExit(0)
    
    print(f"Loaded {len(queue)} games from queue.")
    
    master_library = load_master_library()
    print(f"Loaded {len(master_library)} games from master library.")
    
    # Process each game in the queue
    print(f"\nFetching metadata for {len(queue)} games...")
    enriched_count = 0
    skipped_count = 0
    
    for i, store_game in enumerate(queue, 1):
        game_title = store_game.get("title", "Unknown")
        print(f"[{i}/{len(queue)}] Processing: {game_title}", end="")
        
        # Fetch IGDB metadata
        igdb_data = fetch_igdb_metadata(game_title, bearer_token, client_id)
        
        # Combine and enrich
        enriched_game = enrich_game(store_game, igdb_data)
        
        # Append to master library
        master_library.append(enriched_game)
        enriched_count += 1
        
        if not igdb_data:
            skipped_count += 1
            print(" (no IGDB match)")
        else:
            print(" ✓")
    
    # Save results
    print(f"\nSaving {enriched_count} enriched games to master library...")
    save_master_library(master_library)
    print(f"✓ Master library updated ({len(master_library)} total games)")
    print(f"  - With IGDB metadata: {enriched_count - skipped_count}")
    print(f"  - Store data only: {skipped_count}")
    
    # Empty the queue
    print("Emptying metadata queue...")
    empty_queue()
    print("✓ Queue emptied")
    
    print("\nMetadata enrichment complete!")
