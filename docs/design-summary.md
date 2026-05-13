# EchoFinder Design Summary

## Vision
To bridge the gap between "Nostalgic Taste" and "New Discovery." EchoFinder treats a user's love for legacy artists (e.g., *Death Cab for Cutie*, *Brand New*) as a map to find modern artists (e.g., *Phoebe Bridgers*, *Movements*) who share the same stylistic lineage.

## The "Modern Echo" Concept
A "Modern Echo" is an artist who:
1.  **Emerged recently:** Ideally within the last 5 years (max 10 for the prototype).
2.  **Shares DNA:** Has high stylistic overlap in tags, moods, and instrumentation.
3.  **Has Traction:** Is active (recent releases) but not necessarily "Mainstream."

## Scoring Components
The **Echo Score** is a composite metric:
- **Style Similarity (30%):** How well tags and genres align.
- **Scene Lineage (20%):** Cultural connection between the legacy seed and the new artist.
- **Current Activity (15%):** Evidence of releases or touring in the last 24 months.
- **Emergence (10%):** Bonus for being truly "new" (0–5 year window).
- **Traction (10%):** Filter to ensure the artist is professional/established enough to recommend.

## User Flow
1.  **Input:** User provides 1–3 "Legacy Anchors."
2.  **Analysis:** System builds a "Sound DNA" profile (e.g., *Literate, Emo-adjacent, Folk-rock textures*).
3.  **Discovery:** System crawls 1st and 2nd-degree similarity graphs.
4.  **Filtering:** Removes any artist that debuted before 2012–2015.
5.  **Ranking:** Applies the Echo Score and presents the top "Modern Echoes."
