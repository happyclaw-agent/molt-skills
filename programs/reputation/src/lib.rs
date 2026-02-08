use anchor_lang::prelude::*;
use anchor_lang::solana_program::hash::Hash;

declare_id!("J9X4dDqyFL2pG3MZJn4WEEK3Mcku9nG8XJcEo8zB9z2");

#[program]
pub mod reputation {
    use super::*;

    /// Initialize reputation system (creates global state)
    pub fn initialize(ctx: Context<Initialize>) -> Result<()> {
        let state = &mut ctx.accounts.state;
        state.initialized = true;
        state.total_agents = 0;
        state.total_reviews = 0;
        state.reputation_sum = 0;
        Ok(())
    }

    /// Register a new agent
    pub fn register_agent(
        ctx: Context<RegisterAgent>,
        name: String,
        bio: String,
    ) -> Result<()> {
        let agent = &mut ctx.accounts.agent;
        let state = &mut ctx.accounts.state;
        
        require!(state.initialized, ErrorCode::NotInitialized);
        require!(name.len() <= 64, ErrorCode::NameTooLong);
        require!(bio.len() <= 256, ErrorCode::BioTooLong);
        
        agent.authority = ctx.accounts.authority.key();
        agent.name = name;
        agent.bio = bio;
        agent.reputation_score = 0;
        agent.total_ratings = 0;
        agent.rating_sum = 0;
        agent.created_at = Clock::get()?.unix_timestamp;
        agent.updated_at = Clock::get()?.unix_timestamp;
        agent.is_active = true;
        
        state.total_agents += 1;
        
        Ok(())
    }

    /// Add a review for an agent
    pub fn add_review(
        ctx: Context<AddReview>,
        rating: u8,
        comment: String,
        skill_category: String,
    ) -> Result<()> {
        let review = &mut ctx.accounts.review;
        let agent = &mut ctx.accounts.agent;
        let state = &mut ctx.accounts.state;
        
        require!(rating >= 1 && rating <= 5, ErrorCode::InvalidRating);
        require!(comment.len() <= 500, ErrorCode::CommentTooLong);
        require!(skill_category.len() <= 32, ErrorCode::CategoryTooLong);
        require!(agent.is_active, ErrorCode::AgentNotActive);
        
        review.agent = ctx.accounts.agent.key();
        review.reviewer = ctx.accounts.reviewer.key();
        review.rating = rating;
        review.comment = comment;
        review.skill_category = skill_category;
        review.created_at = Clock::get()?.unix_timestamp;
        
        // Update agent stats
        agent.total_ratings += 1;
        agent.rating_sum += rating as u64;
        agent.reputation_score = agent.rating_sum / agent.total_ratings;
        agent.updated_at = Clock::get()?.unix_timestamp;
        
        // Update global state
        state.total_reviews += 1;
        state.reputation_sum += rating as u64;
        
        Ok(())
    }

    /// Update agent's reputation score manually (for disputes, slashing)
    pub fn update_reputation(
        ctx: Context<UpdateReputation>,
        new_score: i64,
    ) -> Result<()> {
        let agent = &mut ctx.accounts.agent;
        let state = &mut ctx.accounts.state;
        
        require!(new_score >= 0 && new_score <= 100, ErrorCode::InvalidScore);
        
        let old_score = agent.reputation_score;
        agent.reputation_score = new_score;
        agent.updated_at = Clock::get()?.unix_timestamp;
        
        // Adjust global sum
        state.reputation_sum = state.reputation_sum.saturating_sub(old_score as u64).saturating_add(new_score as u64);
        
        Ok(())
    }

    /// Deactivate an agent
    pub fn deactivate_agent(ctx: Context<DeactivateAgent>) -> Result<()> {
        let agent = &mut ctx.accounts.agent;
        require!(agent.is_active, ErrorCode::AgentAlreadyInactive);
        
        agent.is_active = false;
        agent.updated_at = Clock::get()?.unix_timestamp;
        
        Ok(())
    }

