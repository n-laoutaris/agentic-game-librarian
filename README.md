# Agentic Game Librarian

An event-driven Agentic AI pipeline that syncs my fragmented game libraries, learns my hardware and habits and uses natural language to recommend the perfect game for my current mood.

[Placeholder for UI/Terminal Demo Image]

## The Problem

I am a gamer with a massive "backlog" of games, fragmented across multiple storefronts. Many were acquired during sales or claimed as free gifts, leaving me with a library so large, I rarely know what I actually own.

Scrolling through this catalog is a chore, especially when I only have 60 minutes to play or want to find a specific experience for a game night. Traditional storefront algorithms fail me because they rely on tags that capture mechanics, not mood. I needed a unified system that understands my immediate mood and recommends what I should play right now.

## The Solution

An Agentic AI application that acts as a personal librarian with direct access to my entire gaming library, enriched with metadata. It interviews me to learn my hardware constraints, typical session lengths and emotional preferences. By conversing in natural language, the agent learns my tastes over time, providing highly contextual, mood-based recommendations pulled directly from the games I already own.

## Features & Skills

Built on the **agentskills.io** framework.

- **Update Library Skill**: An ETL pipeline that reads Playnite's multi-store CSV export and transforms it into a clean file, enriched with full metadata. Includes taxonomy extraction to catalog all available genres, tags, and features.
- **Recommend Game Skill**: Interprets user mood and constructs intelligent filter queries against the library using the universal `--filter` interface (e.g., `--filter genre:RPG,Adventure`). Ranks recommendations using stored hardware constraints and preference memory.

## Core Architecture 

```mermaid
graph TD
    %% Define styles
    classDef agent fill:#f9f2f4,stroke:#333,stroke-width:2px;
    classDef python fill:#e8f4f8,stroke:#333,stroke-width:1px;
    classDef db fill:#f4f9f4,stroke:#333,stroke-width:1px;
    classDef external fill:#fff8e8,stroke:#333,stroke-width:1px;
    
    %% Nodes
    User([User])
    Agent{LLM Agent}:::agent
    Playnite[Playnite Multi-Store\nExport]:::external
    

    Normalize[Normalize CSV: Clean HTML, Parse Dates, Array Fields, Convert Times]:::python

    
    subgraph Database State
        Master[(Enriched Library)]:::db
        Profile[(User Profile)]:::db
    end

    %% Flow
    User -->|Prompt: What should I play?| Agent
    Playnite -->|Auto-Export| Normalize
    Normalize -->|Transforms & Cleans| Master
    
    Agent -->|Triggers Library Sync| Normalize
    Master -.->|Reads Context| Agent
    Profile -.->|Reads Preferences| Agent
    Agent -->|Contextual Recommendation| User
```

Initial architecture used custom Python ETL scripts querying the IGDB API. However, the pipeline was refactored to use Playnite as an automated background ETL agent, reducing custom codebase size by 60% while maintaining identical data output.

## Future Work

- **Profile-Aware Scoring**: Add optional relevance scoring to `filter_games.py` for agent-driven ranking without external API calls.
- **Linux Support**: Linux gaming is a thing now. Add ProtonDB compatibility detection to filter recommendations for Linux/Steam Deck users.
- **Deep Metadata Enrichment**: Integrate APIs for richer metadata, such as the Co-Optimus API (for exact local/online player counts) or HowLongToBeat (for session planning).
- **Mood Tracking**: Track recommendation patterns over time to identify seasonal preferences and improve future suggestions.
