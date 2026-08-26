"""
Per-model USD pricing used only to compute the cost_usd estimate stored in
llm_call_log. Rates below were verified against multiple sources (Anthropic's
own pricing docs plus independent trackers) as of July 2026 -- confirm
against https://platform.claude.com/docs/en/about-claude/pricing before
trusting cost_usd for anything real (budgeting, chargeback, etc.), since
Anthropic updates pricing over time and this file is not auto-synced to it.
"""

# USD per 1,000,000 tokens. Key must match the ANTHROPIC_MODEL value exactly.
PRICING_TABLE = {
    "claude-sonnet-4-6": {"input_per_mtok": 3.00, "output_per_mtok": 15.00},
    "claude-sonnet-5": {"input_per_mtok": 2.00, "output_per_mtok": 10.00},  # intro pricing through 2026-08-31; $3/$15 standard after
    "claude-opus-4-8": {"input_per_mtok": 5.00, "output_per_mtok": 25.00},
    "claude-haiku-4-5-20251001": {"input_per_mtok": 1.00, "output_per_mtok": 5.00},
}


def get_pricing_for_model(model_name):
    return PRICING_TABLE.get(model_name)