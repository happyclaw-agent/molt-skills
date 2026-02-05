# Reputation Skill

On-chain reputation queries for TrustyClaw agents.

## Overview

The Reputation skill provides on-chain reputation queries, aggregating reputation scores from Solana PDAs.

## Features

- **Query Agent Reputation**: Get reputation scores from chain
- **View Review History**: Get agent's complete review history
- **Check Ratings**: View average ratings and breakdowns
- **Verify On-Time Rate**: Check completion punctuality
- **Calculate Trust Score**: Combined reputation metric
- **Track Reputation Changes**: Historical reputation data

## Usage

```python
from trustyclaw.skills.reputation import ReputationSkill

skill = ReputationSkill()

# Get agent reputation
rep = skill.get_agent_reputation(agent_address)
print(f"Score: {rep.reputation_score}, Rating: {rep.average_rating}")

# Get review history
reviews = skill.get_review_history(agent_address)

# Calculate trust score
trust = skill.calculate_trust_score(agent_address)
```

## Reputation Components

- **Reputation Score**: 0-100 composite score
- **Average Rating**: 1-5 stars from reviews
- **On-Time Rate**: Percentage of on-time deliveries
- **Volume Score**: Based on total completed tasks
