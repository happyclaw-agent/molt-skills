"""
Negotiation Models for TrustyClaw

Defines auto-negotiation rules, price negotiation ranges, 
delivery time preferences, and mandate acceptance criteria.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, List, Dict, Any

class NegotiationStrategy(Enum):
    """Strategies for negotiation behavior"""
    AUTO_ACCEPT = "auto-accept"
    PRICE_NEGOTIATE = "price-negotiate"
    ALWAYS_COUNTER = "always-counter"
    MANUAL_REVIEW = "manual-review"

class PriceRange(Enum):
    """Price range preferences"""
    FIXED = "fixed"
    FLEXIBLE_5_PERCENT = "flexible-5-percent"
    FLEXIBLE_10_PERCENT = "flexible-10-percent"
    FLEXIBLE_20_PERCENT = "flexible-20-percent"
    OPEN = "open"

class DeliveryPreference(Enum):
    """Delivery time preferences"""
    EXPRESS = "express"  # Fast delivery priority
    STANDARD = "standard"
    FLEXIBLE = "flexible"
    NEGOTIABLE = "negotiable"

@dataclass
class AutoAcceptCriteria:
    """Criteria for automatic mandate acceptance"""
    min_price_usdc: int = 0
    max_price_usdc: Optional[int] = None
    require_deposit: bool = True
    require_escrow: bool = True
    max_duration_seconds: Optional[int] = None
    require_quality_badge: bool = False
    min_client_rating: Optional[float] = None
    trusted_clients: List[str] = field(default_factory=list)
    blocked_clients: List[str] = field(default_factory=list)
    
    def should_accept(
        self,
        price_usdc: int,
        duration_seconds: Optional[int],
        client_rating: Optional[float],
        client_address: str,
        has_escrow: bool,
        has_deposit: bool,
    ) -> bool:
        """Determine if a mandate should be auto-accepted"""
        # Check blocked clients first
        if client_address in self.blocked_clients:
            return False
        
        # Check trusted clients override - trusted clients bypass other checks
        if client_address in self.trusted_clients:
            return True
        
        # Check blocked clients
        if client_address in self.blocked_clients:
            return False
        
        # Check price range
        if price_usdc < self.min_price_usdc:
            return False
        if self.max_price_usdc and price_usdc > self.max_price_usdc:
            return False
        
        # Check duration
        if self.max_duration_seconds and duration_seconds:
            if duration_seconds > self.max_duration_seconds:
                return False
        
        # Check client rating
        if self.min_client_rating and client_rating:
            if client_rating < self.min_client_rating:
                return False
        
        # Check requirements
        if self.require_escrow and not has_escrow:
            return False
        if self.require_deposit and not has_deposit:
            return False
        
        # Check trusted clients override
        if client_address in self.trusted_clients:
            return True
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "min_price_usdc": self.min_price_usdc,
            "max_price_usdc": self.max_price_usdc,
            "require_deposit": self.require_deposit,
            "require_escrow": self.require_escrow,
            "max_duration_seconds": self.max_duration_seconds,
            "require_quality_badge": self.require_quality_badge,
            "min_client_rating": self.min_client_rating,
            "trusted_clients": self.trusted_clients,
            "blocked_clients": self.blocked_clients,
        }

@dataclass
class PriceNegotiationRules:
    """Rules for price negotiation"""
    strategy: PriceRange
    min_counter_offers: int = 1
    max_counter_offers: int = 3
    counter_deadline_seconds: int = 3600  # 1 hour
    auto_accept_counter: bool = True
    minimum_counter_increment_percent: float = 5.0  # Minimum 5% improvement
    
    def get_acceptable_range(self, base_price: int) -> tuple:
        """Get the acceptable price range for negotiation"""
        if self.strategy == PriceRange.FIXED:
            return (base_price, base_price)
        elif self.strategy == PriceRange.FLEXIBLE_5_PERCENT:
            return (base_price * 0.95, base_price * 1.05)
        elif self.strategy == PriceRange.FLEXIBLE_10_PERCENT:
            return (base_price * 0.90, base_price * 1.10)
        elif self.strategy == PriceRange.FLEXIBLE_20_PERCENT:
            return (base_price * 0.80, base_price * 1.20)
        else:  # OPEN
            return (0, float('inf'))
    
    def is_counter_acceptable(
        self,
        base_price: int,
        counter_price: int,
        counter_number: int,
    ) -> bool:
        """Check if a counter-offer is acceptable"""
        min_price, max_price = self.get_acceptable_range(base_price)
        
        # Check counter count (max_counter_offers means 0 to max_counter_offers-1 are valid)
        # Check counter count (max_counter_offers means 0 to max_counter_offers-1 are valid)
        if counter_number >= self.max_counter_offers:
            return False
        
        # Check if counter is within range
        if counter_price < min_price or counter_price > max_price:
            return False
        
        # Check minimum increment
        if counter_number > 0:
            # Calculate percentage change from previous offer
            # This would need previous offer tracking
            pass
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy": self.strategy.value,
            "min_counter_offers": self.min_counter_offers,
            "max_counter_offers": self.max_counter_offers,
            "counter_deadline_seconds": self.counter_deadline_seconds,
            "auto_accept_counter": self.auto_accept_counter,
            "minimum_counter_increment_percent": self.minimum_counter_increment_percent,
        }

@dataclass
class DeliveryPreferences:
    """Delivery time preferences"""
    preference: DeliveryPreference
    preferred_duration_seconds: Optional[int] = None
    min_duration_seconds: Optional[int] = None
    max_duration_seconds: Optional[int] = None
    express_multiplier: float = 1.5  # Price multiplier for express delivery
    allow_extensions: bool = True
    max_extensions: int = 2
    
    def get_adjusted_price(
        self,
        base_price: int,
        requested_duration: int,
    ) -> tuple:
        """Get adjusted price based on delivery preference"""
        if self.preference == DeliveryPreference.EXPRESS:
            return (base_price * self.express_multiplier, requested_duration)
        
        if self.preference == DeliveryPreference.STANDARD:
            if self.preferred_duration_seconds:
                if requested_duration <= self.preferred_duration_seconds:
                    return (base_price, requested_duration)
                elif self.max_duration_seconds:
                    if requested_duration <= self.max_duration_seconds:
                        # Slight penalty for longer delivery
                        return (base_price * 0.9, requested_duration)
        
        if self.preference == DeliveryPreference.FLEXIBLE:
            if self.min_duration_seconds and self.max_duration_seconds:
                if self.min_duration_seconds <= requested_duration <= self.max_duration_seconds:
                    return (base_price, requested_duration)
        
        # Default: return base price and requested duration
        return (base_price, requested_duration)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "preference": self.preference.value,
            "preferred_duration_seconds": self.preferred_duration_seconds,
            "min_duration_seconds": self.min_duration_seconds,
            "max_duration_seconds": self.max_duration_seconds,
            "express_multiplier": self.express_multiplier,
            "allow_extensions": self.allow_extensions,
            "max_extensions": self.max_extensions,
        }

@dataclass
class NegotiationRules:
    """Complete negotiation rules for an agent"""
    strategy: NegotiationStrategy
    auto_accept: AutoAcceptCriteria = field(default_factory=AutoAcceptCriteria)
    price_rules: PriceNegotiationRules = field(default_factory=lambda: PriceNegotiationRules(PriceRange.FLEXIBLE_10_PERCENT))
    delivery_preferences: DeliveryPreferences = field(default_factory=lambda: DeliveryPreferences(DeliveryPreference.STANDARD))
    auto_response_delay_seconds: int = 60  # Auto-respond within 1 minute
    max_concurrent_negotiations: int = 5
    
    def should_auto_accept(
        self,
        price_usdc: int,
        duration_seconds: Optional[int],
        client_rating: Optional[float],
        client_address: str,
        has_escrow: bool,
        has_deposit: bool,
    ) -> bool:
        """Determine if should auto-accept a mandate"""
        if self.strategy != NegotiationStrategy.AUTO_ACCEPT:
            return False
        
        return self.auto_accept.should_accept(
            price_usdc,
            duration_seconds,
            client_rating,
            client_address,
            has_escrow,
            has_deposit,
        )
    
    def get_response_deadline(self) -> datetime:
        """Get the deadline for responding to negotiations"""
        return datetime.utcnow() + timedelta(seconds=self.auto_response_delay_seconds)
        return datetime.utcnow() + datetime.timedelta(seconds=self.auto_response_delay_seconds)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy": self.strategy.value,
            "auto_accept": self.auto_accept.to_dict(),
            "price_rules": self.price_rules.to_dict(),
            "delivery_preferences": self.delivery_preferences.to_dict(),
            "auto_response_delay_seconds": self.auto_response_delay_seconds,
            "max_concurrent_negotiations": self.max_concurrent_negotiations,
        }

@dataclass
class NegotiationSession:
    """Active negotiation session"""
    session_id: str
    agent_address: str
    client_address: str
    skill_id: str
    status: str  # active, accepted, rejected, expired
    counter_number: int = 0
    agent_offer: Optional[int] = None
    client_offer: Optional[int] = None
    agent_duration: Optional[int] = None
    client_duration: Optional[int] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    deadline: str = field(default_factory=lambda: (datetime.utcnow() + timedelta(hours=24)).isoformat())
    deadline: str = field(default_factory=lambda: (datetime.utcnow() + datetime.timedelta(hours=24)).isoformat())
    history: List[Dict] = field(default_factory=list)
    
    def add_counter(
        self,
        offerer: str,
        price: int,
        duration: int,
    ):
        """Add a counter-offer to the negotiation"""
        self.counter_number += 1
        self.updated_at = datetime.utcnow().isoformat()
        
        if offerer == "agent":
            self.agent_offer = price
        else:
            self.client_offer = price
        
        if offerer == "agent":
            self.agent_duration = duration
        else:
            self.client_duration = duration
        
        self.history.append({
            "counter_number": self.counter_number,
            "offerer": offerer,
            "price": price,
            "duration": duration,
            "timestamp": datetime.utcnow().isoformat(),
        })
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "agent_address": self.agent_address,
            "client_address": self.client_address,
            "skill_id": self.skill_id,
            "status": self.status,
            "counter_number": self.counter_number,
            "agent_offer": self.agent_offer,
            "client_offer": self.client_offer,
            "agent_duration": self.agent_duration,
            "client_duration": self.client_duration,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "deadline": self.deadline,
            "history": self.history,
        }
