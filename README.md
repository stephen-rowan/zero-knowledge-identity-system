# Zero-Knowledge Identity System

A Python library for creating and managing multiple cryptographically unlinkable alias identities. Each alias has its own cryptographic key pair that can be derived independently or from a master seed. Users can prove alias ownership through zero-knowledge proofs (Schnorr signatures) without revealing private keys or relationships between aliases.

## Features

- **Multiple Unlinkable Identities**: Create independent or seed-derived aliases with cryptographically unlinkable public keys
- **Zero-Knowledge Proofs**: Prove alias ownership using Schnorr signatures (Fiat-Shamir) without revealing private keys
- **Anonymous Authentication**: Authenticate to services using alias identities
- **Verifiable Credentials**: Present W3C Verifiable Credentials anonymously
- **Key Management**: Master seed backup/restore functionality with secure storage guidance

## Installation

### Quick Setup (Recommended)

Run the setup script to create a virtual environment and install dependencies:

**Linux/macOS:**
```bash
./setup.sh
```

**Windows:**
```cmd
setup.bat
```

This will:
- Check Python version (requires 3.11+)
- Create a virtual environment (`.venv/`)
- Install production dependencies
- Optionally install development dependencies
- Install the package in editable mode

After setup, activate the virtual environment:

```bash
source .venv/bin/activate
```

### Manual Installation

If you prefer to set up manually:

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# For development
pip install -r requirements-dev.txt

# Install package in editable mode
pip install -e .
```

### Requirements

- Python 3.11 or later
- pip (Python package manager)

## Quick Start

```python
from zkidentity import create_independent_alias, derive_alias_from_seed

# Create an independent alias
alias = create_independent_alias("my-identity")
print(f"Public key: {alias.public_key.hex()}")

# Create aliases from a master seed
from zkidentity import generate_master_seed
seed = generate_master_seed()
work_alias = derive_alias_from_seed(seed, "work-identity")
personal_alias = derive_alias_from_seed(seed, "personal-identity")
```

## CLI Usage

```bash
# Generate a master seed
zkidentity seed generate

# Create an alias
zkidentity alias create --id "my-identity"

# Derive alias from seed
zkidentity alias derive --seed <seed-hex> --id "work-identity"
```

## Simulation Demo

An interactive Streamlit simulation is available in the `demo/` directory:

```bash
cd demo
pip install -r requirements.txt
streamlit run app.py
```

**Note**: The simulation uses dummy cryptographic functions for educational purposes only. Do not use in production.

## Documentation

- [API Documentation](specs/001-zk-identity-system/contracts/api.md)
- [Data Model](specs/001-zk-identity-system/data-model.md)
- [Quickstart Guide](specs/001-zk-identity-system/quickstart.md)

## Security

- Private keys and master seeds are **never** stored by the system
- Users are responsible for secure storage of keys and seeds
- The system provides backup/export functionality but does not manage storage
- Zero exposure of sensitive data in logs, errors, or system outputs

## License

[Add license information]

