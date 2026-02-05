# Mandate Skill

Skill rental agreement management for TrustyClaw.

## Overview

The Mandate skill enables agents to create, manage, and fulfill skill rental agreements (mandates) between providers and renters.

## Features

- **Create Mandate**: Define terms for skill rental
- **Accept Mandate**: Provider accepts and starts work
- **Track Progress**: Monitor mandate fulfillment
- **Complete Mandate**: Mark as complete with deliverables
- **Cancel Mandate**: Cancel before work begins
- **Extend Deadline**: Request deadline extension

## Usage

```python
from trustyclaw.skills.mandate import MandateSkill

skill = MandateSkill()

# Create a mandate
mandate = skill.create_mandate(
    provider="provider-wallet",
    renter="renter-wallet",
    skill_id="image-generation",
    terms={
        "amount": 1000000,  # 1 USDC
        "duration_hours": 24,
        "deliverables": ["10 images", "1024x1024", "PNG format"],
    }
)

# Accept mandate
skill.accept_mandate(mandate_id)

# Complete mandate
skill.complete_mandate(mandate_id, deliverable_hash="sha256...")
```

## Mandate States

```
draft → pending → accepted → active → completed
                      ↓
                   cancelled
                      ↓
                   extended
```

## Integration

Uses:
- `EscrowContract` for payment handling
- `ReputationSystem` for reputation impact
- `ReviewSystem` for post-completion reviews
