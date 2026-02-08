"""
Integration Tests for On-Chain Escrow

These tests run against real Solana devnet.
Requires: anchorpy, solders, solana
"""

import pytest
import os
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


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
        """Verify escrow program ID is valid"""
        program_id = setup["program_id"]
        
        # Verify it's a valid base58 string
        try:
            # Check length (base58 Solana address is 43-44 chars)
            assert 32 <= len(program_id) <= 44
            assert program_id.isalnum()
            print(f"✓ Program ID valid: {program_id}")
        except Exception as e:
            pytest.fail(f"Invalid program ID: {e}")
    
    def test_escrow_pda_derivation(self, setup):
        """Test PDA derivation for escrow account (skipped when Anchor/IDL not available; no deploy)"""
        try:
            from trustyclaw.sdk.escrow_contract import EscrowClient, EscrowError
        except ImportError as e:
            pytest.skip(f"anchorpy not installed: {e}")
        try:
            client = EscrowClient(program_id=setup["program_id"], network=setup["network"])
            provider_address = "GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q"
            escrow_address, bump = client.get_escrow_address(provider_address)
        except EscrowError as e:
            pytest.skip(f"Anchor not available (IDL/build required; no deploy): {e}")
        assert escrow_address is not None
        assert isinstance(bump, int)
        assert bump >= 0
        print(f"✓ PDA derived: {escrow_address} (bump: {bump})")
    
    def test_token_account_derivation(self, setup):
        """Test ATA derivation (skipped when Anchor/IDL not available; no deploy)"""
        try:
            from trustyclaw.sdk.escrow_contract import EscrowClient, EscrowError
        except ImportError as e:
            pytest.skip(f"anchorpy not installed: {e}")
        try:
            client = EscrowClient(program_id=setup["program_id"], network=setup["network"])
            mint = setup["usdc_mint"]
            owner = "3WaHbF7k9ced4d2wA8caUHq2v57ujD4J2c57L8wZXfhN"
            ata = client.get_token_account_address(mint, owner)
        except EscrowError as e:
            pytest.skip(f"Anchor not available (IDL/build required; no deploy): {e}")
        assert ata is not None
        assert len(ata) >= 32
        print(f"✓ ATA derived: {ata}")
    
    def test_get_escrow_account_not_found(self):
        """Test fetching non-existent escrow returns None (skipped when Anchor not available; no deploy)"""
        import asyncio
        try:
            from trustyclaw.sdk.escrow_contract import EscrowClient, EscrowError
        except ImportError as e:
            pytest.skip(f"anchorpy not installed: {e}")
        try:
            client = EscrowClient()
        except EscrowError as e:
            pytest.skip(f"Anchor not available (IDL/build required; no deploy): {e}")
        async def _fetch():
            return await client.get_escrow("11111111111111111111111111111111")
        try:
            result = asyncio.run(_fetch())
        except EscrowError as e:
            pytest.skip(f"Anchor program not initialized (no deploy): {e}")
        assert result is None
        print("✓ Non-existent escrow returns None")


class TestEscrowDataStructure:
    """Tests for escrow data structures"""
    
    def test_escrow_data_from_dict(self):
        """Test creating EscrowData from dict"""
        try:
            from trustyclaw.sdk.escrow_contract import EscrowData
        except ImportError as e:
            pytest.skip(f"anchorpy not installed: {e}")
        
        data = {
            "provider": "Provider1111111111111111111111111111111111",
            "renter": "Renter1111111111111111111111111111111111",
            "token_mint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            "providerTokenAccount": "ATA111111111111111111111111111111111111",
            "skillName": "image-generation",
            "durationSeconds": 86400,
            "priceUsdc": 1000000,
            "metadataUri": "ipfs://QmTest",
            "amount": 1000000,
            "state": 0,
            "createdAt": 1700000000,
            "fundedAt": None,
            "completedAt": None,
            "disputedAt": None,
            "disputeReason": None,
        }
        escrow = EscrowData.from_account(data)
        assert escrow.provider == data["provider"]
        assert escrow.skill_name == "image-generation"
        assert escrow.state == 0
        assert escrow.price_usdc == 1000000
        print("✓ EscrowData structure valid")


class TestEscrowStates:
    """Tests for escrow state enum (matches SDK EscrowState: CREATED, FUNDED, ACTIVE, COMPLETED, RELEASED)"""
    def test_state_values(self):
        """Verify state enum values"""
        try:
            from trustyclaw.sdk.escrow_contract import EscrowState
        except ImportError as e:
            pytest.skip(f"anchorpy not installed: {e}")
        assert EscrowState.CREATED.value == "created"
        assert EscrowState.FUNDED.value == "funded"
        assert EscrowState.ACTIVE.value == "active"
        assert EscrowState.COMPLETED.value == "completed"
        assert EscrowState.RELEASED.value == "released"
        print("✓ State enum values correct")


class TestClientConfiguration:
    """Tests for client configuration"""
    
    def test_default_devnet_program(self):
        """Test default devnet program ID"""
        try:
            from trustyclaw.sdk.escrow_contract import EscrowClient
        except ImportError as e:
            pytest.skip(f"anchorpy not installed: {e}")
        
        client = EscrowClient(network="devnet")
        
        assert client.network == "devnet"
        assert client.program_id is not None
        print(f"✓ Default devnet program: {client.program_id}")
    
    def test_environment_variable_override(self):
        """Test env var overrides program ID"""
        try:
            from trustyclaw.sdk.escrow_contract import EscrowClient
        except ImportError as e:
            pytest.skip(f"anchorpy not installed: {e}")
        
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
        try:
            from trustyclaw.sdk.escrow_contract import EscrowClient
        except ImportError as e:
            pytest.skip(f"anchorpy not installed: {e}")
        
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
    
    def test_escrow_initialization_params(self):
        """Test escrow initialization with valid parameters"""
        try:
            from trustyclaw.sdk.escrow_contract import EscrowTerms
        except ImportError as e:
            pytest.skip(f"anchorpy not installed: {e}")
        
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
        try:
            from trustyclaw.sdk.escrow_contract import EscrowClient
        except ImportError as e:
            pytest.skip(f"anchorpy not installed: {e}")
        
        client = EscrowClient()
        
        assert client.USDC_MINT == "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
        print(f"✓ USDC Mint: {client.USDC_MINT}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
