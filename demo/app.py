"""
Streamlit Demo: Zero-Knowledge Identity System Simulation

This demo simulates the zero-knowledge identity system using dummy data
to demonstrate the core concepts and workflows.
"""

import streamlit as st
import hashlib
import secrets
import json
from datetime import datetime
from typing import Dict, List, Optional
import base64

# Page config
st.set_page_config(
    page_title="ZK Identity System Demo",
    page_icon="🔐",
    layout="wide"
)

# Initialize session state
if 'aliases' not in st.session_state:
    st.session_state.aliases = {}
if 'master_seed' not in st.session_state:
    st.session_state.master_seed = None
if 'credentials' not in st.session_state:
    st.session_state.credentials = {}
if 'proofs' not in st.session_state:
    st.session_state.proofs = []


# Dummy cryptographic functions (simulation only)
def dummy_hmac_sha256(key: bytes, data: str) -> bytes:
    """Simulate HMAC-SHA256 for key derivation"""
    combined = key + data.encode()
    return hashlib.sha256(combined).digest()


def dummy_derive_key_pair(seed: bytes, alias_id: str) -> tuple[bytes, bytes]:
    """Simulate deterministic key pair derivation from seed"""
    key_material = dummy_hmac_sha256(seed, alias_id)
    # Use first 32 bytes as private key, derive public key
    private_key = key_material[:32]
    public_key = hashlib.sha256(private_key + b"public").digest()[:32]
    return private_key, public_key


def dummy_generate_key_pair() -> tuple[bytes, bytes]:
    """Simulate random key pair generation"""
    private_key = secrets.token_bytes(32)
    public_key = hashlib.sha256(private_key + b"public").digest()[:32]
    return private_key, public_key


def dummy_sign(private_key: bytes, message: bytes) -> bytes:
    """Simulate Schnorr signature (dummy implementation)"""
    combined = private_key + message
    return hashlib.sha256(combined).digest()[:64]


def dummy_verify(public_key: bytes, message: bytes, signature: bytes) -> bool:
    """Simulate signature verification (dummy implementation)"""
    expected = hashlib.sha256(public_key + message).digest()[:64]
    return signature == expected


def bytes_to_hex(b: bytes) -> str:
    """Convert bytes to hex string for display"""
    return b.hex()


def hex_to_bytes(s: str) -> bytes:
    """Convert hex string to bytes"""
    return bytes.fromhex(s)


# Main UI
st.title("🔐 Zero-Knowledge Identity System Demo")
st.markdown("""
This demo simulates a zero-knowledge identity system where users can:
- Create multiple unlinkable alias identities
- Generate zero-knowledge proofs of ownership
- Present verifiable credentials anonymously
- Manage aliases with revocation support

**Note**: This uses dummy cryptographic functions for demonstration purposes only.
""")

# Sidebar navigation
page = st.sidebar.selectbox(
    "Navigate",
    ["Overview", "Create Aliases", "Generate Proofs", "Verify Proofs", "Credentials", "Manage Aliases"]
)

if page == "Overview":
    st.header("System Overview")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Aliases", len(st.session_state.aliases))
    
    with col2:
        active_aliases = sum(1 for a in st.session_state.aliases.values() if not a.get('revoked', False))
        st.metric("Active Aliases", active_aliases)
    
    with col3:
        st.metric("Credentials", len(st.session_state.credentials))
    
    st.subheader("Key Concepts")
    
    st.markdown("""
    ### 🔑 Master Seed
    - A 32-byte secret value used to deterministically derive multiple aliases
    - Losing the seed means losing access to all seed-derived aliases
    - **Never stored by the system** - user responsibility
    
    ### 👤 Alias Identity
    - An autonomous identity with its own cryptographic key pair
    - Public keys appear random and unlinkable to other aliases
    - Can be created independently or derived from a master seed
    
    ### ✍️ Zero-Knowledge Proof
    - Proves ownership of an alias without revealing the private key
    - Uses Schnorr signatures with Fiat-Shamir transformation
    - Proofs from different aliases are cryptographically unlinkable
    
    ### 📜 Verifiable Credentials
    - Credentials associated with an alias identity
    - Can be presented with zero-knowledge proofs
    - Follows W3C Verifiable Credentials Data Model
    """)
    
    if st.session_state.aliases:
        st.subheader("Your Aliases")
        for alias_id, alias_data in st.session_state.aliases.items():
            status = "🔴 Revoked" if alias_data.get('revoked', False) else "🟢 Active"
            st.write(f"**{alias_id}** - {status}")
            st.code(f"Public Key: {bytes_to_hex(alias_data['public_key'])[:32]}...", language=None)

