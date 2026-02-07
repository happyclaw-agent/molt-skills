use anchor_lang::prelude::*;

declare_id!("ESCRwJwfT1XpTwzPfkQ9NyTXfHWHnhCWdK1vYhmjbUF");

#[program]
pub mod escrow {
    use super::*;

    pub fn initialize(ctx: Context<Initialize>) -> Result<()> {
        let escrow = &mut ctx.accounts.escrow;
        escrow.provider = ctx.accounts.provider.key();
        escrow.renter = ctx.accounts.provider.key();
        escrow.amount = 0;
        escrow.state = 0;
        escrow.timestamp = Clock::get()?.unix_timestamp;
        Ok(())
    }

    pub fn fund(ctx: Context<Fund>, amount: u64) -> Result<()> {
        let escrow = &mut ctx.accounts.escrow;
        escrow.renter = ctx.accounts.renter.key();
        escrow.amount = amount;
        escrow.state = 1;
        Ok(())
    }

    pub fn release(ctx: Context<Release>) -> Result<()> {
        let escrow = &mut ctx.accounts.escrow;
        escrow.state = 2;
        Ok(())
    }

    pub fn refund(ctx: Context<Refund>) -> Result<()> {
        let escrow = &mut ctx.accounts.escrow;
        escrow.state = 3;
        Ok(())
    }
}

#[derive(Accounts)]
pub struct Initialize<'info> {
    #[account(mut)]
    pub provider: Signer<'info>,
    #[account(
        init,
        payer = provider,
        space = 100,
        seeds = [b"escrow", provider.key().as_ref()],
        bump
    )]
    pub escrow: Account<'info, Escrow>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct Fund<'info> {
    #[account(mut)]
    pub renter: Signer<'info>,
    #[account(
        mut,
        seeds = [b"escrow", escrow.provider.as_ref()],
        bump,
        has_one = provider,
    )]
    pub escrow: Account<'info, Escrow>,
    pub provider: UncheckedAccount<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct Release<'info> {
    #[account(mut)]
    pub renter: Signer<'info>,
    #[account(
        mut,
        seeds = [b"escrow", escrow.provider.as_ref()],
        bump,
        has_one = renter,
    )]
    pub escrow: Account<'info, Escrow>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct Refund<'info> {
    #[account(mut)]
    pub provider: Signer<'info>,
    #[account(
        mut,
        seeds = [b"escrow", escrow.provider.as_ref()],
        bump,
    )]
    pub escrow: Account<'info, Escrow>,
    pub system_program: Program<'info, System>,
}

#[account]
pub struct Escrow {
    pub provider: Pubkey,
    pub renter: Pubkey,
    pub amount: u64,
    pub state: u8,
    pub timestamp: i64,
}
