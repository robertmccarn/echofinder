# Echo Score v1 Model

EchoFinder's current MVP scoring path is a transparent weighted model implemented in `backend/app/scoring.py`.

This document describes the active score signals, weights, recommendation class rules, and confidence calculation used for API responses.

## Recommendation Classes

Score classification thresholds:

- `modern_echo`: candidate is in modern window and `echo_score >= 30.0`
- `bridge_artist`: candidate is outside modern window and `echo_score >= 20.0`
- `excluded`: candidate does not meet either threshold

Threshold constants:

- `MODERN_ECHO_MIN_SCORE = 30.0`
- `BRIDGE_MIN_SCORE = 20.0`

## Weighted Signal Model

The manual weighted model computes six component signals, then scales to a 0-100 score:

- `emotional_match` weight: `0.35`
- `scene_match` weight: `0.25`
- `lyrical_match` weight: `0.15`
- `production_match` weight: `0.10`
- `vocal_match` weight: `0.10`
- `emerging_bonus` weight: `0.05`

Weights sum to `1.0`.

Signal calculations:

- list-like fields use Jaccard overlap (`emotional_tones`, `lyrical_themes`)
- text-like fields use token-overlap Jaccard (`scene_lineage`, `production_style`, `vocal_style`)
- `emerging_bonus = 1.0` when the candidate is in the modern emergence window, else `0.0`

Score formula:

```text
raw = sum(component_i * weight_i)
echo_score = round(raw * 100, 1)
```

## Confidence

Confidence is derived from non-bonus dimensions only:

```text
confidence = weighted_non_bonus_sum / non_bonus_weight_sum
```

Where:

- `non_bonus_weight_sum = 0.95`
- `confidence` is rounded to 3 decimals
- `emerging_bonus` is excluded so confidence reflects similarity strength rather than recency boost

## Response Shape Example

Example recommendation card JSON (placeholder values):

```json
{
  "artist_name": "Example Artist",
  "classification": "modern_echo",
  "echo_score": 34.3,
  "confidence": 0.308,
  "emergence_type": "first_known_recent",
  "emergence_year": 2022,
  "emergence_resolution": {
    "source_field": "first_known_year",
    "fallback_used": false,
    "is_modern_window": true,
    "window_start_year": 2021,
    "window_end_year": 2026,
    "note": "resolved"
  },
  "shared_tags": [
    "emo",
    "indie rock"
  ],
  "shared_tag_weights": [
    {
      "tag": "emo",
      "weight": 0.5
    },
    {
      "tag": "indie rock",
      "weight": 0.5
    }
  ],
  "component_scores": {
    "emotional_match": 0.4,
    "scene_match": 0.27,
    "lyrical_match": 0.4,
    "production_match": 0.06,
    "vocal_match": 0.17,
    "emerging_bonus": 1.0
  },
  "sources": [
    "manual_pool"
  ],
  "source_note": "Example rationale from source data",
  "spotify_url": "",
  "image_url": "",
  "genres": []
}
```

