"""Build illustrative mapping plans only; these are not vendor API requests."""

import hashlib
import json
from .context import source_digest


SYSTEM_ALIASES = {
    "sales force": "salesforce",
    "salesforce": "salesforce",
    "sfdc": "salesforce",
    "hubspot": "hubspot",
    "attio": "attio",
    "crm": "generic_crm",
    "gong": "gong",
    "gong.io": "gong",
    "database": "warehouse",
    "warehouse": "warehouse",
    "client ops db": "warehouse",
}

NAMING_CONVENTIONS = {
    "objects": "singular_snake_case",
    "fields": "snake_case",
    "crm_status": "snake_case",
    "external_id": "sha256(account_id + canonical communication identities)",
    "handoff_keys": "team.reason.status",
}

DESTINATION_CONTRACTS = {
    "salesforce": {
        "object": "opportunity",
        "operation": "upsert",
        "id_field": "external_account_key",
        "field_map": {
            "StageName": "recommended_status",
            "NextStep": "next_step_summary",
            "Description": "evidence_summary",
        },
    },
    "hubspot": {
        "object": "deal",
        "operation": "upsert",
        "id_field": "external_account_key",
        "field_map": {
            "dealstage": "recommended_status",
            "next_step": "next_step_summary",
            "notes_last_contacted": "evidence_summary",
        },
    },
    "attio": {
        "object": "company",
        "operation": "upsert",
        "id_field": "external_account_key",
        "field_map": {
            "client_status": "recommended_status",
            "next_action": "next_step_summary",
            "last_client_signal": "evidence_summary",
        },
    },
    "generic_crm": {
        "object": "account",
        "operation": "upsert",
        "id_field": "external_account_key",
        "field_map": {
            "client_status": "recommended_status",
            "next_step": "next_step_summary",
            "last_signal": "evidence_summary",
        },
    },
    "gong": {
        "object": "call_transcript",
        "operation": "attach_note",
        "id_field": "call_external_id",
        "field_map": {
            "call_summary": "evidence_summary",
            "follow_up_items": "next_step_summary",
            "crm_status_recommendation": "recommended_status",
        },
    },
    "warehouse": {
        "object": "client_communication_event",
        "operation": "insert",
        "id_field": "event_external_id",
        "field_map": {
            "source": "source",
            "speaker": "speaker",
            "text": "text",
            "detected_signals": "signals",
            "recommended_status": "recommended_status",
        },
    },
}


def normalize_system_name(name):
    return SYSTEM_ALIASES.get(name.strip().lower(), name.strip().lower().replace(" ", "_"))


def build_integration_plan(analysis, communications, requested_systems=None, *, account_id=None):
    if analysis.get("source_digest") != source_digest(communications):
        raise ValueError("analysis does not match the supplied source records")
    if account_id is not None and (not isinstance(account_id, str) or not account_id.strip()):
        raise ValueError("account_id must be a non-empty string")
    supplied_ids = {item["account_id"] for item in communications if item.get("account_id")}
    if account_id:
        supplied_ids.add(account_id)
    if len(supplied_ids) > 1:
        raise ValueError("one integration plan must contain exactly one account")
    selected_account = next(iter(supplied_ids), None)
    if selected_account and (not isinstance(selected_account, str) or not selected_account.strip()):
        raise ValueError("account_id must be a non-empty string")
    # An explicit batch-level ID can supply identity for legacy inputs.
    identity_complete = bool(selected_account) and (
        bool(account_id) or all(item.get("account_id") == selected_account for item in communications)
    )
    systems = requested_systems if requested_systems is not None else _infer_destinations(analysis, communications)
    communications = sorted(communications, key=lambda item: tuple(
        item.get(key, "") for key in ("timestamp", "communication_id", "source", "speaker", "text")
    ))
    writes = []
    seen_systems = set()
    for system in systems:
        normalized = normalize_system_name(system)
        if normalized not in DESTINATION_CONTRACTS:
            raise ValueError(f"unsupported destination: {system}")
        if normalized in seen_systems:
            continue
        seen_systems.add(normalized)
        contract = DESTINATION_CONTRACTS[normalized]
        if identity_complete and communications and analysis["signals"]:
            writes.append(_build_write(normalized, contract, analysis, communications, selected_account))

    return {
        "naming_conventions": NAMING_CONVENTIONS,
        "writes": writes,
        "adapter_only": True,
        "hold_reason": (
            "missing_account_identity" if not identity_complete else
            "no_communications" if not communications else
            "no_actionable_signals" if not analysis["signals"] else None
        ),
        "review_gate": {
            "mode": "recommendation_only",
            "required_before_write": ["human_approval", "valid_external_id", "evidence_present", "vendor_schema_validation", "explicit_target_record"],
        },
    }


def _infer_destinations(analysis, communications):
    destinations = ["generic_crm", "warehouse"]
    if any(item["source"] == "call" for item in communications):
        destinations.append("gong")
    return destinations


def _build_write(system, contract, analysis, communications, account_id):
    payload = _payload_for(contract, analysis, communications)
    return {
        "destination": system,
        "object": contract["object"],
        "operation": contract["operation"],
        "id_field": contract["id_field"],
        "account_id": account_id,
        "external_id": _external_id(communications, account_id=account_id),
        "field_map": {target: source for target, source in contract["field_map"].items() if target in payload},
        "payload": payload,
    }


def _payload_for(contract, analysis, communications):
    summary = _evidence_summary(analysis)
    next_steps = "; ".join(action["next_step"] for action in analysis["actions"])
    first = communications[0] if communications else {"source": "", "speaker": "", "text": ""}
    values = {
        "recommended_status": analysis["crm"]["recommended_status"],
        "next_step_summary": next_steps,
        "evidence_summary": summary,
        "source": first["source"],
        "speaker": first["speaker"],
        "text": first["text"],
        "signals": ", ".join(analysis["signals"]),
    }
    return {
        target: values[source] for target, source in contract["field_map"].items()
        if source != "recommended_status" or values[source] != "no_change"
    }


def _evidence_summary(analysis):
    lines = []
    for signal, evidence_items in analysis["evidence"].items():
        lines.append(f"{signal}: {evidence_items[0]}")
    return " | ".join(lines)


def _external_id(communications, *, account_id):
    """Stable recommendation ID, not an account, opportunity, or vendor record ID."""
    if not communications or not account_id:
        raise ValueError("account identity and communications are required")
    identities = []
    for item in communications:
        identity = {"source": item["source"]}
        if item.get("communication_id"):
            identity["communication_id"] = item["communication_id"]
        else:
            identity.update({key: item.get(key, "") for key in ("timestamp", "speaker", "text")})
        identities.append(json.dumps(identity, sort_keys=True, ensure_ascii=False))
    canonical = json.dumps(
        {"account_id": account_id, "communications": sorted(set(identities))},
        sort_keys=True, ensure_ascii=False,
    )
    return "recommendation:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()
