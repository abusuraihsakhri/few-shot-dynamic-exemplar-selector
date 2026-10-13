"""
Command-Line Interface for ExemplarSelector: Semantic Distance & Diversity Few-Shot Prompt Builder.
"""
import argparse
import csv
import json
import sys
from .models import FrontierPayload
from .agents import ExemplarCoordinator
from .selection import select_exemplars
from pathlib import Path

coordinator = ExemplarCoordinator()



def parse_csv_bool(value):
    """Interpret explicit CSV boolean values; reject ambiguous input."""
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in ("true", "1", "yes", "y"):
        return True
    if normalized in ("false", "0", "no", "n", ""):
        return False
    raise ValueError(f"Invalid is_critical_flag boolean: {value!r}")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="few-shot-dynamic-exemplar-selector", description="ExemplarSelector: Semantic Distance & Diversity Few-Shot Prompt Builder")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_select = subparsers.add_parser("select", help="Choose few-shot examples using lexical TF-IDF + MMR")
    p_select.add_argument("--query", required=True, help="Query to match")
    p_select.add_argument("--pool", required=True, help="JSON file containing an array of exemplar objects")
    p_select.add_argument("-k", type=int, default=3, help="Maximum number of examples (1-50)")
    p_select.add_argument("--diversity", type=float, default=0.65, help="MMR query relevance weight (0-1)")
    p_select.add_argument("--token-budget", type=int, default=None, help="Approximate character-based budget")
    p_select.add_argument("--domain", default=None, help="Optional exact domain filter")

    # Audit
    p_audit = subparsers.add_parser("audit", help="Run single task evaluation")
    p_audit.add_argument("--task-id", default="TASK-2026-001")
    p_audit.add_argument("--target", default="TARGET-GEN-01")
    p_audit.add_argument("--primary", type=float, default=29.4)
    p_audit.add_argument("--secondary", type=float, default=15.1)
    p_audit.add_argument("--critical", action="store_true")
    p_audit.add_argument("--status", default="DISCORDANT")

    # Chat
    p_chat = subparsers.add_parser("chat", help="System configuration query")
    p_chat.add_argument("query", nargs="+")

    # Batch
    p_batch = subparsers.add_parser("batch", help="Batch process CSV records")
    p_batch.add_argument("-i", "--input", required=True)
    p_batch.add_argument("-o", "--output", default="results.csv")

    # Serve
    p_serve = subparsers.add_parser("serve", help="Launch FastAPI REST server")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8000)

    args = parser.parse_args(argv)

    if args.command == "select":
        try:
            pool = Path(args.pool)
            if pool.stat().st_size > 2_000_000:
                raise ValueError("pool JSON file is too large (maximum 2 MB)")
            exemplars = json.loads(pool.read_text(encoding="utf-8"))
            result = select_exemplars(
                args.query, exemplars, k=args.k, diversity=args.diversity,
                token_budget=args.token_budget, domain=args.domain
            )
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            print(f"Selection error: {exc}", file=sys.stderr)
            return 2
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "audit":
        payload = FrontierPayload(
            task_id=args.task_id,
            target_identifier=args.target,
            primary_metric=args.primary,
            secondary_metric=args.secondary,
            status_descriptor=args.status,
            is_critical_flag=args.critical,
        )
        dossier = coordinator.process(payload)
        print("=" * 80)
        print(f"  EXEMPLARSELECTOR: SEMANTIC DISTANCE & DIVERSITY FEW-SHOT PROMPT BUILDER")
        print(f"  Domain: Autonomous Context Management & State Engines | Standard: Dynamic In-Context Learning Optimization")
        print(f"  Task: {dossier['task_id']} | Status: [{dossier['overall_status']}] | Total Alerts: {dossier['total_alerts']}")
        print("=" * 80)
        for a in dossier["alerts"]:
            print(f"\n  [{a['status']}] from {a['origin_agent']}:")
            print(f"  Summary: {a['summary']}")
            print(f"  Details: {a['technical_details']}")
            print(f"  Action:  {a['actionable_remediation']}")
        print("\n" + "=" * 80)
        return 0

    if args.command == "chat":
        ans = coordinator.query_supervisory_chat(" ".join(args.query))
        print(f"\n[ExemplarCoordinator]:\n{ans}\n")
        return 0

    if args.command == "batch":
        with open(args.input, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            fieldnames = list(reader.fieldnames or [])
            rows = list(reader)

        out_fields = fieldnames + ["overall_status", "total_alerts", "critical_count", "consensus_summary"]
        out_rows = []
        for r in rows:
            payload = FrontierPayload(
                task_id=r.get("task_id", "TASK-01"),
                target_identifier=r.get("target_identifier", "TARGET-01"),
                primary_metric=float(r.get("primary_metric", 15.0)),
                secondary_metric=float(r.get("secondary_metric", 5.0)),
                status_descriptor=r.get("status_descriptor", "NOMINAL"),
                is_critical_flag=parse_csv_bool(r.get("is_critical_flag", False)),
            )
            dossier = coordinator.process(payload)
            row_dict = dict(r)
            row_dict["overall_status"] = dossier["overall_status"]
            row_dict["total_alerts"] = dossier["total_alerts"]
            row_dict["critical_count"] = dossier["critical_count"]
            row_dict["consensus_summary"] = dossier["consensus_summary"]
            out_rows.append(row_dict)

        with open(args.output, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=out_fields)
            writer.writeheader()
            writer.writerows(out_rows)
        print(f"Processed {len(out_rows)} records -> {args.output}")
        return 0

    if args.command == "serve":
        try:
            import uvicorn
            from .server import create_app
            app = create_app()
            if app:
                print(f"Starting ExemplarSelector: Semantic Distance & Diversity Few-Shot Prompt Builder on http://{args.host}:{args.port}")
                uvicorn.run(app, host=args.host, port=args.port)
        except ImportError:
            print("FastAPI / uvicorn not installed. Run 'pip install fastapi uvicorn'")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
