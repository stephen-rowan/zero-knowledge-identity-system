"""
Main CLI entry point for zkidentity.
"""

import click
from cli.commands import alias, seed


@click.group()
@click.version_option(version='0.1.0')
def main():
    """Zero-Knowledge Identity System CLI"""
    pass


# Register command groups
main.add_command(alias.alias_group)
main.add_command(seed.seed_group)


if __name__ == '__main__':
    main()

