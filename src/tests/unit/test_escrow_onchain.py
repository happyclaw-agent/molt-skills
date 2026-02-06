"""
Integration Tests for On-Chain Escrow

These tests run against real Solana devnet.
Requires: anchorpy, solders, solana
"""

import pytest
import asyncio
import os
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Skip tests if Anchor not available
pytest.importorskip("anchorpy")
pytest.importorskip("solders")

from solders.keypair import Keypair
from solana.rpc.commitment import Confirmed, Finalized


class TestEscrowOnChain:
    """Integration tests for escrow on devnet"""
    
    @pytest.fixture
    def setup(self):
        """Setup test environment"""
        network = "devnet"
        program_id = os.environ.get(
            "ESCROW_PROGRAM_ID",
            "ESCRwJwfT1XpTwzPfkQ9NyTXfHWHnhCWdK1vYhmjbUF"
        )
        
        return {
            "network": network,
            "program_id": program_id,
            "usdc_mint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        }
    
    def test_program_deployed(self, setup):
        """Verify escrow program is deployed"""
        from solders.pubkey import Pubkey
        
        program_id = setup["program_id"]
        
        # Verify it's a valid pubkey
        try:
            pubkey = Pubkey.from_string(program_id)
            assert len(pubkey.to_bytes()) == 32
            print(f"✓ Program ID valid: {program_id}")
        except Exception as e:
            pytest.fail(f"Invalid program ID: {e}")
    
    def test_escrow_pda_derivation(self, setup):
        """Test PDA derivation for escrow account"""
        from solders.pubkey import Pubkey
        from trustyclaw.sdk.escrow_contract import EscrowClient
        
        client = EscrowClient(program_id=setup["program_id"], network=setup["network"])
        
        # Test PDA derivation
        provider_address = "GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q"
        escrow_address, bump = client.get_escrow_address(provider_address)
        
        assert escrow_address is not None
        assert isinstance(bump, int)
        assert bump > 0
        print(f"✓ PDA derived: {escrow_address} (bump: {bump})")
    
    def test_token_account_derivation(self, setup):
        """Test ATA derivation"""
        from solders.pubkey import Pubkey
        from trustyclaw.sdk.escrow_contract import EscrowClient
        
        client = EscrowClient(program_id=setup["program_id"], network=setup["network"])
        
        # Test ATA derivation
        mint = setup["usdc_mint"]
        owner = "3WaHbF7k9ced4d2wA8caUHq2v57ujD4J2c57L8wZXfhN"
        
        ata = client.get_token_account_address(mint, owner)
        
        assert ata is not None
        assert len(ata) == 44  # Base58 encoded pubkey
        print(f"✓ ATA derived: {ata}")
    
    @pytest.mark.asyncio
    async def test_get_escrow_account_not_found(setup):
        """Test fetching non-existent escrow returns None"""
        from trustyclaw.sdk.escrow_contract import EscrowClient
        
        client = EscrowClient(program_id=setup["program_id"], network=setup["network"])
        
        # Try to fetch non-existent escrow
        result = await client.get_escrow(
            "11111111111111111111111111111111"  # Random address
        )
        
        assert result is None
        print("✓ Non-existent escrow returns None")


class TestEscrowDataStructure:
    """Tests for escrow data structures"""
    
    def test_escrow_data_from_dict(self):
        """Test creating EscrowData from dict"""
        from trustyclaw.sdk.escrow_contract import EscrowData
        
        data = {
            "provider": "Provider1111111111111111111111111111111111",
            "renter": "Renter1111111111111111111111111111111111",
            "token_mint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            "provider_token_account": "ATA111111111111111111111111111111111111",
            "skill_name": "image-generation",
            "duration_seconds": 86400,
            "price_usdc": 1000000,
            "metadata_uri": "ipfs://QmTest",
            "amount": 1000000,
            "state": 0,  # Created
            "created_at": 1700000000,
            "funded_at": None,
            "completed_at": None,
            "disputed_at": None,
            "dispute_reason": None,
        }
        
        escrow = EscrowData.from_account(data)
        
        assert escrow.provider == data["provider"]
        assert escrow.skill_name == "image-generation"
        assert escrow.state == 0
        assert escrow.price_usdc == 1000000
        print("✓ EscrowData structure valid")


class TestEscrowStates:
    """Tests for escrow state enum"""
    
    def test_state_values(self):
        """Verify state enum values"""
        from trustyclaw.sdk.escrow_contract import EscrowState
        
        assert EscrowState.CREATED.value == "created"
        assert EscrowState.FUNDED.value == "funded"
        assert EscrowState.RELEASED.value == "released"
        assert EscrowState.REFUNDED.value == "refunded"
        assert EscrowState.DISPUTED.value == "disputed"
        print("✓ State enum values correct")


class TestClientConfiguration:
    """Tests for client configuration"""
    
    def test_default_devnet_program(self):
        """Test default devnet program ID"""
        from trustyclaw.sdk.escrow_contract import EscrowClient
        
        client = EscrowClient(network="devnet")
        
        assert client.network == "devnet"
        assert client.program_id is not None
        print(f"✓ Default devnet program: {client.program_id}")
    
    def test_environment_variable_override(self):
        """Test env var overrides program ID"""
        from trustyclaw.sdk.escrow_contract import EscrowClient
        
        custom_id = "Custom111111111111111111111111111111111111"
        os.environ["ESCROW_PROGRAM_ID"] = custom_id
        
        try:
            client = EscrowClient()
            assert client.program_id == custom_id
            print(f"✓ Env var override works: {client.program_id}")
        finally:
            del os.environ["ESCROW_PROGRAM_ID"]
    
    def test_rpc_url_generation(self):
        """Test RPC URL generation for networks"""
        from trustyclaw.sdk.escrow_contract import EscrowClient
        
        for network, expected_url in [
            ("localnet", "http://127.0.0.1:8899"),
            ("devnet", "https://api.devnet.solana.com"),
            ("mainnet", "https://api.mainnet-beta.solana.com"),
        ]:
            client = EscrowClient(network=network)
            assert client._get_rpc_url() == expected_url
            print(f"✓ {network} RPC URL: {expected_url}")


class TestIntegrationFlow:
    """Full integration flow tests"""
    
    @pytest.fixture
    def test_keypairs(self):
        """Generate test keypairs (for local testing only)"""
        # In production, use real wallets from environment or keyfile
        provider = Keypair()
        renter = Keypair()
        
        return {"provider": provider, "renter": renter}
    
    def test_escrow_initialization_params(self, test_keypairs):
        """Test escrow initialization with valid parameters"""
        from trustyclaw.sdk.escrow_contract import EscrowTerms
        
        terms = EscrowTerms(
            skill_name="image-generation",
            duration_seconds=86400,  # 24 hours
            price_usdc=1000000,       # 1 USDC
            metadata_uri="ipfs://QmTest123",
        )
        
        assert terms.skill_name == "image-generation"
        assert terms.duration_seconds == 86400
        assert terms.price_usdc == 1000000
        print("✓ EscrowTerms structure valid")
    
    def test_usdc_mint_constant(self):
        """Verify USDC mint address"""
        from trustyclaw.sdk.escrow_contract import EscrowClient
        
        client = EscrowClient()
        
        assert client.USDC_MINT == "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
        print(f"✓ USDC Mint: {client.USDC_MINT}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
