---
name: update-library
description: Loads and normalizes Playnite multi-store export into enriched library.json
---

This skill handles the complete library update process: loading Playnite's multi-store export and normalizing it into a clean, enriched library format ready for agent recommendations and usage with helper parsing or filtering scripts.

## Execution steps

### Step 1: Normalize Playnite Export

- Script: `scripts/normalize_playnite_export.py`
- Input: `database/playnite_export.csv` (automatically maintained by Playnite)
- Output: `database/library.json` (enriched multi-store catalog) and a printed summary (e.g., "Normalized 247 games, 3 skipped").
- Time: ~1-2 seconds for typical libraries 

### Step 2: Update Taxonomy

- Script: `scripts/update_taxonomy.py`
- Input: `database/library.json`
- Output: `database/taxonomy.json`
- Time: ~1 second for typical libraries

## Data Transformations

The normalization script performs the following transformations:

### Input: Playnite CSV Columns
```
Name, Description, Developers, Features, Genres, Release Date, Completion Status, Time Played, Sources, Tags, Community Score, Critic Score, Id
```

### Output: Enriched library.json Schema

Example of what each game entry in `database/library.json` contains:

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

### Multi-Store Support Note

Games appearing on multiple storefronts (e.g., same game on both Steam and Epic) will appear as separate entries with different `sources` arrays.