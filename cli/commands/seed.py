"""
CLI commands for master seed management.
"""

import click
from zkidentity.seed import (
    generate_master_seed,
    export_seed_backup,
    import_seed_backup,
    warn_seed_loss,
    MasterSeed,
)


@click.group()
def seed_group():
    """Master seed management commands"""
    pass


@seed_group.command('generate')
def generate():
    """Generate a new master seed"""
    seed = generate_master_seed()
    click.echo("✅ Master seed generated")
    click.echo(f"Seed (hex): {seed.seed_bytes.hex()}")
    click.echo("")
    click.echo(warn_seed_loss())
    click.echo("⚠️  IMPORTANT: Store this seed securely - it cannot be recovered if lost!")


@seed_group.command('export')
@click.option('--seed', required=True, help='Master seed (hex)')
@click.option('--password', required=True, prompt=True, hide_input=True, help='Password for encryption')
def export(seed: str, password: str):
    """Export master seed in encrypted backup format"""
    try:
        seed_bytes = bytes.fromhex(seed)
        master_seed = MasterSeed(seed_bytes)
        backup = export_seed_backup(master_seed, password)
        click.echo("✅ Seed backup created")
        click.echo(f"Backup: {backup}")
        click.echo("")
        click.echo("⚠️  Store this backup securely in a password manager or encrypted file")
    except ValueError as e:
        click.echo(f"❌ Error: {e}", err=True)
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)


@seed_group.command('import')
@click.option('--backup', required=True, help='Encrypted backup string')
@click.option('--password', required=True, prompt=True, hide_input=True, help='Password for decryption')
def import_backup(backup: str, password: str):
    """Import master seed from encrypted backup"""
    try:
        master_seed = import_seed_backup(backup, password)
        click.echo("✅ Seed imported successfully")
        click.echo(f"Seed (hex): {master_seed.seed_bytes.hex()}")
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        click.echo("Check that backup format is correct and password is correct", err=True)

