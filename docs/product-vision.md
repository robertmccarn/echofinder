# Product Vision

EchoFinder helps listeners turn nostalgic taste into current discovery.

The core product question is:

> If I love this older artist, genre, or scene, who is carrying that sound forward now?

## Intended Users

EchoFinder is for listeners who:

- Have older favorite artists or bands.
- Want newer artists without losing the musical DNA they care about.
- Prefer explainable recommendations over black-box discovery.
- Want results that distinguish new discoveries from lineage context.

## Core Concepts

Legacy artists are older favorite artists or bands that anchor the search.

Modern Echoes are newer artists, preferably emerging within the last 0-5 years, that share tags, genre language, mood, scene lineage, or other explainable signals with a legacy seed.

Bridge Artists are older or non-emerging artists that help explain lineage. They may be good recommendations, but they are not the primary "new artist" promise.

## Discovery Inputs

The intended product supports three entry paths:

- Specific legacy artist or band.
- Genre.
- Scene or lineage.

The backend-first MVP should begin with a single legacy artist seed, then expand once the response contract and scoring logic are stable.

## Spotify-Centered Direction

EchoFinder is Spotify-centered because Spotify is the expected user account and listening context. Spotify login, library import, and playlist creation are planned capabilities.

Current repository state does not yet implement Spotify login, user-library import, playlist creation, or a frontend. Documentation and issues should describe those as planned until they exist and are validated.

## Truthful Recommendation Rules

EchoFinder should:

- Separate Modern Echoes from Bridge Artists.
- Explain why each artist was recommended.
- Prefer newer artists within a 0-5 year emergence window.
- Show source transparency, including manual candidate pool matches.
- Return empty or partial results honestly when signals are missing.
- Avoid inventing artists, metadata, traction, or source confidence.

## Initial Seeds

The current prototype uses these seed examples:

- Manchester Orchestra
- Thrice
- The Decemberists
