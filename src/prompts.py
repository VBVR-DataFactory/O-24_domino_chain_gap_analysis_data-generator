"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                           DOMINO CHAIN PROMPTS                                ║
║                                                                               ║
║  Prompts for Domino Chain Gap Analysis task.                                  ║
║  Unified parameterized prompt template.                                       ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""


# ══════════════════════════════════════════════════════════════════════════════
#  UNIFIED PROMPT TEMPLATE
# ══════════════════════════════════════════════════════════════════════════════

PROMPT_TEMPLATE = (
    "Analyze the domino chain and determine which domino is the last to fall. "
    "{analysis_focus} "
    "Push the first domino and {animation_desc}."
)

PROMPT_PARAMS = {
    "default": {
        "analysis_focus": "Look for gaps in the spacing that would stop the chain reaction",
        "animation_desc": "show the chain reaction stopping at the gap"
    },
    "analysis": {
        "analysis_focus": "One gap is too wide for the chain reaction to continue",
        "animation_desc": "show exactly where the chain stops, highlighting the problematic gap"
    },
    "prediction": {
        "analysis_focus": "Examine the spacing to predict the stopping point",
        "animation_desc": "animate the dominos falling until they reach the break point"
    }
}


def get_prompt(task_type: str = "default") -> str:
    """
    Get unified prompt for the given task type.

    Args:
        task_type: Type of task - "default", "analysis", or "prediction"

    Returns:
        Formatted prompt string for the specified type
    """
    params = PROMPT_PARAMS.get(task_type, PROMPT_PARAMS["default"])
    return PROMPT_TEMPLATE.format(**params)


def get_all_prompts(task_type: str = "default") -> list[str]:
    """Get all prompts for a given task type (returns single prompt in a list for compatibility)."""
    return [get_prompt(task_type)]
