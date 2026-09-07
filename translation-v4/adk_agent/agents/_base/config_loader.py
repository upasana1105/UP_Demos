"""
Config Loader — Reads agent YAML configs and merges with defaults.

Usage:
    from agents._base.config_loader import load_agent_config
    config = load_agent_config("employee_verification")
"""

import os
import importlib
import logging
from pathlib import Path
from copy import deepcopy

import yaml

logger = logging.getLogger(__name__)

# Project root is the parent of the agents/ directory
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge override into base. Lists are replaced, not appended."""
    merged = deepcopy(base)
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = deepcopy(value)
    return merged


def get_agent_config_path(agent_name: str) -> Path:
    """Return the path to an agent's YAML config file."""
    return _PROJECT_ROOT / "config" / f"{agent_name}.yaml"


def get_defaults_path() -> Path:
    """Return the path to the _defaults.yaml config file."""
    return _PROJECT_ROOT / "config" / "_defaults.yaml"


def list_available_agents() -> list[str]:
    """List all agent names that have config YAML files."""
    config_dir = _PROJECT_ROOT / "config"
    agents = []
    for f in sorted(config_dir.glob("*.yaml")):
        if f.stem.startswith("_"):
            continue  # skip _defaults.yaml
        agents.append(f.stem)
    return agents


def load_agent_config(agent_name: str) -> dict:
    """Load an agent config, merged with defaults.

    Args:
        agent_name: Name of the agent (matches config/<agent_name>.yaml)

    Returns:
        Merged config dict with all defaults applied.
    """
    defaults_path = get_defaults_path()
    agent_path = get_agent_config_path(agent_name)

    if not agent_path.exists():
        raise FileNotFoundError(
            f"Agent config not found: {agent_path}\n"
            f"Available agents: {list_available_agents()}"
        )

    # Load defaults
    defaults = {}
    if defaults_path.exists():
        with open(defaults_path) as f:
            defaults = yaml.safe_load(f) or {}

    # Load agent-specific config
    with open(agent_path) as f:
        agent_config = yaml.safe_load(f) or {}

    # Merge: agent overrides defaults
    merged = _deep_merge(defaults, agent_config)

    # Inject agent_name
    merged["_agent_name"] = agent_name

    logger.info(f"Loaded config for agent '{agent_name}' from {agent_path}")
    return merged


def resolve_tool_functions(tool_paths: list[str]) -> list:
    """Import and return tool functions from dot-path strings.

    Args:
        tool_paths: List like ["tools.employee.lookup_employee.lookup_employee"]

    Returns:
        List of actual Python function objects.
    """
    functions = []
    for path in tool_paths:
        parts = path.rsplit(".", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid tool path '{path}'. Expected 'module.path.function_name'")
        module_path, func_name = parts
        try:
            module = importlib.import_module(module_path)
            func = getattr(module, func_name)
            functions.append(func)
            logger.info(f"  Loaded tool: {path}")
        except (ImportError, AttributeError) as e:
            raise ImportError(f"Could not load tool '{path}': {e}") from e
    return functions
