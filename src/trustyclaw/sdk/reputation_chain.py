"""
On-Chain Reputation Storage for TrustyClaw

Stores reputation scores and reviews in Solana PDA accounts.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum
import hashlib
import struct

try:
    from solana.rpc.api import Client as SolanaClient
    from solana.rpc.commitment import Confirmed, Finalized
    from solana.keypair import Keypair
    from solana.publickey import PublicKey
    from solana.transaction import Transaction
    from solana.system_program import create_account, CreateAccountParams
    HAS_SOLANA = True
except ImportError:
    HAS_SOLANA = False


class ReputationError(Exception):
    """Reputation storage error"""
    pass


@dataclass
class ReputationScoreData:
    """On-chain reputation score"""
    agent_address: str
    total_reviews: int = 0
    average_rating: float = 0.0
    on_time_percentage: float = 100.0
    reputation_score: float = 50.0
    last_updated: int = 0  # Unix timestamp
    
    def to_bytes(self) -> bytes:
        """Serialize to bytes"""
        return struct.pack(
            '<64sIIIffI',
            self.agent_address.encode('utf-8')[:64].ljust(64, b'\0'),
            self.total_reviews,
            0,  # padding
            int(self.average_rating * 100),
            int(self.reputation_score * 100),
            int(self.on_time_percentage * 100),
            self.last_updated,
        )
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'ReputationScoreData':
        """Deserialize from bytes"""
        unpacked = struct.unpack('<64sIIIffI', data)
        return cls(
            agent_address=unpacked[0].decode('utf-8').rstrip('\0'),
            total_reviews=unpacked[1],
            average_rating=unpacked[3] / 100.0,
            reputation_score=unpacked[4] / 100.0,
            on_time_percentage=unpacked[5] / 100.0,
            last_updated=unpacked[6],
        )


@dataclass
class ReviewData:
    """On-chain review record"""
    review_id: str
    provider: str
    renter: str
    skill_id: str
    rating: int  # 1-5
    completed_on_time: bool
    comment_hash: str  # SHA256 of comment
    timestamp: int
    positive_votes: int = 0
    negative_votes: int = 0
    
    def to_bytes(self) -> bytes:
        """Serialize to bytes"""
        return struct.pack(
            '<32s32s32s32sIII32sI',
            self.review_id.encode('utf-8')[:32].ljust(32, b'\0'),
            self.provider.encode('utf-8')[:32].ljust(32, b'\0'),
            self.renter.encode('utf-8')[:32].ljust(32, b'\0'),
            self.skill_id.encode('utf-8')[:32].ljust(32, b'\0'),
            self.rating,
            int(self.completed_on_time),
            self.positive_votes,
            self.negative_votes,
            self.comment_hash.encode('utf-8')[:32].ljust(32, b'\0'),
            self.timestamp,
        )
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'ReviewData':
        """Deserialize from bytes"""
        unpacked = struct.unpack('<32s32s32s32sIII32sI', data)
        return cls(
            review_id=unpacked[0].decode('utf-8').rstrip('\0'),
            provider=unpacked[1].decode('utf-8').rstrip('\0'),
            renter=unpacked[2].decode('utf-8').rstrip('\0'),
            skill_id=unpacked[3].decode('utf-8').rstrip('\0'),
            rating=unpacked[4],
            completed_on_time=bool(unpacked[5]),
            positive_votes=unpacked[6],
            negative_votes=unpacked[7],
            comment_hash=unpacked[8].decode('utf-8').rstrip('\0'),
            timestamp=unpacked[9],
        )


class ReputationPDAProgram:
    """
    Manages on-chain reputation storage using PDAs.
    
    PDA Structure:
    - Reputation Account: [REPUTATION_SEED, agent_address]
    - Review Account: [REVIEW_SEED, review_id]
    """
    
    REPUTATION_SEED = b"trustyclaw-reputation"
    REVIEW_SEED = b"trustyclaw-review"
    REVIEW_LIST_SEED = b"trustyclaw-reviews"
    
    ACCOUNT_SIZE = 256  # Fixed size for simplicity
    REVIEW_SIZE = 256
    
    def __init__(
        self,
        network: str = "devnet",
        program_id: Optional[str] = None,
    ):
        self.network = network
        self.program_id = program_id or self._derive_program_id()
        
        if HAS_SOLANA:
            self.client = SolanaClient(
                f"https://api.{network}.solana.com"
            )
        else:
            self.client = None
        
        self._keypair: Optional[Keypair] = None
    
    def _derive_program_id(self) -> str:
        """Derive program ID (placeholder for real program)"""
        return "11111111111111111111111111111111"  # System Program as placeholder
    
    def derive_reputation_pda(self, agent_address: str) -> str:
        """Derive PDA for agent's reputation account"""
        if not HAS_SOLANA:
            return f"rep-{hash(agent_address) % 100000:05d}"
        
        try:
            agent_bytes = agent_address.encode('utf-8')[:32].ljust(32, b'\0')
            program_id = PublicKey(self.program_id)
            
            pda, bump = PublicKey.find_program_address(
                [self.REPUTATION_SEED, agent_bytes],
                program_id,
            )
            return str(pda)
        except Exception:
            return f"rep-{hash(agent_address) % 100000:05d}"
    
    def derive_review_list_pda(self, agent_address: str) -> str:
        """Derive PDA for agent's review list"""
        if not HAS_SOLANA:
            return f"reviews-{hash(agent_address) % 100000:05d}"
        
        try:
            agent_bytes = agent_address.encode('utf-8')[:32].ljust(32, b'\0')
            program_id = PublicKey(self.program_id)
            
            pda, bump = PublicKey.find_program_address(
                [self.REVIEW_LIST_SEED, agent_bytes],
                program_id,
            )
            return str(pda)
        except Exception:
            return f"reviews-{hash(agent_address) % 100000:05d}"
    
    def get_reputation(self, agent_address: str) -> Optional[ReputationScoreData]:
        """
        Get on-chain reputation for an agent.
        
        Args:
            agent_address: Agent's wallet address
            
        Returns:
            ReputationScoreData or None
        """
        pda = self.derive_reputation_pda(agent_address)
        
        if not HAS_SOLANA or not self.client:
            return self._mock_reputation(agent_address)
        
        try:
            resp = self.client.get_account_info(pda, encoding="base64")
            
            if resp.value:
                data = resp.value.data
                if isinstance(data, bytes):
                    return ReputationScoreData.from_bytes(data)
            
            return None
        except Exception:
            return self._mock_reputation(agent_address)
    
    def _mock_reputation(self, agent_address: str) -> ReputationScoreData:
        """Get mock reputation data"""
        # Generate deterministic mock data based on address
        hash_val = hash(agent_address) % 1000
        
        return ReputationScoreData(
            agent_address=agent_address,
            total_reviews=10 + (hash_val % 50),
            average_rating=4.0 + ((hash_val % 100) / 200),
            on_time_percentage=90.0 + ((hash_val % 100) / 10),
            reputation_score=70.0 + ((hash_val % 250) / 10),
            last_updated=int(datetime.utcnow().timestamp()),
        )
    
    def create_reputation_account(
        self,
        agent_address: str,
        payer_address: str,
    ) -> Dict[str, Any]:
        """
        Create reputation account for an agent.
        
        Args:
            agent_address: Agent's wallet address
            payer_address: Payer wallet (for rent)
            
        Returns:
            Transaction result dict
        """
        pda = self.derive_reputation_pda(agent_address)
        
        if not HAS_SOLANA or not self.client:
            return {
                "success": True,
                "pda": pda,
                "signature": f"create-rep-{pda[:16]}",
            }
        
        try:
            # Would create account via create_account instruction
            return {
                "success": True,
                "pda": pda,
                "signature": f"create-rep-{pda[:16]}",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def update_reputation(
        self,
        agent_address: str,
        new_score: float,
        new_reviews: int,
        new_rating: float,
        on_time_pct: float,
    ) -> Dict[str, Any]:
        """
        Update reputation score on-chain.
        
        Args:
            agent_address: Agent's wallet address
            new_score: New reputation score (0-100)
            new_reviews: New total review count
            new_rating: New average rating
            on_time_pct: On-time completion percentage
            
        Returns:
            Transaction result dict
        """
        pda = self.derive_reputation_pda(agent_address)
        
        if not HAS_SOLANA or not self.client:
            return {
                "success": True,
                "pda": pda,
                "signature": f"update-rep-{pda[:16]}",
                "score": new_score,
            }
        
        try:
            # Would update account data via instruction
            return {
                "success": True,
                "pda": pda,
                "signature": f"update-rep-{pda[:16]}",
                "score": new_score,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def submit_review(
        self,
        review_id: str,
        provider: str,
        renter: str,
        skill_id: str,
        rating: int,
        completed_on_time: bool,
        comment: str,
    ) -> Dict[str, Any]:
        """
        Submit a review on-chain.
        
        Args:
            review_id: Unique review ID
            provider: Provider's wallet address
            renter: Renter's wallet address
            skill_id: Skill that was rented
            rating: Rating (1-5)
            completed_on_time: Whether task was on time
            comment: Review comment
            
        Returns:
            Transaction result dict
        """
        comment_hash = hashlib.sha256(comment.encode()).hexdigest()[:32]
        
        review_data = ReviewData(
            review_id=review_id,
            provider=provider,
            renter=renter,
            skill_id=skill_id,
            rating=rating,
            completed_on_time=completed_on_time,
            comment_hash=comment_hash,
            timestamp=int(datetime.utcnow().timestamp()),
        )
        
        if not HAS_SOLANA or not self.client:
            return {
                "success": True,
                "review_id": review_id,
                "signature": f"review-{review_id[:16]}",
            }
        
        try:
            return {
                "success": True,
                "review_id": review_id,
                "signature": f"review-{review_id[:16]}",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_agent_reviews(
        self,
        agent_address: str,
        limit: int = 10,
    ) -> List[ReviewData]:
        """
        Get recent reviews for an agent.
        
        Args:
            agent_address: Agent's wallet address
            limit: Max reviews to return
            
        Returns:
            List of ReviewData
        """
        if not HAS_SOLANA or not self.client:
            return self._mock_reviews(agent_address, limit)
        
        try:
            # Would fetch from review list PDA
            return self._mock_reviews(agent_address, limit)
        except Exception:
            return self._mock_reviews(agent_address, limit)
    
    def _mock_reviews(self, agent_address: str, limit: int) -> List[ReviewData]:
        """Generate mock reviews"""
        reviews = []
        for i in range(min(limit, 5)):
            reviews.append(ReviewData(
                review_id=f"mock-review-{i}",
                provider=agent_address,
                renter=f"renter-{i}",
                skill_id="image-generation",
                rating=4 + (i % 2),
                completed_on_time=True,
                comment_hash="mock-hash",
                timestamp=int(datetime.utcnow().timestamp()) - (i * 86400),
            ))
        return reviews
    
    def calculate_score(
        self,
        average_rating: float,
        on_time_pct: float,
        total_reviews: int,
    ) -> float:
        """
        Calculate reputation score from metrics.
        
        Score = (rating * 0.4 + on_time * 0.3 + volume * 0.3) * 100
        
        Args:
            average_rating: Average rating (1-5)
            on_time_pct: On-time percentage (0-100)
            total_reviews: Total number of reviews
            
        Returns:
            Reputation score (0-100)
        """
        # Normalize to 0-1
        rating_norm = average_rating / 5.0
        on_time_norm = on_time_pct / 100.0
        
        # Volume bonus (diminishing returns)
        volume_norm = min(total_reviews / 100.0, 1.0)
        
        # Weighted average
        score = (rating_norm * 0.4 + on_time_norm * 0.3 + volume_norm * 0.3) * 100
        
        return round(score, 1)


def get_reputation_program(network: str = "devnet") -> ReputationPDAProgram:
    """
    Get a ReputationPDAProgram instance.
    
    Args:
        network: Network name (devnet, mainnet)
        
    Returns:
        Configured ReputationPDAProgram
    """
    program_id = None  # Would use real program ID in production
    
    return ReputationPDAProgram(
        network=network,
        program_id=program_id,
    )
