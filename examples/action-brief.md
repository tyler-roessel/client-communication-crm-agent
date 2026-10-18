# Client Communication Action Brief

## Review summary
- Analysis: deterministic rules; human review required.
- Recommended CRM status: `proposal_requested`.
- Write mode: `recommendation_only` until a human or approved automation commits the change.

## Next Steps
- sales: Clarify pricing, package next step, and send proposal-ready summary.
  Evidence: We are ready for proposal if pricing is clarified and the rollout plan is concrete
- engineering: Confirm technical owner, unblock requirements, and define integration path.
  Evidence: The integration is blocked until we understand the SSO and API mapping requirements
- marketing: Attach relevant proof, case study, or reference narrative.
  Evidence: They asked for customer proof, launch messaging support, and a clearer onboarding handoff
- marketing: Prepare launch/messaging support and assign content owner.
  Evidence: They asked for customer proof, launch messaging support, and a clearer onboarding handoff
- customer_success: Convert feedback into onboarding improvement and client-facing recovery note.
  Evidence: Feedback: the first onboarding pass felt too generic for how our team actually works

## Team Handoffs
- sales
  - pricing_or_proposal: Review client signal `proposal_requested` and confirm owner, deadline, and closure criteria.
- marketing
  - proof_or_messaging: Review client signal `customer_proof_needed` and confirm owner, deadline, and closure criteria.
  - proof_or_messaging: Review client signal `launch_or_messaging` and confirm owner, deadline, and closure criteria.
- engineering
  - technical_blocker: Review client signal `technical_blocker` and confirm owner, deadline, and closure criteria.
- customer_success
  - client_feedback: Review client signal `onboarding_feedback` and confirm owner, deadline, and closure criteria.

## Feedback Loop
- technical_blocker: Add this pattern to future qualification, onboarding, or handoff checks.
- customer_proof_needed: Add this pattern to future qualification, onboarding, or handoff checks.
- onboarding_feedback: Add this pattern to future qualification, onboarding, or handoff checks.
