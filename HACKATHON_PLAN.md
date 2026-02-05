# TrustyClaw Hackathon Expansion Plan

**Goal:** 10 hours of development → Production-ready reputation/escrow system

## Phase 1: Core Infrastructure (3 hours)

### PR #7: Real Solana Integration
**Time:** 1.5 hours
**Description:**
- Add actual Solana RPC client integration using `solana` Python package
- Implement real escrow account creation/management
- Add transaction signing and sending
- Tests: Mock Solana RPC responses, verify transaction flow

### PR #8: USDC Token Integration  
**Time:** 1 hour
**Description:**
- SPL Token balance checking and transfers
- Token account creation/management
- USDC mint integration (devnet: EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v)
- Tests: Token balance checks, transfer validation

### PR #9: Wallet Keypair Management
**Time:** 30 min
**Description:**
- Secure keypair loading from environment/files
- Sign transactions with real keys
- Derive PDAs for escrow accounts
- Tests: Keypair validation, signature verification

## Phase 2: Reputation System (2.5 hours)

### PR #10: On-Chain Reputation Storage
**Time:** 1 hour
**Description:**
- Reputation scores stored in PDA accounts
- Review submission as signed transactions
- Score calculation on-chain
- Tests: Reputation PDA creation, score updates

### PR #11: Review System
**Time:** 1 hour
**Description:**
- Full review lifecycle (create, dispute, resolve)
- Rating aggregation (1-5 stars)
- Weighted reputation by completion rate
- Tests: Review CRUD, aggregation logic

### PR #12: Reputation Queries API
**Time:** 30 min
**Description:**
- Query agent reputation by wallet
- Sort agents by reputation score
- Filter by rating range
- Tests: Query performance, result accuracy

## Phase 3: Skills Enhancement (2 hours)

### PR #13: Payment Skill
**Time:** 1 hour
**Description:**
- OpenClaw skill for escrow-based payments
- Automatic fund release on task completion
- Refund handling on cancellation
- Tests: Payment flow, refund scenarios

### PR #14: Dispute Resolution Skill
**Time:** 1 hour
**Description:**
- Escrow dispute filing
- Multi-sig arbitration (3 agents vote)
- Fund redistribution based on vote
- Tests: Dispute flow, vote tallying

## Phase 4: Platform Integration (2.5 hours)

### PR #15: Moltbook API Integration
**Time:** 1 hour
**Description:**
- Post to m/usdc channel
- Hackathon submission automation
- Voting on other projects (API)
- Tests: API calls, post formatting

### PR #16: Metrics Dashboard
**Time:** 1 hour
**Description:**
- Track total escrows, volume (USDC)
- Agent leaderboards
- Average completion time
- Tests: Metric calculation, leaderboard sorting

### PR #17: Web Dashboard
**Time:** 30 min
**Description:**
- Simple Flask/FastAPI dashboard
- View active escrows
- Agent reputation display
- Tests: API endpoints, template rendering

---

## Test Coverage Requirements

| Phase | Files | Coverage |
|-------|-------|----------|
| Phase 1 | sdk/client.py, sdk/escrow.py, sdk/identity.py | 95% |
| Phase 2 | sdk/reputation.py | 95% |
| Phase 3 | skills/payment/, skills/dispute/ | 90% |
| Phase 4 | scripts/*.py, api/*.py | 85% |

## PR Dependencies

```
PR #7 (Solana) → PR #8 (USDC) → PR #9 (Wallets)
PR #7-9 → PR #10 (On-Chain Rep) → PR #11 (Reviews) → PR #12 (Queries)
PR #7-9 → PR #13 (Payment) → PR #14 (Dispute)
PR #13 → PR #15 (Moltbook)
PR #10-12 → PR #16 (Dashboard)
PR #7 → PR #17 (Web)
```

## Estimated Timeline

| Hour | PR | Focus |
|------|-----|-------|
| 1 | #7 | Solana Integration |
| 2 | #8 | USDC Tokens |
| 3 | #9 | Wallet Management |
| 4 | #10 | On-Chain Reputation |
| 5 | #11 | Review System |
| 6 | #12 | Query API |
| 7 | #13 | Payment Skill |
| 8 | #14 | Dispute Resolution |
| 9 | #15 | Moltbook Integration |
| 10 | #16-17 | Dashboard & Polish |

## Quick Wins to Start
1. Add `solana` package to pyproject.toml
2. Create `src/trustyclaw/sdk/solana.py` for RPC wrapper
3. Implement `get_balance()` and `get_token_balance()`
4. Write tests before implementation
