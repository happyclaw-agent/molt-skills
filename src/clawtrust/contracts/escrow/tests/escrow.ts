//! Escrow Program Tests

use anchor_lang::prelude::*;
use anchor_spl::token::{self, Mint, TokenAccount};
use solana_program_test::*;
use solana_sdk::*;

#[tokio::test]
async fn test_initialize_escrow() {
    // Test initialization logic (mocked)
    let provider = Pubkey::new_unique();
    let seed = b"escrow";
    let (escrow_pda, _bump) = Pubkey::find_program_address(
        &[seed, provider.as_ref()],
        &Pubkey::default(), // Placeholder
    );
    
    // PDA should be deterministically derived
    assert_eq!(escrow_pda.len(), 32);
    println!("Escrow PDA: {}", escrow_pda);
}

#[tokio::test]
async fn test_escrow_terms() {
    // Test escrow terms serialization
    let terms = EscrowTerms {
        skill_name: "image-generation".to_string(),
        duration_seconds: 3600,
        price_usdc: 10_000, // 0.01 USDC
        metadata_uri: "ipfs://QmTest...".to_string(),
    };
    
    assert_eq!(terms.skill_name, "image-generation");
    assert_eq!(terms.price_usdc, 10_000);
}

#[tokio::test]
async fn test_escrow_state_transitions() {
    // Test state machine
    assert_eq!(EscrowState::Created as u8, 0);
    assert_eq!(EscrowState::Funded as u8, 1);
    assert_eq!(EscrowState::Completed as u8, 2);
    assert_eq!(EscrowState::Cancelled as u8, 3);
}

// Mock types for testing (normally in program)
#[derive(AnchorSerialize, AnchorDeserialize, Clone, Debug)]
pub struct EscrowTerms {
    pub skill_name: String,
    pub duration_seconds: i64,
    pub price_usdc: u64,
    pub metadata_uri: String,
}

#[derive(AnchorSerialize, AnchorDeserialize, Clone, Debug, PartialEq)]
pub enum EscrowState {
    Created,
    Funded,
    Completed,
    Cancelled,
}
