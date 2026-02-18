"""Configuration and credential management for the Handwrytten CLI."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

import click

from handwrytten.client import Handwrytten

CONFIG_DIR = Path.home() / ".config" / "handwrytten"
CONFIG_FILE = CONFIG_DIR / "config.json"


def load_api_key() -> Optional[str]:
    """Load API key from config file, falling back to None.

    Priority:
      1. HANDWRYTTEN_API_KEY env var (handled by Click envvar)
      2. ~/.config/handwrytten/config.json
    """
    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text())
            return data.get("api_key")
        except (json.JSONDecodeError, OSError):
            pass
    return None


def save_api_key(api_key: str) -> None:
    """Persist API key to ~/.config/handwrytten/config.json."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    data = {}
    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    data["api_key"] = api_key
    CONFIG_FILE.write_text(json.dumps(data, indent=2))
    # Restrict permissions to owner only
    CONFIG_FILE.chmod(0o600)


def get_client(ctx: click.Context) -> Handwrytten:
    """Build a Handwrytten client from CLI context, or exit with a helpful error."""
    api_key = ctx.obj.get("api_key")
    if not api_key:
        click.echo(
            click.style("Error: ", fg="red", bold=True)
            + "No API key found.\n\n"
            "Set it with one of:\n"
            "  1. handwrytten account login\n"
            "  2. export HANDWRYTTEN_API_KEY=your_key\n"
            "  3. handwrytten --api-key your_key ...\n",
            err=True,
        )
        ctx.exit(1)

    kwargs = {"api_key": api_key}
    base_url = ctx.obj.get("base_url")
    if base_url:
        kwargs["base_url"] = base_url
    return Handwrytten(**kwargs)
