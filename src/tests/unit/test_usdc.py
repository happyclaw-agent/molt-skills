"""
Tests for USDC Token Integration

Uses trustyclaw.sdk.usdc (PYTHONPATH=src). When client has no RPC (HAS_SOLANA False),
get_balance returns 0.0 and find_associated_token_account returns None.
"""

import pytest
from unittest.mock import patch


class TestUSDCClient:
    """Tests for USDC token client"""

    @pytest.fixture
    def client(self):
        """Create client; patch so no Solana RPC (client is None)."""
        with patch("trustyclaw.sdk.usdc.HAS_SOLANA", False):
            from trustyclaw.sdk.usdc import USDCClient
            return USDCClient(network="devnet")

    @pytest.fixture
    def usdc_client_class(self):
        """Import USDCClient for assertions that need the class."""
        from trustyclaw.sdk.usdc import USDCClient
        return USDCClient

    def test_init(self, client, usdc_client_class):
        """Test client initialization"""
        assert client.network == "devnet"
        assert client.mint == usdc_client_class.DEVNET_MINT
        assert client._keypair is None

    def test_address_property_no_keypair(self, client):
        """Test address property without keypair"""
        assert client.address is None

    def test_get_balance_no_rpc(self, client):
        """When no RPC client, get_balance returns 0.0"""
        assert client.get_balance("GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q") == 0.0
        assert client.get_balance("3WaHbF7k9ced4d2wA8caUHq2v57ujD4J2c57L8wZXfhN") == 0.0
        assert client.get_balance("unknown-wallet") == 0.0

    def test_find_associated_token_account_no_rpc(self, client):
        """When no RPC client, find_associated_token_account returns None"""
        account = client.find_associated_token_account(
            "GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q"
        )
        assert account is None

    def test_transfer_mock(self, client):
        """Transfer returns CONFIRMED and signature format (mock behavior in usdc.py)"""
        result = client.transfer(
            from_wallet="GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q",
            to_wallet="HajVDaadfi6vxrt7y6SRZWBHVYCTscCc8Cwurbqbmg5B",
            amount=10.0,
        )
        assert result.status.value == "confirmed"
        assert result.amount == 10.0
        assert result.token == "USDC"
        assert "transfer-" in result.signature
        assert "explorer.solana.com" in result.explorer_url

    def test_decimals(self, client):
        """Test USDC decimals"""
        assert client.decimals() == 6

    def test_amount_to_raw(self, client):
        """Test amount to raw conversion"""
        assert client.amount_to_raw(1.0) == 1_000_000
        assert client.amount_to_raw(0.01) == 10_000
        assert client.amount_to_raw(100.0) == 100_000_000

    def test_raw_to_amount(self, client):
        """Test raw to amount conversion"""
        assert client.raw_to_amount(1_000_000) == 1.0
        assert client.raw_to_amount(10_000) == 0.01
        assert client.raw_to_amount(100_000_000) == 100.0


class TestTransferResult:
    """Tests for TransferResult dataclass"""

    def test_explorer_url(self):
        """Test explorer URL generation"""
        from trustyclaw.sdk.usdc import TransferResult, TransferStatus

        result = TransferResult(
            signature="5hJ7Xg8Yz3N7JW6Z7Z2V4K8Y9Q1M2N3O4P5Q6R7S8T",
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


class TestTokenAccount:
    """Tests for TokenAccount dataclass"""

    def test_balance_raw(self):
        """Test raw balance calculation"""
        from trustyclaw.sdk.usdc import TokenAccount

        account = TokenAccount(
            address="test-account",
            mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            owner="test-owner",
            balance=100.0,
            decimals=6,
        )
        assert account.balance_raw == 100_000_000


class TestGetUSDCClient:
    """Tests for get_usdc_client function"""

    def test_get_client_devnet(self):
        """Test getting devnet client"""
        from trustyclaw.sdk.usdc import get_usdc_client

        client = get_usdc_client("devnet")
        assert client.network == "devnet"

    def test_get_client_mainnet(self):
        """Test getting mainnet client"""
        from trustyclaw.sdk.usdc import get_usdc_client, USDCClient

        client = get_usdc_client("mainnet")
        assert client.network == "mainnet"
        assert client.mint == USDCClient.MAINNET_MINT


class TestTokenError:
    """Tests for TokenError"""

    def test_raise_error(self):
        """Test raising token error"""
        from trustyclaw.sdk.usdc import TokenError

        with pytest.raises(TokenError):
            raise TokenError("Test error message")

    def test_error_message(self):
        """Test error message"""
        from trustyclaw.sdk.usdc import TokenError

        error = TokenError("Insufficient funds")
        assert "Insufficient funds" in str(error)
