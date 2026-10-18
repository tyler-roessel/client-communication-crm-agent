import pytest

from src.client_ops.analyze import analyze_threads
from src.client_ops.integrations import build_integration_plan
from src.client_ops.normalize import normalize_communications


def communications(text, account="account-a", event="event-1"):
    return normalize_communications([{
        "account_id": account, "communication_id": event,
        "source": "email", "body": text,
    }])


@pytest.mark.parametrize("text", [
    "We do not want a proposal or pricing discussion.",
    "Our capital planning is complete.",
    "The integration is no longer blocked.",
    "Our API works well.",
    "No customer proof is needed.",
    "Onboarding went well.",
    "We do not need integration.",
    "Our integration is not required.",
    "The proposal is blocked on budget.",
    "There is no API issue.",
])
def test_non_actionable_language_does_not_advance_crm(text):
    analysis = analyze_threads(communications(text))
    assert analysis["signals"] == []
    assert analysis["crm"]["recommended_status"] == "no_change"


def test_resolved_clause_does_not_hide_a_separate_active_request():
    analysis = analyze_threads(communications(
        "The integration is no longer blocked, but please send a proposal."
    ))
    assert analysis["signals"] == ["proposal_requested"]
    assert analysis["evidence"]["proposal_requested"] == ["please send a proposal"]


def test_resolution_and_negation_do_not_hide_independent_requests():
    assert analyze_threads(communications("SSO is resolved, and API mapping is blocked"))["signals"] == ["technical_blocker"]
    assert analyze_threads(communications("We don't need a proposal, please send pricing"))["signals"] == ["proposal_requested"]


def test_non_stage_signals_never_map_no_change_into_a_status_field():
    items = communications("Feedback: onboarding felt confusing.")
    plan = build_integration_plan(analyze_threads(items), items, ["salesforce", "hubspot", "attio", "warehouse"])
    assert plan["writes"]
    for write in plan["writes"]:
        assert "no_change" not in write["payload"].values()
        assert "recommended_status" not in write["field_map"].values()


def test_analysis_from_another_account_cannot_be_attached_to_this_account():
    first = communications("Please send pricing.", account="account-a")
    second = communications("Please send pricing.", account="account-b")
    with pytest.raises(ValueError, match="does not match"):
        build_integration_plan(analyze_threads(first), second)


def test_normalization_analysis_and_mapping_are_account_aware_and_repeatable():
    items = communications("Please send pricing.")
    analysis = analyze_threads(items)
    first = build_integration_plan(analysis, items, ["attio"])
    assert first == build_integration_plan(analysis, items, ["attio"])
    other = communications("Please send pricing.", account="account-b")
    second = build_integration_plan(analyze_threads(other), other, ["attio"])
    assert first["writes"][0]["external_id"] != second["writes"][0]["external_id"]
    assert first["writes"][0]["account_id"] == "account-a"
    assert first["adapter_only"] is True


def test_same_day_events_have_distinct_ids_and_order_does_not_change_a_batch():
    one = communications("Please send pricing.", event="one")
    two = communications("Please send pricing.", event="two")
    def identifier(items):
        return build_integration_plan(analyze_threads(items), items)["writes"][0]["external_id"]
    assert identifier(one) != identifier(two)
    assert identifier(one + two) == identifier(two + one)
    assert build_integration_plan(analyze_threads(one + two), one + two) == build_integration_plan(
        analyze_threads(two + one), two + one,
    )


def test_destination_aliases_are_deduplicated_and_empty_selection_stays_empty():
    items = communications("Please send pricing.")
    analysis = analyze_threads(items)
    assert len(build_integration_plan(analysis, items, ["sfdc", "salesforce"])["writes"]) == 1
    assert build_integration_plan(analysis, items, [])["writes"] == []


def test_missing_identity_holds_and_mixed_accounts_are_rejected():
    missing = normalize_communications([{"body": "Please send pricing."}])
    plan = build_integration_plan(analyze_threads(missing), missing)
    assert plan["writes"] == []
    assert plan["hold_reason"] == "missing_account_identity"
    mixed = communications("Please send pricing.") + communications("Please send pricing.", account="b")
    with pytest.raises(ValueError, match="exactly one account"):
        build_integration_plan(analyze_threads(mixed), mixed)


def test_no_signal_has_no_mapping_and_unknown_destinations_are_explicit_errors():
    items = communications("Thanks.")
    analysis = analyze_threads(items)
    assert build_integration_plan(analysis, items)["writes"] == []
    with pytest.raises(ValueError, match="unsupported destination"):
        build_integration_plan(analysis, items, ["unknown-vendor"])


@pytest.mark.parametrize("raw", [{}, [None], [{"body": 42}], [{"body": "Hi", "account_id": []}]])
def test_malformed_input_is_rejected(raw):
    with pytest.raises(ValueError):
        normalize_communications(raw)


def test_empty_communications_are_not_converted_into_crm_activity():
    items = normalize_communications([{"body": "  "}])
    analysis = analyze_threads(items)
    assert items == []
    assert analysis["crm"]["recommended_status"] == "no_change"
    assert build_integration_plan(analysis, items, account_id="a")["writes"] == []
