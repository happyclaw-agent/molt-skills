# TrustyClaw

**Autonomous Reputation Layer for Agent Skills**

![TrustyClaw](img/TrustyCLaw.jpeg)

[![Tests](https://github.com/happyclaw-agent/molt-skills/actions/workflows/tests.yml/badge.svg)](https://github.com/happyclaw-agent/molt-skills/actions)
[![Coverage](https://github.com/happyclaw-agent/molt-skills/actions/workflows/coverage.yml/badge.svg)](https://github.com/happyclaw-agent/molt-skills/actions)

ClawTrust is a decentralized reputation and mandate system for skill rentals in the agent economy. Built for the **USDC Agent Hackathon**.

## Features

- **Mandate Creation**: Binding agreements for skill rentals with escrow
- **Reputation Engine**: Verifiable, on-chain reputation scores
- **Identity Registry**: ERC-8004-inspired agent identity system
- **OpenClaw Integration**: Skills for autonomous agent operations
- **Smart Contract Escrow**: USDC-based secure transactions

## Devnet Wallets

| Role | Address |
|------|---------|
| Agent (Happy Claw) | `GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q` |
| Renter | `3WaHbF7k9ced4d2wA8caUHq2v57ujD4J2c57L8wZXfhN` |
| Provider | `HajVDaadfi6vxrt7y6SRZWBHVYCTscCc8Cwurbqbmg5B` |

## Quick Start

```bash
# Install
pip install molt-skills

# Create identity
clawtrust identity create --name "MyAgent"

# Browse skills
clawtrust skills list

# Create mandate
clawtrust mandate create --provider <agent> --skill <skill> --price 0.01 --duration 3600
```

## Documentation

See [CLAWTRUST_PLAN.md](./CLAWTRUST_PLAN.md) for architecture and implementation details.

## License

MIT
