"""
CLI commands for alias management.
"""

import click
from zkidentity import (
    create_independent_alias,
    derive_alias_from_seed,
    revoke_alias,
    get_alias,
    list_aliases,
    AliasError,
)
from zkidentity.seed import MasterSeed


@click.group()
def alias_group():
    """Alias management commands"""
    pass


@alias_group.command('create')
@click.option('--id', 'alias_id', required=True, help='Alias identifier')
def create_independent(alias_id: str):
    """Create an independent alias with random key pair"""
    try:
        alias = create_independent_alias(alias_id)
        click.echo(f"✅ Alias '{alias_id}' created successfully")
        click.echo(f"Public key: {alias.public_key.hex()}")
        click.echo("⚠️  Store your private key securely - it cannot be recovered!")
    except ValueError as e:
        click.echo(f"❌ Error: {e}", err=True)
    except AliasError as e:
        click.echo(f"❌ Error: {e}", err=True)


@alias_group.command('derive')
@click.option('--seed', required=True, help='Master seed (hex)')
@click.option('--id', 'alias_id', required=True, help='Alias identifier')
def derive_from_seed(seed: str, alias_id: str):
    """Derive an alias from a master seed"""
    try:
        seed_bytes = bytes.fromhex(seed)
        master_seed = MasterSeed(seed_bytes)
        alias = derive_alias_from_seed(master_seed, alias_id)
        click.echo(f"✅ Alias '{alias_id}' derived from seed successfully")
        click.echo(f"Public key: {alias.public_key.hex()}")
    except ValueError as e:
        click.echo(f"❌ Error: {e}", err=True)
    except AliasError as e:
        click.echo(f"❌ Error: {e}", err=True)


@alias_group.command('list')
def list_all():
    """List all aliases"""
    aliases = list_aliases()
    if not aliases:
        click.echo("No aliases found")
        return
    
    click.echo(f"Found {len(aliases)} alias(es):")
    for alias in aliases:
        status = "🔴 Revoked" if alias.is_revoked else "🟢 Active"
        click.echo(f"  {alias.alias_id} - {status} - {alias.public_key.hex()[:32]}...")


@alias_group.command('revoke')
@click.option('--id', 'alias_id', required=True, help='Alias identifier to revoke')
def revoke(alias_id: str):
    """Revoke an alias (prevents future use, past proofs remain valid)"""
    try:
        alias = get_alias(alias_id)
        if not alias:
            click.echo(f"❌ Alias '{alias_id}' not found", err=True)
            return
        
        revoke_alias(alias)
        click.echo(f"✅ Alias '{alias_id}' revoked successfully")
        click.echo("⚠️  Past proofs remain valid, but new operations are blocked")
    except AliasError as e:
        click.echo(f"❌ Error: {e}", err=True)

