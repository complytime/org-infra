# SPDX-License-Identifier: Apache-2.0
"""Shared pytest configuration and helpers for the org-infra test suite."""

import re

import yaml

# PyYAML follows YAML 1.1, while GitHub Actions treats only ``true`` and
# ``false`` as booleans. The loader below drops the inherited YAML 1.1 boolean
# resolver so a workflow's ``on`` key stays a string.
YAML_BOOLEAN_TAG = "tag:yaml.org,2002:bool"


class GitHubActionsLoader(yaml.SafeLoader):
    """Load YAML without treating the GitHub Actions ``on`` key as true."""


GitHubActionsLoader.yaml_implicit_resolvers = {
    first_character: [(tag, pattern) for tag, pattern in resolvers if tag != YAML_BOOLEAN_TAG]
    for first_character, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}
GitHubActionsLoader.add_implicit_resolver(
    YAML_BOOLEAN_TAG,
    re.compile(r"^(?:true|True|TRUE|false|False|FALSE)$"),
    list("tTfF"),
)
