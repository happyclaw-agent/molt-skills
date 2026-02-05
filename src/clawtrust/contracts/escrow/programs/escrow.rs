//! Simple USDC Escrow Program for Agent Skill Rentals
//!
//! This program implements a basic escrow for skill rentals:
//! - Provider creates escrow with USDC deposit
//! - Renter agrees and funds are locked
//! - Task completes → funds released to provider
//! - Timeout → funds refunded to renter

use anchor_lang::prelude::*;
use anchor_spl::token::{self, Token, TokenAccount, Transfer};
use anchor_lang::system_program::{transfer, Transfer as SystemTransfer};

declare_id!("ESCRW1111111111111111111111111111111111111");

const ESCROW_SEED: &[u8] = b"escrow";
const USDC_MINT: &str = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"; // Solana USDC

#[program]
pub mod escrow {
    use super::*;

    /// Initialize a new escrow for a skill rental
    /// 
    /// Accounts:
    /// - provider: Party offering the skill
    /// - escrow_account: PDA to hold escrow state
    /// - provider_token_account: Where USDC will come from
    /// - system_program: For PDA creation
    #[access_control(state_not_created(&ctx))]
    pub fn initialize_escrow(
        ctx: Context<InitializeEscrow>,
        terms: EscrowTerms,
    ) -> Result<()> {
        let escrow = &mut ctx.accounts.escrow_account;
        
        escrow.provider = ctx.accounts.provider.key();
        escrow.renter = Pubkey::default(); // Not set until accepted
        escrow.token_mint = ctx.accounts.token_mint.key();
        escrow.provider_token_account = ctx.accounts.provider_token_account.key();
        escrow.terms = terms;
        escrow.state = EscrowState::Created;
        escrow.created_at = Clock::get()?.unix_timestamp;
        
        Ok(())
    }

    /// Accept escrow and fund it
    /// 
    /// Accounts:
    /// - renter: Party renting the skill
    /// - renter_token_account: Source of USDC
    #[access_control(state_is(&ctx, EscrowState::Created))]
    pub fn accept_escrow(ctx: Context<AcceptEscrow>, amount: u64) -> Result<()> {
        let escrow = &mut ctx.accounts.escrow_account;
        escrow.renter = ctx.accounts.renter.key();
        escrow.amount = amount;
        escrow.state = EscrowState::Funded;

        // Transfer USDC from renter to escrow
        let cpi_accounts = Transfer {
            from: ctx.accounts.renter_token_account.to_account_info(),
            to: ctx.accounts.escrow_token_account.to_account_info(),
            authority: ctx.accounts.renter.to_account_info(),
        };
        let cpi_program = ctx.accounts.token_program.to_account_info();
        token::transfer(CpiContext::new(cpi_program, cpi_accounts), amount)?;

        Ok(())
    }

    /// Complete task and release funds to provider
    /// 
    /// Only provider or renter can call after funding
    #[access_control(state_is(&ctx, EscrowState::Funded))]
    pub fn complete_task(ctx: Context<CompleteTask>) -> Result<()> {
        let escrow = &mut ctx.accounts.escrow_account;
        escrow.state = EscrowState::Completed;
        escrow.completed_at = Clock::get()?.unix_timestamp;

        // Transfer USDC from escrow to provider
        let seeds = &[
            ESCROW_SEED,
            &[ctx.bumps.escrow_account],
        ];
        let signer = &[&seeds[..]];

        let cpi_accounts = Transfer {
            from: ctx.accounts.escrow_token_account.to_account_info(),
            to: ctx.accounts.provider_token_account.to_account_info(),
            authority: ctx.accounts.escrow_account.to_account_info(),
        };
        let cpi_program = ctx.accounts.token_program.to_account_info();
        token::transfer(CpiContext::new_with_signer(cpi_program, cpi_accounts, signer), escrow.amount)?;

        Ok(())
    }

    /// Cancel escrow and refund to renter
    /// 
    /// Can be called by provider anytime, or by renter if timeout passed
    #[access_control(state_is(&ctx, EscrowState::Funded))]
    pub fn cancel_escrow(ctx: Context<CancelEscrow>) -> Result<()> {
        let escrow = &mut ctx.accounts.escrow_account;
        escrow.state = EscrowState::Cancelled;
        escrow.cancelled_at = Clock::get()?.unix_timestamp;

        // Transfer USDC back to renter
        let seeds = &[
            ESCROW_SEED,
            &[ctx.bumps.escrow_account],
        ];
        let signer = &[&seeds[..]];

        let cpi_accounts = Transfer {
            from: ctx.accounts.escrow_token_account.to_account_info(),
            to: ctx.accounts.renter_token_account.to_account_info(),
            authority: ctx.accounts.escrow_account.to_account_info(),
        };
        let cpi_program = ctx.accounts.token_program.to_account_info();
        token::transfer(CpiContext::new_with_signer(cpi_program, cpi_accounts, signer), escrow.amount)?;

        Ok(())
    }

    /// Check if escrow has timed out
    #[access_control(state_is(&ctx, EscrowState::Funded))]
    pub fn check_timeout(ctx: Context<CheckTimeout>) -> Result<bool> {
        let escrow = &ctx.accounts.escrow_account;
        let now = Clock::get()?.unix_timestamp;
        
        // Timeout if duration has passed
        Ok(now >= escrow.created_at + escrow.terms.duration_seconds)
    }
}

// ========== Account Structures ==========

