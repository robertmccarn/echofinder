# Learning Goals

EchoFinder is designed as a curriculum-based project. As you build it, focus on these core competencies:

## 1. Full-Stack Architecture
- **Goal:** Understand how data flows from a raw API call to a React component.
- **Focus:** Separation of concerns between scripts (research), the backend (logic/storage), and the frontend (UI).

## 2. API Integration & Data Wrangling
- **Goal:** Handle multiple, sometimes conflicting, data sources.
- **Focus:** 
    - **Spotify:** OAuth flows and catalog search.
    - **MusicBrainz:** Parsing complex XML/JSON for historical data.
    - **Last.fm:** Leveraging community-driven tags for similarity.

## 3. Database Modeling
- **Goal:** Design a schema that supports complex discovery.
- **Focus:** Using PostgreSQL to cache external data and eventually using `pgvector` for similarity searches.

## 4. Algorithmic Thinking (The Echo Score)
- **Goal:** Build a "transparent" recommendation engine.
- **Focus:** Instead of a "black box" algorithm, we write explicit logic that we can explain to the user (e.g., "Recommended because of shared 'Literate Storytelling' tags").

## 5. Modern Frontend Development
- **Goal:** Build a responsive, "music-tech" aesthetic.
- **Focus:** Mastering Tailwind CSS for dark-mode native designs and TypeScript for type-safe data handling.
