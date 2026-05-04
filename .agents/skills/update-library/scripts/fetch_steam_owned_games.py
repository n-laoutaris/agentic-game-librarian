import json
import os
from pathlib import Path
import requests
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
DB_DIR = BASE_DIR / "database"
ENV_FILE = BASE_DIR / ".env"
RAW_STEAM_LIST_PATH = DB_DIR / "raw_steam.json"
STEAM_API_BASE_URL = "https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/"

# Load environment variables
load_dotenv(ENV_FILE)


def fetch_steam_games(api_key, steam_id):
    params = {
        "key": api_key,
        "steamid": steam_id,
        "format": "json",
        "include_appinfo": 1,
        "include_played_free_games": 1,
    }

    try:
        response = requests.get(STEAM_API_BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get("response", {}).get("games", [])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Steam games: {e}")
        return []


def save_raw_steam_list(games):
    raw_list = [
        {
            "title": game.get("name"),
            "platform": "Steam",
            "source_id": game.get("appid"),
            "playtime_hours": game.get("playtime_forever", 0) / 60,
        }
        for game in games
    ]
    
    with RAW_STEAM_LIST_PATH.open("w", encoding="utf-8") as f:
        json.dump(raw_list, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    # Get credentials from environment
    steam_api_key = os.getenv("STEAM_API_KEY")
    steam_id = os.getenv("STEAM_ID")
    
    if not steam_api_key or not steam_id:
        print("Error: STEAM_API_KEY and STEAM_ID must be set in .env file")
        raise SystemExit(1)
    
    steam_games = fetch_steam_games(steam_api_key, steam_id)

    if not steam_games:
        print("No Steam games found or an error occurred.")
        raise SystemExit(1)

    save_raw_steam_list(steam_games)
    print(f"Saved {len(steam_games)} owned Steam games to {RAW_STEAM_LIST_PATH}")
