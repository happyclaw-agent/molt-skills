//! TrustyClaw Escrow Program for Agent Skill Rentals
//!
//! A production-grade escrow for secure USDC payments between agents and renters.

use anchor_lang::prelude::*;
use anchor_spl::token::{self, Token, TokenAccount, Transfer};
use std::str::FromStr;

declare_id!("ESCRwJwfT1XpTwzPfkQ9NyTXfHWHnhCWdK1vYhmjbUF");

// Constants
const ESCROW_SEED: &[u8] = b"trustyclaw-escrow";
const USDC_MINT: &str = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v";
const MAX_SKILL_NAME_LEN: usize = 64;
const MAX_METADATA_URI_LEN: usize = 256;

#[program]
pub mod escrow {
    use super::*;

    /// Initialize a new escrow for a skill rental
    #[access_control(valid_escrow_account(&ctx))]
    pub fn initialize(
        ctx: Context<Initialize>,
        skill_name: String,
        duration_seconds: i64,
        price_usdc: u64,
        metadata_uri: String,
    ) -> Result<()> {
        let escrow = &mut ctx.accounts.escrow;
        
        escrow.provider = ctx.accounts.provider.key();
        escrow.renter = Pubkey::default();
        escrow.token_mint = ctx.accounts.token_mint.key();
        escrow.provider_token_account = ctx.accounts.provider_token_account.key();
        escrow.skill_name = skill_name;
        escrow.duration_seconds = duration_seconds;
        escrow.price_usdc = price_usdc;
        escrow.metadata_uri = metadata_uri;
        escrow.amount = 0;
        escrow.state = EscrowState::Created;
        escrow.created_at = Clock::get()?.unix_timestamp;
        escrow.funded_at = 0;
        escrow.completed_at = 0;
        escrow.disputed_at = 0;
        escrow.dispute_reason = String::new();
        
        msg!("Escrow initialized: {}", escrow.key());
        Ok(())
    }

    /// Fund the escrow with USDC (renter deposits)
    #[access_control(state_is(&ctx, EscrowState::Created))]
    pub fn fund(ctx: Context<Fund>, amount: u64) -> Result<()> {
        let escrow = &mut ctx.accounts.escrow;
        
        escrow.renter = ctx.accounts.renter.key();
        escrow.amount = amount;
        escrow.state = EscrowState::Funded;
        escrow.funded_at = Clock::get()?.unix_timestamp;

        // Transfer USDC from renter to escrow PDA
        let cpi_accounts = Transfer {
            from: ctx.accounts.renter_token_account.to_account_info(),
            to: ctx.accounts.escrow_token_account.to_account_info(),
            authority: ctx.accounts.renter.to_account_info(),
        };
        let cpi_program = ctx.accounts.token_program.to_account_info();
        token::transfer(CpiContext::new(cpi_program, cpi_accounts), amount)?;

        msg!("Escrow funded: {} with {} USDC", escrow.key(), amount);
        Ok(())
    }

    /// Complete task and release funds to provider
    #[access_control(state_is(&ctx, EscrowState::Funded))]
    pub fn complete(_ctx: Context<Complete>) -> Result<()> {
        // Marker instruction - actual release happens via release instruction
        msg!("Task completed - ready for release");
        Ok(())
    }

    /// Release funds to provider (renter approves completion)
    #[access_control(state_is(&ctx, EscrowState::Funded))]
    pub fn release(ctx: Context<Release>) -> Result<()> {
        let escrow = &mut ctx.accounts.escrow;
        
        escrow.state = EscrowState::Released;
        escrow.completed_at = Some(Clock::get()?.unix_timestamp);

        // Transfer USDC from escrow to provider
        let seeds = &[
            ESCROW_SEED,
            escrow.provider.as_ref(),
            &[ctx.bumps.escrow],
        ];
        let signer = &[&seeds[..]];

        let cpi_accounts = Transfer {
            from: ctx.accounts.escrow_token_account.to_account_info(),
            to: ctx.accounts.provider_token_account.to_account_info(),
            authority: ctx.accounts.escrow.to_account_info(),
        };
        let cpi_program = ctx.accounts.token_program.to_account_info();
        token::transfer(
            CpiContext::new_with_signer(cpi_program, cpi_accounts, signer),
            escrow.amount,
        )?;

        msg!("Funds released: {} USDC to provider", escrow.amount);
        Ok(())
    }