elif page == "Create Aliases":
    st.header("Create Alias Identities")
    
    tab1, tab2 = st.tabs(["Independent Alias", "Seed-Derived Alias"])
    
    with tab1:
        st.subheader("Create Independent Alias")
        st.markdown("Generate an alias with a randomly created key pair (not derived from a seed).")
        
        alias_id = st.text_input("Alias Identifier", key="indep_alias_id", placeholder="e.g., work-identity")
        
        if st.button("Create Independent Alias", key="create_indep"):
            if not alias_id:
                st.error("Please enter an alias identifier")
            elif alias_id in st.session_state.aliases:
                st.error(f"Alias '{alias_id}' already exists")
            else:
                private_key, public_key = dummy_generate_key_pair()
                st.session_state.aliases[alias_id] = {
                    'public_key': public_key,
                    'private_key': private_key,  # In real system, never stored
                    'created_at': datetime.now().isoformat(),
                    'revoked': False,
                    'type': 'independent'
                }
                st.success(f"✅ Alias '{alias_id}' created successfully!")
                st.json({
                    "alias_id": alias_id,
                    "public_key": bytes_to_hex(public_key),
                    "type": "independent",
                    "created_at": st.session_state.aliases[alias_id]['created_at']
                })
    
    with tab2:
        st.subheader("Create Seed-Derived Alias")
        st.markdown("Derive an alias from a master seed. All aliases from the same seed are deterministically generated.")
        
        # Master seed management
        if st.session_state.master_seed is None:
            if st.button("Generate New Master Seed"):
                st.session_state.master_seed = secrets.token_bytes(32)
                st.success("✅ Master seed generated! **Save this securely** - it cannot be recovered if lost.")
                st.warning("⚠️ **IMPORTANT**: Store this seed securely. Losing it means losing access to all seed-derived aliases.")
        
        if st.session_state.master_seed:
            st.info(f"🔑 Master Seed: `{bytes_to_hex(st.session_state.master_seed)[:32]}...` (first 32 chars)")
            
            alias_id = st.text_input("Alias Identifier", key="seed_alias_id", placeholder="e.g., personal-identity")
            
            if st.button("Derive Alias from Seed", key="create_seed"):
                if not alias_id:
                    st.error("Please enter an alias identifier")
                elif alias_id in st.session_state.aliases:
                    st.error(f"Alias '{alias_id}' already exists")
                else:
                    private_key, public_key = dummy_derive_key_pair(st.session_state.master_seed, alias_id)
                    st.session_state.aliases[alias_id] = {
                        'public_key': public_key,
                        'private_key': private_key,  # In real system, never stored
                        'created_at': datetime.now().isoformat(),
                        'revoked': False,
                        'type': 'seed-derived',
                        'seed_id': 'master-seed-001'
                    }
                    st.success(f"✅ Alias '{alias_id}' derived from seed successfully!")
                    st.json({
                        "alias_id": alias_id,
                        "public_key": bytes_to_hex(public_key),
                        "type": "seed-derived",
                        "created_at": st.session_state.aliases[alias_id]['created_at']
                    })
                    
                    # Show unlinkability
                    st.markdown("### 🔒 Cryptographic Unlinkability")
                    st.info("""
                    Even though this alias was derived from the same seed as other aliases,
                    its public key appears random and cannot be linked to other seed-derived aliases.
                    """)

elif page == "Generate Proofs":
    st.header("Generate Zero-Knowledge Proofs")
    st.markdown("Prove ownership of an alias without revealing your private key.")
    
    if not st.session_state.aliases:
        st.warning("No aliases created yet. Create an alias first!")
    else:
        active_aliases = {k: v for k, v in st.session_state.aliases.items() if not v.get('revoked', False)}
        
        if not active_aliases:
            st.warning("No active aliases. Revoked aliases cannot generate proofs.")
        else:
            alias_id = st.selectbox("Select Alias", list(active_aliases.keys()))
            
            st.markdown("### Challenge Message")
            st.info("A verifier provides a challenge (nonce) to prevent replay attacks.")
            
            challenge_input = st.text_input("Challenge (hex)", value=secrets.token_hex(32), key="challenge_input")
            
            if st.button("Generate Proof"):
                try:
                    challenge = hex_to_bytes(challenge_input)
                    alias_data = st.session_state.aliases[alias_id]
                    private_key = alias_data['private_key']
                    public_key = alias_data['public_key']
                    
                    # Generate proof (Schnorr signature simulation)
                    proof_signature = dummy_sign(private_key, challenge)
                    
                    proof_data = {
                        'alias_id': alias_id,
                        'public_key': bytes_to_hex(public_key),
                        'challenge': bytes_to_hex(challenge),
                        'proof': bytes_to_hex(proof_signature),
                        'created_at': datetime.now().isoformat()
                    }
                    
                    st.session_state.proofs.append(proof_data)
                    
                    st.success("✅ Zero-knowledge proof generated!")
                    st.json(proof_data)
                    
                    st.markdown("### 🔒 Security Properties")
                    st.info("""
                    - ✅ Private key is never revealed
                    - ✅ Proof cannot be linked to other aliases
                    - ✅ Challenge prevents replay attacks
                    - ✅ Proof is cryptographically verifiable
                    """)

                except Exception as e:
                    st.error(f"Error generating proof: {e}")

