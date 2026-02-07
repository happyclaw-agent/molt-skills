import pytest
import subprocess
import sys
from trustyclaw.sdk.escrow_contract import EscrowClient

PROVIDER_WALLET = "GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q"
RENTER_WALLET = "3WaHbF7k9ced4d2wA8caUHq2v57ujD4J2c57L8wZXfhN"

def test_escrow_create():
    &quot;&quot;&quot;Test escrow creation&quot;&quot;&quot;
    escrow = EscrowClient(network=&quot;devnet&quot;)
    result = escrow.create_escrow(
        renter=RENTER_WALLET,
        provider=PROVIDER_WALLET,
        skill_id=&quot;image-generation&quot;,
        amount=1000000,  # 1 USDC
        duration_hours=24,
        deliverable_hash=&quot;abc123def456789&quot;
    )
    assert result is not None
    assert hasattr(result, &#x27;escrow_id&#x27;)
    assert result.escrow_id
    assert hasattr(result, &#x27;state&#x27;)
    assert result.state == &#x27;created&#x27;

def test_escrow_fund():
    &quot;&quot;&quot;Test escrow funding&quot;&quot;&quot;
    escrow = EscrowClient(network=&quot;devnet&quot;)
    new_escrow = escrow.create_escrow(
        renter=RENTER_WALLET,
        provider=PROVIDER_WALLET,
        skill_id=&quot;image-generation&quot;,
        amount=1000000,
        duration_hours=24,
        deliverable_hash=&quot;abc123def456789&quot;
    )
    funded = escrow.fund_escrow(new_escrow.escrow_id)
    assert funded.state == &#x27;funded&#x27;

def test_release_escrow():
    &quot;&quot;&quot;Test escrow release&quot;&quot;&quot;
    escrow = EscrowClient(network=&quot;devnet&quot;)
    new_escrow = escrow.create_escrow(
        renter=RENTER_WALLET,
        provider=PROVIDER_WALLET,
        skill_id=&quot;image-generation&quot;,
        amount=1000000,
        duration_hours=24,
        deliverable_hash=&quot;abc123def456789&quot;
    )
    funded = escrow.fund_escrow(new_escrow.escrow_id)
    released = escrow.release_escrow(new_escrow.escrow_id)
    assert released.state == &#x27;released&#x27;

def test_full_demo():
    &quot;&quot;&quot;Test entire demo flow&quot;&quot;&quot;
    result = subprocess.run([sys.executable, &#x27;demo.py&#x27;], cwd=&#x27;..&#x27; * 3, capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, f&quot;Demo failed:\\n{result.stdout}\\n{result.stderr}&quot;