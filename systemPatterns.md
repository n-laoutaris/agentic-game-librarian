# System Patterns: Game Library Recommender System

## Agent-Managed Architecture
- **Modular Design:** System is composed of independent modules (e.g., Data Ingestion, Preference Manager, Recommendation Engine) that communicate via well-defined interfaces.

## Core Operating Directives (The Prime Directive)

- You are Autonomous: You can use your tools to perform basic file edits, data corrections, or logic updates. If the user makes a request that is not covered by a specific Skill, use your native tools to fulfill it.
- Fluid Data Structures: The JSON and Markdown files in this project are living documents. You have full authorization to add new fields, arrays, or keys to library.json or user_profile.json on the fly to capture nuanced user data.
- The User is the Source of Truth: If the user states a fact that contradicts external API data (e.g., "I have 50 hours in Divinity, even if Steam says 0"), the user is always right. Mutate the database to reflect their reality, perhaps by creating a "manual_overrides" field.

## Data Storage and Retrieval
- **Game Data:** Stored locally in a structured format (e.g., JSON, SQLite) for efficient querying.
- **User Preferences:** Stored persistently, updated with each interaction, enabling personalized recommendations.

## Recommendation Logic
- **Mood-Based Filtering:** Initial filtering of games based on user-provided mood (e.g., 'relaxing', 'exciting').
- **Preference-Based Scoring:** Ranking of mood-filtered games using user historical data (e.g., genre preferences, past ratings).
- **Hybrid Approach:** Combination of content-based filtering (game attributes) and collaborative filtering (user behavior) for robust recommendations.

## Interaction Patterns
- **Prompt-Response:** User provides mood/preferences, system responds with recommendations.
- **Feedback Loop:** User feedback on recommendations (e.g., likes/dislikes) is used to refine future suggestions and update preferences.

## Error Handling and Resilience
- **Graceful Degradation:** System should provide basic recommendations even if external data sources are unavailable.
- **Logging:** Comprehensive logging for debugging and performance monitoring.

## Security Considerations
- **Local Data Storage:** Emphasize secure local storage for user preferences and sensitive data.
- **Input Sanitization:** Validate and sanitize all user inputs to prevent injection attacks.
