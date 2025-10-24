"""Shared utilities for environment handlers."""

from typing import Optional, Tuple
from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.types import (
    EnvironmentStartToken,
    EnvironmentEndToken,
    EnvironmentType,
    Token,
)


def create_environment_start_token(
    expander: ExpanderCore,
    env_name: str,
) -> EnvironmentStartToken:
    """Create an environment start token with proper metadata.

    Args:
        expander: The expander instance
        env_name: Name of the environment

    Returns:
        EnvironmentStartToken with display name, numbering, and type set
    """
    env_def = expander.get_environment_definition(env_name)

    display_name = env_name
    env_type = EnvironmentType.DEFAULT
    counter_name = None

    if env_def:
        display_name = env_def.display_name
        env_type = env_def.env_type
        counter_name = env_def.counter_name

    numbering = None
    if counter_name and expander.has_counter(counter_name):
        numbering = expander.get_counter_display(counter_name)

    return EnvironmentStartToken(
        env_name,
        display_name=display_name,
        numbering=numbering,
        env_type=env_type,
    )


def create_environment_end_token(
    env_name: str,
) -> EnvironmentEndToken:
    """Create an environment end token.

    Args:
        env_name: Name of the environment

    Returns:
        EnvironmentEndToken
    """
    return EnvironmentEndToken(env_name)
