"""Tests for the digest markdown renderer."""

from __future__ import annotations

from signal_engine.web.mdrender import render_digest


def test_headings_and_list() -> None:
    md = (
        "# Signal digest — 2026-08-26\n\n"
        "## Top rising pains\n\n"
        "1. **chargebacks** — 3 mentions\n\n"
        "> losing hope\n\n"
        "- `fees` ×4"
    )
    html = render_digest(md)
    assert "<h1>Signal digest — 2026-08-26</h1>" in html
    assert "<h2>Top rising pains</h2>" in html
    assert "<ol>" in html
    assert "<strong>chargebacks</strong>" in html
    assert "<blockquote>losing hope</blockquote>" in html
    assert "<code>fees</code>" in html
    assert "<ul>" in html


def test_links_restricted_to_https() -> None:
    md = "[bad](javascript:alert(1)) [good](https://reddit.com/)"
    html = render_digest(md)
    # javascript: must never become a clickable link — it stays literal.
    assert 'href="javascript:' not in html
    assert 'href="https://reddit.com/"' in html


def test_escapes_raw_html() -> None:
    md = "note <script>alert(1)</script> done"
    html = render_digest(md)
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_empty_string() -> None:
    assert render_digest("") == ""
