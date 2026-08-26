"""Signal Engine database queries — all SQL isolated here."""
from __future__ import annotations

import re

from signal_engine.web.mdrender import render_digest


def _db():
    from signal_engine.cli import _open_db
    return _open_db()[1]


def _sanitize_fts(raw: str) -> str:
    terms = []
    for m in re.finditer(r'"([^"]+)"|(\S+)', raw):
        phrase = (m.group(1) if m.group(1) is not None else m.group(2)).replace('"', " ").strip()
        if phrase:
            terms.append(f'"{phrase}"' if m.group(1) is not None else f'"{phrase}"*')
    return " ".join(terms)


def get_digest() -> dict:
    conn = _db()
    row = conn.execute("SELECT date, md FROM digests ORDER BY date DESC LIMIT 1").fetchone()
    if not row:
        return {"date": None, "markdown": None, "html": None}
    return {"date": row["date"], "markdown": row["md"], "html": render_digest(row["md"])}


def get_pains() -> dict:
    conn = _db()
    clusters = conn.execute(
        "SELECT id, label, mention_count, desperation_score, first_seen, last_seen "
        "FROM pain_clusters ORDER BY desperation_score DESC LIMIT 100"
    ).fetchall()
    return {"clusters": [dict(c) for c in clusters]}


def get_pain_detail(cluster_id: int) -> dict | None:
    conn = _db()
    cluster = conn.execute(
        "SELECT id, label, mention_count, desperation_score, first_seen, last_seen "
        "FROM pain_clusters WHERE id = ?", (cluster_id,),
    ).fetchone()
    if not cluster:
        return None
    members = conn.execute(
        "SELECT m.ref_type, m.ref_id, m.quote, "
        "COALESCE(p.permalink, c.permalink) AS permalink "
        "FROM cluster_members m "
        "LEFT JOIN posts p ON m.ref_type = 'post' AND p.id = m.ref_id "
        "LEFT JOIN comments c ON m.ref_type = 'comment' AND c.id = m.ref_id "
        "WHERE m.cluster_id = ?", (cluster_id,),
    ).fetchall()
    return {"cluster": dict(cluster), "members": [dict(m) for m in members]}


def get_profile(subreddit: str, build: bool = False) -> dict:
    conn = _db()
    if build:
        from signal_engine.analyze.profile import build_profile
        from signal_engine.config import load_settings
        from signal_engine.llm.base import make_provider
        provider = make_provider(load_settings())
        build_profile(
            conn, subreddit, provider=provider,
            monthly_cap=load_settings().monthly_llm_budget,
        )
    snapshots = conn.execute(
        "SELECT snapshot_md, generated_at FROM profiles WHERE subreddit = ? "
        "ORDER BY generated_at DESC LIMIT 1", (subreddit,),
    ).fetchall()
    return {"subreddit": subreddit, "snapshots": [dict(s) for s in snapshots]}


def get_eval() -> dict:
    conn = _db()
    flagged = [dict(r) for r in conn.execute(
        "SELECT s.ref_type, s.ref_id, COALESCE(s.llm_score, s.heuristic_score) AS score, "
        "COALESCE(NULLIF(p.title, ''), substr(c.body, 1, 140)) AS snippet, "
        "COALESCE(p.permalink, c.permalink) AS permalink, s.scored_at "
        "FROM intent_scores s "
        "LEFT JOIN posts p ON s.ref_type = 'post' AND p.id = s.ref_id "
        "LEFT JOIN comments c ON s.ref_type = 'comment' AND c.id = s.ref_id "
        "WHERE COALESCE(s.llm_score, s.heuristic_score) >= 4 "
        "AND COALESCE(p.permalink, c.permalink) IS NOT NULL "
        "ORDER BY s.scored_at DESC LIMIT 10"
    )]
    for f in flagged:
        row = conn.execute("SELECT verdict FROM eval_marks WHERE ref_type = ? AND ref_id = ?",
                           (f["ref_type"], f["ref_id"])).fetchone()
        f["verdict"] = row["verdict"] if row else None
    marked = [f for f in flagged if f["verdict"] is not None]
    evaluated = len(marked)
    p10 = sum(1 for f in marked if f["verdict"] == "real_problem") / evaluated if evaluated else 0.0
    if evaluated == 0:
        recommendation = "no marks yet."
    elif p10 < 0.7:
        recommendation = f"precision@10 is {p10:.2f}, below the 0.70 target."
    else:
        recommendation = f"precision@10 is {p10:.2f}. Above the 0.70 target."
    return {
        "flagged": flagged, "p10": p10, "evaluated": evaluated,
        "sample_size": len(flagged), "recommendation": recommendation,
    }


def mark_eval(ref_type: str, ref_id: str, verdict: str) -> None:
    conn = _db()
    conn.execute(
        "INSERT INTO eval_marks(ref_type, ref_id, verdict) VALUES (?, ?, ?) "
        "ON CONFLICT(ref_type, ref_id) DO UPDATE SET "
        "verdict = excluded.verdict, marked_at = strftime('%Y-%m-%dT%H:%M:%fZ','now')",
        (ref_type, ref_id, verdict),
    )
    conn.commit()


def get_eval_marks() -> list[dict]:
    conn = _db()
    return [dict(r) for r in conn.execute(
        "SELECT ref_type, ref_id, verdict, marked_at FROM eval_marks"
        " ORDER BY marked_at DESC LIMIT 1000"
    )]


def search(q: str, sub: str, type: str, from_: str, to: str) -> dict:
    conn = _db()
    results = []
    match_expr = _sanitize_fts(q)
    if match_expr:
        type_filter = type if type in ("post", "comment") else ""
        to_inc = f"{to}~" if to else ""
        params = [match_expr, sub, sub, type_filter, type_filter, from_, from_, to, to_inc]
        results = [dict(r) for r in conn.execute(
            "SELECT ref_type, ref_id, subreddit, permalink, created_utc, title, "
            "snippet(search_index, 4, '<mark>', '</mark>', '…', 14) AS snip "
            "FROM search_index WHERE search_index MATCH ? "
            "AND (? = '' OR subreddit = ?) "
            "AND (? = '' OR ref_type = ?) "
            "AND (? = '' OR created_utc >= ?) "
            "AND (? = '' OR created_utc <= ?) "
            "ORDER BY created_utc DESC LIMIT 200", params
        )]
    indexed = conn.execute("SELECT COUNT(*) AS c FROM search_index").fetchone()["c"]
    return {"q": q, "sub": sub, "type": type_filter if match_expr else type,
            "from": from_, "to": to, "results": results, "indexed": indexed}


def get_status() -> dict:
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
    recent_errors = [dict(r) for r in conn.execute(
        "SELECT url, http_status, ts FROM fetch_log "
        "WHERE http_status >= 400 OR http_status IS NULL ORDER BY id DESC LIMIT 10"
    )]
    return {"subs": subs, "recent_errors": recent_errors}
