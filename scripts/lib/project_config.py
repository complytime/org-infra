# SPDX-License-Identifier: Apache-2.0

"""Shared project-sync config helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_config(path: Path) -> Any:
    """Read a YAML mapping; callers validate the shape."""
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def parse_project_target(config: Any) -> tuple[str, int]:
    """Return (owner, number) from a project-sync config mapping."""
    if not isinstance(config, dict):
        raise ValueError("Config must be a mapping")
    project = config.get("project")
    if not isinstance(project, dict):
        raise ValueError("Config is missing project")
    owner = project.get("owner")
    number = project.get("number")
    if not isinstance(owner, str) or not owner:
        raise ValueError("project.owner must be a non-empty string")
    if not isinstance(number, int) or isinstance(number, bool):
        raise ValueError("project.number must be an integer")
    return owner, number


def load_project_target(path: Path) -> tuple[str, int]:
    """Read project owner/number from the board-sync config file."""
    return parse_project_target(load_config(path))
