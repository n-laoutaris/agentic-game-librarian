---
name: update-profile
description: Updates the player's profile with new information. If the profile is empty, acts as onboarding to initialize it. Collects or updates PC hardware facts, play preferences, and session patterns through conversational reasoning.
---

# Update Profile Skill

## When to use this skill

Trigger this skill when:
- User requests profile updates or wants to refine preferences
- `database/user_profile.json` has empty `favorite_games` and an empty `persona` (initialization mode)
- User is interacting with the Game Library Agent for the first time (acts as onboarding)
- User wants to adjust hardware specifications or gaming preferences

## What this skill does

1. **Detects profile state** by checking whether the user profile is empty (initialization mode) or already populated (update mode)
2. **Initializes or updates** based on profile state:
   - **Initialization Mode** (empty profile): Acts as onboarding, providing full first-run setup
   - **Update Mode** (existing profile): Focuses on refining or adding new preference signals
3. **Provides library context** by showing top-played games from `database/library.json`
4. **Collects or updates factual data** about PC hardware (CPU, GPU, RAM, OS, display, input devices)
5. **Engages in conversational prompts** to understand the user's current mood, play goals, and changing preferences
6. **Infers preference signals** from natural language responses without explicit genre rankings
7. **Persists the profile** with updated preference data, experience notes, and profile completion status
8. **Marks profile as initialized** in the context for future skill runs

## Data inputs

- `database/library.json` — user's game library with playtime data
- `database/user_profile.json` — current profile (may be empty for initialization)

## Data outputs

- Updated `database/user_profile.json`. Store results capturing both initialization and updates:
  - `pc_build` facts from user input (updated or created)
  - `experience_notes` capturing reasoning from this session
  - `implicit_signals` for preference inference (merged with existing)
  - `recommendation_state` with current mood and preferences

## Conversation flow

### Initialization Mode (Empty Profile)

#### Step 1: Greeting & context
```
"Welcome! I see this is your first time here. Let me help you set up your profile.

I can see your Steam library has [N] games. Your top-played titles are:
1. [Game title] — [playtime] hours
2. [Game title] — [playtime] hours
...

We'll start by collecting a few facts about your setup, and then I'd like to understand what you enjoy playing."
```

#### Step 2: PC build facts (conversational, not scripted)
Ask the user about their hardware:
- "What's your PC CPU and GPU?"
- "How much RAM do you have?"
- "What OS are you running?"
- "What input devices do you use? (keyboard, mouse, gamepad, etc.)"

Store responses in `pc_build` section.

#### Step 3: Current mood & intent
```
"What kind of game would you want to play right now?"
```

Store in `recommendation_state.current_mood`.

#### Step 4: Library feedback
```
"I noticed you've invested a lot of time in [top game]. 
 What did you enjoy most about it? What kept you coming back?"
```

Capture as experience notes for preference inference.

#### Step 5: Avoidances (open-ended)
```
"Are there any game types, atmospheres, or mechanics you want to avoid right now?"
```

Store in `implicit_signals.avoid_signals`.

### Update Mode (Existing Profile)

#### Step 1: Recap & context
```
"Welcome back! I see your profile was last updated on [date].

Your top-played titles remain:
1. [Game title] — [playtime] hours
2. [Game title] — [playtime] hours
...

What would you like to update? We can refine your preferences, update your hardware, or adjust what you're in the mood for."
```

#### Step 2: Selective hardware updates
Only ask about hardware changes if the user indicates their setup has evolved:
- "Has your PC hardware changed since last time?"
- If yes: "What's different? (CPU, GPU, RAM, OS, peripherals?)"

Update `pc_build` section only where new data is provided.

#### Step 3: Preference refinement
```
"How have your gaming preferences evolved? Are there new genres or types of experiences you're drawn to?"
```

Merge new signals with existing `implicit_signals`.

#### Step 4: Current mood
```
"What kind of game are you looking for today?"
```

Update `recommendation_state.current_mood`.

IMPORTANT: Do not ask all questions at once. Ask one question, wait for the user to respond, and then ask the next.

## Preference inference rules

The agent should reason about the user's preferences based on conversational inputs:

- **Explicit keywords** from user responses (e.g., "I love co-op", "horror makes me uncomfortable")
- **Library patterns** (e.g., top 5 games are all sci-fi → `sci-fi` genre signal)
- **Play behavior** (e.g., if one game has 1000 hours and others have <100 → user prefers deep, long-term progression)
- **Inverse signals** (e.g., "I'm tired of [genre]" → add to `avoid_signals`)
- **Updated signals** on profile updates: merge new preferences with existing ones rather than replacing them

Store inferred signals in:
- `persona.preferred_play_style` — list of inferred play styles
- `favorite_genres.explicit_favorites` — genres mentioned or evident from library
- `favorite_genres.avoid_genres` — genres or themes user wants to avoid
- `implicit_signals.recent_interest_trends` — what the user is currently drawn to
- `experience_notes` — detailed reasoning from profile session

## Multi-platform readiness

- Store game identifiers as `source_id` format: `steam:12345`, `epic:xxxxx`, `gog:xxxxx`
- When building `favorite_games`, normalize source IDs from `database/library.json`

## Profile completion marker

After the conversation, directly update `database/user_profile.json` with the collected profile data, timestamps, and experience notes.

## Error handling & graceful fallbacks

- If library is empty or too small: provide minimal greeting and focus on hardware + current mood
- If user skips PC build questions: use defaults and note in experience_notes that hardware is unknown
- If updating existing profile but user provides no changes: gracefully exit and confirm profile remains current
- If user provides vague responses: use library data as primary preference source
- Future sessions can refine the profile with additional AI reasoning

## Related skills & future extensions

- **Recommendation engine** skill will use this onboarded profile to suggest games
- **Profile refinement** skill will accept natural language mood/preference updates over time
