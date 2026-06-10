---
name: recommend-game
description: Recommends a game based on user's current mood and gaming profile, using intelligent filtering and contextual reasoning.
---

# Recommend Game Skill

## When to use this skill

Trigger this skill when:
- User asks: "What should I play?", "Recommend a game for me", "I'm in the mood for [X]"
- User has already initialized their profile via the `update-profile` skill
- User wants contextual game suggestions based on their current mood and available time
- User wants to explore their existing library with specific criteria

## What this skill does

1. **Interprets user mood** from the conversation (e.g., "I want something relaxing", "I'm feeling competitive")
2. **Accesses the user's profile** (`database/user_profile.json`) to understand preferences, avoid_genres, and PC hardware constraints
3. **Reasons about library taxonomy** to map mood keywords to available game categories
4. **Constructs filter queries** using boolean expressions to find matching games
5. **Evaluates results** using profile affinity scores and play patterns
6. **Recommends 1-3 games** with clear reasoning tied to the user's mood and profile

## Data inputs

- **User's chat message** — Current mood statement (e.g., "I want to chill with something co-op")
- `database/library.json` — Game library (AGENT MUST NOT READ DIRECTLY; use filter_games.py)
- `database/user_profile.json` — Player preferences, hardware, favorite genres, avoid_genres
- `database/taxonomy.json` — Available genres, tags, features (optional; can call get_taxonomy.py as reference)

## Data outputs

None permanent; recommendations are provided conversationally.

## Execution steps

### Step 1: Get Taxonomy Reference (Optional)
If you need to refresh your understanding of available categories, run:
```bash
python .agents/skills/update-library/scripts/get_taxonomy.py
```

This outputs:
- All unique genres, tags, features, and sources
- Numeric ranges for playtime, community score, critic score

Store this mentally or as context for building filter queries.

### Step 2: Interpret User Mood

From the user's message, identify:
- **Primary mood keywords**: relaxing, competitive, story-driven, action-packed, social, solo, challenging
- **Session type**: Quick 30-min session vs. long-form evening
- **Mood strength**: Strong preference (e.g., "MUST be co-op") vs. exploratory ("open to anything")

Example interpretation:
```
User: "I have about an hour and want to play something fun with a friend."
Mood: co-op, multiplayer, ~60 minute session, social/fun
```

### Step 3: Access User Profile

Load the user's profile to understand:
- `favorite_genres.explicit_favorites` — Genres they love
- `favorite_genres.avoid_genres` — Genres/themes to exclude
- `implicit_signals.recent_interest_trends` — What they're currently drawn to
- `recommendation_state.available_time_minutes` — Session length constraints
- `persona.preferred_play_style` — Their typical gaming approach (e.g., "co-op progression", "competitive teamwork")
- `play_history` — Top-played games to infer patterns

### Step 4: Map Mood to Filter Criteria

Combine mood keywords with profile data to construct filter criteria:

1. **Start with mood keywords** → map to genres, tags, or features
2. **Fill gaps with profile** → if mood says "co-op" but not specific genre, check `favorite_genres`
3. **Apply constraints** → exclude `avoid_genres`, respect `available_time_minutes`
4. **Prioritize backlog** → prefer `completion_status: "Not Played"` or low `time_played_hours`

**Example mapping**:
- User mood: "Something quick and competitive"
- Profile: `favorite_genres: ["Strategy", "MOBA"]`, `avoid_genres: ["Horror"]`, `available_time: 45 mins`
- Query result: Games tagged "Competitive" OR "Multiplayer", genres Strategy/MOBA, under 2 hours playtime, not Horror

### Step 5: Construct Boolean Filter Query

Build a query string for `filter_games.py` using the syntax below.

**Query Syntax**:
```
Field prefixes:  genre:, tag:, feature:, source:, timeEarned:, score:, criticScore:
Operators:       AND (high precedence), OR, NOT
Ranges:          field:[min-max]   (e.g., timeEarned:[0.0-100.0])
Literals:        field:VALUE or field:"Value With Spaces"
```

**Examples**:
```
# Co-op games that are not Horror
(tag:Co-op OR tag:Multiplayer) AND NOT genre:Horror

# RPGs the user hasn't played much (under 5 hours)
genre:RPG AND timeEarned:[0.0-5.0]

# Competitive multiplayer on Steam
tag:Competitive AND source:Steam

# Games with good community score
genre:"Role-playing (RPG)" AND score:[75-90]

# Feature: Full Controller Support
feature:"Full Controller Support"
```

