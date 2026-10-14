"""Shared fixtures and utilities for org-infra test suite."""

from __future__ import annotations

import re

import yaml

YAML_BOOLEAN_TAG = "tag:yaml.org,2002:bool"


class GitHubActionsLoader(yaml.SafeLoader):
    """Load YAML without treating the GitHub Actions ``on`` key as true."""


GitHubActionsLoader.yaml_implicit_resolvers = {
    first_character: [
        (tag, pattern)
        for tag, pattern in resolvers
        if tag != YAML_BOOLEAN_TAG
    ]
    for first_character, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}
GitHubActionsLoader.add_implicit_resolver(
    YAML_BOOLEAN_TAG,
    re.compile(r"^(?:true|True|TRUE|false|False|FALSE)$"),
    list("tTfF"),
)
