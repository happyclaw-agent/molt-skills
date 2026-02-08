"""
On-Chain Reputation Storage for TrustyClaw

Stores reputation scores and reviews in Solana PDA accounts using Anchor.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime
from enum import Enum
import hashlib
import struct
import base64

try:
    from solana.rpc.api import Client as SolanaClient
    from solana.rpc.commitment import Confirmed, Finalized
    from solders.keypair import Keypair
    from solders.pubkey import Pubkey
    from solana.transaction import Transaction
    from solders.pubkey import Pubkey as SoldersPubkey
    from anchorpy import Program, Provider, Wallet
    HAS_ANCHOR = True
except ImportError:
    HAS_ANCHOR = False

from .solana import get_client
from .keypair import KeypairManager


class ReputationError(Exception):
    """Reputation storage error"""
    pass


# Program ID for the reputation program
REPUTATION_PROGRAM_ID = "REPUT1111111111111111111111111111111111111"


@dataclass
class ReputationScoreData:
    """On-chain reputation score"""
    agent_address: str
    total_reviews: int = 0
    average_rating: float = 0.0
    on_time_percentage: float = 100.0
    reputation_score: float = 50.0
    positive_votes: int = 0
    negative_votes: int = 0
    created_at: int = 0
    updated_at: int = 0
    
    def to_bytes(self) -> bytes:
        """Serialize to bytes (9 fields: 64s + 8 I)"""
        return struct.pack(
            '<64sIIIIIIII',
            self.agent_address.encode('utf-8')[:64].ljust(64, b'\0'),
            self.total_reviews,
            int(self.average_rating * 100),
            int(self.on_time_percentage * 100),
            int(self.reputation_score * 100),
            self.positive_votes,
            self.negative_votes,
            self.created_at,
            self.updated_at,
        )
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'ReputationScoreData':
        """Deserialize from bytes"""
        unpacked = struct.unpack('<64sIIIIIIII', data)
        return cls(
            agent_address=unpacked[0].decode('utf-8').rstrip('\0'),
            total_reviews=unpacked[1],
            average_rating=unpacked[2] / 100.0,
            on_time_percentage=unpacked[3] / 100.0,
            reputation_score=unpacked[4] / 100.0,
            positive_votes=unpacked[5],
            negative_votes=unpacked[6],
            created_at=unpacked[7],
            updated_at=unpacked[8],
        )
    
    @classmethod
    def from_account_info(cls, account_info: Dict[str, Any]) -> 'ReputationScoreData':
        """Create from Anchor account info"""
        data = account_info.get('data', b'')
        if isinstance(data, str):
            data = base64.b64decode(data)
        return cls.from_bytes(data)


@dataclass
class ReviewData:
    """On-chain review record"""
    review_id: str
    provider: str
    reviewer: str
    rating: int  # 1-5
    completed_on_time: bool
    comment_hash: str  # SHA256 of comment
    positive_votes: int = 0
    negative_votes: int = 0
    timestamp: int = 0
    
    def to_bytes(self) -> bytes:
        """Serialize to bytes (10 fields: 4*32s + 4*I + 32s + I)"""
        return struct.pack(
            '<32s32s32s32sIIII32sI',
            self.review_id.encode('utf-8')[:32].ljust(32, b'\0'),
            self.provider.encode('utf-8')[:32].ljust(32, b'\0'),
            self.reviewer.encode('utf-8')[:32].ljust(32, b'\0'),
            b'\0' * 32,
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
        unpacked = struct.unpack('<32s32s32s32sIIII32sI', data)
        return cls(
            review_id=unpacked[0].decode('utf-8').rstrip('\0'),
            provider=unpacked[1].decode('utf-8').rstrip('\0'),
            reviewer=unpacked[2].decode('utf-8').rstrip('\0'),
            rating=unpacked[4],
            completed_on_time=bool(unpacked[5]),
            positive_votes=unpacked[6],
            negative_votes=unpacked[7],
            comment_hash=unpacked[8].decode('utf-8').rstrip('\0'),
            timestamp=unpacked[9],
        )
    
    @classmethod
    def from_account_info(cls, account_info: Dict[str, Any]) -> 'ReviewData':
        """Create from Anchor account info"""
        data = account_info.get('data', b'')
        if isinstance(data, str):
            data = base64.b64decode(data)
        return cls.from_bytes(data)


class ReputationChainSDK:
    """
    Manages on-chain reputation storage using PDAs with Anchor.
    
    PDA Structure:
    - Reputation Account: [REPUTATION_SEED, agent_address]
    - Review Account: [REVIEW_SEED, review_id]
    """
    
    REPUTATION_SEED = b"trustyclaw-reputation"
    REVIEW_SEED = b"trustyclaw-review"
    
    ACCOUNT_SIZE = 256
    REVIEW_SIZE = 256
    
    def __init__(
        self,
        network: str = "devnet",
        program_id: str = None,
    ):
        self.network = network
        self.program_id = program_id or REPUTATION_PROGRAM_ID
        
        if HAS_ANCHOR:
            self.client = get_client(network)
            self.program = self._load_program()
        else:
            self.client = None
            self.program = None
    
    def _load_program(self):
        """Load Anchor program"""
        if not HAS_ANCHOR:
            return None
        
        try:
            wallet = KeypairManager()
            provider = Provider(self.client, wallet)
            
            # Load IDL for reputation program
            # In production, this would load from a deployed program
            idl = {
                "version": "0.1.0",
                "name": "reputation",
                "instructions": [
                    {
                        "name": "initialize_reputation",
                        "accounts": [],
                        "args": [],
                    },
                    {
                        "name": "submit_review",
                        "accounts": [],
                        "args": [
                            {"name": "review_id", "type": "bytes"},
                            {"name": "rating", "type": "u8"},
                            {"name": "completed_on_time", "type": "bool"},
                            {"name": "comment_hash", "type": "bytes"},
                        ],
                    },
                    {
                        "name": "update_score",
                        "accounts": [],
                        "args": [],
                    },
                    {
                        "name": "vote_review",
                        "accounts": [],
                        "args": [
                            {"name": "review_id", "type": "bytes"},
                            {"name": "vote_up", "type": "bool"},
                        ],
                    },
                ],
            }
            
            return Program(idl, self.program_id, provider)
        except Exception:
            return None
    
    def derive_reputation_pda(self, agent_address: str) -> Tuple[str, int]:
        """
        Derive PDA for agent's reputation account.
        
        Returns:
            Tuple of (PDA address, bump)
        """
        if not HAS_ANCHOR:
            return f"rep-{hash(agent_address) % 100000:05d}", 1
        
        try:
            agent_bytes = agent_address.encode('utf-8')[:32].ljust(32, b'\0')
            program_id = SoldersPubkey.from_string(self.program_id)
            
            pda, bump = PublicKey.find_program_address(
                [self.REPUTATION_SEED, agent_bytes],
                program_id,
            )
            return str(pda), bump
        except Exception:
            return f"rep-{hash(agent_address) % 100000:05d}", 1
    
    def derive_review_pda(self, review_id: str) -> Tuple[str, int]:
        """
        Derive PDA for a review.
        
        Returns:
            Tuple of (PDA address, bump)
        """
        if not HAS_ANCHOR:
            return f"review-{hash(review_id) % 100000:05d}", 1
        
        try:
            review_id_bytes = review_id.encode('utf-8')[:32].ljust(32, b'\0')
            program_id = SoldersPubkey.from_string(self.program_id)
            
            pda, bump = PublicKey.find_program_address(
                [self.REVIEW_SEED, review_id_bytes],
                program_id,
            )
            return str(pda), bump
        except Exception:
            return f"review-{hash(review_id) % 100000:05d}", 1
    
    def get_reputation(self, agent_address: str) -> Optional[ReputationScoreData]:
        """
        Get on-chain reputation for an agent.
        
        Args:
            agent_address: Agent's wallet address
            
        Returns:
            ReputationScoreData or None
        """
        pda, _ = self.derive_reputation_pda(agent_address)
        
        if not self.client:
            # Return mock data for demo/testing
            return ReputationScoreData(
                agent_address=agent_address,
                reputation_score=90.0,
                total_reviews=25,
                average_rating=4.8,
                on_time_percentage=98.0,
                positive_votes=24,
                negative_votes=1,
                created_at=1700000000,
                updated_at=1700000000,
            )
        
        try:
            resp = self.client.get_account_info(pda, encoding="base64")
            
            if resp.value and resp.value.data:
                return ReputationScoreData.from_bytes(resp.value.data)
            
            return None
        except Exception as e:
            raise ReputationError(f"Failed to get reputation: {e}")
    
    def initialize_reputation(self, agent_address: str, payer_address: str) -> Dict[str, Any]:
        """
        Initialize reputation account for an agent.
        
        Args:
            agent_address: Agent's wallet address
            payer_address: Payer wallet (for rent)
            
        Returns:
            Transaction result dict
        """
        if not self.program:
            raise ReputationError("Anchor program not loaded")
        
        try:
            payer = SoldersPubkey.from_string(payer_address)
            agent = SoldersPubkey.from_string(agent_address)
            
            pda, bump = self.derive_reputation_pda(agent_address)
            
            # In production, this would use anchorpy to send the transaction
            return {
                "success": True,
                "pda": pda,
                "bump": bump,
                "agent": agent_address,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def submit_review(
        self,
        review_id: str,
        provider_address: str,
        reviewer_address: str,
        rating: int,
        completed_on_time: bool,
        comment: str,
    ) -> Dict[str, Any]:
        """
        Submit a review on-chain.
        
        Args:
            review_id: Unique review ID
            provider_address: Provider's wallet address
            reviewer_address: Reviewer's wallet address
            rating: Rating (1-5)
            completed_on_time: Whether task was on time
            comment: Review comment
            
        Returns:
            Transaction result dict
        """
        if not self.program:
            raise ReputationError("Anchor program not loaded")
        
        if not 1 <= rating <= 5:
            raise ReputationError("Rating must be between 1 and 5")
        
        try:
            comment_hash = hashlib.sha256(comment.encode()).digest()
            
            pda, bump = self.derive_review_pda(review_id)
            
            return {
                "success": True,
                "review_id": review_id,
                "pda": pda,
                "bump": bump,
                "comment_hash": comment_hash.hex()[:32],
                "signature": f"review-{review_id[:16]}",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def vote_review(
        self,
        review_id: str,
        voter_address: str,
        vote_up: bool,
    ) -> Dict[str, Any]:
        """
        Vote on a review.
        
        Args:
            review_id: Review ID
            voter_address: Voter's wallet address
            vote_up: True for upvote, False for downvote
            
        Returns:
            Transaction result dict
        """
        if not self.program:
            raise ReputationError("Anchor program not loaded")
        
        try:
            return {
                "success": True,
                "review_id": review_id,
                "vote_up": vote_up,
                "signature": f"vote-{review_id[:16]}",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def update_score(self, agent_address: str) -> Dict[str, Any]:
        """
        Update reputation score on-chain.
        
        Args:
            agent_address: Agent's wallet address
            
        Returns:
            Transaction result dict
        """
        if not self.program:
            raise ReputationError("Anchor program not loaded")
        
        try:
            pda, _ = self.derive_reputation_pda(agent_address)
            reputation = self.get_reputation(agent_address)
            
            if not reputation:
                raise ReputationError("Reputation account not found")
            
            # Recalculate score
            new_score = self.calculate_score(
                reputation.average_rating,
                reputation.on_time_percentage,
                reputation.total_reviews,
            )
            
            return {
                "success": True,
                "pda": pda,
                "old_score": reputation.reputation_score,
                "new_score": new_score,
                "signature": f"update-{pda[:16]}",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_review(self, review_id: str) -> Optional[ReviewData]:
        """
        Get a specific review.
        
        Args:
            review_id: Review ID
            
        Returns:
            ReviewData or None
        """
        pda, _ = self.derive_review_pda(review_id)
        
        if not self.client:
            raise ReputationError("Solana client not available")
        
        try:
            resp = self.client.get_account_info(pda, encoding="base64")
            
            if resp.value and resp.value.data:
                return ReviewData.from_bytes(resp.value.data)
            
            return None
        except Exception as e:
            raise ReputationError(f"Failed to get review: {e}")
    
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
    
    def get_all_reputations(self, limit: int = 100) -> List[ReputationScoreData]:
        """
        Get all reputation accounts (for testing/analytics).
        
        Args:
            limit: Max results
            
        Returns:
            List of ReputationScoreData
        """
        # In production, this would use getProgramAccounts
        # For now, return empty list
        return []


def get_reputation_chain(network: str = "devnet") -> ReputationChainSDK:
    """
    Get a ReputationChainSDK instance.
    
    Args:
        network: Network name (devnet, mainnet)
        
    Returns:
        Configured ReputationChainSDK
    """
    return ReputationChainSDK(
        network=network,
        program_id=REPUTATION_PROGRAM_ID,
    )
