"""Conservative rules for a local reference sample; no model inference occurs."""

import re


SIGNAL_RULES = {
    "proposal_requested": ("proposal", "pricing", "commercial terms", "ready to move"),
    "technical_blocker": ("blocked", "blocker", "api", "integration", "sso", "data mapping"),
    "customer_proof_needed": ("case study", "case studies", "reference", "proof", "roi"),
    "onboarding_feedback": ("feedback", "onboarding", "confusing", "generic", "handoff"),
    "launch_or_messaging": ("launch", "messaging", "announcement", "positioning"),
}

TEAM_BY_SIGNAL = {
    "proposal_requested": "sales",
    "technical_blocker": "engineering",
    "customer_proof_needed": "marketing",
    "onboarding_feedback": "customer_success",
    "launch_or_messaging": "marketing",
}

REASON_BY_SIGNAL = {
    "proposal_requested": "pricing_or_proposal",
    "technical_blocker": "technical_blocker",
    "customer_proof_needed": "proof_or_messaging",
    "onboarding_feedback": "client_feedback",
    "launch_or_messaging": "proof_or_messaging",
}


def analyze_threads(communications):
    account_ids = {item["account_id"] for item in communications if item.get("account_id")}
    if len(account_ids) > 1:
        raise ValueError("one analysis must contain exactly one account")
    signals = []
    evidence_by_signal = {}

    for item in sorted(communications, key=lambda item: tuple(
        item.get(key, "") for key in ("timestamp", "communication_id", "source", "speaker", "text")
    )):
        for clause in re.split(r"[.!?;]+|\bbut\b|\bhowever\b", item["text"], flags=re.IGNORECASE):
            clause = clause.strip()
            if not clause:
                continue
            for signal, keywords in SIGNAL_RULES.items():
                if _is_active_signal(clause, signal, keywords):
                    if signal not in signals:
                        signals.append(signal)
                    evidence_by_signal.setdefault(signal, []).append(clause)

    actions = [_action_for_signal(signal, evidence_by_signal[signal][0]) for signal in signals]
    handoffs = [_handoff_for_signal(signal, evidence_by_signal[signal][0]) for signal in signals]
    feedback_loop = _feedback_loop(signals, evidence_by_signal)
    crm = _crm_recommendation(signals)

    return {
        "signals": signals,
        "actions": actions,
        "handoffs": handoffs,
        "feedback_loop": feedback_loop,
        "crm": crm,
        "evidence": evidence_by_signal,
        "analysis_method": "deterministic_rules",
        "needs_human_review": True,
    }


def _is_active_signal(clause, signal, keywords):
    text = clause.lower().replace("’", "'")
    matches = list(re.finditer(r"\b(?:" + "|".join(re.escape(word) for word in keywords) + r")\b", text))
    if not matches:
        return False
    if signal == "technical_blocker":
        if re.search(r"\b(no longer (?:blocked|stuck|waiting)|not blocked|unblocked|resolved|fixed|complete(?:d)?|no (?:remaining )?blockers?)\b", text):
            return False
        if re.search(r"\b(?:no|don't|doesn't|do not|does not)\s+(?:need\s+)?(?:new\s+)?(?:api|integration|sso|data mapping)\b|\b(?:api|integration|sso|data mapping)\s+(?:is\s+)?not\s+(?:needed|required)\b", text):
            return False
        technical_topic = re.search(r"\b(api|integration|sso|data mapping|technical)\b", text)
        open_concern = re.search(r"\b(blocked|blocker|unclear|unresolved|waiting|cannot|can't|need|needs|required|requirements|issue|problem|error)\b", text)
        return bool(technical_topic and open_concern)
    # Negation is scoped to a clause and must precede the matched topic.
    active = [
        match for match in matches
        if not re.search(r"\b(no|not|never|without|don't|doesn't|didn't|won't|no longer)\b", text[:match.start()])
    ]
    if not active:
        return False
    request = re.search(r"\b(need|needs|want|wants|request|requested|send|share|ready|clarified|clarify|please|asked|discuss|waiting)\b|\b(?:can|could) you\b", text)
    if signal == "onboarding_feedback":
        return bool(re.search(r"\b(feedback|confusing|generic|friction|problem)\b", text))
    return bool(request)


def _action_for_signal(signal, evidence):
    team = TEAM_BY_SIGNAL[signal]
    action_by_signal = {
        "proposal_requested": "Clarify pricing, package next step, and send proposal-ready summary.",
        "technical_blocker": "Confirm technical owner, unblock requirements, and define integration path.",
        "customer_proof_needed": "Attach relevant proof, case study, or reference narrative.",
        "onboarding_feedback": "Convert feedback into onboarding improvement and client-facing recovery note.",
        "launch_or_messaging": "Prepare launch/messaging support and assign content owner.",
    }
    return {"owner_team": team, "next_step": action_by_signal[signal], "evidence": evidence}


def _handoff_for_signal(signal, evidence):
    return {
        "team": TEAM_BY_SIGNAL[signal],
        "reason": REASON_BY_SIGNAL[signal],
        "evidence": evidence,
        "handoff_note": f"Review client signal `{signal}` and confirm owner, deadline, and closure criteria.",
    }


def _feedback_loop(signals, evidence_by_signal):
    loop = []
    for signal in signals:
        if signal in {"onboarding_feedback", "technical_blocker", "customer_proof_needed"}:
            loop.append(
                {
                    "type": "feedback",
                    "source_signal": signal,
                    "learning": evidence_by_signal[signal][0],
                    "process_update": "Add this pattern to future qualification, onboarding, or handoff checks.",
                }
            )
    return loop


def _crm_recommendation(signals):
    if "proposal_requested" in signals:
        status = "proposal_requested"
        reason = "Client asked for pricing/proposal movement."
    elif "technical_blocker" in signals:
        status = "technical_review"
        reason = "Client progress depends on engineering clarification."
    elif "customer_proof_needed" in signals:
        status = "proof_requested"
        reason = "Client needs confidence material before advancing."
    else:
        status = "no_change"
        reason = "No supported stage-change signal; review the source before updating CRM."

    return {
        "recommended_status": status,
        "reason": reason,
        "write_mode": "recommendation_only",
    }

