"""Tests for the http.client-based httpx transport."""

from __future__ import annotations

import httpx
import pytest

from signal_engine.sources.polite import (
    PacedClient,
    _host_allowed,
    httpClientTransport,
)


def test_host_allowed_reddit() -> None:
    assert _host_allowed("https://www.reddit.com/r/python/.rss")
    assert _host_allowed("https://old.reddit.com/r/x/.rss")
    assert _host_allowed("https://reddit.com/r/x/.rss")


def test_host_blocked_non_reddit() -> None:
    assert not _host_allowed("https://evil.com/steal")
    assert not _host_allowed("http://127.0.0.1/admin")
    assert not _host_allowed("http://10.0.0.1/secret")
    assert not _host_allowed("file:///etc/passwd")


def test_transport_rejects_blocked_url() -> None:
    transport = httpClientTransport()
    request = httpx.Request("GET", "https://evil.com/steal")
    with pytest.raises(httpx.TransportError):
        transport.handle_request(request)


def test_paced_client_uses_http_client_default() -> None:
    # Default transport should be the http.client one (bypasses TLS block).
    client = PacedClient(pace_seconds=0)
    assert isinstance(client._client._transport, httpClientTransport)
    client.close()
