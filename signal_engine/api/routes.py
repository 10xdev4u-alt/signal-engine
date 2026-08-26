"""Signal Engine API routes — pure JSON, no templates."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from signal_engine.api import queries


def create_api_router() -> APIRouter:
    r = APIRouter()

    @r.get("/api/digest")
    def api_digest():
        return queries.get_digest()

    @r.get("/api/pains")
    def api_pains():
        return queries.get_pains()

    @r.get("/api/pains/{cluster_id}")
    def api_pain_detail(cluster_id: int):
        result = queries.get_pain_detail(cluster_id)
        if result is None:
            raise HTTPException(status_code=404)
        return result

    @r.get("/api/profile/{subreddit}")
    def api_profile(subreddit: str, build: bool = False):
        return queries.get_profile(subreddit, build)

    @r.get("/api/eval")
    def api_eval():
        return queries.get_eval()

    @r.post("/api/eval/{ref_type}/{ref_id}")
    def api_eval_mark(ref_type: str, ref_id: str, verdict: str):
        if verdict not in ("real_problem", "noise"):
            raise HTTPException(status_code=400)
        queries.mark_eval(ref_type, ref_id, verdict)
        return {"ok": True}

    @r.get("/api/eval/marks.json")
    def api_eval_export():
        return queries.get_eval_marks()

    @r.get("/api/search")
    def api_search(
        q: str = "",
        sub: str = "",
        type: str = "",
        from_: str = Query(default="", alias="from"),
        to: str = "",
    ):
        return queries.search(q, sub, type, from_, to)

    @r.get("/api/status")
    def api_status():
        return queries.get_status()

    return r
