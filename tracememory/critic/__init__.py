"""
Critic Module — Valuation Organs for TraceOS

Contains:
- GeminiCritic: Aesthetic evaluation using Gemini API (v2.5)
- GutCritic: Emotional state valuation from micro-reactions (v3.0)

@organ valuation
"""

from tracememory.critic.gemini_critic import GeminiCritic
from tracememory.critic.gut_state import GutCritic

__all__ = ["GeminiCritic", "GutCritic"]