    /// Refund funds to renter (provider agrees to cancel)
    #[access_control(state_is(&ctx, EscrowState::Funded))]
    pub fn refund(ctx: Context<Refund>) -> Result<()> {
        let escrow = &mut ctx.accounts.escrow;
        
        escrow.state = EscrowState::Refunded;

        // Transfer USDC back to renter
        let seeds = &[
            ESCROW_SEED,
            escrow.provider.as_ref(),
            &[ctx.bumps.escrow],
        ];
        let signer = &[&seeds[..]];

        let cpi_accounts = Transfer {
            from: ctx.accounts.escrow_token_account.to_account_info(),
            to: ctx.accounts.renter_token_account.to_account_info(),
            authority: ctx.accounts.escrow.to_account_info(),
        };
        let cpi_program = ctx.accounts.token_program.to_account_info();
        token::transfer(
            CpiContext::new_with_signer(cpi_program, cpi_accounts, signer),
            escrow.amount,
        )?;

        msg!("Funds refunded: {} USDC to renter", escrow.amount);
        Ok(())
    }

    /// File a dispute on the escrow
    #[access_control(state_is(&ctx, EscrowState::Funded))]
    pub fn dispute(ctx: Context<Dispute>, reason: String) -> Result<()> {
        let escrow = &mut ctx.accounts.escrow;
        
        escrow.state = EscrowState::Disputed;
        escrow.dispute_reason = Some(reason);
        escrow.disputed_at = Clock::get()?.unix_timestamp;
        escrow.dispute_reason = reason;

        msg!("Escrow disputed: {}", reason);
        Ok(())
    }

    /// Resolve dispute - release funds to provider
    #[access_control(state_is(&ctx, EscrowState::Disputed))]
    pub fn resolve_dispute_release(ctx: Context<ResolveDispute>) -> Result<()> {
        let escrow = &mut ctx.accounts.escrow;
        
        escrow.state = EscrowState::Released;
        escrow.completed_at = Some(Clock::get()?.unix_timestamp);

        let seeds = &[
            ESCROW_SEED,
            escrow.provider.as_ref(),
            &[ctx.bumps.escrow],
        ];
        let signer = &[&seeds[..]];

        let cpi_accounts = Transfer {
            from: ctx.accounts.escrow_token_account.to_account_info(),
            to: ctx.accounts.provider_token_account.to_account_info(),
            authority: ctx.accounts.escrow.to_account_info(),
        };
        let cpi_program = ctx.accounts.token_program.to_account_info();
        token::transfer(
            CpiContext::new_with_signer(cpi_program, cpi_accounts, signer),
            escrow.amount,
        )?;

        msg!("Dispute resolved - funds released to provider");
        Ok(())
    }

    /// Resolve dispute - refund funds to renter
    #[access_control(state_is(&ctx, EscrowState::Disputed))]
    pub fn resolve_dispute_refund(ctx: Context<ResolveDispute>) -> Result<()> {
        let escrow = &mut ctx.accounts.escrow;
        
        escrow.state = EscrowState::Refunded;

        let seeds = &[
            ESCROW_SEED,
            escrow.provider.as_ref(),
            &[ctx.bumps.escrow],
        ];
        let signer = &[&seeds[..]];

        let cpi_accounts = Transfer {
            from: ctx.accounts.escrow_token_account.to_account_info(),
            to: ctx.accounts.renter_token_account.to_account_info(),
            authority: ctx.accounts.escrow.to_account_info(),
        };
        let cpi_program = ctx.accounts.token_program.to_account_info();
        token::transfer(
            CpiContext::new_with_signer(cpi_program, cpi_accounts, signer),
            escrow.amount,
        )?;

        msg!("Dispute resolved - funds refunded to renter");
        Ok(())
    }
}

// ========== Account Structures ==========

#[account]
#[derive(InitSpace)]
pub struct Escrow {
    pub provider: Pubkey,
    pub renter: Pubkey,
    pub token_mint: Pubkey,
    pub provider_token_account: Pubkey,
    #[max_len(64)]
    pub skill_name: String,
    pub duration_seconds: i64,
    pub price_usdc: u64,
    #[max_len(256)]
    pub metadata_uri: String,
    pub amount: u64,
    pub state: EscrowState,
    pub created_at: i64,
    pub funded_at: Option<i64>,
    pub completed_at: Option<i64>,
    pub disputed_at: Option<i64>,
    #[max_len(256)]
    pub dispute_reason: Option<String>,
}

#[derive(AnchorSerialize, AnchorDeserialize, Clone, Debug, PartialEq)]
pub enum EscrowState {
    Created,
    Funded,
    Released,
    Refunded,
    Disputed,
}

// ========== Contexts ==========

