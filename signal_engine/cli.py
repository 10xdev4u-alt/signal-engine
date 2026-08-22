"""Signal Engine command line interface."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from signal_engine import __version__


def _open_db():
    from signal_engine.config import load_settings
    from signal_engine.db import connect, migrate

    settings = load_settings()
    Path(settings.db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = connect(settings.db_path)
    migrate(conn)
    return settings, conn


def cmd_add_subreddit(args) -> int:
    from signal_engine.db import add_subreddit

    _, conn = _open_db()
    add_subreddit(conn, args.name, args.group)
    print(f"monitoring r/{args.name} ({args.group})")
    return 0


def cmd_status(_args) -> int:
    if not Path(load_settings_quiet().db_path).exists():
        print("no database yet — nothing collected so far")
        return 0
    _, conn = _open_db()
    subs = conn.execute(
        "SELECT name FROM subreddits WHERE active = 1 ORDER BY name"
    ).fetchall()
    if not subs:
        print("no subreddits registered — use add-subreddit")
        return 0
    from rich.console import Console
    from rich.table import Table

    table = Table(title="signal engine status")
    table.add_column("subreddit")
    table.add_column("posts", justify="right")
    table.add_column("comments", justify="right")
    table.add_column("last success")
    table.add_column("7d error rate", justify="right")
    for row in subs:
        name = row["name"]
        posts = conn.execute(
            "SELECT COUNT(*) c FROM posts WHERE subreddit=?", (name,)
        ).fetchone()["c"]
        comments = conn.execute(
            "SELECT COUNT(*) c FROM comments WHERE subreddit=?", (name,)
        ).fetchone()["c"]
        last_ok = conn.execute(
            "SELECT value FROM settings WHERE key=?", (f"last_fetch_ok:{name}",)
        ).fetchone()
        errors = conn.execute(
            "SELECT SUM(CASE WHEN http_status >= 400 THEN 1 ELSE 0 END) bad, COUNT(*) total "
            "FROM fetch_log WHERE url LIKE ? AND ts >= datetime('now', '-7 days')",
            (f"%/r/{name}/%",),
        ).fetchone()
        rate = f"{100.0 * (errors['bad'] or 0) / errors['total']:.1f}%" if errors["total"] else "-"
        last_success = "never"
        if last_ok:
            age_min = (time.time() - float(last_ok["value"])) / 60
            last_success = f"{age_min:.0f} min ago"
        table.add_row(name, str(posts), str(comments), last_success, rate)
    Console().print(table)
    return 0


def load_settings_quiet():
    from signal_engine.config import load_settings

    return load_settings()


def cmd_fetch(args) -> int:
    from rich.console import Console

    from signal_engine.ingest.fetch import fetch_subreddits
    from signal_engine.sources.polite import PacedClient

    settings, conn = _open_db()
    client = PacedClient(pace_seconds=settings.pace_seconds)
    summary = fetch_subreddits(conn, client, names=args.subreddits)
    from signal_engine.ingest.fetch import fetch_comments

    comments_summary = fetch_comments(
        conn,
        client,
        max_age_h=settings.comment_max_age_h,
        budget=max(1, int(settings.fetch_window_min * 60 / settings.pace_seconds) // 2),
    )
    console = Console()
    for name, count in summary.fetched_counts:
        console.print(f"[green]{name}: {count} new posts[/green]")
    for name in summary.not_modified:
        console.print(f"[dim]{name}: not modified[/dim]")
    for name in summary.skipped:
        console.print(f"[dim]{name}: skipped (recently polled, nothing new)[/dim]")
    for name, err in summary.errors:
        console.print(f"[red]{name}: {err}[/red]")
    for url, delay in client.backoff_events:
        console.print(f"[yellow]backing off {delay}s after block on {url}[/yellow]")
    if summary.breaker_tripped or comments_summary.breaker_tripped:
        console.print(
            f"[bold red]BREAKER TRIPPED — run stopped:[/bold red] "
            f"{summary.breaker_tripped or comments_summary.breaker_tripped}"
        )
        return 1
    for post_id, count in comments_summary.fetched_counts:
        console.print(f"[green]{post_id}: {count} new comments[/green]")
    return 1 if summary.errors or comments_summary.errors else 0


def cmd_not_implemented(name: str):
    def handler(_args) -> int:
        print(f"'{name}' is not implemented yet", file=sys.stderr)
        return 1

    return handler


def cmd_analyze(_args) -> int:
    from rich.console import Console

    from signal_engine.analyze import build_phrase_stats, rebuild_clusters, record_intent

    _, conn = _open_db()
    phrases = build_phrase_stats(conn)
    scored = record_intent(conn)
    clusters = rebuild_clusters(conn)
    Console().print(
        f"[green]analyzed:[/green] {phrases} phrase stats, "
        f"{scored} items intent-scored, {clusters} pain clusters"
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="signal-engine", description=__doc__)
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command")

    p_add = sub.add_parser("add-subreddit", help="register a subreddit to monitor")
    p_add.add_argument("name")
    p_add.add_argument("--group", default="core", choices=["core", "discovery"])
    p_add.set_defaults(func=cmd_add_subreddit)

    p_fetch = sub.add_parser("fetch", help="pull new posts politely")
    p_fetch.add_argument("--subreddits", nargs="*", help="restrict to these subs")
    p_fetch.add_argument("--verbose", action="store_true")
    p_fetch.set_defaults(func=cmd_fetch)

    sub.add_parser("status", help="per-subreddit collection health").set_defaults(
        func=cmd_status
    )

    sub.add_parser("analyze", help="extract signals from collected data").set_defaults(
        func=cmd_analyze
    )

    for future in ("digest", "serve", "report"):
        sub.add_parser(future).set_defaults(func=cmd_not_implemented(future))
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
