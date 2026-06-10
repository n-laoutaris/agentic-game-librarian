"""
Extract Taxonomy from Library JSON

Reads database/library.json and extracts all unique categorical values
(genres, tags, features, sources) plus numeric ranges. This taxonomy is used
by the recommendation skill to guide filtering queries.

Output: Clean, agent-readable taxonomy (both printed and optional JSON export)
"""

import json
from pathlib import Path
from collections import defaultdict


BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
DB_DIR = BASE_DIR / "database"
LIBRARY_PATH = DB_DIR / "library.json"
TAXONOMY_OUTPUT_PATH = DB_DIR / "taxonomy.json"


def extract_taxonomy(games):
    """Extract unique categorical and numeric values from game library."""
    
    taxonomy = {
        "genres": set(),
        "tags": set(),
        "features": set(),
        "sources": set(),
        "numeric_ranges": {
            "time_played_hours": {"min": None, "max": None},
            "community_score": {"min": None, "max": None},
            "critic_score": {"min": None, "max": None},
        }
    }
    
    for game in games:
        # Extract categorical arrays
        if game.get("genres"):
            taxonomy["genres"].update(game["genres"])
        if game.get("tags"):
            taxonomy["tags"].update(game["tags"])
        if game.get("features"):
            taxonomy["features"].update(game["features"])
        if game.get("sources"):
            taxonomy["sources"].update(game["sources"])
        
        # Extract numeric ranges
        time_played = game.get("time_played_hours")
        if time_played is not None and isinstance(time_played, (int, float)):
            if taxonomy["numeric_ranges"]["time_played_hours"]["min"] is None:
                taxonomy["numeric_ranges"]["time_played_hours"]["min"] = time_played
                taxonomy["numeric_ranges"]["time_played_hours"]["max"] = time_played
            else:
                taxonomy["numeric_ranges"]["time_played_hours"]["min"] = min(
                    taxonomy["numeric_ranges"]["time_played_hours"]["min"], time_played
                )
                taxonomy["numeric_ranges"]["time_played_hours"]["max"] = max(
                    taxonomy["numeric_ranges"]["time_played_hours"]["max"], time_played
                )
        
        community_score = game.get("community_score")
        if community_score is not None and isinstance(community_score, (int, float)):
            if taxonomy["numeric_ranges"]["community_score"]["min"] is None:
                taxonomy["numeric_ranges"]["community_score"]["min"] = community_score
                taxonomy["numeric_ranges"]["community_score"]["max"] = community_score
            else:
                taxonomy["numeric_ranges"]["community_score"]["min"] = min(
                    taxonomy["numeric_ranges"]["community_score"]["min"], community_score
                )
                taxonomy["numeric_ranges"]["community_score"]["max"] = max(
                    taxonomy["numeric_ranges"]["community_score"]["max"], community_score
                )
        
        critic_score = game.get("critic_score")
        if critic_score is not None and isinstance(critic_score, (int, float)):
            if taxonomy["numeric_ranges"]["critic_score"]["min"] is None:
                taxonomy["numeric_ranges"]["critic_score"]["min"] = critic_score
                taxonomy["numeric_ranges"]["critic_score"]["max"] = critic_score
            else:
                taxonomy["numeric_ranges"]["critic_score"]["min"] = min(
                    taxonomy["numeric_ranges"]["critic_score"]["min"], critic_score
                )
                taxonomy["numeric_ranges"]["critic_score"]["max"] = max(
                    taxonomy["numeric_ranges"]["critic_score"]["max"], critic_score
                )
    
    # Convert sets to sorted lists for output
    return {
        "genres": sorted(list(taxonomy["genres"])),
        "tags": sorted(list(taxonomy["tags"])),
        "features": sorted(list(taxonomy["features"])),
        "sources": sorted(list(taxonomy["sources"])),
        "numeric_ranges": taxonomy["numeric_ranges"],
    }


def load_library():
    """Load library.json."""
    if not LIBRARY_PATH.exists():
        print(f"Error: {LIBRARY_PATH} not found.")
        raise SystemExit(1)
    
    try:
        with LIBRARY_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, list):
                print("Error: library.json should be an array of game objects.")
                raise SystemExit(1)
            return data
    except json.JSONDecodeError as e:
        print(f"Error reading library.json: {e}")
        raise SystemExit(1)


def print_taxonomy(taxonomy):
    """Print taxonomy in a clean, readable format."""
    print("\n" + "=" * 70)
    print("GAME LIBRARY TAXONOMY")
    print("=" * 70)
    
    # Genres
    print(f"\n📂 GENRES ({len(taxonomy['genres'])} total):")
    print("  " + ", ".join(taxonomy["genres"][:10]))
    if len(taxonomy["genres"]) > 10:
        print(f"  ... and {len(taxonomy['genres']) - 10} more")
    
    # Tags
    print(f"\n🏷️  TAGS ({len(taxonomy['tags'])} total):")
    tags_preview = taxonomy["tags"][:15]
    print("  " + ", ".join(tags_preview))
    if len(taxonomy["tags"]) > 15:
        print(f"  ... and {len(taxonomy['tags']) - 15} more")
    
    # Features
    print(f"\n⚙️  FEATURES ({len(taxonomy['features'])} total):")
    features_preview = taxonomy["features"][:10]
    print("  " + ", ".join(features_preview))
    if len(taxonomy["features"]) > 10:
        print(f"  ... and {len(taxonomy['features']) - 10} more")
    
    # Sources
    print(f"\n🛒 SOURCES ({len(taxonomy['sources'])} total):")
    print("  " + ", ".join(taxonomy["sources"]))
    
    # Numeric Ranges
    print(f"\n📊 NUMERIC RANGES:")
    time_range = taxonomy["numeric_ranges"]["time_played_hours"]
    print(f"  Time Played (hours): {time_range['min']} - {time_range['max']}")
    
    comm_range = taxonomy["numeric_ranges"]["community_score"]
    if comm_range['min'] is not None:
        print(f"  Community Score: {comm_range['min']} - {comm_range['max']}")
    else:
        print(f"  Community Score: No data")
    
    crit_range = taxonomy["numeric_ranges"]["critic_score"]
    if crit_range['min'] is not None:
        print(f"  Critic Score: {crit_range['min']} - {crit_range['max']}")
    else:
        print(f"  Critic Score: No data")
    
    print("\n" + "=" * 70)


def save_taxonomy_json(taxonomy):
    """Optionally save taxonomy as JSON for caching."""
    try:
        with TAXONOMY_OUTPUT_PATH.open("w", encoding="utf-8") as f:
            json.dump(taxonomy, f, indent=2, ensure_ascii=False)
        print(f"✓ Taxonomy saved to {TAXONOMY_OUTPUT_PATH}")
    except Exception as e:
        print(f"⚠ Warning: Could not save taxonomy.json: {e}")


if __name__ == "__main__":
    print("Loading library...")
    games = load_library()
    print(f"✓ Loaded {len(games)} games")
    
    print("Extracting taxonomy...")
    taxonomy = extract_taxonomy(games)
    print("✓ Taxonomy extracted")
    
    # Print to console
    print_taxonomy(taxonomy)
    
    # Save as JSON for caching
    save_taxonomy_json(taxonomy)
    
    print("\nTaxonomy ready for use by recommendation filters!")
