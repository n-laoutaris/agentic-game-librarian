---
name: update-library
description: Loads and normalizes Playnite multi-store export into enriched library.json
---

This skill handles the complete library update process: loading Playnite's multi-store export and normalizing it into a clean, enriched library format ready for agent recommendations.

## Execution Steps

When running this skill, execute the following:

1. **Normalize Playnite Export**: Run the normalization script to clean and transform the raw Playnite CSV
   - Script: `scripts/normalize_playnite_export.py`
   - Input: `database/playnite_export.csv` (automatically maintained by Playnite)
   - Output: `database/library.json` (enriched multi-store catalog)
   - Time: ~1-2 seconds for typical libraries (no external API calls)

## Data Transformations

The normalization script performs the following transformations:

### Input: Playnite CSV Columns
```
Name, Description, Developers, Features, Genres, Release Date, 
Completion Status, Time Played, Sources, Tags, Community Score, Critic Score, Id
```

### Output: Enriched library.json Schema

Each game entry in `database/library.json` contains:

```json
{
  "id": "771147b7-ca35-4264-8389-ae0ccd86f469",
  "title": "10 Second Ninja X",
  "description": "Clean plain text without HTML tags",
  "developers": ["Four Circle Interactive"],
  "genres": ["Arcade", "Fighting", "Indie", "Platform", "Puzzle"],
  "features": ["Single Player"],
  "tags": ["2D", "2D Platformer", "Action", "Arcade", "Casual", "Difficult"],
  "release_date": "2016-07-19",
  "completion_status": "Not Played",
  "time_played_hours": 45.5,
  "sources": ["Steam"],
  "community_score": 65,
  "critic_score": 77
}
```

### Transformation Details

| Field | Transformation |
|-------|---|
| **Id** | Kept as-is (Playnite UUID serves as primary key) |
| **Name** | Trimmed whitespace → title |
| **Description** | HTML tags stripped, entities decoded, whitespace normalized |
| **Developers** | Comma-separated string → array of strings |
| **Genres** | Comma-separated string → array of strings |
| **Features** | Comma-separated string → array of strings |
| **Tags** | Comma-separated string → array of strings |
| **Release Date** | Multiple formats normalized to ISO (YYYY-MM-DD) |
| **Completion Status** | Preserved as-is or null if empty |
| **Time Played** | Converted to float hours (handles "45 mins", "1.5h", etc.) |
| **Sources** | Comma-separated string → array (e.g., ["Steam"], ["Steam", "Epic"]) |
| **Community Score** | Empty → null, otherwise parsed as integer |
| **Critic Score** | Empty → null, otherwise parsed as integer |

### Data Cleaning Features

1. **HTML Stripping**: Removes all HTML tags and script content from descriptions, preserves text
2. **Entity Decoding**: Converts `&quot;`, `&amp;`, etc. to readable characters
3. **Time Format Handling**:
   - `"0"` → `0.0` hours
   - `"45 mins"` → `0.75` hours
   - `"1.5"` → `1.5` hours
   - Empty → `0.0` hours
4. **Date Normalization**:
   - Supports: `19/7/2016`, `2016-07-19`, `07/19/2016`, `2016/7/19`, `2016` (year only)
   - Output: ISO format `YYYY-MM-DD` or `null`
5. **Graceful Null Handling**: Empty fields become `null` in JSON, arrays default to `[]`

## Running the Skill

### Manual Execution

```powershell
# From the project root (PowerShell):
$env:PYTHONIOENCODING="utf-8"; & "c:\programdata\anaconda3\python.exe" ".agents\skills\update-library\scripts\normalize_playnite_export.py"

# Or from bash:
python .agents/skills/update-library/scripts/normalize_playnite_export.py
```

**Note**: The script handles BOM-encoded CSV files automatically (uses `encoding="utf-8-sig"`), so Playnite exports are processed correctly.

### From the Agent

Invoke with:
```
Update my game library from Playnite
Run the update-library skill
Sync my library
```

The agent will execute the normalization and provide a summary (e.g., "Normalized 247 games, 3 skipped").

## Important Notes

### Multi-Store Support

Games appearing on multiple storefronts (e.g., same game on both Steam and Epic) will appear as separate entries with different `sources` arrays. This preserves:
- Per-store achievements and stats
- Platform-specific install locations
- Store-specific ratings and reviews

### CSV Export Setup (Playnite)

1. Install [Playnite](https://playnite.link/)
2. Import your libraries (Steam, Epic, GOG, Xbox, etc.)
3. Configure auto-export in Playnite settings:
   - Path: `<project>/database/playnite_export.csv`
   - Format: CSV
   - Frequency: On library change (automatic)

The normalization script will pick up changes automatically.

### Performance

- Reading CSV: ~0.1-0.5 seconds (depending on library size)
- Transformations: ~1-2 seconds for typical libraries (200-500 games)
- Writing JSON: ~0.5 seconds
- **Total**: ~2-3 seconds (no waiting for external APIs!)

### Error Handling

The normalization script:
- Logs skipped rows with reasons
- Continues processing on minor errors (graceful degradation)
- Validates all required fields (title, id)
- Reports summary statistics at completion

If a game fails to normalize, it's logged and skipped—the rest of the library proceeds normally.

## Output Formats

### library.json Structure

The output `database/library.json` is an array of game objects, one per game:

```json
[
  { game 1 with all fields... },
  { game 2 with all fields... },
  { game N... }
]
```

**Total size**: Typically 10-30 MB for large libraries (readable, human-friendly format)

## Backward Compatibility

If you have a legacy library setup:
- Old scripts (`fetch_steam_owned_games.py`, `find_new_games.py`, `fetch_metadata.py`) are deprecated but preserved
- They're marked with deprecation notices
- Don't use them; use Playnite export instead

To migrate from Steam API to Playnite:
1. Install Playnite and import your Steam library
2. Configure auto-export to `database/playnite_export.csv`
3. Run `normalize_playnite_export.py`
4. Delete old intermediate files (raw_steam.json, needs_metadata.json)

Done! Your library.json now contains multi-store data with no API management.

---

**Next Steps**: Use the enriched `library.json` with the agent's recommendation and analysis skills.
