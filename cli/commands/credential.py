"""
CLI commands for verifiable credential management.
"""

import click
import json
import secrets
from zkidentity import (
    get_alias,
    AliasError,
    CredentialError,
)
from zkidentity.credential import (
    create_credential,
    present_credential,
    VerifiableCredential,
    CredentialPresentation,
)
from zkidentity.proof import generate_challenge
from zkidentity.storage import get_default_storage


@click.group()
def credential_group():
    """Verifiable credential commands"""
    pass


@credential_group.command('create')
@click.option('--alias-id', required=True, help='Alias identifier to associate credential with')
@click.option('--data', required=True, help='Credential data as JSON string')
@click.option('--issuer', help='Issuer identifier (defaults to alias public key)')
@click.option('--type', 'credential_type', help='Additional credential type')
@click.option('--expires', help='Expiration date (ISO format)')
def create(alias_id: str, data: str, issuer: str = None, credential_type: str = None, expires: str = None):
    """Create a verifiable credential associated with an alias"""
    try:
        # Get alias
        alias = get_alias(alias_id)
        if alias is None:
            click.echo(f"❌ Error: Alias '{alias_id}' not found", err=True)
            return
        
        # Parse credential data
        try:
            credential_data = json.loads(data)
        except json.JSONDecodeError as e:
            click.echo(f"❌ Error: Invalid JSON in credential data: {e}", err=True)
            return
        
        # Create credential
        credential = create_credential(
            alias=alias,
            credential_data=credential_data,
            issuer=issuer,
            credential_type=credential_type,
            expires_at=expires
        )
        
        click.echo(f"✅ Credential '{credential.credential_id}' created successfully")
        click.echo(f"Credential ID: {credential.credential_id}")
        click.echo(f"Alias: {alias_id}")
        click.echo(f"Public key: {alias.public_key.hex()}")
        
    except AliasError as e:
        click.echo(f"❌ Error: {e}", err=True)
    except CredentialError as e:
        click.echo(f"❌ Error: {e}", err=True)
    except ValueError as e:
        click.echo(f"❌ Error: {e}", err=True)
    except Exception as e:
        click.echo(f"❌ Unexpected error: {e}", err=True)


@credential_group.command('present')
@click.option('--credential-id', required=True, help='Credential identifier')
@click.option('--alias-id', required=True, help='Alias identifier to present with')
@click.option('--challenge', help='Challenge from verifier (hex). If not provided, generates random challenge')
@click.option('--output', help='Output file path for presentation JSON')
def present(credential_id: str, alias_id: str, challenge: str = None, output: str = None):
    """Present a verifiable credential with a zero-knowledge proof"""
    try:
        # Get alias
        alias = get_alias(alias_id)
        if alias is None:
            click.echo(f"❌ Error: Alias '{alias_id}' not found", err=True)
            return
        
        # Load credential from storage
        storage = get_default_storage()
        cred_data = storage.load_credential(credential_id)
        if cred_data is None:
            click.echo(f"❌ Error: Credential '{credential_id}' not found", err=True)
            return
        
        # Reconstruct credential object
        credential = VerifiableCredential(
            credential_id=cred_data['credential_id'],
            credential_subject=cred_data['credential_json'].get('credentialSubject', {}),
            issuer=cred_data['credential_json'].get('issuer', ''),
            alias_public_key=bytes.fromhex(cred_data['alias_public_key']),
            credential_json=cred_data['credential_json'],
            created_at=cred_data['created_at'],
            expires_at=cred_data.get('expires_at')
        )
        
        # Verify alias matches credential
        if alias.public_key != credential.alias_public_key:
            click.echo(f"❌ Error: Alias '{alias_id}' does not match credential's alias", err=True)
            return
        
        # Get or generate challenge
        if challenge:
            try:
                challenge_bytes = bytes.fromhex(challenge)
            except ValueError:
                click.echo(f"❌ Error: Invalid challenge hex format", err=True)
                return
        else:
            challenge_bytes = generate_challenge()
            click.echo(f"Generated challenge: {challenge_bytes.hex()}")
        
        # Present credential
        presentation = present_credential(credential, alias, challenge_bytes)
        
        # Verify presentation
        if not presentation.verify():
            click.echo(f"❌ Error: Presentation verification failed", err=True)
            return
        
        # Prepare output
        output_data = {
            "credential": presentation.credential.credential_json,
            "proof": {
                "proof_bytes": presentation.proof.proof_bytes.hex(),
                "public_key": presentation.proof.public_key.hex(),
                "challenge": presentation.proof.challenge.hex(),
                "created_at": presentation.proof.created_at
            },
            "presented_at": presentation.presented_at
        }
        
        # Output to file or stdout
        if output:
            with open(output, 'w') as f:
                json.dump(output_data, f, indent=2)
            click.echo(f"✅ Presentation saved to {output}")
        else:
            click.echo("✅ Credential presentation generated successfully")
            click.echo(json.dumps(output_data, indent=2))
        
    except AliasError as e:
        click.echo(f"❌ Error: {e}", err=True)
    except CredentialError as e:
        click.echo(f"❌ Error: {e}", err=True)
    except ValueError as e:
        click.echo(f"❌ Error: {e}", err=True)
    except Exception as e:
        click.echo(f"❌ Unexpected error: {e}", err=True)


@credential_group.command('list')
@click.option('--alias-id', help='Filter by alias identifier')
def list_credentials(alias_id: str = None):
    """List all credentials, optionally filtered by alias"""
    try:
        storage = get_default_storage()
        
        if alias_id:
            # Get alias to get public key
            alias = get_alias(alias_id)
            if alias is None:
                click.echo(f"❌ Error: Alias '{alias_id}' not found", err=True)
                return
            credentials = storage.list_credentials(alias.public_key.hex())
        else:
            credentials = storage.list_credentials()
        
        if not credentials:
            click.echo("No credentials found")
            return
        
        click.echo(f"Found {len(credentials)} credential(s):")
        for cred in credentials:
            click.echo(f"  - {cred['credential_id']} (alias: {cred['alias_public_key'][:16]}...)")
            click.echo(f"    Created: {cred['created_at']}")
            if cred.get('expires_at'):
                click.echo(f"    Expires: {cred['expires_at']}")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)


@credential_group.command('show')
@click.option('--credential-id', required=True, help='Credential identifier')
def show(credential_id: str):
    """Show credential details"""
    try:
        storage = get_default_storage()
        cred_data = storage.load_credential(credential_id)
        
        if cred_data is None:
            click.echo(f"❌ Error: Credential '{credential_id}' not found", err=True)
            return
        
        click.echo(f"Credential ID: {cred_data['credential_id']}")
        click.echo(f"Alias Public Key: {cred_data['alias_public_key']}")
        click.echo(f"Created: {cred_data['created_at']}")
        if cred_data.get('expires_at'):
            click.echo(f"Expires: {cred_data['expires_at']}")
        click.echo("\nCredential JSON:")
        click.echo(json.dumps(cred_data['credential_json'], indent=2))
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)

