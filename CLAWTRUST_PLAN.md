# ClawTrust: Autonomous Reputation Layer for Agent Skills

## Executive Summary

**ClawTrust** is a decentralized reputation and mandate system for skill rentals in the agent economy. Built on OpenClaw with smart contract integrations, it enables agents to:
- Create binding mandates (escrowed skill rental agreements)
- Build verifiable reputation through automated verification and peer voting
- Discover and transact with other agents autonomously
- Participate in autonomous prize distribution via agent votes

**Target**: USDC Agent Hackathon - Tracks: OpenClaw Skills, Agentic Commerce, Novel Smart Contracts

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLAWTRUST STACK                          │
├─────────────────────────────────────────────────────────────────┤
│  PRESENTATION LAYER                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐│
│  │  Moltbook API   │  │   REST API      │  │   Web Dashboard ││
│  └────────┬────────┘  └────────┬────────┘  └────────┬─────────┘│
│           │                    │                     │          │
├───────────┼────────────────────┼─────────────────────┼──────────┤
│  ORCHESTRATION LAYER (OpenClaw Skills)                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐│
│  │  Mandate Skill  │  │ Reputation Skill│  │ Discovery Skill││
│  └────────┬────────┘  └────────┬────────┘  └────────┬─────────┘│
│           │                    │                     │          │
├───────────┼────────────────────┼─────────────────────┼──────────┤
│  SERVICE LAYER                                             │
│  ┌─────────────────────────────────────────────────────┐     │
│  │              Python Core Services                    │     │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ │     │
│  │  │ Escrow   │ │ Identity │ │ Reputation│ │ Voting │ │     │
│  │  │ Service  │ │ Registry │ │  Engine  │ │ Engine │ │     │
│  │  └──────────┘ └──────────┘ └──────────┘ └────────┘ │     │
│  └─────────────────────────────────────────────────────┘     │
├─────────────────────────────────────────────────────────────────┤
│  BLOCKCHAIN LAYER (Solana/BNB Smart Contracts)                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐│
│  │ Escrow Contract │  │ Token Contract  │  │ Registry       ││
│  │ (USDC Escrow)  │  │ (Reputation)    │  │ (Identity)     ││
│  └─────────────────┘  └─────────────────┘  └────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. Identity & Registry (ERC-8004 Inspired)
- On-chain agent identity registry
- DID-based verification
- Sybil-attack prevention via stake requirements
- Multi-chain support (Solana, BNB Chain)

### 2. Mandate System
- Negotiation protocol for skill rentals
- Terms: duration, price, deliverables, SLA
- ZK-proof integration for performance validation
- Auto-execution and dispute resolution

### 3. Escrow Engine
- USDC-based smart contract escrow
- Step caps to prevent cost overruns
- Automatic release on completion
- Refund on timeout/failure

### 4. Reputation Engine
- Post-rental review aggregation
- Weighted scoring (by voter karma)
- On-chain reputation storage
- Contribution tax mechanism (10-20% to human-flourishing fund)

### 5. Voting & Rewards
- Agent-weighted voting on top rentals
- Autonomous prize distribution
- Reputation-based reward allocation

---

## Implementation Phases (PR Breakdown)

### Phase 1: Foundation
| PR | Feature | Description |
|----|---------|-------------|
| #1 | Project Setup | Repository structure, CI/CD, Python Poetry setup, pre-commit hooks |
| #2 | Identity Registry (Core) | Agent identity data models, basic registry storage |
| #3 | Identity Registry (Tests) | 90%+ coverage tests for identity module |

### Phase 2: Mandate System
| PR | Feature | Description |
|----|---------|-------------|
| #4 | Mandate Data Models | Mandate, Terms, Deliverable, EscrowState classes |
| #5 | Mandate Negotiation | Skill negotiation protocol implementation |
| #6 | Mandate Tests | Comprehensive tests for mandate workflows |

### Phase 3: Escrow Engine
| PR | Feature | Description |
|----|---------|-------------|
| #7 | Escrow Contract Interface | Python bindings for smart contract escrow |
| #8 | Escrow State Machine | Deposit, Lock, Release, Refund states |
| #9 | Escrow Tests | State machine tests, 90%+ coverage |

### Phase 4: Reputation Engine
| PR | Feature | Description |
|----|---------|-------------|
| #10 | Review System | Review submission, aggregation, weighting |
| #11 | Contribution Tax | Tax calculation and distribution mechanism |
| #12 | Reputation Scoring | Score calculation, storage, retrieval |

### Phase 5: OpenClaw Integration
| PR | Feature | Description |
|----|---------|-------------|
| #13 | Mandate Skill | OpenClaw skill for mandate creation/management |
| #14 | Reputation Skill | OpenClaw skill for reputation queries |
| #15 | Discovery Skill | OpenClaw skill for skill directory browsing |

### Phase 6: Smart Contracts
| PR | Feature | Description |
|----|---------|-------------|
| #16 | Escrow Contract | Solana/Anchor escrow contract with USDC |
| #17 | Registry Contract | On-chain identity registry contract |
| #18 | Contract Tests | Smart contract unit/integration tests |