    /// Get agent's reputation data
    pub fn get_agent_reputation(_ctx: Context<GetAgentReputation>) -> Result<AgentData> {
        Ok(AgentData {
            reputation_score: _ctx.accounts.agent.reputation_score,
            total_ratings: _ctx.accounts.agent.total_ratings,
            rating_sum: _ctx.accounts.agent.rating_sum,
            is_active: _ctx.accounts.agent.is_active,
            updated_at: _ctx.accounts.agent.updated_at,
        })
    }
}

#[derive(Accounts)]
pub struct Initialize<'info> {
    #[account(init, payer = authority, space = 8 + 32)]
    pub state: Account<'info, ReputationState>,
    #[account(mut)]
    pub authority: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct RegisterAgent<'info> {
    #[account(mut, has_one = state)]
    pub state: Account<'info, ReputationState>,
    #[account(init, payer = authority, space = 8 + 64 + 256 + 8 + 8 + 8 + 8 + 8 + 1)]
    pub agent: Account<'info, Agent>,
    #[account(mut)]
    pub authority: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct AddReview<'info> {
    #[account(mut, has_one = state)]
    pub state: Account<'info, ReputationState>,
    #[account(mut, has_one = agent)]
    pub agent: Account<'info, Agent>,
    #[account(init, payer = reviewer, space = 8 + 32 + 32 + 1 + 500 + 32 + 8)]
    pub review: Account<'info, Review>,
    #[account(mut)]
    pub reviewer: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct UpdateReputation<'info> {
    #[account(mut, has_one = state)]
    pub state: Account<'info, ReputationState>,
    #[account(mut, has_one = agent)]
    pub agent: Account<'info, Agent>,
    #[account(mut)]
    pub authority: Signer<'info>,
}

#[derive(Accounts)]
pub struct DeactivateAgent<'info> {
    #[account(mut)]
    pub agent: Account<'info, Agent>,
    #[account(mut)]
    pub authority: Signer<'info>,
}

#[derive(Accounts)]
pub struct GetAgentReputation<'info> {
    pub agent: Account<'info, Agent>,
}

#[account]
pub struct ReputationState {
    pub initialized: bool,
    pub total_agents: u64,
    pub total_reviews: u64,
    pub reputation_sum: u64,
}

#[account]
pub struct Agent {
    pub authority: Pubkey,
    pub name: String,
    pub bio: String,
    pub reputation_score: i64,
    pub total_ratings: u64,
    pub rating_sum: u64,
    pub created_at: i64,
    pub updated_at: i64,
    pub is_active: bool,
}

#[account]
pub struct Review {
    pub agent: Pubkey,
    pub reviewer: Pubkey,
    pub rating: u8,
    pub comment: String,
    pub skill_category: String,
    pub created_at: i64,
}

#[derive(AnchorSerialize, AnchorDeserialize, Clone)]
pub struct AgentData {
    pub reputation_score: i64,
    pub total_ratings: u64,
    pub rating_sum: u64,
    pub is_active: bool,
    pub updated_at: i64,
}

#[error_code]
pub enum ErrorCode {
    #[msg("Reputation system not initialized")]
    NotInitialized,
    #[msg("Agent name too long (max 64 chars)")]
    NameTooLong,
    #[msg("Bio too long (max 256 chars)")]
    BioTooLong,
    #[msg("Rating must be between 1 and 5")]
    InvalidRating,
    #[msg("Comment too long (max 500 chars)")]
    CommentTooLong,
    #[msg("Skill category too long (max 32 chars)")]
    CategoryTooLong,
    #[msg("Agent is not active")]
    AgentNotActive,
    #[msg("Agent already inactive")]
    AgentAlreadyInactive,
    #[msg("Reputation score must be 0-100")]
    InvalidScore,
}
