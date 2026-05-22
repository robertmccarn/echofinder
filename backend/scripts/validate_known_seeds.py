"""
Known-seed validation runner for EchoFinder MVP.

Usage:
    python backend/scripts/validate_known_seeds.py

Checks:
- Canonical seed dataset exists and is executable.
- Recommendation response validates against the Pydantic contract.
- Each seed returns at least one recommendation overall.
- If Spotify credentials are configured, each seed returns non-empty modern echoes.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.models import RecommendationsResponse

DATASET_PATH = REPO_ROOT / "backend" / "tests" / "fixtures" / "known_seed_validation_set.json"


def _load_dataset() -> dict[str, Any]:
    with DATASET_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


def _has_credentials(group_name: str, groups: dict[str, list[str]]) -> bool:
    env_names = groups.get(group_name, [])
    if not env_names:
        return False
    return all(bool(os.getenv(name, "").strip()) for name in env_names)


def _validate_case(
    client: TestClient, case: dict[str, Any], credential_groups: dict[str, list[str]]
) -> list[str]:
    errors: list[str] = []
    seed = case["seed"]

    response = client.get("/api/recommendations", params={"seed": seed})
    if response.status_code != 200:
        return [f"{seed}: expected 200, got {response.status_code}"]

    body = response.json()

    if case.get("require_response_schema"):
        try:
            RecommendationsResponse.model_validate(body)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{seed}: response schema validation failed ({exc})")

    modern = body.get("modern_echoes", [])
    bridge = body.get("bridge_artists", [])

    if case.get("require_any_recommendations") and not (modern or bridge):
        errors.append(f"{seed}: expected non-empty recommendations (modern or bridge)")

    cred_group = case.get("require_non_empty_modern_if_credentials")
    if cred_group and _has_credentials(cred_group, credential_groups) and not modern:
        errors.append(
            f"{seed}: expected non-empty modern_echoes when '{cred_group}' credentials are configured"
        )

    return errors


def main() -> int:
    if not DATASET_PATH.exists():
        print(f"FAILED: dataset not found at {DATASET_PATH}")
        return 1

    dataset = _load_dataset()
    cases = dataset.get("cases", [])
    credential_groups = dataset.get("credential_groups", {})
    client = TestClient(app)

    print("Known-seed validation run")
    print(f"Dataset: {DATASET_PATH}")
    print(f"Cases: {len(cases)}")

    all_errors: list[str] = []
    for case in cases:
        seed = case.get("seed", "<unknown>")
        errors = _validate_case(client, case, credential_groups)
        if errors:
            print(f"[FAIL] {seed}")
            for err in errors:
                print(f"  - {err}")
            all_errors.extend(errors)
        else:
            print(f"[PASS] {seed}")

    if all_errors:
        print(f"\nKnown-seed validation FAILED ({len(all_errors)} issue(s)).")
        return 1

    print("\nKnown-seed validation PASSED.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
