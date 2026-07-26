#!/usr/bin/env python3
import datetime as dt
import json
import re
import sys
from pathlib import Path

EXPECTED_CATEGORIES = {
    "keep_going": 20,
    "early_days": 10,
    "restart": 10,
    "goal_reached": 10,
    "long_streak": 10,
}
ROOT_FIELDS = {"version", "updatedAt", "categories"}
MESSAGE_FIELDS = {"id", "message", "encouragement"}
ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*-\d{3}$")


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        root = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return [f"Invalid JSON: {error}"]

    if not isinstance(root, dict):
        return ["Root must be an object."]
    if set(root) != ROOT_FIELDS:
        errors.append(f"Root fields must be exactly: {sorted(ROOT_FIELDS)}")
    if root.get("version") != 1:
        errors.append("version must be 1.")
    try:
        dt.date.fromisoformat(root.get("updatedAt", ""))
    except (TypeError, ValueError):
        errors.append("updatedAt must use YYYY-MM-DD.")

    categories = root.get("categories")
    if not isinstance(categories, dict):
        return errors + ["categories must be an object."]
    if set(categories) != set(EXPECTED_CATEGORIES):
        errors.append(
            f"Categories must be exactly: {sorted(EXPECTED_CATEGORIES)}"
        )

    seen_ids: set[str] = set()
    for category, minimum in EXPECTED_CATEGORIES.items():
        messages = categories.get(category)
        if not isinstance(messages, list):
            errors.append(f"{category} must be an array.")
            continue
        if len(messages) < minimum:
            errors.append(f"{category} must contain at least {minimum} messages.")
        for index, item in enumerate(messages):
            location = f"{category}[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{location} must be an object.")
                continue
            if set(item) != MESSAGE_FIELDS:
                errors.append(
                    f"{location} fields must be exactly: {sorted(MESSAGE_FIELDS)}"
                )
                continue
            message_id = item["id"]
            message = item["message"]
            encouragement = item["encouragement"]
            if not isinstance(message_id, str) or not ID_PATTERN.fullmatch(message_id):
                errors.append(f"{location}.id has an invalid format.")
            elif message_id in seen_ids:
                errors.append(f"Duplicate id: {message_id}")
            else:
                seen_ids.add(message_id)
            if not isinstance(message, str) or not 20 <= len(message.strip()) <= 300:
                errors.append(f"{location}.message must have 20 to 300 characters.")
            if (
                not isinstance(encouragement, str)
                or not 3 <= len(encouragement.strip()) <= 80
            ):
                errors.append(
                    f"{location}.encouragement must have 3 to 80 characters."
                )

    return errors


if __name__ == "__main__":
    catalog_path = Path(sys.argv[1] if len(sys.argv) > 1 else "messages.json")
    validation_errors = validate(catalog_path)
    if validation_errors:
        for validation_error in validation_errors:
            print(f"ERROR: {validation_error}")
        raise SystemExit(1)
    print(f"OK: {catalog_path} is valid.")
