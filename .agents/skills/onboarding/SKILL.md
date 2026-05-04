---
name: onboarding
description: Guides a new user through their first profile setup by analyzing library data, collecting PC hardware facts, and inferring play preferences through conversational reasoning.
---

# First-Run Onboarding Skill

## When to use this skill

Trigger this skill when:
- `database/user_profile.json` has empty `favorite_games` and an empty `persona` (first-run condition)
- User is interacting with the Game Library Agent for the first time
- `memory-bank/activeContext.md` does not contain a `profile_initialized: true` flag

## What this skill does

1. **Detects first-run state** by checking the user profile for empty preference signals
2. **Provides library context** by showing the user's top-played games from `database/library.json`
3. **Collects factual data** about PC hardware (CPU, GPU, RAM, OS, display, input devices)
4. **Engages in conversational prompts** to understand the user's current mood and play goals
5. **Infers preference signals** from natural language responses without explicit genre rankings
6. **Persists the profile** with initial preference data, experience notes, and onboarding completion status
7. **Marks onboarding complete** in the context for future skill runs

## Data inputs

- `database/library.json` — user's game library with playtime data
- `memory-bank/activeContext.md` — system context and state tracking

## Data outputs

- Updated `database/user_profile.json`. Store the results in whatever format you think is best for future recommendation tasks. Key sections to populate include:
  - `pc_build` facts from user input
  - `experience_notes` capturing onboarding reasoning
  - `implicit_signals` for preference inference
  - `recommendation_state` with current mood
- Updated `memory-bank/activeContext.md` with:
  - `profile_initialized: true`
  - reference to onboarding completion timestamp

## Conversation flow

### Step 1: Greeting & context
```
"Welcome! I see this is your first time here. Let me help you set up your profile.

I can see your Steam library has [N] games. Your top-played titles are:
1. [Game title] — [playtime] hours
2. [Game title] — [playtime] hours
...

We'll start by collecting a few facts about your setup, and then I'd like to understand what you enjoy playing."
```

### Step 2: PC build facts (conversational, not scripted)
Ask the user about their hardware:
- "What's your PC CPU and GPU?"
- "How much RAM do you have?"
- "What OS are you running?"
- "What input devices do you use? (keyboard, mouse, gamepad, etc.)"

Store responses in `pc_build` section.

### Step 3: Current mood & intent
```
"What kind of game would you want to play right now?"

```

Store in `recommendation_state.current_mood`.

### Step 4: Library feedback
```
"I noticed you've invested a lot of time in [top game]. 
 What did you enjoy most about it? What kept you coming back?"
```

Capture as experience notes for preference inference.

### Step 5: Avoidances (open-ended)
```
"Are there any game types, atmospheres, or mechanics you want to avoid right now?"
```

Store in `implicit_signals.avoid_signals`.

IMPORTANT: Do not ask all questions at once. Ask one question, wait for the user to respond, and then ask the next.

## Preference inference rules

The agent should reason about the user's preferences based on conversational inputs:

- **Explicit keywords** from user responses (e.g., "I love co-op", "horror makes me uncomfortable")
- **Library patterns** (e.g., top 5 games are all sci-fi → `sci-fi` genre signal)
- **Play behavior** (e.g., if one game has 1000 hours and others have <100 → user prefers deep, long-term progression)
- **Inverse signals** (e.g., "I'm tired of [genre]" → add to `avoid_signals`)

Store inferred signals in:
- `persona.preferred_play_style` — list of inferred play styles
- `favorite_genres.explicit_favorites` — genres mentioned or evident from library
- `favorite_genres.avoid_genres` — genres or themes user wants to avoid
- `implicit_signals.recent_interest_trends` — what the user is currently drawn to
- `experience_notes` — detailed reasoning from onboarding conversation

## Multi-platform readiness

- Store game identifiers as `source_id` format: `steam:12345`, `epic:xxxxx`, `gog:xxxxx`
- When building `favorite_games`, normalize source IDs from `database/library.json`

## Onboarding completion marker

After the conversation, update both:

1. **database/user_profile.json**: Add a completion note by running the script `scripts/update_user_profile_notes.py`.
2. **memory-bank/activeContext.md**: Mark as initialized by running the script `scripts/update_active_context.py`.

## Error handling & graceful fallbacks

- If library is empty or too small: provide minimal greeting and focus on hardware + current mood
- If user skips PC build questions: use defaults and note in experience_notes that hardware is unknown
- If user provides vague responses: use library data as primary preference source
- Future sessions can refine the profile with additional AI reasoning

## Related skills & future extensions

- **Recommendation engine** skill will use this onboarded profile to suggest games
- **Profile refinement** skill will accept natural language mood/preference updates over time
