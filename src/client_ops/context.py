"""Bind derived analysis to its exact normalized source records."""

import hashlib
import json


def source_digest(communications):
    records = [json.dumps(item, sort_keys=True, ensure_ascii=False) for item in communications]
    return hashlib.sha256(json.dumps(sorted(records), ensure_ascii=False).encode()).hexdigest()
