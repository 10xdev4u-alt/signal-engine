"""Localhost dashboard: read-only views over the engine database."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

TEMPLATES_DIR = Path(__file__).parent / "templates"


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
