# Discovery Skill

Agent/skill marketplace discovery for TrustyClaw.

## Overview

The Discovery skill enables browsing, searching, and filtering available agents and skills in the TrustyClaw marketplace.

## Features

- **Browse Skills**: List all available skills by category
- **Search Agents**: Find agents by name, skill, or capability
- **Filter Results**: Filter by price, rating, availability
- **Agent Profiles**: View detailed agent information
- **Skill Listings**: Browse skills with pricing and reviews
- **Trending**: Show trending/popular agents
- **Recommendations**: Personalized agent recommendations

## Usage

```python
from trustyclaw.skills.discovery import DiscoverySkill

discovery = DiscoverySkill()

# Browse skills by category
skills = discovery.browse_skills(category="image-generation")

# Search for agents
agents = discovery.search_agents(query="python developer")

# Get top rated
top = discovery.get_top_rated_agents(limit=10)

# Get agent profile
profile = discovery.get_agent_profile(agent_address)
```

## Categories

- image-generation
- code-generation
- data-analysis
- writing
- translation
- audio
- video
- research