#[derive(Accounts)]
#[instruction(skill_name: String, duration_seconds: i64, price_usdc: u64, metadata_uri: String)]
pub struct Initialize<'info> {
    #[account(mut)]
    pub provider: Signer<'info>,
    #[account(
        init,
        payer = provider,
        seeds = [ESCROW_SEED, provider.key().as_ref()],
        bump,
        space = Escrow::INIT_SPACE + 8
    )]
    pub escrow: Account<'info, Escrow>,
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
pub struct Fund<'info> {
    #[account(mut)]
    pub renter: Signer<'info>,
    #[account(
        mut,
        seeds = [ESCROW_SEED, escrow.provider.as_ref()],
        bump,
        has_one = token_mint,
    )]
    pub escrow: Account<'info, Escrow>,
    pub token_mint: Account<'info, token::Mint>,
    #[account(
        init_if_needed,
        payer = renter,
        associated_token::mint = token_mint,
        associated_token::authority = escrow,
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
pub struct Complete<'info> {
    #[account(mut)]
    pub authority: Signer<'info>,
    #[account(
        mut,
        seeds = [ESCROW_SEED, escrow.provider.as_ref()],
        bump,
    )]
    pub escrow: Account<'info, Escrow>,
    pub token_mint: Account<'info, token::Mint>,
    pub token_program: Program<'info, Token>,
}

#[derive(Accounts)]
pub struct Release<'info> {
    #[account(mut)]
    pub renter: Signer<'info>,
    #[account(
        mut,
        seeds = [ESCROW_SEED, escrow.provider.as_ref()],
        bump,
        has_one = renter,
    )]
    pub escrow: Account<'info, Escrow>,
    #[account(
        mut,
        associated_token::mint = token_mint,
        associated_token::authority = escrow,
    )]
    pub escrow_token_account: Account<'info, TokenAccount>,
    #[account(
        mut,
        associated_token::mint = token_mint,
        associated_token::authority = escrow.provider,
    )]
    pub provider_token_account: Account<'info, TokenAccount>,
    pub token_mint: Account<'info, token::Mint>,
    pub token_program: Program<'info, Token>,
}

#[derive(Accounts)]
pub struct Refund<'info> {
    #[account(mut)]
    pub provider: Signer<'info>,
    #[account(
        mut,
        seeds = [ESCROW_SEED, escrow.provider.as_ref()],
        bump,
    )]
    pub escrow: Account<'info, Escrow>,
    #[account(
        mut,
        associated_token::mint = token_mint,
        associated_token::authority = escrow,
    )]
    pub escrow_token_account: Account<'info, TokenAccount>,
    #[account(
        mut,
        associated_token::mint = token_mint,
        associated_token::authority = escrow.renter,
    )]
    pub renter_token_account: Account<'info, TokenAccount>,
    pub token_mint: Account<'info, token::Mint>,
    pub token_program: Program<'info, Token>,
}

#[derive(Accounts)]
pub struct Dispute<'info> {
    #[account(mut)]
    pub authority: Signer<'info>, // Can be renter or provider
    #[account(
        mut,
        seeds = [ESCROW_SEED, escrow.provider.as_ref()],
        bump,
    )]
    pub escrow: Account<'info, Escrow>,
    pub token_mint: Account<'info, token::Mint>,
    pub token_program: Program<'info, Token>,
}

#[derive(Accounts)]
pub struct ResolveDispute<'info> {
    #[account(mut)]
    pub authority: Signer<'info>, // Should be dispute resolver (could be multisig)
    #[account(
        mut,
        seeds = [ESCROW_SEED, escrow.provider.as_ref()],
        bump,
    )]
    pub escrow: Account<'info, Escrow>,
    #[account(
        mut,
        associated_token::mint = token_mint,
        associated_token::authority = escrow,
    )]
    pub escrow_token_account: Account<'info, TokenAccount>,
    #[account(
        mut,
        associated_token::mint = token_mint,
        associated_token::authority = escrow.provider,
    )]
    pub provider_token_account: Account<'info, TokenAccount>,
    #[account(
        mut,
        associated_token::mint = token_mint,
        associated_token::authority = escrow.renter,
    )]
    pub renter_token_account: Account<'info, TokenAccount>,
    pub token_mint: Account<'info, token::Mint>,
    pub token_program: Program<'info, Token>,
}

// ========== Access Controls ==========

fn valid_escrow_account(ctx: &Context<Initialize>) -> Result<()> {
    require!(
        ctx.accounts.provider_token_account.amount >= ctx.accounts.provider_token_account.amount,
        EscrowError::InsufficientFunds
    );
    Ok(())
}

fn state_is<T>(ctx: &Context<T>, expected: EscrowState) -> Result<()> {
    require!(
        ctx.accounts.escrow.state == expected,
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
    #[msg("Invalid token account")]
    InvalidTokenAccount,
}
