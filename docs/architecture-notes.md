# Architecture Notes

> **Note on Implementation Status:** This document captures earlier architecture thinking. For the implemented vs. planned status of these systems, refer to the [Current Architecture](./current-architecture.md) document.

## Overview
EchoFinder follows a decoupled architecture, separating the long-running data enrichment tasks from the user-facing API.

## Layered Design

### 1. Data Layer (Planned/Future)
- **Artists Table:** A local cache of metadata to avoid hitting API rate limits.
- **Signals Table:** Stores time-series data (releases, tour dates) used for the "Activity" score.
- **pgvector (Future):** Will allow us to store artist "Embeddings" for lightning-fast similarity lookups.

### 2. Service Layer (Implementation in progress)
- **Scoring Engine:** The logic that combines signals into the Echo Score.
- **Integrators:** Specialized classes for each external API (Spotify, MB, Last.fm).
- **Background Tasks (Future):** Using a task queue (like Celery) to fetch MusicBrainz data without blocking the UI.

### 3. Frontend Layer (Planned/Future)
- **State Management:** Using React hooks and potentially TanStack Query for data fetching.
- **Design System:** Tailwind CSS with a custom palette (Near Black, Electric Violet, Signal Teal).

## Key Decisions
- **Why MusicBrainz?** Spotify's release dates can be unreliable for "Emergence" (re-releases, remasters). MusicBrainz provides a more accurate "Begin Date."
- **Why Last.fm?** Last.fm tags are richer and more descriptive of "vibes" than Spotify's broad genre categories.
- **No Heavy Audio Analysis:** For the MVP, we are relying on **Metadata DNA** (tags, lineage) rather than processing raw audio files, as it is faster and more explainable.
