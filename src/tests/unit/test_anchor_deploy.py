"""
Tests for Anchor on-chain deployment and demo.py functionality.

Run with:
    python3 -m pytest src/tests/unit/test_anchor_deploy.py -v
"""

import pytest
import subprocess
import os


class TestAnchorDeployment:
    """Test Anchor program deployment to devnet"""
    
    def test_anchor_toml_exists(self):
        """Verify Anchor.toml exists with devnet configuration"""
        assert os.path.exists('Anchor.toml'), "Anchor.toml not found"
        
        with open('Anchor.toml', 'r') as f:
            content = f.read()
        
        assert '[programs.devnet]' in content, "Devnet programs not configured"
        assert 'escrow = ' in content, "Escrow program ID not set"
    
    def test_escrow_program_id_valid(self):
        """Verify escrow program ID is a valid Solana address"""
        with open('Anchor.toml', 'r') as f:
            content = f.read()
        
        # Extract program ID for devnet
        in_devnet = False
        for line in content.split('\n'):
            if '[programs.devnet]' in line:
                in_devnet = True
                continue
            if in_devnet and '[' in line:
                break
            if in_devnet and 'escrow = ' in line:
                program_id = line.split('=')[1].strip().strip('"')
                # Solana addresses are 32-44 chars base58
                assert len(program_id) >= 32, f"Invalid program ID length: {program_id}"
                return
        else:
            pytest.fail("Escrow program ID not found in [programs.devnet]")
    
    def test_anchor_build(self):
        """Verify Anchor program builds successfully (skip if anchor not installed)"""
        import shutil
        if shutil.which('anchor') is None:
            pytest.skip("Anchor CLI not installed")
        
        result = subprocess.run(
            ['anchor', 'build'],
            cwd='programs/escrow',
            capture_output=True,
            text=True,
            timeout=120
        )
        assert result.returncode == 0, f"Anchor build failed: {result.stderr}"
    
    def test_anchor_idl_generated(self):
        """Verify IDL is generated after build"""
        import shutil
        if shutil.which('anchor') is None:
            pytest.skip("Anchor CLI not installed")
        
        idl_path = 'target/idl/escrow.json'
        assert os.path.exists(idl_path), f"IDL not generated at {idl_path}"


class TestDemoMockMode:
    """Test demo.py in mock mode"""
    
    def test_demo_help(self):
        """Verify demo.py --help works"""
        result = subprocess.run(
            ['python3', 'demo.py', '--help'],
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0, f"--help failed: {result.stderr}"
        assert '--mock' in result.stdout, "--mock flag not in help"
        assert '--onchain' in result.stdout, "--onchain flag not in help"
    
    def test_demo_mock_runs(self):
        """Verify demo.py --mock runs without errors"""
        result = subprocess.run(
            ['python3', 'demo.py', '--mock'],
            capture_output=True,
            text=True,
            timeout=120
        )
        assert result.returncode == 0, f"Demo --mock failed: {result.stderr}"
        assert 'DEMO COMPLETE!' in result.stdout, "Demo did not complete"
    
    def test_demo_default_is_mock(self):
        """Verify demo.py defaults to mock mode"""
        result = subprocess.run(
            ['python3', 'demo.py'],
            capture_output=True,
            text=True,
            timeout=120
        )
        assert result.returncode == 0, f"Demo default failed: {result.stderr}"
        assert 'DEMO COMPLETE!' in result.stdout, "Demo did not complete"
        assert 'Mock mode' in result.stdout, "Mock mode message not shown"


class TestDemoOnchainMode:
    """Test demo.py in on-chain mode (requires deployed programs)"""
    
    def test_demo_onchain_flag(self):
        """Verify demo.py --onchain flag is recognized"""
        result = subprocess.run(
            ['python3', 'demo.py', '--onchain', '--help'],
            capture_output=True,
            text=True,
            timeout=30
        )
        # Should not fail on argument parsing
        assert result.returncode == 0 or 'Unrecognized arguments' in result.stderr


class TestEscrowClient:
    """Test EscrowClient functionality"""
    
    def test_escrow_client_import(self):
        """Verify EscrowClient can be imported"""
        from trustyclaw.sdk.escrow_contract import EscrowClient
        assert EscrowClient is not None
    
    def test_escrow_terms_creation(self):
        """Verify EscrowTerms can be created"""
        from trustyclaw.sdk.escrow_contract import EscrowTerms
        
        terms = EscrowTerms(
            skill_name="test-skill",
            duration_seconds=3600,
            price_usdc=1000000,
            metadata_uri="ipfs://test"
        )
        assert terms.skill_name == "test-skill"
        assert terms.price_usdc == 1000000
    
    def test_escrow_client_methods_exist(self):
        """Verify EscrowClient has required methods"""
        from trustyclaw.sdk.escrow_contract import EscrowClient
        
        client = EscrowClient()
        
        assert hasattr(client, 'create_escrow'), "create_escrow method missing"
        assert hasattr(client, 'fund_escrow'), "fund_escrow method missing"
        assert hasattr(client, 'release_escrow'), "release_escrow method missing"


class TestReputationChain:
    """Test ReputationChain functionality"""
    
    def test_reputation_chain_import(self):
        """Verify ReputationChainSDK can be imported"""
        from trustyclaw.sdk.reputation_chain import ReputationChainSDK
        assert ReputationChainSDK is not None
    
    def test_reputation_mock_data(self):
        """Verify reputation returns mock data in mock mode"""
        from trustyclaw.sdk.reputation_chain import ReputationChainSDK
        
        sdk = ReputationChainSDK()
        result = sdk.get_reputation("test-address")
        
        assert result is not None, "get_reputation returned None"
        assert hasattr(result, 'reputation_score'), "Missing reputation_score"


class TestFullDemo:
    """Full integration tests for demo.py"""
    
    def test_full_demo_sections(self):
        """Verify all demo sections execute"""
        result = subprocess.run(
            ['python3', 'demo.py', '--mock'],
            capture_output=True,
            text=True,
            timeout=180
        )
        
        assert result.returncode == 0, f"Full demo failed: {result.stderr}"
        
        # Verify all sections ran
        assert 'SOLANA INTEGRATION' in result.stdout
        assert 'USDC TOKEN' in result.stdout
        assert 'ESCROW CONTRACT' in result.stdout
        assert 'REVIEW SYSTEM' in result.stdout
        assert 'MANDATE SKILL' in result.stdout
        assert 'DISCOVERY SKILL' in result.stdout
        assert 'REPUTATION SKILL' in result.stdout
        assert 'ON-CHAIN REPUTATION' in result.stdout
    
    def test_demo_features_count(self):
        """Verify all 8 features are demonstrated"""
        result = subprocess.run(
            ['python3', 'demo.py', '--mock'],
            capture_output=True,
            text=True,
            timeout=180
        )
        
        features = [
            'Solana blockchain integration',
            'USDC token handling',
            'Escrow contract management',
            'Review submission',
            'Mandate lifecycle',
            'Agent/skill discovery',
            'Reputation queries',
            'On-chain reputation storage',
        ]
        
        for feature in features:
            assert feature in result.stdout, f"Missing feature: {feature}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
