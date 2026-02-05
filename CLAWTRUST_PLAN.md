# ClawTrust MVP: 3-Day Sprint Plan

## Executive Summary

**ClawTrust MVP** is a minimal viable prototype for the USDC Agent Hackathon, demonstrating:
- Autonomous skill rentals with USDC escrow
- Simple reputation scoring
- OpenClaw skill integration

**Deadline**: February 8, 2026, 12:00 PM PST

---

## Core Loop

```
Agent rents skill → Escrows USDC → Completes task → Funds released → Reputation updates
```

---

## MVP Components

### 1. Escrow Contract (Solana/Anchor)
- Simple USDC deposit/release
- PDA-based escrow accounts
- Devnet deployment
- Timeout-based refund

### 2. OpenClaw Skills (3 total)

| Skill | Purpose |
|-------|---------|
| **Mandate** | Negotiate terms, create escrow, call contract |
| **Discovery** | Browse skill directory (hardcoded for MVP) |
| **Reputation** | Record/compute simple score (counter-based) |

### 3. Python SDK
- Wrapper for Solana contract calls
- Simple identity management (wallet-based)
- Reputation calculation

---

## What's Included

✅ Simple escrow contract (Solana devnet)
✅ 3 OpenClaw skills
✅ Python SDK for contract interaction
✅ Demo script for Moltbook posting
✅ Unit tests (90% coverage)

---

## What's NOT Included (Deferred)

❌ Full identity registry (use wallet addresses)
❌ ZK proofs
❌ Contribution tax
❌ REST API / Web dashboard
❌ CLI tool
❌ IPFS / PostgreSQL
❌ Multi-chain support
❌ Complex voting engine

---

## File Structure

```
molt-skills/
├── CLAWTRUST_PLAN.md
├── pyproject.toml
├── README.md
├── src/
│   ├── clawtrust/
│   │   ├── __init__.py
│   │   ├── contracts/
│   │   │   └── escrow/          # Anchor project
│   │   ├── skills/
│   │   │   ├── mandate/
│   │   │   │   └── SKILL.md
│   │   │   ├── discovery/
│   │   │   │   └── SKILL.md
│   │   │   └── reputation/
│   │   │       └── SKILL.md
│   │   └── sdk/
│   │       ├── __init__.py
│   │       ├── client.py
│   │       ├── identity.py
│   │       └── reputation.py
│   └── tests/
│       └── unit/
├── scripts/
│   └── demo.py
└── docs/
    └── demo-guide.md
```

---

## Implementation Phases

### PR #1: Project Setup + SDK Foundation
- Poetry project setup
- SDK client skeleton
- Pytest configuration

### PR #2: Escrow Contract + Python Bindings
- Anchor escrow program
- Python wrapper for contract calls
- Contract unit tests

### PR #3: Mandate + Discovery Skills
- Mandate SKILL.md + wrapper
- Discovery SKILL.md + wrapper
- Skill integration tests

### PR #4: Reputation Skill
- Reputation SKILL.md + wrapper
- Simple score calculation
- Skill tests

### PR #5: Demo + Integration
- Demo script for Moltbook
- Integration test
- Documentation

---

## Demo Flow

1. Agent posts skill listing (Discovery)
2. Agent A rents from Agent B (Mandate, escrows 0.01 USDC)
3. Task completes (simulated)
4. Funds released to Agent B
5. Reputation score updates
6. Agent votes on 5+ other projects

---

## Success Metrics

- [ ] Escrow contract deploys to Solana devnet
- [ ] All 3 skills load in OpenClaw
- [ ] End-to-end flow works in demo
- [ ] 90% test coverage
- [ ] Moltbook demo post submitted

---

*Revised for 3-day sprint - February 5, 2026*
