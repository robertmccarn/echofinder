# Emergence Year Resolution Rules

EchoFinder resolves an artist emergence year before classification so the Modern Echo window is enforced consistently.

## Window

- Default modern window: last `5` years.
- API override: `modern_window_years` query parameter.
- Current implementation accepts `0` to `20` years.
- Window is inclusive: an emergence year equal to `current_year - modern_window_years` is considered modern.

## Resolution Order

EchoFinder checks fields in this order and uses the first valid year:

1. `first_known_year`
2. `emergence_year`
3. `debut_year`
4. `formed_year`

Accepted formats:

- integer year (for example `2022`)
- numeric string year (for example `"2022"`)
- free text containing a year value (for example `"debuted in 2022"`)

Invalid years are ignored (before 1900 or more than one year ahead of the current year).

## Fallback Behavior

- If the primary field is missing/invalid, fallback fields are attempted in order.
- If no valid year is found, emergence is unresolved and the candidate is treated as non-modern.

## API Explanation Fields

Each recommendation includes:

- `emergence_year`: resolved year or `null`
- `emergence_resolution.source_field`: field that provided the resolved year
- `emergence_resolution.fallback_used`: whether a non-primary field was used
- `emergence_resolution.is_modern_window`: whether year is inside configured window
- `emergence_resolution.window_start_year`
- `emergence_resolution.window_end_year`
- `emergence_resolution.note`: `resolved` or `unresolved_year`
