# Integration Routing Plan

Illustrative mappings only. No vendor requests are executed.
Hold reason: none; mapping preview only.

## Naming Conventions
- `objects`: `singular_snake_case`
- `fields`: `snake_case`
- `crm_status`: `snake_case`
- `external_id`: `sha256(account_id + canonical communication identities)`
- `handoff_keys`: `team.reason.status`

## Mapping Previews
- `generic_crm` `upsert` `account`
  - external_id: `recommendation:09d0aac6ce08e8bf02a72debb21a039ce628105b584288947c781044e948cfb2`
  - id_field: `external_account_key`
  - fields: client_status, next_step, last_signal
- `warehouse` `insert` `client_communication_event`
  - external_id: `recommendation:09d0aac6ce08e8bf02a72debb21a039ce628105b584288947c781044e948cfb2`
  - id_field: `event_external_id`
  - fields: source, speaker, text, detected_signals, recommended_status
- `gong` `attach_note` `call_transcript`
  - external_id: `recommendation:09d0aac6ce08e8bf02a72debb21a039ce628105b584288947c781044e948cfb2`
  - id_field: `call_external_id`
  - fields: call_summary, follow_up_items, crm_status_recommendation

## Review Gate
- mode: `recommendation_only`
- required_before_write: human_approval, valid_external_id, evidence_present, vendor_schema_validation, explicit_target_record
