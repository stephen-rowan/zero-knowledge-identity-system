# Zero-Knowledge Identity System - Streamlit Demo

A Streamlit web application that simulates the zero-knowledge identity system using dummy data to demonstrate core concepts and workflows.

## Features

- **Create Aliases**: Generate independent aliases or derive them from a master seed
- **Generate Proofs**: Create zero-knowledge proofs of alias ownership
- **Verify Proofs**: Verify that proofs demonstrate private key possession
- **Credentials**: Create and present verifiable credentials
- **Manage Aliases**: View and revoke aliases

## Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

## Running the Demo

```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`.

## Important Notes

⚠️ **This is a simulation using dummy cryptographic functions!**

- Uses simplified hash-based functions for demonstration
- **NOT suitable for production use**
- Real implementation would use proper cryptographic libraries:
  - `cryptography` for HMAC-SHA256
  - `pynacl` for Ed25519 Schnorr signatures
  - Proper Fiat-Shamir transformation

## Usage Guide

### 1. Create Aliases

- **Independent Alias**: Generate a new alias with a random key pair
- **Seed-Derived Alias**: Derive an alias from a master seed (deterministic)

### 2. Generate Proofs

- Select an active alias
- Provide a challenge (nonce) from a verifier
- Generate a zero-knowledge proof

### 3. Verify Proofs

- View recent proofs and their verification status
- Manually verify proofs by providing components

### 4. Credentials

- Create verifiable credentials associated with aliases
- Present credentials with zero-knowledge proofs

### 5. Manage Aliases

- View all aliases and their status
- Revoke aliases (prevents future use, past proofs remain valid)

## Security Disclaimer

This demo is for educational purposes only. The cryptographic functions are simplified simulations and should **never** be used in production systems.