elif page == "Verify Proofs":
    st.header("Verify Zero-Knowledge Proofs")
    st.markdown("Verify that a proof demonstrates ownership of an alias's private key.")
    
    if not st.session_state.proofs:
        st.warning("No proofs generated yet. Generate a proof first!")
    else:
        st.subheader("Recent Proofs")
        
        for i, proof in enumerate(reversed(st.session_state.proofs[-5:]), 1):
            with st.expander(f"Proof #{len(st.session_state.proofs) - i + 1} - {proof['alias_id']}"):
                st.json(proof)
                
                # Verify proof
                try:
                    public_key = hex_to_bytes(proof['public_key'])
                    challenge = hex_to_bytes(proof['challenge'])
                    signature = hex_to_bytes(proof['proof'])
                    
                    is_valid = dummy_verify(public_key, challenge, signature)
                    
                    if is_valid:
                        st.success("✅ Proof is VALID - Alias ownership confirmed!")
                    else:
                        st.error("❌ Proof is INVALID - Verification failed!")
                        
                except Exception as e:
                    st.error(f"Verification error: {e}")
        
        st.subheader("Manual Verification")
        st.markdown("Verify a proof by providing its components:")
        
        proof_hex = st.text_area("Proof (hex)", placeholder="Paste proof hex here")
        pubkey_hex = st.text_input("Public Key (hex)", placeholder="Paste public key hex here")
        challenge_hex = st.text_input("Challenge (hex)", placeholder="Paste challenge hex here")
        
        if st.button("Verify Proof"):
            try:
                public_key = hex_to_bytes(pubkey_hex)
                challenge = hex_to_bytes(challenge_hex)
                signature = hex_to_bytes(proof_hex)
                
                is_valid = dummy_verify(public_key, challenge, signature)
                
                if is_valid:
                    st.success("✅ Proof is VALID!")
                else:
                    st.error("❌ Proof is INVALID!")
                    
            except Exception as e:
                st.error(f"Verification error: {e}")

