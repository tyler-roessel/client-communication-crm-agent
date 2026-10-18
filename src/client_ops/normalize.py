PUBLIC_FIELDS = ("source", "speaker", "text", "timestamp")


def normalize_communications(raw_items):
    """Reduce calls, emails, and notes into a shared public-safe shape."""
    if not isinstance(raw_items, list):
        raise ValueError("communications must be a list of objects")
    normalized = []
    for item in raw_items:
        if not isinstance(item, dict):
            raise ValueError("each communication must be an object")
        text = item.get("text") or item.get("body") or item.get("notes") or item.get("transcript") or ""
        if not isinstance(text, str):
            raise ValueError("communication text must be a string")
        if not text.strip():
            continue
        record = {
            "source": str(item.get("source") or "unknown").strip(),
            "speaker": str(item.get("speaker") or item.get("from") or "Unknown").strip(),
            "text": " ".join(text.split()),
            "timestamp": str(item.get("timestamp") or "").strip(),
        }
        for field in ("account_id", "communication_id"):
            value = item.get(field)
            if value is not None:
                if not isinstance(value, str) or not value.strip():
                    raise ValueError(f"{field} must be a non-empty string")
                record[field] = value.strip()
        normalized.append(record)
    return normalized

