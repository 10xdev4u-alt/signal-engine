"""Signal Engine web server — includes API routes and optional static frontend."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from signal_engine.api.routes import create_api_router

STATIC_DIR = Path(__file__).parent / "static"


def create_app() -> FastAPI:
    app = FastAPI(title="Signal Engine", docs_url=None, redoc_url=None)
    app.include_router(create_api_router())
    if STATIC_DIR.is_dir():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    return app


def run_server(host: str = "127.0.0.1", port: int | None = None) -> None:
    """Launch uvicorn bound to loopback only."""
    if not host.startswith("127.") and host != "localhost":
        raise ValueError("signal-engine serves on loopback only")
    import uvicorn
    if port is None:
        from signal_engine.config import load_settings
        port = load_settings().port
    uvicorn.run(create_app(), host=host, port=port, log_level="warning")
