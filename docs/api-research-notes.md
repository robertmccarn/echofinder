# API Research Notes

## Spotify Web API
- **Strength:** The gold standard for catalog, user libraries, and playback.
- **Constraint (2026):** Restricted access to `recommendations` and `related-artists` endpoints.
- **Strategy:** Use Spotify primarily for **Artist Resolution** (finding the right name/ID) and **User Context** (top artists).

## MusicBrainz API
- **Strength:** Deep historical data, "Begin Dates," and release groups.
- **Constraint:** Slower API, strict rate limits (1 request per second).
- **Strategy:** Must be queried in the background and cached heavily in our PostgreSQL database. Use MBIDs (MusicBrainz IDs) as our primary internal unique identifier.

## Last.fm API
- **Strength:** Exceptional "Similar Artist" graph and granular user-generated tags (e.g., "midwest emo," "literate songwriting").
- **Constraint:** Similarity match scores are relative and need normalization.
- **Strategy:** Use `artist.getSimilar` as the primary discovery engine and `artist.getTopTags` to build the "Sound DNA."

## The "Emergence" Challenge
Defining when an artist "emerged" is difficult. 
- **Method A:** First release date (MusicBrainz).
- **Method B:** "Begin Date" (MusicBrainz).
- **Method C:** First "Verified Activity" (e.g., first Last.fm scrobble or first playlist addition).
- **EchoFinder Strategy:** We combine Method A and B, using 2012 as a rough cutoff for the "Legacy" vs. "Modern" boundary in our prototype.
