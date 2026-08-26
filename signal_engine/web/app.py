"""Localhost dashboard: read-only views over the engine database."""

from __future__ import annotations

import re
from pathlib import Path

from fastapi import APIRouter, FastAPI, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

TEMPLATES_DIR = Path(__file__).parent / "templates"
STATIC_DIR = Path(__file__).parent / "static"


def sanitize_fts_query(raw: str) -> str:
    """Build a safe FTS5 MATCH expression.

    Bare terms get a trailing prefix star so `chargeback` matches
    `chargebacks` (FTS5 does not stem). Explicitly quoted phrases keep
    exact semantics — no star.
    """
    terms: list[str] = []
    for match in re.finditer(r'"([^"]+)"|(\S+)', raw):
        quoted_phrase = match.group(1)
        phrase = (
            quoted_phrase if quoted_phrase is not None else match.group(2)
        ).replace('"', " ").strip()
        if not phrase:
            continue
        if quoted_phrase is not None:
            terms.append(f'"{phrase}"')
        else:
            terms.append(f'"{phrase}"*')
    return " ".join(terms)


def _db():
    from signal_engine.cli import _open_db

    return _open_db()[1]


def create_app() -> FastAPI:
    app = FastAPI(title="Signal Engine", docs_url=None, redoc_url=None)
    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
    router = APIRouter()

    @router.get("/", response_class=HTMLResponse)
    def index():
        return RedirectResponse("/digest", status_code=302)

    @router.get("/digest", response_class=HTMLResponse)
    def digest(request: Request):
        conn = _db()
        row = conn.execute(
            "SELECT date, md FROM digests ORDER BY date DESC LIMIT 1"
        ).fetchone()
        return templates.TemplateResponse(
            request,
            "digest.html",
            {"date": row["date"] if row else None, "markdown": row["md"] if row else None},
        )

    @router.get("/pains", response_class=HTMLResponse)
    def pains(request: Request):
        conn = _db()
        clusters = conn.execute(
            "SELECT id, label, mention_count, desperation_score, first_seen, last_seen "
            "FROM pain_clusters ORDER BY desperation_score DESC LIMIT 100"
        ).fetchall()
        return templates.TemplateResponse(
            request, "pains.html", {"clusters": [dict(c) for c in clusters]}
        )

    @router.get("/pains/{cluster_id}", response_class=HTMLResponse)
    def pain_detail(cluster_id: int, request: Request):
        conn = _db()
        cluster = conn.execute(
            "SELECT id, label, mention_count, desperation_score, first_seen, last_seen "
            "FROM pain_clusters WHERE id = ?",
            (cluster_id,),
        ).fetchone()
        if not cluster:
            raise HTTPException(status_code=404)
        members = conn.execute(
            "SELECT m.ref_type, m.ref_id, m.quote, "
            "COALESCE(p.permalink, c.permalink) AS permalink "
            "FROM cluster_members m "
            "LEFT JOIN posts p ON m.ref_type = 'post' AND p.id = m.ref_id "
            "LEFT JOIN comments c ON m.ref_type = 'comment' AND c.id = m.ref_id "
            "WHERE m.cluster_id = ?",
            (cluster_id,),
        ).fetchall()
        return templates.TemplateResponse(
            request,
            "pain_detail.html",
            {"cluster": dict(cluster), "members": [dict(m) for m in members]},
        )

    @router.get("/profile/{subreddit}", response_class=HTMLResponse)
    def profile(subreddit: str, request: Request):
        conn = _db()
        snapshots = conn.execute(
            "SELECT snapshot_md, generated_at FROM profiles "
            "WHERE subreddit = ? ORDER BY generated_at DESC LIMIT 1",
            (subreddit,),
        ).fetchall()
        return templates.TemplateResponse(
            request,
            "profile.html",
            {"subreddit": subreddit, "snapshots": [dict(s) for s in snapshots]},
        )

    @router.post("/eval/{ref_type}/{ref_id}", response_class=RedirectResponse)
    def eval_mark(
        ref_type: str,
        ref_id: str,
        verdict: str = Form(...),
    ):
        if verdict not in ("real_problem", "noise"):
            raise HTTPException(status_code=400)
        conn = _db()
        mark_query = (
            "INSERT INTO eval_marks(ref_type, ref_id, verdict) VALUES (?, ?, ?)"
            " ON CONFLICT(ref_type, ref_id) DO UPDATE SET"
            " verdict = excluded.verdict, marked_at = strftime('%Y-%m-%dT%H:%M:%fZ','now')"
        )
        mark_params = (ref_type, ref_id, verdict)
        conn.execute(mark_query, mark_params)
        conn.commit()
        return RedirectResponse("/eval", status_code=303)

    @router.get("/eval", response_class=HTMLResponse)
    def eval_overview(request: Request):
        conn = _db()
        recent_query = (
            "SELECT s.ref_type, s.ref_id,"
            " COALESCE(s.llm_score, s.heuristic_score) AS score,"
            " COALESCE(p.permalink, c.permalink) AS permalink,"
            " s.scored_at"
            " FROM intent_scores s"
            " LEFT JOIN posts p ON s.ref_type = 'post' AND p.id = s.ref_id"
            " LEFT JOIN comments c ON s.ref_type = 'comment' AND c.id = s.ref_id"
            " WHERE COALESCE(s.llm_score, s.heuristic_score) >= 4"
            " AND COALESCE(p.permalink, c.permalink) IS NOT NULL"
            " ORDER BY s.scored_at DESC LIMIT 10"
        )
        flagged = [dict(r) for r in conn.execute(recent_query)]
        verdict_query = "SELECT verdict FROM eval_marks WHERE ref_type = ? AND ref_id = ?"
        for f in flagged:
            row = conn.execute(verdict_query, (f["ref_type"], f["ref_id"])).fetchone()
            f["verdict"] = row["verdict"] if row else None
        marked = [f for f in flagged if f["verdict"] is not None]
        evaluated = len(marked)
        p10 = (
            sum(1 for f in marked if f["verdict"] == "real_problem") / evaluated
            if evaluated
            else 0.0
        )
        if evaluated == 0:
            recommendation = (
                "no marks yet. Mark items below; the precision@10"
                " figure will populate as you mark."
            )
        elif p10 < 0.7:
            recommendation = (
                f"precision@10 is {p10:.2f}, below the 0.70 target."
                " Tighten the intent threshold or the cluster similarity cut."
            )
        else:
            recommendation = (
                f"precision@10 is {p10:.2f}. Above the 0.70 target."
                " Hold the current thresholds."
            )
        week_digests = [
            dict(r) for r in conn.execute(
                "SELECT date, md FROM digests"
                " WHERE date >= date('now', '-7 days') ORDER BY date DESC"
            )
        ]
        return templates.TemplateResponse(
            request,
            "eval.html",
            {
                "flagged": flagged,
                "p10": p10,
                "evaluated": evaluated,
                "sample_size": len(flagged),
                "recommendation": recommendation,
                "week_digests": week_digests,
            },
        )

    @router.get("/eval/marks.json")
    def eval_export():
        conn = _db()
        export_query = (
            "SELECT ref_type, ref_id, verdict, marked_at FROM eval_marks"
            " ORDER BY marked_at DESC LIMIT 1000"
        )
        import json
        rows = [dict(r) for r in conn.execute(export_query)]
        return HTMLResponse(
            f"<pre>{json.dumps(rows, indent=2)}</pre>",
            headers={"Content-Disposition": "attachment; filename=eval_marks.json"},
        )

    @router.get("/search", response_class=HTMLResponse)
    def search(
        request: Request,
        q: str = "",
        sub: str = "",
        type: str = "",  # noqa: A002 - matches the query-string name
        from_: str = Query(default="", alias="from"),
        to: str = "",
    ):
        conn = _db()
        results: list[dict] = []
        match_expr = sanitize_fts_query(q)
        if match_expr:
            to_inclusive = f"{to}~" if to else ""
            type_filter = type if type in ("post", "comment") else ""
            sql = (
                "SELECT ref_type, ref_id, subreddit, permalink, created_utc, title,"
                " snippet(search_index, 4, '<mark>', '</mark>', '…', 14) AS snip"
                " FROM search_index WHERE search_index MATCH ?"
                " AND (? = '' OR subreddit = ?)"
                " AND (? = '' OR ref_type = ?)"
                " AND (? = '' OR created_utc >= ?)"
                " AND (? = '' OR created_utc <= ?)"
                " ORDER BY created_utc DESC LIMIT 200"
            )
            date_from = from_
            date_to_inclusive = to_inclusive
            params = [match_expr]
            params.append(sub)
            params.append(sub)
            params.append(type_filter)
            params.append(type_filter)
            params.append(date_from)
            params.append(date_from)
            params.append(to)
            params.append(date_to_inclusive)
            rows = conn.execute(sql, params)
            results = [dict(r) for r in rows]
        indexed = conn.execute(
            "SELECT COUNT(*) AS c FROM search_index"
        ).fetchone()["c"]
        return templates.TemplateResponse(
            request,
            "search.html",
            {
                "q": q,
                "sub": sub,
                "type": type_filter if match_expr else type,
                "from": from_,
                "to": to,
                "results": results,
                "indexed": indexed,
            },
        )

    @router.get("/status", response_class=HTMLResponse)
    def status(request: Request):
        conn = _db()
        subs = []
        for row in conn.execute(
            "SELECT name FROM subreddits WHERE active = 1 ORDER BY name"
        ):
            name = row["name"]
            posts = conn.execute(
                "SELECT COUNT(*) c FROM posts WHERE subreddit=?", (name,)
            ).fetchone()["c"]
            comments = conn.execute(
                "SELECT COUNT(*) c FROM comments WHERE subreddit=?", (name,)
            ).fetchone()["c"]
            subs.append({"name": name, "posts": posts, "comments": comments})
        recent_errors = [
            dict(r)
            for r in conn.execute(
                "SELECT url, http_status, ts FROM fetch_log "
                "WHERE http_status >= 400 OR http_status IS NULL "
                "ORDER BY id DESC LIMIT 10"
            )
        ]
        return templates.TemplateResponse(
            request,
            "status.html",
            {"subs": subs, "recent_errors": recent_errors},
        )

    app.include_router(router)
    if STATIC_DIR.is_dir():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    return app


def run_server(host: str = "127.0.0.1", port: int | None = None) -> None:
    """Launch uvicorn bound to loopback only — this tool stays private."""
    if not host.startswith("127.") and host != "localhost":
        raise ValueError("signal-engine serves on loopback only")
    import uvicorn

    if port is None:
        from signal_engine.config import load_settings

        port = load_settings().port
    uvicorn.run(create_app(), host=host, port=port, log_level="warning")
