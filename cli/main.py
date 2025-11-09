"""
Main CLI entry point for zkidentity.
"""

import sys
from pathlib import Path

# Ensure project root is in path for module resolution
# This file is in cli/, so parent is project root
project_root = Path(__file__).parent.parent
if str(project_root.resolve()) not in [str(Path(p).resolve()) for p in sys.path]:
    sys.path.insert(0, str(project_root.resolve()))

import click
from cli.commands import alias, seed, proof, credential


@click.group()
@click.version_option(version='0.1.0')
def main():
    """Zero-Knowledge Identity System CLI"""
    pass


# Register command groups
main.add_command(alias.alias_group)
main.add_command(seed.seed_group)
main.add_command(proof.proof_group)
main.add_command(credential.credential_group)


if __name__ == '__main__':
    main()

