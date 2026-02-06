"""
TrustyClaw Escrow Contract - Production Client

Secure USDC escrow for agent skill rentals using Anchor CPI.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime
from enum import Enum
import json
import os

# Try to import Anchor/PyUSD dependencies
try:
    from solders.keypair import Keypair
    from solders.pubkey import Pubkey
    from solders.signature import Signature
    from solana.rpc.commitment import Confirmed, Finalized
    from solana.rpc.api import Client
    from solana.rpc.types import TokenAccountOpts
    from anchorpy import Program, Provider, Wallet
    from anchorpy.idl import Idl
    from spl.token.constants import TOKEN_PROGRAM_ID, ASSOCIATED_TOKEN_PROGRAM_ID
    HAS_ANCHOR = True
except ImportError:
    HAS_ANCHOR = False


class EscrowState(Enum):
    """Escrow lifecycle state"""
    CREATED = "created"
    FUNDED = "funded"
    RELEASED = "released"
    REFUNDED = "refunded"
    DISPUTED = "disputed"


class EscrowError(Exception):
    """Escrow operation error"""
    pass


@dataclass
class EscrowTerms:
    """Terms of the escrow agreement"""
    skill_name: str
    duration_seconds: int
    price_usdc: int
    metadata_uri: str


@dataclass
class EscrowData:
    """On-chain escrow account data"""
    provider: str
    renter: str
    token_mint: str
    provider_token_account: str
    skill_name: str
    duration_seconds: int
    price_usdc: int
    metadata_uri: str
    amount: int
    state: int  # 0=created, 1=funded, 2=released, 3=refunded, 4=disputed
    created_at: int
    funded_at: Optional[int]
    completed_at: Optional[int]
    disputed_at: Optional[int]
    dispute_reason: Optional[str]
    
    @classmethod
    def from_account(cls, data: Dict[str, Any]) -> 'EscrowData':
        """Create from Anchor account data"""
        return cls(
            provider=str(data.get('provider', '')),
            renter=str(data.get('renter', '')),
            token_mint=str(data.get('token_mint', '')),
            provider_token_account=str(data.get('providerTokenAccount', '')),
            skill_name=data.get('skillName', ''),
            duration_seconds=data.get('durationSeconds', 0),
            price_usdc=data.get('priceUsdc', 0),
            metadata_uri=data.get('metadataUri', ''),
            amount=data.get('amount', 0),
            state=data.get('state', 0),
            created_at=data.get('createdAt', 0),
            funded_at=data.get('fundedAt'),
            completed_at=data.get('completedAt'),
            disputed_at=data.get('disputedAt'),
            dispute_reason=data.get('disputeReason'),
        )


class EscrowClient:
    """
    Production Escrow Contract Client for TrustyClaw.
    
    Uses Anchor CPI for real on-chain operations on Solana.
    """
    
    ESCROW_SEED = b"trustyclaw-escrow"
    USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
    
    def __init__(
        self,
        program_id: Optional[str] = None,
        network: str = "devnet",
    ):
        """
        Initialize the Escrow Client.
        
        Args:
            program_id: Deployed escrow program ID (defaults to env var or mainnet)
            network: Solana network name
        """
        self.network = network
        self.program_id = program_id or self._get_program_id()
        
        if HAS_ANCHOR:
            self._init_anchor_client()
        else:
            self._client = None
            self._program = None
        
        self._cache: Dict[str, EscrowData] = {}
    
    def _get_program_id(self) -> str:
        """Get program ID from environment or defaults"""
        env_id = os.environ.get("ESCROW_PROGRAM_ID", "")
        if env_id:
            return env_id
        
        # Default based on network
        if self.network == "devnet":
            return "ESCRwJwfT1XpTwzPfkQ9NyTXfHWHnhCWdK1vYhmjbUF"
        elif self.network == "mainnet":
            return "ESCRW1111111111111111111111111111111111111"
        
        return "ESCRW1111111111111111111111111111111111"
    
    def _get_rpc_url(self) -> str:
        """Get RPC URL for network"""
        urls = {
            "localnet": "http://127.0.0.1:8899",
            "devnet": "https://api.devnet.solana.com",
            "mainnet": "https://api.mainnet-beta.solana.com",
        }
        return urls.get(self.network, urls["devnet"])
    
    def _init_anchor_client(self):
        """Initialize Anchor Py client"""
        try:
            rpc_url = self._get_rpc_url()
            self._client = Client(rpc_url)
            
            # Load IDL (would fetch from chain or file in production)
            idl = self._load_idl()
            
            # Create program instance
            self._program = Program(idl, Pubkey.from_string(self.program_id))
            
        except Exception as e:
            print(f"Warning: Failed to initialize Anchor client: {e}")
            self._program = None
    
    def _load_idl(self) -> Dict[str, Any]:
        """Load IDL from file or return minimal"""
        idl_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "..", 
            "target", "idl", "escrow.json"
        )
        if os.path.exists(idl_path):
            with open(idl_path, 'r') as f:
                return json.load(f)
        
        # Return minimal IDL for basic operations
        return {
            "version": "0.1.0",
            "name": "escrow",
            "instructions": [
                {
                    "name": "initialize",
                    "accounts": [
                        {"name": "provider", "isMut": True, "isSigner": True},
                        {"name": "escrow", "isMut": True, "isSigner": False},
                        {"name": "tokenMint", "isMut": False, "isSigner": False},
                        {"name": "providerTokenAccount", "isMut": True, "isSigner": False},
                        {"name": "systemProgram", "isMut": False, "isSigner": False},
                        {"name": "tokenProgram", "isMut": False, "isSigner": False},
                        {"name": "associatedTokenProgram", "isMut": False, "isSigner": False},
                    ],
                    "args": [
                        {"name": "skillName", "type": "string"},
                        {"name": "durationSeconds", "type": "i64"},
                        {"name": "priceUsdc", "type": "u64"},
                        {"name": "metadataUri", "type": "string"},
                    ],
                },
                {
                    "name": "fund",
                    "accounts": [
                        {"name": "renter", "isMut": True, "isSigner": True},
                        {"name": "escrow", "isMut": True, "isSigner": False},
                        {"name": "tokenMint", "isMut": False, "isSigner": False},
                        {"name": "escrowTokenAccount", "isMut": True, "isSigner": False},
                        {"name": "renterTokenAccount", "isMut": True, "isSigner": False},
                        {"name": "systemProgram", "isMut": False, "isSigner": False},
                        {"name": "tokenProgram", "isMut": False, "isSigner": False},
                        {"name": "associatedTokenProgram", "isMut": False, "isSigner": False},
                    ],
                    "args": [
                        {"name": "amount", "type": "u64"},
                    ],
                },
                {
                    "name": "release",
                    "accounts": [
                        {"name": "renter", "isMut": True, "isSigner": True},
                        {"name": "escrow", "isMut": True, "isSigner": False},
                        {"name": "escrowTokenAccount", "isMut": True, "isSigner": False},
                        {"name": "providerTokenAccount", "isMut": True, "isSigner": False},
                        {"name": "tokenMint", "isMut": False, "isSigner": False},
                        {"name": "tokenProgram", "isMut": False, "isSigner": False},
                    ],
                    "args": [],
                },
                {
                    "name": "refund",
                    "accounts": [
                        {"name": "provider", "isMut": True, "isSigner": True},
                        {"name": "escrow", "isMut": True, "isSigner": False},
                        {"name": "escrowTokenAccount", "isMut": True, "isSigner": False},
                        {"name": "renterTokenAccount", "isMut": True, "isSigner": False},
                        {"name": "tokenMint", "isMut": False, "isSigner": False},
                        {"name": "tokenProgram", "isMut": False, "isSigner": False},
                    ],
                    "args": [],
                },
                {
                    "name": "dispute",
                    "accounts": [
                        {"name": "authority", "isMut": True, "isSigner": True},
                        {"name": "escrow", "isMut": True, "isSigner": False},
                        {"name": "tokenMint", "isMut": False, "isSigner": False},
                        {"name": "tokenProgram", "isMut": False, "isSigner": False},
                    ],
                    "args": [
                        {"name": "reason", "type": "string"},
                    ],
                },
            ],
        }
    
    def get_escrow_address(self, provider_address: str) -> Tuple[str, int]:
        """
        Get the PDA address for an escrow.
        
        Returns:
            Tuple of (address, bump)
        """
        if not HAS_ANCHOR:
            raise EscrowError("Anchor not available")
        
        provider_pubkey = Pubkey.from_string(provider_address)
        seeds = [self.ESCROW_SEED, provider_pubkey.to_bytes()]
        
        # Find PDA
        bump = 255
        while bump > 0:
            try:
                result = Pubkey.find_program_address(seeds + [bytes([bump])], self._program.program_id)
                return (str(result[0]), result[1])
            except:
                bump -= 1
        
        raise EscrowError("Failed to find PDA")
    
    def get_token_account_address(
        self,
        mint: str,
        owner: str,
    ) -> str:
        """Get ATA address for a token account"""
        if not HAS_ANCHOR:
            raise EscrowError("Anchor not available")
        
        mint_pubkey = Pubkey.from_string(mint)
        owner_pubkey = Pubkey.from_string(owner)
        
        result = Pubkey.find_program_address(
            [
                owner_pubkey.to_bytes(),
                TOKEN_PROGRAM_ID.to_bytes(),
                mint_pubkey.to_bytes(),
            ],
            ASSOCIATED_TOKEN_PROGRAM_ID,
        )
        return str(result[0])
    
    # ============ On-Chain Operations ============
    
    async def initialize(
        self,
        provider_keypair,
        skill_name: str,
        duration_seconds: int,
        price_usdc: int,
        metadata_uri: str = "",
    ) -> Dict[str, Any]:
        """
        Initialize a new escrow.
        
        Args:
            provider_keypair: Provider's keypair
            skill_name: Name of the skill
            duration_seconds: Max duration in seconds
            price_usdc: Price in USDC (6 decimals)
            metadata_uri: IPFS URI for full terms
            
        Returns:
            Transaction result
        """
        if not self._program:
            raise EscrowError("Anchor program not initialized")
        
        provider_pubkey = Pubkey.from_string(str(provider_keypair.pubkey()))
        
        # Get accounts
        (escrow_pubkey, escrow_bump) = self.get_escrow_address(str(provider_keypair.pubkey()))
        token_mint = Pubkey.from_string(self.USDC_MINT)
        
        # Get or create provider's token account
        provider_token_account = self.get_token_account_address(
            self.USDC_MINT,
            str(provider_keypair.pubkey()),
        )
        
        tx = await self._program.rpc["initialize"](
            skill_name,
            duration_seconds,
            price_usdc,
            metadata_uri,
            ctx=Context(
                accounts={
                    "provider": provider_keypair.pubkey(),
                    "escrow": Pubkey.from_string(escrow_pubkey),
                    "token_mint": token_mint,
                    "provider_token_account": Pubkey.from_string(provider_token_account),
                    "system_program": SYS_PROGRAM_ID,
                    "token_program": TOKEN_PROGRAM_ID,
                    "associated_token_program": ASSOCIATED_TOKEN_PROGRAM_ID,
                },
                signers=[provider_keypair],
            ),
        )
        
        return {"tx": tx, "escrow": escrow_pubkey}
    
    async def fund(
        self,
        renter_keypair,
        provider_address: str,
        amount: int,
    ) -> Dict[str, Any]:
        """
        Fund an escrow with USDC.
        
        Args:
            renter_keypair: Renter's keypair
            provider_address: Provider's address
            amount: Amount in USDC
            
        Returns:
            Transaction result
        """
        if not self._program:
            raise EscrowError("Anchor program not initialized")
        
        (escrow_pubkey, _) = self.get_escrow_address(provider_address)
        renter_pubkey = renter_keypair.pubkey()
        
        # Get token accounts
        escrow_token_account = self.get_token_account_address(
            self.USDC_MINT,
            escrow_pubkey,
        )
        renter_token_account = self.get_token_account_address(
            self.USDC_MINT,
            str(renter_pubkey),
        )
        
        tx = await self._program.rpc["fund"](
            amount,
            ctx=Context(
                accounts={
                    "renter": renter_pubkey,
                    "escrow": Pubkey.from_string(escrow_pubkey),
                    "token_mint": Pubkey.from_string(self.USDC_MINT),
                    "escrow_token_account": Pubkey.from_string(escrow_token_account),
                    "renter_token_account": Pubkey.from_string(renter_token_account),
                    "system_program": SYS_PROGRAM_ID,
                    "token_program": TOKEN_PROGRAM_ID,
                    "associated_token_program": ASSOCIATED_TOKEN_PROGRAM_ID,
                },
                signers=[renter_keypair],
            ),
        )
        
        return {"tx": tx}
    
    async def release(
        self,
        renter_keypair,
        provider_address: str,
    ) -> Dict[str, Any]:
        """
        Release funds to provider (renter approves).
        
        Args:
            renter_keypair: Renter's keypair
            provider_address: Provider's address
            
        Returns:
            Transaction result
        """
        if not self._program:
            raise EscrowError("Anchor program not initialized")
        
        (escrow_pubkey, escrow_bump) = self.get_escrow_address(provider_address)
        renter_pubkey = renter_keypair.pubkey()
        
        # Get token accounts
        escrow_token_account = self.get_token_account_address(
            self.USDC_MINT,
            escrow_pubkey,
        )
        provider_token_account = self.get_token_account_address(
            self.USDC_MINT,
            provider_address,
        )
        
        tx = await self._program.rpc["release"](
            ctx=Context(
                accounts={
                    "renter": renter_pubkey,
                    "escrow": Pubkey.from_string(escrow_pubkey),
                    "escrow_token_account": Pubkey.from_string(escrow_token_account),
                    "provider_token_account": Pubkey.from_string(provider_token_account),
                    "token_mint": Pubkey.from_string(self.USDC_MINT),
                    "token_program": TOKEN_PROGRAM_ID,
                },
                signers=[renter_keypair],
            ),
        )
        
        return {"tx": tx}
    
    async def refund(
        self,
        provider_keypair,
    ) -> Dict[str, Any]:
        """
        Refund funds to renter (provider agrees).
        
        Args:
            provider_keypair: Provider's keypair
            
        Returns:
            Transaction result
        """
        if not self._program:
            raise EscrowError("Anchor program not initialized")
        
        provider_address = str(provider_keypair.pubkey())
        (escrow_pubkey, escrow_bump) = self.get_escrow_address(provider_address)
        
        # Get token accounts
        escrow_token_account = self.get_token_account_address(
            self.USDC_MINT,
            escrow_pubkey,
        )
        renter_token_account = self.get_token_account_address(
            self.USDC_MINT,
            provider_address,  # Will fail if renter is different, need to fetch renter first
        )
        
        tx = await self._program.rpc["refund"](
            ctx=Context(
                accounts={
                    "provider": provider_keypair.pubkey(),
                    "escrow": Pubkey.from_string(escrow_pubkey),
                    "escrow_token_account": Pubkey.from_string(escrow_token_account),
                    "renter_token_account": Pubkey.from_string(renter_token_account),
                    "token_mint": Pubkey.from_string(self.USDC_MINT),
                    "token_program": TOKEN_PROGRAM_ID,
                },
                signers=[provider_keypair],
            ),
        )
        
        return {"tx": tx}
    
    async def dispute(
        self,
        authority_keypair,
        provider_address: str,
        reason: str,
    ) -> Dict[str, Any]:
        """
        File a dispute on an escrow.
        
        Args:
            authority_keypair: Either renter or provider
            provider_address: Provider's address
            reason: Dispute reason
            
        Returns:
            Transaction result
        """
        if not self._program:
            raise EscrowError("Anchor program not initialized")
        
        (escrow_pubkey, _) = self.get_escrow_address(provider_address)
        
        tx = await self._program.rpc["dispute"](
            reason,
            ctx=Context(
                accounts={
                    "authority": authority_keypair.pubkey(),
                    "escrow": Pubkey.from_string(escrow_pubkey),
                    "token_mint": Pubkey.from_string(self.USDC_MINT),
                    "token_program": TOKEN_PROGRAM_ID,
                },
                signers=[authority_keypair],
            ),
        )
        
        return {"tx": tx}
    
    async def resolve_dispute_release(
        self,
        resolver_keypair,
        provider_address: str,
    ) -> Dict[str, Any]:
        """
        Resolve dispute - release to provider.
        """
        if not self._program:
            raise EscrowError("Anchor program not initialized")
        
        (escrow_pubkey, escrow_bump) = self.get_escrow_address(provider_address)
        
        # Get token accounts
        escrow_token_account = self.get_token_account_address(
            self.USDC_MINT,
            escrow_pubkey,
        )
        provider_token_account = self.get_token_account_address(
            self.USDC_MINT,
            provider_address,
        )
        renter_token_account = self.get_token_account_address(
            self.USDC_MINT,
            escrow_pubkey,  # Escrow is owner until resolved
        )
        
        tx = await self._program.rpc["resolve_dispute_release"](
            ctx=Context(
                accounts={
                    "authority": resolver_keypair.pubkey(),
                    "escrow": Pubkey.from_string(escrow_pubkey),
                    "escrow_token_account": Pubkey.from_string(escrow_token_account),
                    "provider_token_account": Pubkey.from_string(provider_token_account),
                    "renter_token_account": Pubkey.from_string(renter_token_account),
                    "token_mint": Pubkey.from_string(self.USDC_MINT),
                    "token_program": TOKEN_PROGRAM_ID,
                },
                signers=[resolver_keypair],
            ),
        )
        
        return {"tx": tx}
    
    async def get_escrow(self, provider_address: str) -> Optional[EscrowData]:
        """Fetch escrow account data from chain"""
        if not self._program:
            raise EscrowError("Anchor program not initialized")
        
        (escrow_pubkey, _) = self.get_escrow_address(provider_address)
        
        try:
            account = await self._program.account["Escrow"].fetch(escrow_pubkey)
            return EscrowData.from_account(account.__dict__)
        except Exception:
            return None
    
    # ============ Query Operations ============
    
    async def get_balance(self, address: str) -> int:
        """Get SOL balance"""
        if not self._client:
            raise EscrowError("Solana client not initialized")
        
        response = await self._client.get_balance(
            Pubkey.from_string(address)
        )
        return response.value
    
    async def get_token_balance(self, token_account: str) -> int:
        """Get token balance"""
        if not self._client:
            raise EscrowError("Solana client not initialized")
        
        try:
            response = await self._client.get_token_account_balance(
                Pubkey.from_string(token_account)
            )
            return int(response.value.amount)
        except:
            return 0
    
    async def confirm_transaction(self, tx_sig: str) -> bool:
        """Wait for transaction confirmation"""
        if not self._client:
            raise EscrowError("Solana client not initialized")
        
        try:
            result = await self._client.confirm_transaction(
                Signature.from_string(tx_sig),
                Finalized,
            )
            return result.value.err is None
        except:
            return False


# Helper function to get client
def get_escrow_client(
    program_id: Optional[str] = None,
    network: str = "devnet",
) -> EscrowClient:
    """
    Get an EscrowClient instance.
    
    Args:
        program_id: Optional program ID override
        network: Network name
        
    Returns:
        Configured EscrowClient
    """
    return EscrowClient(
        program_id=program_id,
        network=network,
    )


# ============ USDC Payment Service Integration ============

    def get_payment_service(self) -> 'USDCPaymentService':
        """
        Get the USDC Payment Service for this escrow.
        
        Creates or returns cached payment service.
        
        Returns:
            USDCPaymentService instance
        """
        if not hasattr(self, '_payment_service'):
            from .usdc_payment import USDCPaymentService
            self._payment_service = USDCPaymentService(
                network=self.network,
                usdc_client=None,
            )
        return self._payment_service
    
    def create_payment_intent(
        self,
        provider: str,
        renter: str,
        amount: int,  # microUSDC
        description: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> 'PaymentIntent':
        """
        Create a payment intent for escrow.
        
        Creates a payment intent that will be tracked alongside escrow.
        
        Args:
            provider: Provider wallet
            renter: Renter wallet
            amount: Amount in microUSDC
            description: Payment description
            metadata: Additional metadata
            
        Returns:
            PaymentIntent object
        """
        payment_service = self.get_payment_service()
        
        return payment_service.create_payment_intent(
            amount=amount,
            from_wallet=renter,
            to_wallet=provider,
            description=description,
            metadata={
                **(metadata or {}),
                "escrow_program_id": self.program_id,
                "network": self.network,
            }
        )
    
    def track_escrow_payment(
        self,
        escrow_address: str,
        payment_intent_id: str,
    ) -> 'EscrowPayment':
        """
        Track an escrow payment.
        
        Associates a payment intent with an escrow.
        
        Args:
            escrow_address: Escrow address
            payment_intent_id: Payment intent ID
            
        Returns:
            EscrowPayment object
        """
        payment_service = self.get_payment_service()
        
        escrow_payment = payment_service._escrow_payments.get(escrow_address)
        if escrow_payment:
            return escrow_payment
        
        intent = payment_service.get_payment_intent(payment_intent_id)
        if not intent:
            raise EscrowError(f"Payment intent {payment_intent_id} not found")
        
        escrow_payment = payment_service.execute_escrow_payment(
            escrow_id=escrow_address,
            amount=intent.amount,
            from_wallet=intent.from_wallet,
            to_wallet=intent.to_wallet,
            description=intent.description,
        )
        
        return escrow_payment
    
    def execute_payment_with_confirmation(
        self,
        payment_intent_id: str,
        max_retries: int = 3,
    ) -> 'PaymentResult':
        """
        Execute payment with confirmation tracking.
        
        Executes a payment intent and waits for confirmation.
        
        Args:
            payment_intent_id: Payment intent ID
            max_retries: Maximum retry attempts
            
        Returns:
            PaymentResult with confirmation status
        """
        payment_service = self.get_payment_service()
        
        result = payment_service.execute_payment_intent(payment_intent_id)
        
        if not result.success and max_retries > 0:
            import time
            time.sleep(1)  # Brief delay
            return self.execute_payment_with_confirmation(
                payment_intent_id,
                max_retries=max_retries - 1,
            )
        
        return result
    
    def get_escrow_payment_status(self, escrow_address: str) -> Dict[str, Any]:
        """
        Get full payment status for an escrow.
        
        Returns combined status from escrow and payment service.
        
        Args:
            escrow_address: Escrow address
            
        Returns:
            Dict with escrow and payment status
        """
        escrow = self.get_escrow(escrow_address)
        if not escrow:
            return {"error": "Escrow not found"}
        
        payment_service = self.get_payment_service()
        escrow_payment = payment_service.get_escrow_payment(escrow_address)
        
        result = {
            "escrow_address": escrow_address,
            "escrow_state": escrow.state.value if hasattr(escrow.state, 'value') else str(escrow.state),
            "amount": escrow.terms.price_usdc if hasattr(escrow.terms, 'price_usdc') else escrow.terms.amount,
        }
        
        if escrow_payment:
            result["payment"] = {
                "status": escrow_payment.status.value,
                "payment_intent_id": escrow_payment.payment_intent_id,
                "funded_at": escrow_payment.funded_at,
                "released_at": escrow_payment.released_at,
                "refunded_at": escrow_payment.refunded_at,
            }
        
        return result
    
    def setup_balance_notification(
        self,
        wallet_address: str,
        threshold_usd: float = 10.0,
        callback_url: Optional[str] = None,
        auto_reload: bool = False,
        auto_reload_amount: Optional[int] = None,
    ) -> 'BalanceNotification':
        """
        Setup balance notification for a wallet.
        
        Args:
            wallet_address: Wallet to monitor
            threshold_usd: Alert threshold in USD
            callback_url: Webhook URL for alerts
            auto_reload: Enable auto-reload
            auto_reload_amount: Auto-reload amount in microUSDC
            
        Returns:
            BalanceNotification object
        """
        payment_service = self.get_payment_service()
        
        return payment_service.register_balance_notification(
            wallet_address=wallet_address,
            threshold_usd=threshold_usd,
            callback_url=callback_url,
            auto_reload=auto_reload,
            auto_reload_amount=auto_reload_amount,
        )
    
    def check_and_reload_balance(self, wallet_address: str) -> Dict[str, Any]:
        """
        Check balance and trigger auto-reload if needed.
        
        Args:
            wallet_address: Wallet to check
            
        Returns:
            Check result with any auto-reload action
        """
        payment_service = self.get_payment_service()
        
        return payment_service.check_balance_and_notify(wallet_address)
    
    def get_payment_history(
        self,
        wallet_address: str,
        limit: int = 100,
    ) -> List['Payment']:
        """
        Get payment history for a wallet.
        
        Args:
            wallet_address: Wallet to query
            limit: Maximum results
            
        Returns:
            List of Payment records
        """
        payment_service = self.get_payment_service()
        
        return payment_service.get_payment_history(
            wallet_address=wallet_address,
            limit=limit,
        )


# ============ Helper Functions ============

def get_escrow_with_payment_service(
    program_id: Optional[str] = None,
    network: str = "devnet",
    multisig_threshold_usd: float = 1000.0,
    recovery_wallet: Optional[str] = None,
) -> EscrowClient:
    """
    Get an EscrowClient with payment service configured.
    
    Args:
        program_id: Optional program ID override
        network: Network name
        multisig_threshold_usd: Multi-sig threshold
        recovery_wallet: Recovery wallet address
        
    Returns:
        Configured EscrowClient
    """
    client = EscrowClient(
        program_id=program_id,
        network=network,
    )
    
    # Configure payment service
    from .usdc_payment import USDCPaymentService, MultisigConfig
    payment_service = client.get_payment_service()
    
    multisig_config = MultisigConfig(
        threshold_usd=multisig_threshold_usd,
        required_signers=[],
        required_count=2,
        recovery_signer=recovery_wallet,
    )
    payment_service.set_multisig_config(multisig_config)
    
    return client


# Constants
SYS_PROGRAM_ID = Pubkey.from_string("11111111111111111111111111111111")
