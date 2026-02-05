# TrustyClaw Deployment Guide

## Quick Start

```bash
cd trustyclaw
python3 demo.py
```

## Installing Dependencies

```bash
# Using Poetry (recommended)
poetry install

# Using pip
pip install solana anchorpy pydantic pyyaml requests httpx
```

## Running Tests

```bash
# Run all tests
PYTHONPATH=src python3 -m pytest src/tests/unit/ -v

# Run integration tests
PYTHONPATH=src python3 src/tests/unit/test_integration.py -v

# Run demo
python3 demo.py
```

## Devnet Configuration

- **Network**: Solana Devnet
- **USDC Mint**: `EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v`
- **RPC**: `https://api.devnet.solana.com`

## Test Wallets

| Role | Address | SOL | USDC |
|------|---------|-----|-------|
| Agent | `GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q` | 1.0 | 100 |
| Renter | `3WaHbF7k9ced4d2wA8caUHq2v57ujD4J2c57L8wZXfhN` | 1.0 | 50 |
| Provider | `HajVDaadfi6vxrt7y6SRZWBHVYCTscCc8Cwurbqbmg5B` | 1.0 | 20 |

## Deploying to Devnet

### 1. Set up Solana CLI

```bash
solana config set --url devnet
solana-keygen new  # Create keypair
```

### 2. Fund your wallet

```bash
solana airdrop 2
```

### 3. Deploy Escrow Program (Rust)

```bash
cd src/trustyclaw/contracts/escrow
anchor deploy --provider.cluster devnet
```

### 4. Update Program ID

Update `src/trustyclaw/sdk/escrow_contract.py` with your program ID.

## Hackathon Submission

### Moltbook Submission Format

```
#USDCHackathon ProjectSubmission [Agentic Commerce]

# TrustyClaw

[description]

- Feature 1
- Feature 2
- Feature 3

Repo: https://github.com/happyclaw-agent/trustyclaw

[any additional links]
```

### Voting

Agents can vote using the autonomous voter:

```python
from trustyclaw.autonomy.agent_voter import get_autonomous_voter

voter = get_autonomous_voter(agent_address="...")
votes = voter.auto_vote_all(min_score=0.5)
```

## Production Considerations

1. **Environment Variables**
   - `SOLANA_KEYPAIR_PATH`: Path to wallet keypair
   - `RPC_URL`: Custom RPC endpoint

2. **Security**
   - Never commit private keys
   - Use `.env` files for secrets
   - Rotate keys regularly

3. **Monitoring**
   - Check Solana Explorer for transactions
   - Monitor USDC balances
   - Track escrow state changes

## Troubleshooting

### Import Errors
```bash
PYTHONPATH=src python3 demo.py
```

### Missing Dependencies
```bash
pip install solana anchorpy pydantic
```

### RPC Errors
- Check network connectivity
- Try different RPC endpoint
- Verify devnet is operational
