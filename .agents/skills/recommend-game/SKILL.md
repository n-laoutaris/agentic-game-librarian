---
name: recommend-game
description: Recommends a game based on user's current mood, leveraging the local library database and the user's native memory context.
---

# Recommend Game Skill

## Core Directives
Trigger this skill when the user asks what to play or wants to explore their library.

## Execution Steps

### Step 1: Check Taxonomy
If you need to verify exact tag or genre strings before filtering, read `database/taxonomy.json`.

### Step 2: Construct & Execute Filter
Determine the user's current mood and constraints. Translate these into query arguments for `filter_games.py`. 
- You can use `--filter field:value` multiple times. 

**Execution Format:**
```
python /recommend-game/scripts/filter_games.py --filter genre:RPG,Horror --filter tag:Co-op --limit 10
```

### Step 3: Evaluate & Rank 
Do not just output the raw script results. Evaluate the returned games against the user's requirements. 
**Priorities for selection:**
1. Hardware capability (Ensure the game fits the intended PC rig if you have access to system requirements).
2. Unplayed/Backlog status.
3. Alignment with current mood and session time constraints.

### Step 4: Recommend
Present 1-3 games. Explain exactly why they fit the user's current mood and historical preferences. Do not mention your filtering process.

## Constraints
- **NEVER** attempt to read `database/library.json` directly. Always use the script.
- If the filter returns 0 results, relax your arguments and run the script again. 
- If tastes have clearly shifted based on the conversation, make a note to update your memory.