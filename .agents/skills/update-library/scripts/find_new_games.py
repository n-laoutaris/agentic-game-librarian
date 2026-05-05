"""DEPRECATED: This script is no longer used.

The update-library skill now uses Playnite's multi-store export instead of a multi-phase
fetch/diff/enrich pipeline. Diffing is no longer necessary since Playnite provides
the complete library in a single export.

See normalize_playnite_export.py for the current implementation.
"""

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
DB_DIR = BASE_DIR / "database"
RAW_STEAM_PATH = DB_DIR / "raw_steam.json"
LIBRARY_PATH = DB_DIR / "library.json"
NEEDS_METADATA_PATH = DB_DIR / "needs_metadata.json"


def load_raw_steam():
    """Load the raw Steam games list."""
    if not RAW_STEAM_PATH.exists():
        print(f"Error: {RAW_STEAM_PATH} not found. Run fetch_steam_owned_games.py first.")
        raise SystemExit(1)
    
    with RAW_STEAM_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_master_library():
    """Load the master library, or return empty list if it doesn't exist."""
    if not LIBRARY_PATH.exists():
        print(f"Master library not found at {LIBRARY_PATH}. Treating as empty.")
        return []
    
    try:
        with LIBRARY_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
            if not data:
                print("Master library is empty.")
                return []
            return data
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error reading master library: {e}. Treating as empty.")
        return []


def find_new_games(raw_games, master_library):
    """Find games in raw_games that don't exist in master_library (by source_id)."""
    # Extract all source_ids from master library
    library_source_ids = set()
    
    # Handle different possible master library structures
    if isinstance(master_library, list):
        for item in master_library:
            if isinstance(item, dict) and "source_id" in item:
                library_source_ids.add(item["source_id"])
    
    new_games = []
    for game in raw_games:
        if game.get("source_id") not in library_source_ids:
            new_games.append(game)
    
    return new_games


def save_needs_metadata(new_games):
    """Save the list of games needing metadata."""
    with NEEDS_METADATA_PATH.open("w", encoding="utf-8") as f:
        json.dump(new_games, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    raw_games = load_raw_steam()
    print(f"Loaded {len(raw_games)} raw games from Steam.")
    
    master_library = load_master_library()
    print(f"Loaded {len(master_library)} games from master library.")
    
    new_games = find_new_games(raw_games, master_library)
    print(f"Found {len(new_games)} new games requiring metadata.")
    
    save_needs_metadata(new_games)
    print(f"Saved needs_metadata.json queue to {NEEDS_METADATA_PATH}")
