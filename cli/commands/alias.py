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
    authenticate,
    create_authentication_request,
    prepare_authentication_response,
    AliasError,
)
from zkidentity.proof import generate_service_challenge, verify_proof
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


@alias_group.command('authenticate')
@click.option('--id', 'alias_id', required=True, help='Alias identifier to authenticate with')
@click.option('--challenge', help='Challenge from service (hex). If not provided, a demo challenge will be generated.')
@click.option('--service-id', help='Service identifier for challenge generation (optional)')
@click.option('--verify', is_flag=True, help='Also verify the generated proof (for demonstration)')
def authenticate_cmd(alias_id: str, challenge: str, service_id: str, verify: bool):
    """
    Authenticate using an alias identity with zero-knowledge proof.
    
    This command demonstrates the authentication flow:
    1. Creates an authentication request with the alias public key
    2. Generates or uses a provided challenge
    3. Generates a zero-knowledge proof
    4. Optionally verifies the proof
    
    Example:
        zkidentity alias authenticate --id "my-identity"
        zkidentity alias authenticate --id "my-identity" --challenge "abc123..." --verify
    """
    try:
        alias = get_alias(alias_id)
        if not alias:
            click.echo(f"❌ Alias '{alias_id}' not found", err=True)
            return
        
        # Step 1: Create authentication request
        request = create_authentication_request(alias)
        click.echo("📤 Authentication Request:")
        click.echo(f"  Public Key: {request['public_key']}")
        click.echo(f"  Alias ID: {request['alias_id']}")
        click.echo()
        
        # Step 2: Generate or use challenge
        if challenge:
            try:
                challenge_bytes = bytes.fromhex(challenge)
            except ValueError:
                click.echo(f"❌ Error: Invalid challenge format (must be hex)", err=True)
                return
        else:
            # Generate demo challenge
            challenge_bytes = generate_service_challenge(service_id=service_id)
            click.echo("📥 Service Challenge (generated for demo):")
            click.echo(f"  Challenge: {challenge_bytes.hex()}")
            if service_id:
                click.echo(f"  Service ID: {service_id}")
            click.echo()
        
        # Step 3: Generate proof
        try:
            proof = authenticate(alias, challenge_bytes)
            click.echo("✅ Zero-Knowledge Proof Generated:")
            click.echo(f"  Proof Bytes: {proof.proof_bytes.hex()}")
            click.echo(f"  Public Key: {proof.public_key.hex()}")
            click.echo(f"  Challenge: {proof.challenge.hex()}")
            click.echo(f"  Created At: {proof.created_at}")
            click.echo()
            
            # Step 4: Prepare response
            response = prepare_authentication_response(proof)
            click.echo("📤 Authentication Response (send to service):")
            click.echo(f"  Proof Bytes: {response['proof_bytes']}")
            click.echo(f"  Public Key: {response['public_key']}")
            click.echo(f"  Challenge: {response['challenge']}")
            click.echo(f"  Created At: {response['created_at']}")
            click.echo()
            
            # Step 5: Verify if requested
            if verify:
                is_valid = verify_proof(proof, alias.public_key, challenge_bytes)
                if is_valid:
                    click.echo("✅ Proof Verification: SUCCESS")
                    click.echo("   The proof is valid and authenticates the alias.")
                else:
                    click.echo("❌ Proof Verification: FAILED")
                    click.echo("   The proof is invalid.")
                click.echo()
            
            click.echo("💡 Note: Each authentication session uses a unique challenge")
            click.echo("   to ensure sessions are cryptographically unlinkable.")
            
        except AliasError as e:
            click.echo(f"❌ Error: {e}", err=True)
        except ValueError as e:
            click.echo(f"❌ Error: {e}", err=True)
            
    except AliasError as e:
        click.echo(f"❌ Error: {e}", err=True)

