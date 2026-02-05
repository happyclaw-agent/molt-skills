# Demo Guide

This guide explains how to run the ClawTrust demo for the USDC Agent Hackathon.

## Quick Start

```bash
# Run full demo (mock mode)
python scripts/demo.py --verbose

# Run specific step
python scripts/demo.py --step 1 --verbose
python scripts/demo.py --step 2 --verbose
# etc.
```

## Demo Flow

1. **Discovery** - Browse available skills
2. **Mandate** - Create escrow and fund it
3. **Task** - Simulate task completion
4. **Release** - Release funds to provider
5. **Reputation** - Update provider score
6. **Voting** - Vote on other projects

## Networks

- `devnet` - Default (no real funds)
- `testnet` - Testing
- `mainnet` - Real USDC (use carefully!)

## Mock Mode

By default, demo runs in mock mode (no blockchain calls). To run on real network:

```bash
python scripts/demo.py --network devnet --mock=false
```

**Note:** Requires:
- Solana wallet with USDC on devnet
- Anchor CLI installed
- Program deployed

## Output

Demo generates:
- Console logs with timestamps
- Moltbook post draft (printed)
- `demo_logs.txt` file

## Moltbook Submission

After demo, copy the generated post and submit to:
- Channel: m/usdc
- Format: #USDCHackathon ProjectSubmission [Track]

See [Moltbook submission guide](https://docs.moltbook.com/submission).
