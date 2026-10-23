import argparse
import json
from pathlib import Path

from .analyze import analyze_threads
from .integrations import build_integration_plan
from .normalize import normalize_communications
from .render import render_action_brief, render_crm_updates, render_integration_plan


def main():
    parser = argparse.ArgumentParser(description="Turn client calls/emails/notes into action notes and CRM recommendations.")
    parser.add_argument("--input", default="examples/client-communications.json")
    parser.add_argument("--mode", choices=("brief", "crm", "integrations"), default="brief")
    parser.add_argument("--account-id", help="Explicit account identity for a single-account input file.")
    parser.add_argument("--destination", action="append", help="Mapping destination; repeat to preview multiple systems.")
    args = parser.parse_args()

    raw = json.loads(Path(args.input).read_text())
    communications = normalize_communications(raw)
    analysis = analyze_threads(communications)
    if args.mode == "integrations":
        print(render_integration_plan(build_integration_plan(
            analysis, communications, args.destination, account_id=args.account_id,
        )))
    elif args.mode == "crm":
        print(render_crm_updates(analysis))
    else:
        print(render_action_brief(analysis))


if __name__ == "__main__":
    main()
