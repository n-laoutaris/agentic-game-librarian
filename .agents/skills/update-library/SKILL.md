---
name: update-library
description: Phases 1-3 - Fetches owned games from Steam, identifies new titles, and enriches with IGDB metadata
---

# Update Library Skill - Phases 1-3 (Fetch, Diff, & Enrich)

This skill handles the complete library update process: fetching owned games from Steam, identifying new titles, and enriching them with metadata from IGDB.

## Execution Steps

When running this skill, execute the following in order:

1. **Fetch Steam Games**: Run the Steam fetch script to query your owned games from the Steam API
   - Script: `scripts/fetch_steam_owned_games.py`
   - Output: `database/raw_steam.json`
   - Format: Array of objects with `title`, `platform` (Steam), `source_id` (Steam App ID), and `playtime_hours` (converted from minutes)

2. **Find New Games**: Compare raw games against the master library to identify which titles need metadata
   - Script: `scripts/find_new_games.py`
   - Inputs: `database/raw_steam.json` and `database/library.json`
   - Output: `database/needs_metadata.json`
   - Logic: Compares by `source_id` only; all raw games are considered new if master library is empty
   - Format: Same as raw_steam.json - objects with `title`, `platform`, `source_id`, and `playtime_hours`

3. **Fetch Metadata**: Enrich new games with metadata from IGDB via Twitch OAuth2 authentication
   - Script: `scripts/fetch_metadata.py`
   - Inputs: `database/needs_metadata.json` and `database/library.json`
   - Outputs: Updated `database/library.json` and emptied `database/needs_metadata.json`
   - Authentication: Requires `TWITCH_CLIENT_ID` and `TWITCH_CLIENT_SECRET` in `user_config.json`
   - Per-game: Fetches name, summary, genres, themes, game modes, player perspectives, keywords, rating, and companies from IGDB
   - Format: Enriched objects combining store data with IGDB metadata

The complete pipeline enriches your library with comprehensive game metadata on each run.

## Important Notes

### Metadata Completeness
- IGDB returns results for ~93% of games in a typical Steam library
- Games without IGDB matches are still added to the library with store data (title, platform, source_id, playtime_hours)
- Some IGDB records may have incomplete fields (e.g., null summary or rating) - these are preserved as-is
- Special characters in game titles (®, ™, etc.) are handled by the search and don't prevent enrichment

### Incremental Updates
- Running the pipeline multiple times is safe - it will only enrich new games not already in library.json
- Comparison is done by source_id, so updating playtime_hours on Steam will preserve existing IGDB metadata

## Output Formats

### raw_steam.json (Phase 1 Output)

The `database/raw_steam.json` file contains all owned games:

```json
[
  {
    "title": "Game Title",
    "platform": "Steam",
    "source_id": 123456,
    "playtime_hours": 42.5
  }
]
```

### needs_metadata.json (Phase 2 Output)

The `database/needs_metadata.json` file contains only games not yet in the master library:

```json
[
  {
    "title": "New Game Title",
    "platform": "Steam",
    "source_id": 987654,
    "playtime_hours": 5.25
  }
]
```

### library.json (Phase 3 Output)

The `database/library.json` file contains enriched games with both store and metadata:

```json
[
  {
    "title": "Game Title",
    "platform": "Steam",
    "source_id": 123456,
    "playtime_hours": 42.5,
    "igdb_id": 9876,
    "summary": "An engaging game about...",
    "genres": ["Action", "Adventure"],
    "themes": ["Fantasy", "Open World"],
    "game_modes": ["Single Player", "Multiplayer"],
    "player_perspectives": ["Third Person"],
    "keywords": ["Open World", "Exploration"],
    "total_rating": 87.5,
    "involved_companies": ["Developer Inc.", "Publisher LLC"]
  }
]
```

This enriched master library is the final output ready for your gaming library application.
