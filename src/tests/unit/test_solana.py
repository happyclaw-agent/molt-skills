"""
Tests for Solana RPC Client
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.trustyclaw.sdk.solana import (
    SolanaRPCClient,
    WalletInfo,
    TransactionInfo,
    Network,
    get_client,
)


class TestWalletInfo:
    """Tests for WalletInfo dataclass"""
    
    def test_sol_balance(self):
        """Test SOL balance conversion"""
        wallet = WalletInfo(
            address="GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q",
            lamports=1_000_000_000,
            usdc_balance=100.0,
        )
        assert wallet.sol_balance == 1.0
    
    def test_usdc_balance(self):
        """Test USDC balance storage"""
        wallet = WalletInfo(
            address="3WaHbF7k9ced4d2wA8caUHq2v57ujD4J2c57L8wZXfhN",
            lamports=2_000_000_000,
            usdc_balance=50.5,
        )
        assert wallet.usdc_balance == 50.5


class TestTransactionInfo:
    """Tests for TransactionInfo dataclass"""
    
    def test_explorer_url(self):
        """Test Explorer URL generation"""
        tx = TransactionInfo(
            signature="5hJ7Xg8Yz3N7JW6Z7Z2V4K8Y9Q1M2N3O4P5Q6R7S8T9U0V1W2X3Y4Z5A6B7C8D9E0F",
            slot=100,
            status="confirmed",
        )
        assert "explorer.solana.com" in tx.explorer_url
        assert tx.signature in tx.explorer_url


class TestSolanaRPCClient:
    """Tests for Solana RPC Client"""
    
    @pytest.fixture
    def client(self):
        """Create client without solana package"""
        with patch('src.trustyclaw.sdk.solana.HAS_SOLANA', False):
            client = SolanaRPCClient(network=Network.DEVNET)
            return client
    
    def test_init(self, client):
        """Test client initialization"""
        assert client.network == Network.DEVNET
        assert client.commitment == "confirmed"
        assert client._keypair is None
    
    def test_address_property_no_keypair(self, client):
        """Test address property with no keypair"""
        assert client.address is None
    
    def test_get_balance_mock(self, client):
        """Test get_balance returns mock data"""
        wallet = client.get_balance("GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q")
        
        assert wallet.address == "GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q"
        assert wallet.lamports == 1000000000
        assert wallet.usdc_balance == 100.0
    
    def test_get_token_balance_mock(self, client):
        """Test get_token_balance returns mock data"""
        balance = client.get_token_balance(
            "GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q",
            "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
        )
        assert balance == 100.0
    
    def test_get_transaction_mock(self, client):
        """Test get_transaction returns mock data"""
        tx = client.get_transaction("mock-signature")
        assert tx is not None
        assert tx.signature == "mock-signature"
        assert tx.status == "confirmed"
    
    def test_derive_escrow_pda(self, client):
        """Test PDA derivation"""
        pda = client.derive_escrow_pda(
            provider="GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q",
            skill_id="image-generation"
        )
        assert "image-generation" in pda
        assert "GFeyFZLm" in pda
    
    def test_simulate_transfer_mock(self, client):
        """Test transfer simulation"""
        result = client.simulate_transfer(
            from_address="GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q",
            to_address="HajVDaadfi6vxrt7y6SRZWBHVYCTscCc8Cwurbqbmg5B",
            lamports=1000000,
        )
        assert result["success"] is True
        assert result["lamports"] == 1000000
    
    def test_request_airdrop_mock(self, client):
        """Test airdrop request"""
        signature = client.request_airdrop("GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q")
        assert signature is not None
        assert "airdrop" in signature


class TestGetClient:
    """Tests for get_client function"""
    
    def test_get_client_devnet(self):
        """Test getting devnet client"""
        with patch('src.trustyclaw.sdk.solana.HAS_SOLANA', False):
            client = get_client("devnet")
            assert client.network == Network.DEVNET
    
    def test_get_client_mainnet(self):
        """Test getting mainnet client"""
        with patch('src.trustyclaw.sdk.solana.HAS_SOLANA', False):
            client = get_client("mainnet")
            assert client.network == Network.MAINNET
    
    def test_get_client_invalid(self):
        """Test getting client with invalid network"""
        with patch('src.trustyclaw.sdk.solana.HAS_SOLANA', False):
            client = get_client("invalid")
            assert client.network == Network.DEVNET  # Falls back to devnet


class TestSolanaImports:
    """Tests for import handling"""
    
    def test_has_solana_false(self):
        """Test HAS_SOLANA flag when package not installed"""
        with patch('src.trustyclaw.sdk.solana.HAS_SOLANA', False):
            from src.trustyclaw.sdk.solana import HAS_SOLANA
            assert HAS_SOLANA is False


class TestEscrowPDA:
    """Tests for escrow PDA generation"""
    
    @pytest.fixture
    def client(self):
        with patch('src.trustyclaw.sdk.solana.HAS_SOLANA', False):
            return SolanaRPCClient(network=Network.DEVNET)
    
    def test_escrow_pda_format(self, client):
        """Test escrow PDA has expected format"""
        pda = client.derive_escrow_pda(
            provider="GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q",
            skill_id="data-analysis"
        )
        # PDA should contain provider prefix and skill_id
        assert "data-analysis" in pda
        assert "GFeyFZLm" in pda
    
    def test_escrow_pda_deterministic(self, client):
        """Test same inputs produce same PDA"""
        pda1 = client.derive_escrow_pda(
            provider="HajVDaadfi6vxrt7y6SRZWBHVYCTscCc8Cwurbqbmg5B",
            skill_id="code-review"
        )
        pda2 = client.derive_escrow_pda(
            provider="HajVDaadfi6vxrt7y6SRZWBHVYCTscCc8Cwurbqbmg5B",
            skill_id="code-review"
        )
        assert pda1 == pda2
    
    def test_escrow_pda_different_skills(self, client):
        """Test different skills produce different PDAs"""
        pda1 = client.derive_escrow_pda(
            provider="GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q",
            skill_id="skill-a"
        )
        pda2 = client.derive_escrow_pda(
            provider="GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q",
            skill_id="skill-b"
        )
        assert pda1 != pda2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