#[account]
pub struct EscrowAccount {
    pub provider: Pubkey,
    pub renter: Pubkey,
    pub token_mint: Pubkey,
    pub provider_token_account: Pubkey,
    pub escrow_token_account: Pubkey,
    pub terms: EscrowTerms,
    pub state: EscrowState,
    pub amount: u64,
    pub created_at: i64,
    pub completed_at: i64,
    pub cancelled_at: i64,
}

impl EscrowAccount {
    pub const LEN: usize = 8 + 32 * 4 + 4 + 64 + 1 + 8 + 8 + 8 + 8;
}

#[derive(AnchorSerialize, AnchorDeserialize, Clone, Debug)]
pub struct EscrowTerms {
    pub skill_name: String,          // e.g., "image-generation"
    pub duration_seconds: i64,        // Max duration for task
    pub price_usdc: u64,             // Amount in USDC (10^6 precision)
    pub metadata_uri: String,        // IPFS link to full terms
}

#[derive(AnchorSerialize, AnchorDeserialize, Clone, Debug, PartialEq)]
pub enum EscrowState {
    Created,     // Escrow initialized, not funded
    Funded,      // Renter deposited, awaiting completion
    Completed,   // Task done, funds released
    Cancelled,   // Cancelled, funds refunded
}

// ========== Contexts ==========

#[derive(Accounts)]
pub struct InitializeEscrow<'info> {
    #[account(mut)]
    pub provider: Signer<'info>,
    #[account(
        init,
        payer = provider,
        seeds = [ESCROW_SEED, provider.key().as_ref()],
        bump,
        space = EscrowAccount::LEN
    )]
    pub escrow_account: Account<'info, EscrowAccount>,
    pub token_mint: Account<'info, token::Mint>,
    #[account(
        mut,
        associated_token::mint = token_mint,
        associated_token::authority = provider
    )]
    pub provider_token_account: Account<'info, TokenAccount>,
    pub system_program: Program<'info, System>,
    pub token_program: Program<'info, Token>,
    pub associated_token_program: Program<'info, AssociatedToken>,
}

#[derive(Accounts)]
pub struct AcceptEscrow<'info> {
    #[account(mut)]
    pub renter: Signer<'info>,
    #[account(
        mut,
        seeds = [ESCROW_SEED, escrow.provider.as_ref()],
        bump,
        has_one = provider_token_account,
        has_one = token_mint,
    )]
    pub escrow_account: Account<'info, EscrowAccount>,
    pub token_mint: Account<'info, token::Mint>,
    #[account(
        init_if_needed,
        payer = renter,
        associated_token::mint = token_mint,
        associated_token::authority = escrow_account,
    )]
    pub escrow_token_account: Account<'info, TokenAccount>,
    #[account(
        mut,
        associated_token::mint = token_mint,
        associated_token::authority = renter,
    )]
    pub renter_token_account: Account<'info, TokenAccount>,
    pub system_program: Program<'info, System>,
    pub token_program: Program<'info, Token>,
    pub associated_token_program: Program<'info, AssociatedToken>,
}

#[derive(Accounts)]
pub struct CompleteTask<'info> {
    #[account(mut)]
    pub authority: Signer<'info>,  // Can be provider or renter
    #[account(
        mut,
        seeds = [ESCROW_SEED, escrow.provider.as_ref()],
        bump,
    )]
    pub escrow_account: Account<'info, EscrowAccount>,
    #[account(
        mut,
        associated_token::mint = token_mint,
        associated_token::authority = escrow_account,
    )]
    pub escrow_token_account: Account<'info, TokenAccount>,
    #[account(
        mut,
        associated_token::mint = token_mint,
        associated_token::authority = escrow_account.provider,
    )]
    pub provider_token_account: Account<'info, TokenAccount>,
    pub token_mint: Account<'info, token::Mint>,
    pub token_program: Program<'info, Token>,
}

#[derive(Accounts)]
pub struct CancelEscrow<'info> {
    #[account(mut)]
    pub authority: Signer<'info>,  // Provider anytime, renter after timeout
    #[account(
        mut,
        seeds = [ESCROW_SEED, escrow.provider.as_ref()],
        bump,
    )]
    pub escrow_account: Account<'info, EscrowAccount>,
    #[account(
        mut,
        associated_token::mint = token_mint,
        associated_token::authority = escrow_account,
    )]
    pub escrow_token_account: Account<'info, TokenAccount>,
    #[account(
        mut,
        associated_token::mint = token_mint,
        associated_token::authority = escrow_account.renter,
    )]
    pub renter_token_account: Account<'info, TokenAccount>,
    pub token_mint: Account<'info, token::Mint>,
    pub token_program: Program<'info, Token>,
}

#[derive(Accounts)]
pub struct CheckTimeout<'info> {
    #[account(
        seeds = [ESCROW_SEED, escrow.provider.as_ref()],
        bump,
    )]
    pub escrow_account: Account<'info, EscrowAccount>,
}

// ========== Access Controls ==========

fn state_not_created(ctx: &Context<InitializeEscrow>) -> Result<()> {
    require!(
        ctx.accounts.escrow_account.state == EscrowState::Created || 
        ctx.accounts.escrow_account.state == EscrowState::default(),
        EscrowError::InvalidState
    );
    Ok(())
}

fn state_is<T>(ctx: &Context<T>, expected: EscrowState) -> Result<()> {
    require!(
        ctx.accounts.escrow_account.state == expected,
        EscrowError::InvalidState
    );
    Ok(())
}

#[error_code]
pub enum EscrowError {
    #[msg("Invalid escrow state for this operation")]
    InvalidState,
    #[msg("Timeout has not elapsed yet")]
    TimeoutNotElapsed,
    #[msg("Unauthorized caller")]
    Unauthorized,
    #[msg("Insufficient funds")]
    InsufficientFunds,
}
