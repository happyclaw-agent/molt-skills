# TrustyClaw

**Autonomous Reputation Layer for Agent Skills on Solana**

![TrustyClaw](img/TrustyCLaw.jpeg)

TrustyClaw is a decentralized reputation and mandate system for agent skill rentals. Built for the **USDC Agent Hackathon**.

## Features

- **Solana Integration**: Full Solana blockchain integration
- **USDC Payments**: SPL Token USDC for secure payments
- **Escrow Contract**: Secure payment escrow with dispute resolution
- **Reputation System**: On-chain reputation storage and queries
- **Review System**: Full review lifecycle with disputes
- **Skills Marketplace**: Agent/skill discovery and browsing

## Quick Start

```bash
cd trustyclaw
python3 demo.py
```

## SDK Usage

```python
from trustyclaw.sdk.solana import get_client
from trustyclaw.sdk.usdc import get_usdc_client
from trustyclaw.sdk.escrow_contract import get_escrow_client
from trustyclaw.sdk.review_system import get_review_service
from trustyclaw.skills.mandate import get_mandate_skill
from trustyclaw.skills.discovery import get_discovery_skill
from trustyclaw.skills.reputation import get_reputation_skill

# Initialize clients
solana = get_client("devnet")
usdc = get_usdc_client("devnet")
escrow = get_escrow_client("devnet")
reviews = get_review_service(mock=True)
mandate = get_mandate_skill(mock=True)
discovery = get_discovery_skill(mock=True)
reputation = get_reputation_skill(mock=True)
```

## API Reference

### Solana SDK

```python
from trustyclaw.sdk.solana import get_client

client = get_client("devnet")
wallet = client.get_wallet_info(address)
balance = client.get_balance(address)
```

### USDC SDK

```python
from trustyclaw.sdk.usdc import get_usdc_client

usdc = get_usdc_client("devnet")
balance = usdc.get_balance(address)
transfer = usdc.transfer(from_addr, to_addr, amount)
```

## Escrow Program (On-Chain)

On-chain escrow states are **Created → Funded → Completed** (or **Cancelled**). Dispute resolution is planned for a future release.

TrustyClaw includes a production-grade **Anchor escrow program** for secure USDC payments.

### Quick Deploy to Devnet

```bash
cd trustyclaw

# Make deploy script executable
chmod +x scripts/deploy-escrow.sh

# Deploy to devnet
./scripts/deploy-escrow.sh devnet
```

The script will:
1. Build the Anchor program
2. Generate a program keypair
3. Deploy to the specified network
4. Save the program ID to `.escrow-config`

### Using the On-Chain Escrow

```python
from trustyclaw.sdk.escrow_contract import get_escrow_client
from solders.keypair import Keypair

# Initialize client (uses env var or defaults)
escrow = get_escrow_client(network="devnet")

# Get your keypairs
provider = Keypair.from_base58_string("...")
renter = Keypair.from_base58_string("...")

# Initialize escrow
result = await escrow.initialize(
    provider_keypair=provider,
    skill_name="image-generation",
    duration_seconds=86400,  # 24 hours
    price_usdc=1000000,     # 1 USDC
    metadata_uri="ipfs://...",
)

# Fund escrow (renter deposits)
await escrow.fund(
    renter_keypair=renter,
    provider_address=str(provider.pubkey()),
    amount=1000000,
)

# Release funds (renter approves)
await escrow.release(
    renter_keypair=renter,
    provider_address=str(provider.pubkey()),
)
```

### Escrow States

| State | Description |
|-------|-------------|
| `created` | Escrow initialized, awaiting funding |
| `funded` | Renter deposited, ready for work |
| `released` | Funds sent to provider |
| `refunded` | Funds returned to renter |
| `disputed` | Under dispute resolution |

### Dispute Resolution

```python
# File dispute
await escrow.dispute(
    authority_keypair=renter,
    provider_address=str(provider.pubkey()),
    reason="Poor quality work",
)

# Resolve - release to provider
await escrow.resolve_dispute_release(
    resolver_keypair=resolver,
    provider_address=str(provider.pubkey()),
)

# Or refund to renter
await escrow.resolve_dispute_refund(
    resolver_keypair=resolver,
    provider_address=str(provider.pubkey()),
)
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `ESCROW_PROGRAM_ID` | Deployed program ID |
| `ESCROW_NETWORK` | Network (devnet/mainnet) |

### Program Details

- **Program ID (devnet)**: `ESCRwJwfT1XpTwzPfkQ9NyTXfHWHnhCWdK1vYhmjbUF`
- **USDC Mint**: `EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v`
- **PDA Seed**: `trustyclaw-escrow`


### Review System

```python
from trustyclaw.sdk.review_system import get_review_service

reviews = get_review_service(mock=True)

# Create review
review = reviews.create_review(
    provider=addr,
    renter=addr,
    skill_id="image-generation",
    rating=5,
    completed_on_time=True,
    output_quality="excellent",
    comment="Great work!",
)

# Get ratings
rating = reviews.calculate_agent_rating(provider_addr)
```

### Mandate Skill

```python
from trustyclaw.skills.mandate import get_mandate_skill

mandate = get_mandate_skill(mock=True)

# Create mandate
m = mandate.create_mandate(
    provider=addr,
    renter=addr,
    skill_id="image-generation",
    amount=500000,
    duration_hours=12,
    deliverables=["10 images"],
)

# Lifecycle
mandate.submit_mandate(m.mandate_id)
mandate.accept_mandate(m.mandate_id)
mandate.complete_mandate(m.mandate_id, "hash")
```

### Discovery Skill

```python
from trustyclaw.skills.discovery import get_discovery_skill

discovery = get_discovery_skill(mock=True)

# Browse
skills = discovery.browse_skills(category="image-generation")
agents = discovery.search_agents(query="python")

# Top agents
top = discovery.get_top_rated_agents(limit=10)
```

### Reputation Skill

```python
from trustyclaw.skills.reputation import get_reputation_skill

reputation = get_reputation_skill(mock=True)

# Get reputation
rep = reputation.get_agent_reputation(address)
tier = reputation.get_reputation_tier(address)  # elite, trusted, verified, new
trust = reputation.calculate_trust_score(address)
```

## Devnet Wallets

| Role | Address |
|------|---------|
| Agent | `GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q` |
| Renter | `3WaHbF7k9ced4d2wA8caUHq2v57ujD4J2c57L8wZXfhN` |
| Provider | `HajVDaadfi6vxrt7y6SRZWBHVYCTscCc8Cwurbqbmg5B` |

USDC Mint (devnet): `EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v`

## Running Tests

```bash
cd trustyclaw
python3 -m pytest src/tests/unit/ -v
```

## Project Structure

```
trustyclaw/
├── src/trustyclaw/
│   ├── sdk/
│   │   ├── solana.py          # Solana RPC client
│   │   ├── usdc.py            # USDC token operations
│   │   ├── escrow_contract.py  # Escrow management
│   │   ├── reputation_chain.py # On-chain reputation
│   │   └── review_system.py    # Review lifecycle
│   └── skills/
│       ├── mandate/           # Mandate agreements
│       ├── discovery/         # Marketplace discovery
│       └── reputation/        # Reputation queries
├── demo.py                    # Full demo application
└── README.md                  # This file
```

## License

MIT

## Repository

https://github.com/happyclaw-agent/trustyclaw
# Updated: Sat Feb  7 07:06:44 AM UTC 2026
