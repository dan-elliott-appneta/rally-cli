"""Completions command for shell completion script generation.

This module implements the 'completions' command for generating shell
completion scripts that can be sourced in the user's shell configuration.
"""

import sys

import click

from rally_tui.cli.main import cli

# Shell-specific instructions for enabling completions
_COMPLETION_INSTRUCTIONS = {
    "bash": (
        'eval "$(_RALLY_CLI_COMPLETE=bash_source rally-cli)"\n\n'
        "# Or add to ~/.bashrc:\n"
        '#   eval "$(_RALLY_CLI_COMPLETE=bash_source rally-cli)"'
    ),
    "zsh": (
        'eval "$(_RALLY_CLI_COMPLETE=zsh_source rally-cli)"\n\n'
        "# Or add to ~/.zshrc:\n"
        '#   eval "$(_RALLY_CLI_COMPLETE=zsh_source rally-cli)"'
    ),
    "fish": (
        "_RALLY_CLI_COMPLETE=fish_source rally-cli | source\n\n"
        "# Or add to ~/.config/fish/config.fish:\n"
        "#   _RALLY_CLI_COMPLETE=fish_source rally-cli | source"
    ),
}


@click.command("completions")
@click.argument("shell", type=click.Choice(["bash", "zsh", "fish"], case_sensitive=False))
def completions(shell: str) -> None:
    """Generate shell completion scripts for rally-cli.

    Outputs the eval/source instruction for the specified shell. Add the
    printed line to your shell configuration file to enable tab completion.

    Examples:

    \b
        # Bash - add to ~/.bashrc
        rally-cli completions bash

    \b
        # Zsh - add to ~/.zshrc
        rally-cli completions zsh

    \b
        # Fish - add to ~/.config/fish/config.fish
        rally-cli completions fish
    """
    shell_lower = shell.lower()
    instruction = _COMPLETION_INSTRUCTIONS.get(shell_lower, "")
    click.echo(instruction)
    sys.exit(0)


# Register command with CLI
cli.add_command(completions)
