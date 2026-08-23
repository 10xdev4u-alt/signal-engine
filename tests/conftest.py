"""Shared fixtures: database bootstrap for dashboard/search tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from signal_engine.db import add_subreddit, connect, migrate
from signal_engine.web.app import create_app


@pytest.fixture()
def db(tmp_path):
    conn = connect(str(tmp_path / "t.db"))
    migrate(conn)
    return conn


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "t.db"))
    conn = connect(str(tmp_path / "t.db"))
    migrate(conn)
    add_subreddit(conn, "smallbusiness")
    http = TestClient(create_app())
    return http, conn
