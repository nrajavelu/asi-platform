"""Command-line entry point for the ASI Platform POC.

    python cli.py list                 # cases available -- no key needed
    python cli.py analyze ev           # full pipeline for one case
    python cli.py analyze ev -q "..."  # with a custom question
    python cli.py serve                # start the HTTP API on :8000
"""
import argparse
import json
import sys

from cases import CASES, list_cases


def cmd_list(_args):
    for c in list_cases():
        print(f"{c['id']:>4}  {c['name']:<24} {c['tag']}")


def cmd_analyze(args):
    from benchmark import run

    if args.case not in CASES:
        print(f"unknown case {args.case!r}. Run `python cli.py list` to see valid ids.", file=sys.stderr)
        sys.exit(1)
    print(json.dumps(run(args.case, args.question), indent=2, default=str))


def cmd_serve(args):
    import uvicorn

    uvicorn.run("server:app", host="127.0.0.1", port=args.port, reload=args.reload)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="list available case corpora").set_defaults(func=cmd_list)

    p_analyze = sub.add_parser("analyze", help="run the full pipeline for one case")
    p_analyze.add_argument("case", help="case id, e.g. ev, nw, mh, vx, cu")
    p_analyze.add_argument("-q", "--question", default=None, help="override the case's default question")
    p_analyze.set_defaults(func=cmd_analyze)

    p_serve = sub.add_parser("serve", help="start the HTTP API")
    p_serve.add_argument("--port", type=int, default=8000)
    p_serve.add_argument("--reload", action="store_true", help="auto-reload on code changes (dev only)")
    p_serve.set_defaults(func=cmd_serve)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
