"""
Integration Tests for USDC On-Chain Operations

Real SPL Token operations tests on Solana devnet.
These tests perform actual blockchain transactions.
"""

import pytest
import os
from unittest.mock import patch
import time


class TestUSDCOnChain:
    """Integration tests for real USDC operations"""
    
    @pytest.fixture
    def client(self):
        """Create USDC client for devnet"""
        from trustyclaw.sdk.usdc import USDCClient, get_usdc_client

        keypair_path = os.environ.get("SOLANA_KEYPAIR_PATH")
        if keypair_path and os.path.exists(keypair_path):
            return USDCClient(network="devnet", keypair_path=keypair_path)
        return get_usdc_client("devnet")
    
    @pytest.fixture
    def test_wallets(self):
        """Test wallet addresses for integration tests"""
        return {
            "source": os.environ.get("TEST_SOURCE_WALLET"),
            "destination": os.environ.get("TEST_DESTINATION_WALLET"),
        }
    
    def test_client_initialization(self, client):
        """Test client initialization"""
        from trustyclaw.sdk.usdc import USDCClient

        assert client.network == "devnet"
        assert client.mint == USDCClient.DEVNET_MINT
        assert client.endpoint is not None
    
    def test_get_balance_real(self, client, test_wallets):
        """Test getting real USDC balance"""
        if not test_wallets["source"]:
            pytest.skip("TEST_SOURCE_WALLET not configured")
        
        balance = client.get_balance(test_wallets["source"])
        
        # Balance should be a non-negative float
        assert isinstance(balance, float)
        assert balance >= 0.0
    
    def test_find_associated_token_account(self, client, test_wallets):
        """Test finding associated token account"""
        if not test_wallets["source"]:
            pytest.skip("TEST_SOURCE_WALLET not configured")
        
        account = client.find_associated_token_account(test_wallets["source"])
        
        # Should return either None or a valid address
        if account is not None:
            assert len(account) >= 32  # Solana address length
    
    def test_get_token_account_info(self, client, test_wallets):
        """Test getting token account info (skip if method not available)"""
        if not test_wallets["source"]:
            pytest.skip("TEST_SOURCE_WALLET not configured")
        if not hasattr(client, "get_token_account_info"):
            pytest.skip("USDCClient has no get_token_account_info")
        account = client.find_associated_token_account(test_wallets["source"])
        if not account:
            pytest.skip("No token account found")
        info = client.get_token_account_info(account)
        if info:
            assert info.mint == client.mint
            assert info.decimals == 6
    
    def test_transfer_authorized(self, client, test_wallets):
        """Test transfer with authorized wallet"""
        from trustyclaw.sdk.usdc import TransferStatus

        if not test_wallets["source"] or not test_wallets["destination"]:
            pytest.skip("Test wallets not configured")
        if not client._keypair:
            pytest.skip("No keypair loaded for signing")
        source_account = client.find_associated_token_account(test_wallets["source"])
        if not source_account:
            pytest.skip("No source token account")
        
        # Get balance
        balance = client.get_balance(test_wallets["source"])
        if balance < 0.01:
            pytest.skip("Insufficient balance for transfer test")
        
        # Perform small transfer (0.01 USDC)
        amount = 0.01
        
        result = client.transfer(
            from_wallet=test_wallets["source"],
            to_wallet=test_wallets["destination"],
            amount=amount,
        )
        
        assert result.amount == amount
        assert result.source_account is not None
        assert result.status in [TransferStatus.CONFIRMED, TransferStatus.PENDING]
        assert len(result.signature) >= 1
        assert "explorer.solana.com" in result.explorer_url
    
    def test_transfer_insufficient_balance(self, client, test_wallets):
        """Test transfer with insufficient balance"""
        if not test_wallets["source"] or not test_wallets["destination"]:
            pytest.skip("Test wallets not configured")
        
        if not client._keypair:
            pytest.skip("No keypair loaded")
        
        from trustyclaw.sdk.usdc import TokenError
        
        # Try to transfer more than balance
        with pytest.raises(TokenError):
            client.transfer(
                from_wallet=test_wallets["source"],
                to_wallet=test_wallets["destination"],
                amount=999999999.0,
            )
    
    def test_get_or_create_associated_token_account(self, client, test_wallets):
        """Test get or create associated token account (skip if not available)"""
        if not test_wallets["destination"]:
            pytest.skip("TEST_DESTINATION_WALLET not configured")
        if not hasattr(client, "get_or_create_associated_token_account"):
            pytest.skip("USDCClient has no get_or_create_associated_token_account")
        account, was_created = client.get_or_create_associated_token_account(
            test_wallets["destination"],
            create_if_missing=False,
        )
        assert account is not None
        assert len(account) >= 32


class TestUSDCClientWithMockFallback:
    """Tests with mock fallback when no real keypair"""
    
    def test_transfer_with_mock_fallback(self):
        """Test transfer falls back to mock when no keypair"""
        from trustyclaw.sdk.usdc import USDCClient, TransferStatus
        
        client = USDCClient(network="devnet")
        assert client._keypair is None
        
        # Transfer should use mock
        result = client.transfer(
            from_wallet="GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q",
            to_wallet="HajVDaadfi6vxrt7y6SRZWBHVYCTscCc8CwCwurbqbmg5B",
            amount=1.0,
        )
        
        assert result.amount == 1.0
        assert result.status == TransferStatus.CONFIRMED
        assert "transfer-" in result.signature or len(result.signature) >= 1


