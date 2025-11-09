"""
CLI commands for zero-knowledge proof generation and verification.
"""

import click
from typing import Optional
from zkidentity import (
    generate_proof,
    verify_proof,
    get_alias,
    AliasError,
    ProofError,
)
from zkidentity.proof import ZeroKnowledgeProof, generate_challenge


@click.group()
def proof_group():
    """Zero-knowledge proof commands"""
    pass


@proof_group.command('generate')
@click.option('--alias-id', 'alias_id', required=True, help='Alias identifier')
@click.option('--challenge', help='Challenge message (hex). If not provided, a random challenge will be generated')
def generate(alias_id: str, challenge: Optional[str] = None):
    """Generate a zero-knowledge proof for an alias"""
    try:
        # Get alias from memory registry first
        alias = get_alias(alias_id)
        
        # If not in memory, try to load from storage
        # Note: For independent aliases, we can't recover private keys from storage
        # For seed-derived aliases, we'd need the master seed to re-derive
        if not alias:
            from zkidentity.storage import get_default_storage
            storage = get_default_storage()
            stored = storage.load_alias(alias_id)
            if stored:
                click.echo(f"❌ Alias '{alias_id}' exists in storage but private key is not available.", err=True)
                click.echo("💡 For independent aliases, create the alias in this session to generate proofs.", err=True)
                click.echo("💡 For seed-derived aliases, use the master seed to re-derive the alias.", err=True)
                return
            else:
                click.echo(f"❌ Alias '{alias_id}' not found", err=True)
                click.echo("💡 Create an alias first: zkidentity alias create --id <alias-id>", err=True)
                return
        
        # Get or generate challenge
        if challenge:
            try:
                challenge_bytes = bytes.fromhex(challenge)
            except ValueError:
                click.echo(f"❌ Invalid challenge format. Must be hex-encoded bytes.", err=True)
                return
        else:
            challenge_bytes = generate_challenge()
            click.echo(f"📝 Generated random challenge: {challenge_bytes.hex()}")
        
        # Generate proof
        proof = generate_proof(alias, challenge_bytes)
        
        click.echo(f"✅ Proof generated successfully for alias '{alias_id}'")
        click.echo(f"Public key: {proof.public_key.hex()}")
        click.echo(f"Challenge: {proof.challenge.hex()}")
        click.echo(f"Proof: {proof.proof_bytes.hex()}")
        click.echo(f"Created at: {proof.created_at}")
        click.echo("")
        click.echo("💡 To verify this proof, use:")
        click.echo(f"   zkidentity proof verify --proof {proof.proof_bytes.hex()} --public-key {proof.public_key.hex()} --challenge {proof.challenge.hex()}")
        
    except AliasError as e:
        click.echo(f"❌ Error: {e}", err=True)
    except ProofError as e:
        click.echo(f"❌ Error: {e}", err=True)
    except Exception as e:
        click.echo(f"❌ Unexpected error: {e}", err=True)


@proof_group.command('verify')
@click.option('--proof', required=True, help='Proof bytes (hex)')
@click.option('--public-key', 'public_key', required=True, help='Public key (hex)')
@click.option('--challenge', required=True, help='Challenge message (hex)')
def verify(proof: str, public_key: str, challenge: str):
    """Verify a zero-knowledge proof"""
    try:
        # Parse hex inputs
        try:
            proof_bytes = bytes.fromhex(proof)
            public_key_bytes = bytes.fromhex(public_key)
            challenge_bytes = bytes.fromhex(challenge)
        except ValueError as e:
            click.echo(f"❌ Invalid hex format: {e}", err=True)
            return
        
        # Create proof object
        proof_obj = ZeroKnowledgeProof(
            proof_bytes=proof_bytes,
            challenge=challenge_bytes,
            public_key=public_key_bytes,
            created_at=""  # Not needed for verification
        )
        
        # Verify proof
        is_valid = verify_proof(proof_obj, public_key_bytes, challenge_bytes)
        
        if is_valid:
            click.echo("✅ Proof is valid!")
            click.echo(f"Public key: {public_key_bytes.hex()}")
            click.echo(f"Challenge: {challenge_bytes.hex()}")
        else:
            click.echo("❌ Proof is invalid")
            click.echo("The proof does not verify against the provided public key and challenge.")
        
    except ProofError as e:
        click.echo(f"❌ Proof verification error: {e}", err=True)
    except ValueError as e:
        click.echo(f"❌ Error: {e}", err=True)
    except Exception as e:
        click.echo(f"❌ Unexpected error: {e}", err=True)


@proof_group.command('challenge')
def create_challenge():
    """Generate a random challenge for proof generation"""
    challenge_bytes = generate_challenge()
    click.echo(f"📝 Generated challenge: {challenge_bytes.hex()}")
    click.echo("")
    click.echo("💡 Use this challenge when requesting a proof:")
    click.echo(f"   zkidentity proof generate --alias-id <alias-id> --challenge {challenge_bytes.hex()}")

