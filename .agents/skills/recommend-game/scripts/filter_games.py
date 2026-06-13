"""
Universal Field Filter (simplified)

This script provides a lightweight, agent-friendly interface to query the library
without reading `library.json` directly. Use the universal `--filter` argument
multiple times to build inclusive-OR filters of the form `field:val1,val2`.

Behavior:
- Multiple `--filter` entries may be supplied; values within a field are ORed.
- Filters across different fields are combined with OR (any field match passes).
- Matching is case-insensitive and supports list or string fields.
- Supported convenience options: `--output-fields`, `--sort-by`, `--limit`.

Examples:
  # Any game matching genre "RPG" or tag "Co-op"
  python filter_games.py --filter genre:RPG --filter tag:Co-op

  # Multiple values in one filter (OR within field)
  python filter_games.py --filter genre:RPG,Adventure --limit 10

  # Field alias example: developer maps to `developers` field
  python filter_games.py --filter developer:BioWare

Return: JSON array of matching game objects (printed to stdout)
"""

import json
import argparse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
DB_DIR = BASE_DIR / "database"
LIBRARY_PATH = DB_DIR / "library.json"


def load_library():
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


def parse_filter_arg(filter_str):
    """Parse 'field:val1,val2' into (field, [values])."""
    if ":" not in filter_str:
        raise ValueError(f"Invalid filter format: {filter_str}. Expected 'field:val1,val2'")
    field, _, values_str = filter_str.partition(":")
    field = field.strip()
    values = [v.strip() for v in values_str.split(",") if v.strip()]
    return field, values


def normalize_field_name(field):
    """Map common aliases to library field names."""
    field_map = {
        "genre": "genres",
        "tag": "tags",
        "feature": "features",
        "source": "sources",
        "timeEarned": "time_played_hours",
        "score": "community_score",
        "criticScore": "critic_score",
        "developer": "developers",
    }
    return field_map.get(field, field)


def matches_value(game_value, filter_values):
    if game_value is None:
        return False
    filter_values_lower = [v.lower() for v in filter_values]
    if isinstance(game_value, list):
        game_values_lower = [str(v).lower() for v in game_value]
        return any(fv in game_values_lower for fv in filter_values_lower)
    # string or numeric -> string-match
    game_value_lower = str(game_value).lower()
    return any(fv in game_value_lower for fv in filter_values_lower)


def filter_games(games, filters, output_fields=None, sort_by=None, limit=None):
    """Inclusive-OR across fields: any field match passes."""
    if not filters:
        matching_games = games[:]
    else:
        matching_games = []
        for game in games:
            match = False
            for field, values in filters.items():
                normalized = normalize_field_name(field)
                game_value = game.get(normalized)
                if matches_value(game_value, values):
                    match = True
                    break
            if match:
                matching_games.append(game)
    # sort
    if sort_by:
        try:
            reverse = sort_by.startswith("-")
            key_field = sort_by.lstrip("-")
            matching_games.sort(key=lambda g: (g.get(key_field) is None, g.get(key_field)), reverse=reverse)
        except Exception as e:
            print(f"Warning: Could not sort by {sort_by}: {e}")
    # limit
    if limit:
        matching_games = matching_games[:limit]
    # output fields
    if output_fields:
        fields = [f.strip() for f in output_fields.split(",") if f.strip()]
        matching_games = [{k: v for k, v in game.items() if k in fields} for game in matching_games]
    return matching_games


def main():
    parser = argparse.ArgumentParser(description="Filter games using repeated --filter field:val1,val2 (inclusive-OR).")
    parser.add_argument("--filter", action="append", help="Generic filter in format field:val1,val2 (repeatable)")
    parser.add_argument("--output-fields", help="Comma-separated fields to include in output")
    parser.add_argument("--sort-by", help="Field to sort by, prefix with '-' for descending")
    parser.add_argument("--limit", type=int, help="Maximum number of results to return")
    args = parser.parse_args()

    # Build filters
    filters = {}
    if args.filter:
        for f in args.filter:
            try:
                field, values = parse_filter_arg(f)
            except ValueError as e:
                print(f"Error: {e}")
                raise SystemExit(1)
            if field in filters:
                filters[field].extend(values)
            else:
                filters[field] = values

    games = load_library()
    results = filter_games(games, filters, output_fields=args.output_fields, sort_by=args.sort_by, limit=args.limit)
    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