class TestKeypairManager:
    """Tests for keypair manager"""
    
    def test_keypair_manager_init(self):
        """Test keypair manager initialization"""
        from trustyclaw.sdk.keypair import KeypairManager
        
        manager = KeypairManager()
        assert manager._key_dir is not None
    
    def test_load_keypair_file(self, tmp_path):
        """Test loading keypair from file"""
        import json
        from trustyclaw.sdk.keypair import KeypairManager
        from solders.keypair import Keypair

        test_keypair = Keypair()
        secret = bytes(test_keypair)
        keypair_path = tmp_path / "test_keypair.json"
        with open(keypair_path, "w") as f:
            json.dump({"secret_key": list(secret)}, f)

        manager = KeypairManager()
        address = manager.load_keypair(str(keypair_path), name="test")
        assert address == str(test_keypair.pubkey())
        assert len(manager.list_wallets()) == 1
    
    def test_list_wallets(self, tmp_path):
        """Test listing loaded wallets"""
        import json
        from trustyclaw.sdk.keypair import KeypairManager
        from solders.keypair import Keypair

        manager = KeypairManager()
        for i in range(3):
            kp = Keypair()
            secret = bytes(kp)
            path = tmp_path / f"keypair_{i}.json"
            with open(path, "w") as f:
                json.dump({"secret_key": list(secret)}, f)
            manager.load_keypair(str(path), name=f"wallet_{i}")
        wallets = manager.list_wallets()
        assert len(wallets) == 3
    
    def test_remove_keypair(self, tmp_path):
        """Test removing a keypair"""
        import json
        from trustyclaw.sdk.keypair import KeypairManager
        from solders.keypair import Keypair

        manager = KeypairManager()
        kp = Keypair()
        secret = bytes(kp)
        path = tmp_path / "remove_test.json"
        with open(path, "w") as f:
            json.dump({"secret_key": list(secret)}, f)
        address = manager.load_keypair(str(path))
        assert len(manager.list_wallets()) == 1
        manager.remove_keypair(address)
        assert len(manager.list_wallets()) == 0
    
    def test_clear_all_keypairs(self, tmp_path):
        """Test clearing all keypairs"""
        import json
        from trustyclaw.sdk.keypair import KeypairManager
        from solders.keypair import Keypair

        manager = KeypairManager()
        for i in range(2):
            kp = Keypair()
            secret = bytes(kp)
            path = tmp_path / f"clear_test_{i}.json"
            with open(path, "w") as f:
                json.dump({"secret_key": list(secret)}, f)
            manager.load_keypair(str(path))
        assert len(manager.list_wallets()) == 2
        manager.clear()
        assert len(manager.list_wallets()) == 0
    
    def test_context_manager(self, tmp_path):
        """Test keypair manager as context manager"""
        import json
        from trustyclaw.sdk.keypair import KeypairManager
        from solders.keypair import Keypair

        kp = Keypair()
        secret = bytes(kp)
        path = tmp_path / "context_test.json"
        with open(path, "w") as f:
            json.dump({"secret_key": list(secret)}, f)
        with KeypairManager() as manager:
            manager.load_keypair(str(path))
            assert len(manager.list_wallets()) == 1
        assert len(manager.list_wallets()) == 0


class TestUSDCAmountConversions:
    """Tests for amount conversion utilities"""
    
    def test_amount_to_raw_usdc(self):
        """Test converting USDC amounts to raw"""
        from trustyclaw.sdk.usdc import USDCClient
        
        client = USDCClient(network="devnet")
        
        assert client.amount_to_raw(1.0) == 1_000_000
        assert client.amount_to_raw(0.01) == 10_000
        assert client.amount_to_raw(100.0) == 100_000_000
        assert client.amount_to_raw(0.000001) == 1
    
    def test_raw_to_amount_usdc(self):
        """Test converting raw USDC to amounts"""
        from trustyclaw.sdk.usdc import USDCClient
        
        client = USDCClient(network="devnet")
        
        assert client.raw_to_amount(1_000_000) == 1.0
        assert client.raw_to_amount(10_000) == 0.01
        assert client.raw_to_amount(100_000_000) == 100.0
        assert client.raw_to_amount(1) == 0.000001


class TestTransferResult:
    """Tests for TransferResult dataclass"""
    
    def test_explorer_url_devnet(self):
        """Test explorer URL for devnet"""
        from trustyclaw.sdk.usdc import TransferResult, TransferStatus
        
        result = TransferResult(
            signature="5hJ7Xg8Yz3N7JW6Z7Z2V4K8Y9Q1M2N3O4P5Q6R7S8T9U0V1W2X3Y4Z5A6B7C8D9E0F",
            status=TransferStatus.CONFIRMED,
            source_account="from-wallet",
            destination_account="to-wallet",
            amount=10.0,
        )
        
        assert "explorer.solana.com" in result.explorer_url
        assert result.signature in result.explorer_url
        assert "devnet" in result.explorer_url
    
    def test_default_token(self):
        """Test default token is USDC"""
        from trustyclaw.sdk.usdc import TransferResult, TransferStatus
        
        result = TransferResult(
            signature="test",
            status=TransferStatus.PENDING,
            source_account="from",
            destination_account="to",
            amount=1.0,
        )
        assert result.token == "USDC"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
