"""Bind derived analysis to its exact normalized source records."""

import hashlib
import json
from datetime import datetime


def source_digest(communications):
    records = [json.dumps(item, sort_keys=True, ensure_ascii=False) for item in communications]
    return hashlib.sha256(json.dumps(sorted(records), ensure_ascii=False).encode()).hexdigest()


def communication_sort_key(item):
    """Prefer the latest known instant; undated records have a stable fallback."""
    instant = float("-inf")
    try:
        parsed = datetime.fromisoformat(item.get("timestamp", "").replace("Z", "+00:00"))
        if parsed.tzinfo is not None:
            instant = parsed.timestamp()
    except (ValueError, TypeError, OverflowError):
        pass
    return (instant, *(item.get(key, "") for key in ("communication_id", "source", "speaker", "text")))
