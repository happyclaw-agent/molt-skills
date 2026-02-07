use anchor_lang::prelude::*;

declare_id!("F2Fx88Qovf28dqhPLomxTuFNa1fm2VBnkJdksqQrQs8N");

#[program]
pub mod escrow {
    use super::*;

    pub fn hello(ctx: Context<Hello>) -> Result<()> {
        let data = &mut ctx.accounts.data;
        data.value = data.value + 1;
        Ok(())
    }
}

#[derive(Accounts)]
pub struct Hello<'info> {
    #[account(mut)]
    pub data: Account<'info, Data>,
}

#[account]
pub struct Data {
    pub value: u64,
}