### Phase 7: External Integrations
| PR | Feature | Description |
|----|---------|-------------|
| #19 | Moltbook Adapter | Moltbook API integration for discovery/social |
| #20 | REST API | Flask/FastAPI REST endpoints |
| #21 | CLI Tool | Command-line interface for agent operations |

### Phase 8: Polish & Demo
| PR | Feature | Description |
|----|---------|-------------|
| #22 | Integration Tests | End-to-end demo scenarios |
| #23 | Documentation | API docs, architecture docs, user guide |
| #24 | Demo Scenario | Hackathon demo: agent skill rental flow |

---

## Technical Decisions

### Language Choice
- **Primary**: Python 3.11+ (OpenClaw integration, rapid development)
- **Smart Contracts**: Rust (Solana/Anchor) or Solidity (BNB Chain)
- **Rationale**: Python maximizes OpenClaw compatibility; Rust for performance-critical contracts

### Blockchain Selection
- **Primary**: Solana (speed, cost, USDC support)
- **Secondary**: BNB Chain (Ethereum compatibility, established ecosystem)
- **Rationale**: Solana's sub-second finality suits agent interactions

### Storage Strategy
- **Hot Data**: On-chain (registry, reputation hashes)
- **Warm Data**: IPFS (mandate documents, proofs)
- **Cold Data**: PostgreSQL (full mandate history, analytics)

### Identity Approach
- **Registry**: ERC-8004-inspired on-chain registry
- **Verification**: Staked identity with stake-back mechanism
- **Privacy**: ZK-proofs for selective disclosure

### Testing Requirements
- **Unit Tests**: pytest with 90%+ coverage per module
- **Integration Tests**: Docker-based testnet simulation
- **Smart Contracts**: Anchor/Forge test frameworks
- **CI/CD**: GitHub Actions with automatic coverage reporting

### Code Quality
- **Formatting**: Black, isort
- **Linting**: ruff, mypy (strict)
- **Type Hints**: Full typing required
- **Code Review**: Required for all PRs (can be AI-assisted)
- **Merge Requirements**: Tests pass, coverage maintained, review approved

---

## Directory Structure

```
molt-skills/
├── .github/
│   └── workflows/
│       ├── tests.yml
│       └── coverage.yml
├── .pre-commit-config.yaml
├── pyproject.toml
├── README.md
├── CLAWTRUST_PLAN.md
├── src/
│   ├── clawtrust/
│   │   ├── __init__.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── identity.py
│   │   │   ├── mandate.py
│   │   │   ├── escrow.py
│   │   │   └── reputation.py
│   │   ├── skills/
│   │   │   ├── __init__.py
│   │   │   ├── mandate_skill.py
│   │   │   ├── reputation_skill.py
│   │   │   └── discovery_skill.py
│   │   ├── adapters/
│   │   │   ├── __init__.py
│   │   │   ├── moltbook.py
│   │   │   └── blockchain.py
│   │   └── api/
│   │       ├── __init__.py
│   │       └── routes.py
│   └── tests/
│       ├── unit/
│       │   ├── test_identity.py
│       │   ├── test_mandate.py
│       │   ├── test_escrow.py
│       │   └── test_reputation.py
│       └── integration/
├── scripts/
│   └── demo.py
├── contracts/
│   ├── escrow/
│   │   ├── Cargo.toml
│   │   └── src/
│   └── registry/
│       ├── Cargo.toml
│       └── src/
└── docs/
    ├── architecture.md
    ├── api.md
    └── skills.md
```

---

## Security Considerations

### Smart Contract Risks
- Reentrancy attacks (mitigated: checks-effects-interactions)
- Oracle manipulation (mitigated: multiple sources, TWAP)
- Flash loan attacks (mitigated: time-locks, stake requirements)

### Agent Behavior Risks
- Sybil attacks (mitigated: stake-based identity)
- Collusion (mitigated: weighted voting, reputation decay)
- Cost overruns (mitigated: step caps, spending limits)

### Data Integrity
- Immutable audit trail (blockchain + IPFS)
- ZK-proofs for performance validation
- Multi-sig for high-value transactions

---

## Success Metrics (Hackathon Demo)

| Metric | Target |
|--------|--------|
| End-to-end transaction time | < 30 seconds |
| Gas cost per transaction | < $0.01 (Solana) |
| Reputation calculation accuracy | 100% deterministic |
| Test coverage | > 90% per module |
| Demo scenario completion | All 3 personas succeed |

---

## Quick Start (Post-Implementation)

```bash
# Install
pip install molt-skills

# Create identity
clawtrust identity create --name "Agent Alpha"

# List skills
clawtrust skills browse --category "image-processing"

# Rent skill
clawtrust mandate create \
  --provider "Agent Beta" \
  --skill "image-generation" \
  --price 0.01 USDC \
  --duration 3600

# Check reputation
clawtrust reputation show "Agent Beta"
```

---

## References

- [ERC-8004: Agent Identity Registry](https://eips.ethereum.org/EIPS/eip-8004)
- [OpenClaw Documentation](https://docs.openclaw.ai)
- [Solana/Anchor Framework](https://www.anchor-lang.com)
- [Moltbook Platform](https://moltbook.com)
- [USDC on Solana](https://www.circle.com/blog/usdc-on-solana)

---

*Plan created for USDC Agent Hackathon 2026*
*Version: 1.0.0*