### Step 6: Execute Filter

Run the filter script with the constructed query:

```bash
python .agents/skills/recommend-game/scripts/filter_games.py \
  --query "genre:RPG AND tag:Co-op AND NOT genre:Horror"
```

This returns a JSON array of ALL matching games. **Agent filters the results contextually.**

### Step 7: Evaluate & Rank Results

From the matching games, apply agent reasoning to select the top 1–3 recommendations:

**Scoring factors** (in priority order):
1. **Backlog priority** — Prefer unplayed games (completion_status: "Not Played") over replayed ones
2. **Genre affinity** — Games in user's top-played genres score higher
3. **Similarity to favorites** — Games similar to user's most-played titles (check tags/genres overlap)
4. **Session fit** — Games with `time_played_hours` matching user's available time
5. **Hardware fit** — Games matching user's PC capabilities (e.g., if they have limited GPU, avoid AAA graphics-intensive titles)
6. **Community sentiment** — Higher `community_score` is a tiebreaker

**Example evaluation**:
```
Filter result: [Terraria, Stardew Valley, Grounded, A Space for the Unbound]

Scoring:
- Terraria: Unplayed, tag:Co-op, familiar Sandbox mechanics (user played Minecraft) → ⭐⭐⭐⭐⭐
- Stardew Valley: Unplayed, tag:Co-op, relaxing (matches mood) → ⭐⭐⭐⭐
- Grounded: Unplayed, tag:Co-op, survival (unfamiliar to user) → ⭐⭐⭐
- A Space for the Unbound: Played before, atmospheric narrative → ⭐⭐ (lower priority)

Recommendation: Terraria
```

### Step 8: Provide Recommendation

Present the top 1–3 games to the user with **clear reasoning** tied to their mood and profile:

**Recommendation template**:
```
"Based on your mood for [X], I recommend:

1. **[Game Title]** — [Brief reason]
   - Why it matches: You loved [similar game], and this has [shared element]
   - Best for: [Session type and mood fit]
   - Playtime: ~[typical session duration]

2. **[Alternative]** — [Brief reason]
   ...
```

**Example**:
```
"Since you want a quick co-op session, here's what stands out:

1. **Terraria** — Fast-paced sandbox exploration with instant cooperative play
   - Why it matches: You loved Stardew Valley's co-op charm, and Terraria has that same cooperative progression with more action.
   - Best for: 30-60 min sessions, unplayed in your library
   - Playtime: Flexible, great for quick sessions

2. **Grounded** — Survival co-op adventure, like a miniature Minecraft with more combat
   - Why it matches: You're drawn to exploration, and this scratches that itch while staying social
   - Best for: Longer sessions (60-90 mins), tactical co-op fun
```

## Error handling & fallbacks

**If filter returns 0 results:**
- Relax a constraint (e.g., drop the "unplayed" filter or expand genre criteria)
- Suggest the user update their profile to refine preferences
- Recommend exploring the taxonomy to discover new categories they might enjoy

**If filter returns too many results (>30):**
- Apply tighter constraints (e.g., add a community score threshold or source filter)
- Use `--limit 5` in filter_games.py and rank the top 5

**If user mood is vague:**
- Ask clarifying questions: "How much time do you have?", "Solo or multiplayer?", "Chill or challenging?"
- Reference their profile: "You usually love [genre], want something similar?"

## Important constraints

⚠️ **AGENT MUST NOT:**
- Read `database/library.json` directly (token limit violation)
- Guess filter criteria without consulting profile or taxonomy
- Recommend games the user explicitly avoided in their profile

✅ **AGENT SHOULD:**
- Use `filter_games.py` as the primary query interface
- Reference user profile signals (favorite_genres, implicit_signals, top played games)
- Explain recommendations in terms of the user's stated mood + profile
- Suggest profile updates if preferences have evolved ("Your tastes seem to have shifted—want to refresh your profile?")

## Related skills & future extensions

- **update-profile** — Initialize or refine user preferences before recommendations
- **update-library** — Sync library from Playnite; includes `get_taxonomy.py` for category reference
- **Future**: Mood-tracking over time to identify seasonal patterns; integration with HowLongToBeat for session planning