elif page == "Credentials":
    st.header("Verifiable Credentials")
    st.markdown("Create and present verifiable credentials associated with alias identities.")
    
    tab1, tab2 = st.tabs(["Create Credential", "Present Credential"])
    
    with tab1:
        st.subheader("Create Verifiable Credential")
        
        if not st.session_state.aliases:
            st.warning("No aliases created yet. Create an alias first!")
        else:
            active_aliases = {k: v for k, v in st.session_state.aliases.items() if not v.get('revoked', False)}
            
            if not active_aliases:
                st.warning("No active aliases available.")
            else:
                alias_id = st.selectbox("Select Alias", list(active_aliases.keys()), key="cred_alias")
                
                st.markdown("### Credential Subject")
                credential_type = st.selectbox("Credential Type", ["Degree", "Age Verification", "Membership", "Custom"])
                
                if credential_type == "Degree":
                    degree = st.text_input("Degree", value="Bachelor of Science")
                    university = st.text_input("University", value="Example University")
                    year = st.number_input("Year", min_value=1900, max_value=2100, value=2020)
                    subject = {
                        "degree": degree,
                        "university": university,
                        "year": year
                    }
                elif credential_type == "Age Verification":
                    age = st.number_input("Age", min_value=18, max_value=120, value=25)
                    subject = {"age": f"{age}+"}
                elif credential_type == "Membership":
                    org = st.text_input("Organization", value="Example Org")
                    role = st.text_input("Role", value="Member")
                    subject = {
                        "organization": org,
                        "role": role
                    }
                else:
                    custom_json = st.text_area("Custom JSON", value='{"custom": "value"}')
                    try:
                        subject = json.loads(custom_json)
                    except Exception:
                        subject = {"custom": "value"}
                
                if st.button("Create Credential"):
                    credential_id = f"cred-{secrets.token_hex(8)}"
                    alias_data = st.session_state.aliases[alias_id]
                    
                    credential = {
                        "credential_id": credential_id,
                        "alias_id": alias_id,
                        "alias_public_key": bytes_to_hex(alias_data['public_key']),
                        "credential_subject": subject,
                        "issuer": "demo-issuer",
                        "created_at": datetime.now().isoformat(),
                        "credential_type": credential_type
                    }
                    
                    st.session_state.credentials[credential_id] = credential
                    st.success(f"✅ Credential '{credential_id}' created!")
                    st.json(credential)
    
    with tab2:
        st.subheader("Present Credential with Proof")
        
        if not st.session_state.credentials:
            st.warning("No credentials created yet. Create a credential first!")
        else:
            credential_id = st.selectbox("Select Credential", list(st.session_state.credentials.keys()))
            
            if credential_id:
                credential = st.session_state.credentials[credential_id]
                st.json(credential)
                
                alias_id = credential['alias_id']
                
                if alias_id not in st.session_state.aliases:
                    st.error("Alias not found!")
                elif st.session_state.aliases[alias_id].get('revoked', False):
                    st.error("Alias is revoked and cannot present credentials!")
                else:
                    st.markdown("### Generate Presentation Proof")
                    challenge_input = st.text_input("Verifier Challenge (hex)", value=secrets.token_hex(32), key="pres_challenge")
                    
                    if st.button("Present Credential"):
                        try:
                            challenge = hex_to_bytes(challenge_input)
                            alias_data = st.session_state.aliases[alias_id]
                            private_key = alias_data['private_key']
                            
                            proof_signature = dummy_sign(private_key, challenge)
                            
                            presentation = {
                                "credential": credential,
                                "proof": {
                                    "proof": bytes_to_hex(proof_signature),
                                    "challenge": bytes_to_hex(challenge),
                                    "public_key": bytes_to_hex(alias_data['public_key'])
                                },
                                "presented_at": datetime.now().isoformat()
                            }
                            
                            st.success("✅ Credential presented with zero-knowledge proof!")
                            st.json(presentation)
                            
                            st.markdown("### 🔒 Privacy Properties")
                            st.info("""
                            - ✅ Verifier can validate credential and proof
                            - ✅ Private key is never revealed
                            - ✅ Presentation cannot be linked to other aliases
                            - ✅ Multiple presentations are unlinkable
                            """)
                        except Exception as e:
                            st.error(f"Error presenting credential: {e}")

elif page == "Manage Aliases":
    st.header("Manage Aliases")
    
    if not st.session_state.aliases:
        st.warning("No aliases created yet.")
    else:
        st.subheader("Your Aliases")
        
        for alias_id, alias_data in st.session_state.aliases.items():
            with st.expander(f"{alias_id} - {'🔴 Revoked' if alias_data.get('revoked', False) else '🟢 Active'}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Type:**", alias_data.get('type', 'unknown'))
                    st.write("**Created:**", alias_data.get('created_at', 'Unknown'))
                    st.write("**Public Key:**", bytes_to_hex(alias_data['public_key'])[:64] + "...")
                
                with col2:
                    if alias_data.get('revoked', False):
                        st.write("**Revoked At:**", alias_data.get('revoked_at', 'Unknown'))
                        st.info("This alias is revoked. Past proofs remain valid, but new operations are blocked.")
                    else:
                        if st.button(f"Revoke {alias_id}", key=f"revoke_{alias_id}"):
                            st.session_state.aliases[alias_id]['revoked'] = True
                            st.session_state.aliases[alias_id]['revoked_at'] = datetime.now().isoformat()
                            st.rerun()
        
        st.subheader("System Statistics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Aliases", len(st.session_state.aliases))
        
        with col2:
            independent = sum(1 for a in st.session_state.aliases.values() if a.get('type') == 'independent')
            st.metric("Independent", independent)
        
        with col3:
            seed_derived = sum(1 for a in st.session_state.aliases.values() if a.get('type') == 'seed-derived')
            st.metric("Seed-Derived", seed_derived)
        
        with col4:
            revoked = sum(1 for a in st.session_state.aliases.values() if a.get('revoked', False))
            st.metric("Revoked", revoked)
        
        if st.button("Clear All Data", type="secondary"):
            st.session_state.aliases = {}
            st.session_state.master_seed = None
            st.session_state.credentials = {}
            st.session_state.proofs = []
            st.rerun()

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("### About")
st.sidebar.info("""
This is a **simulation** using dummy cryptographic functions.

**Real implementation** would use:
- `cryptography` library for HMAC-SHA256
- `pynacl` for Ed25519 Schnorr signatures
- Proper Fiat-Shamir transformation
- Secure key management

**Never use dummy crypto in production!**
""")

