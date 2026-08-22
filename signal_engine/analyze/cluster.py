"""Incremental-in-spirit pain clustering over tf-idf vectors."""

from __future__ import annotations

import math
import sqlite3
from collections import Counter

from signal_engine.analyze.frustration import frustration_level
from signal_engine.analyze.ngrams import tokenize


def _vector(tokens: list[str]) -> dict[str, float]:
    """Normalized binary-presence vector.

    Deliberately unweighted: repeated pains share common words, and idf
    weighting would punish precisely that repetition (ADR-worthy trade-off,
    see issue #6 discussion).
    """
    vec = dict.fromkeys(set(tokens), 1.0)
    norm = math.sqrt(len(vec)) or 1.0
    return {tok: 1.0 / norm for tok in vec}


def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
    if len(b) < len(a):
        a, b = b, a
    return sum(value * b.get(tok, 0.0) for tok, value in a.items())


def rebuild_clusters(conn: sqlite3.Connection, threshold: float = 0.4) -> int:
    """Deterministic full rebuild of pain_clusters from all stored text.

    Chronological greedy assignment: each item joins the closest cluster whose
    centroid cosine similarity clears ``threshold``, else seeds a new cluster.
    Threshold 0.4 is the v0 default for short social texts — the #13 eval
    harness owns tuning it against operator judgments later.
    Returns the number of clusters written.
    """
    items: list[tuple[str, str, str]] = []  # (ref_type, ref_id, text)
    for row in conn.execute(
        "SELECT id, title, selftext, created_utc FROM posts ORDER BY created_utc"
    ):
        items.append(("post", row["id"], f"{row['title']} {row['selftext']}"))
    for row in conn.execute(
        "SELECT id, body, created_utc FROM comments ORDER BY created_utc"
    ):
        items.append(("comment", row["id"], row["body"]))

    documents = [tokenize(text) for _, _, text in items]
    vectors = [_vector(tokens) for tokens in documents]

    clusters: list[dict] = []  # centroid vector, members, token counter
    assignment: list[int] = []
    for index, vec in enumerate(vectors):
        best_index, best_score = -1, 0.0
        for ci, cluster in enumerate(clusters):
            score = _cosine(vec, cluster["centroid"])
            if score > best_score:
                best_index, best_score = ci, score
        if best_index >= 0 and best_score >= threshold:
            cluster = clusters[best_index]
            cluster["members"].append(index)
            size = len(cluster["members"])
            for tok in set(vec):
                cluster["centroid"][tok] = (
                    cluster["centroid"].get(tok, 0.0) * (size - 1) + vec[tok]
                ) / size
            cluster["tokens"].update(documents[index])
            assignment.append(best_index)
        else:
            clusters.append(
                {"centroid": dict(vec), "members": [index], "tokens": Counter(documents[index])}
            )
            assignment.append(len(clusters) - 1)

    conn.execute("DELETE FROM cluster_members")
    conn.execute("DELETE FROM pain_clusters")
    written = 0
    for cluster in clusters:
        members = cluster["members"]
        member_texts = [items[i][2].lower() for i in members]
        desperation = len(members) * (
            1 + max((frustration_level(text) for text in member_texts), default=0)
        )
        label = " ".join(word for word, _ in cluster["tokens"].most_common(3))
        cursor = conn.execute(
            "INSERT INTO pain_clusters(label, mention_count, desperation_score) "
            "VALUES (?, ?, ?)",
            (label, len(members), desperation),
        )
        cluster_id = cursor.lastrowid
        for i in members:
            ref_type, ref_id, text = items[i]
            quote = " ".join(text.split())[:280]
            score = round(_cosine(vectors[i], cluster["centroid"]), 4)
            conn.execute(
                "INSERT INTO cluster_members(cluster_id, ref_type, ref_id, quote, score) "
                "VALUES (?, ?, ?, ?, ?)",
                (cluster_id, ref_type, ref_id, quote, score),
            )
        written += 1
    conn.commit()
    return written
