from .route import route_handoffs


def render_action_brief(analysis):
    lines = [
        "# Client Communication Action Brief",
        "",
        "## Review summary",
        "- Analysis: deterministic rules; human review required.",
        f"- Recommended CRM status: `{analysis['crm']['recommended_status']}`.",
        f"- Write mode: `{analysis['crm']['write_mode']}` until a human or approved automation commits the change.",
        "",
        "## Next Steps",
    ]

    for action in analysis["actions"]:
        lines.append(f"- {action['owner_team']}: {action['next_step']}")
        lines.append(f"  Evidence: {action['evidence']}")

    lines.extend(["", "## Team Handoffs"])
    routed = route_handoffs(analysis)
    for team, handoffs in routed.items():
        if not handoffs:
            continue
        lines.append(f"- {team}")
        for handoff in handoffs:
            lines.append(f"  - {handoff['reason']}: {handoff['handoff_note']}")

    lines.extend(["", "## Feedback Loop"])
    if analysis["feedback_loop"]:
        for item in analysis["feedback_loop"]:
            lines.append(f"- {item['source_signal']}: {item['process_update']}")
    else:
        lines.append("- No durable feedback-loop update from this sample.")

    return "\n".join(lines) + "\n"


def render_crm_updates(analysis):
    crm = analysis["crm"]
    lines = [
        "# CRM Status Change Recommendations",
        "",
        f"- Recommended status: `{crm['recommended_status']}`",
        f"- Reason: {crm['reason']}",
        f"- Write mode: `{crm['write_mode']}`",
        "",
        "## Field Mapping",
        "- `last_client_signal`: strongest evidence line from the latest call/email/note.",
        "- `next_step_owner_team`: team responsible for the next action.",
        "- `client_status`: recommended stage/status after review.",
        "- `feedback_loop_notes`: reusable process improvements learned from the interaction.",
    ]
    return "\n".join(lines) + "\n"


def render_integration_plan(plan):
    lines = [
        "# Integration Routing Plan",
        "",
        "Illustrative mappings only. No vendor requests are executed.",
        f"Hold reason: {plan.get('hold_reason') or 'none; mapping preview only'}.",
        "",
        "## Naming Conventions",
    ]
    for key, value in plan["naming_conventions"].items():
        lines.append(f"- `{key}`: `{value}`")

    lines.extend(["", "## Mapping Previews"])
    for write in plan["writes"]:
        lines.append(f"- `{write['destination']}` `{write['operation']}` `{write['object']}`")
        lines.append(f"  - external_id: `{write['external_id']}`")
        lines.append(f"  - id_field: `{write['id_field']}`")
        lines.append(f"  - fields: {', '.join(write['payload'].keys())}")

    gate = plan["review_gate"]
    lines.extend(
        [
            "",
            "## Review Gate",
            f"- mode: `{gate['mode']}`",
            f"- required_before_write: {', '.join(gate['required_before_write'])}",
        ]
    )
    return "\n".join(lines) + "\n"
