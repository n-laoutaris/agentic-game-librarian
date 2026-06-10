"""
Normalize Playnite CSV Export to Library JSON

Reads the raw Playnite export CSV and transforms it into a clean,
enriched library.json suitable for recommendation and agent reasoning.

Features:
- HTML tag stripping from descriptions
- Time played conversion to float hours
- Array parsing for multi-value fields
- Date normalization to ISO format
- Graceful handling of missing/empty values
- UUID-based primary keys (Playnite native)
"""

import csv
import json
import re
from pathlib import Path
from datetime import datetime
from html.parser import HTMLParser
from html import unescape


BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
DB_DIR = BASE_DIR / "database"
PLAYNITE_EXPORT_PATH = DB_DIR / "playnite_export.csv"
LIBRARY_OUTPUT_PATH = DB_DIR / "library.json"


class HTMLStripper(HTMLParser):
    """Simple HTML tag stripper."""
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = []

    def handle_data(self, data):
        self.text.append(data)

    def get_data(self):
        return ''.join(self.text)


def strip_html_tags(html_text):
    """Remove all HTML tags and decode entities from text."""
    if not html_text or not isinstance(html_text, str):
        return ""
    
    # Remove script and style tags completely
    html_text = re.sub(r'<script[^>]*>.*?</script>', '', html_text, flags=re.DOTALL | re.IGNORECASE)
    html_text = re.sub(r'<style[^>]*>.*?</style>', '', html_text, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove all remaining HTML tags
    html_text = re.sub(r'<[^>]+>', '', html_text)
    
    # Decode HTML entities
    html_text = unescape(html_text)
    
    # Normalize whitespace and line breaks
    html_text = re.sub(r'\s+', ' ', html_text).strip()
    
    # Clean up multiple spaces
    html_text = re.sub(r' +', ' ', html_text)
    
    return html_text


def parse_csv_array(value):
    """Parse comma-separated string into list."""
    if not value or not isinstance(value, str):
        return []
    
    items = [item.strip() for item in value.split(',') if item.strip()]
    return items


def parse_time_played(time_str):
    """Convert time played string to float hours.
    
    Handles formats like:
    - "0" or empty → 0.0
    - "45 mins" → 0.75
    - "1.5" → 1.5
    - "7200" → 2.0 (Playnite exports raw seconds as a bare number)
    - "10:30:45" (HH:MM:SS) → 10.5125
    """
    if not time_str or not isinstance(time_str, str):
        return 0.0
    
    time_str = time_str.strip().lower()
    
    # Empty or zero
    if not time_str or time_str == "0":
        return 0.0
    
    # Minutes notation (e.g., "45 mins")
    if "mins" in time_str or "minutes" in time_str:
        try:
            minutes = float(re.search(r'(\d+(?:\.\d+)?)', time_str).group(1))
            return round(minutes / 60, 2)
        except (AttributeError, ValueError):
            return 0.0
    
    # Hours notation (e.g., "2 hours" or "2.5h")
    if "hour" in time_str or "h" in time_str:
        try:
            hours = float(re.search(r'(\d+(?:\.\d+)?)', time_str).group(1))
            return round(hours, 2)
        except (AttributeError, ValueError):
            return 0.0
    
    # Bare numbers from Playnite export are raw seconds, not hours.
    if time_str.isdigit():
        try:
            seconds = int(time_str)
            return round(seconds / 3600, 2)
        except ValueError:
            return 0.0
    
    # Decimal numbers with no units are treated as hours.
    try:
        return round(float(time_str), 2)
    except ValueError:
        return 0.0


def parse_release_date(date_str):
    """Convert release date to ISO format (YYYY-MM-DD).
    
    Handles formats like:
    - "19/7/2016" → "2016-07-19"
    - "2016-07-19" → "2016-07-19" (pass-through)
    - Empty → None
    """
    if not date_str or not isinstance(date_str, str):
        return None
    
    date_str = date_str.strip()
    if not date_str:
        return None
    
    # Try common date formats
    formats = [
        "%d/%m/%Y",      # 19/7/2016
        "%Y-%m-%d",      # 2016-07-19
        "%m/%d/%Y",      # 7/19/2016
        "%Y/%m/%d",      # 2016/7/19
        "%d-%m-%Y",      # 19-7-2016
        "%Y",            # 2016 (year only)
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    
    # If nothing matched, return None
    return None


def parse_numeric_score(score_str):
    """Parse numeric score, return int or None if empty/invalid."""
    if not score_str or not isinstance(score_str, str):
        return None
    
    score_str = score_str.strip()
    if not score_str:
        return None
    
    try:
        return int(float(score_str))
    except ValueError:
        return None


def normalize_game(row):
    """Transform a CSV row into normalized game entry."""
    try:
        game = {
            "id": row.get("Id", "").strip(),
            "title": row.get("Name", "").strip(),
            "description": strip_html_tags(row.get("Description", "")),
            "developers": parse_csv_array(row.get("Developers", "")),
            "genres": parse_csv_array(row.get("Genres", "")),
            "features": parse_csv_array(row.get("Features", "")),
            "tags": parse_csv_array(row.get("Tags", "")),
            "release_date": parse_release_date(row.get("Release Date", "")),
            "completion_status": row.get("Completion Status", "").strip() or None,
            "time_played_hours": parse_time_played(row.get("Time Played", "")),
            "sources": parse_csv_array(row.get("Sources", "")),
            "community_score": parse_numeric_score(row.get("Community Score", "")),
            "critic_score": parse_numeric_score(row.get("Critic Score", "")),
        }
        
        # Validate required fields
        if not game["id"] or not game["title"]:
            return None
        
        return game
    except Exception as e:
        print(f"  ⚠ Error processing game: {e}")
        return None


def load_and_normalize_playnite():
    """Load Playnite CSV and normalize to library.json."""
    if not PLAYNITE_EXPORT_PATH.exists():
        print(f"Error: {PLAYNITE_EXPORT_PATH} not found.")
        raise SystemExit(1)
    
    games = []
    skipped = 0
    
    print(f"Reading Playnite export from {PLAYNITE_EXPORT_PATH}...")
    
    try:
        with PLAYNITE_EXPORT_PATH.open("r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            
            for i, row in enumerate(reader, 1):
                game = normalize_game(row)
                
                if game:
                    games.append(game)
                    print(f"  [{i}] ✓ {game['title']}")
                else:
                    skipped += 1
                    title = row.get("Name", f"Row {i}")
                    print(f"  [{i}] ✗ Skipped: {title}")
    
    except csv.Error as e:
        print(f"Error reading CSV: {e}")
        raise SystemExit(1)
    except UnicodeDecodeError as e:
        print(f"Error: CSV encoding issue - {e}")
        raise SystemExit(1)
    
    print(f"\n✓ Processed {len(games)} games ({skipped} skipped)")
    
    # Save to library.json
    print(f"Writing normalized library to {LIBRARY_OUTPUT_PATH}...")
    with LIBRARY_OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(games, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Library saved ({len(games)} games)")
    
    return games


if __name__ == "__main__":
    print("=" * 60)
    print("Playnite CSV → Library JSON Normalization")
    print("=" * 60)
    
    games = load_and_normalize_playnite()
    
    print("\n" + "=" * 60)
    print(f"Complete! Library ready for agent recommendations.")
    print("=" * 60)
