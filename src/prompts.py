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
    "Analyze the domino chain to find which domino is the last to fall. "
    "Push the first domino and watch as each domino falls and turns red. "
    "The chain stops at the gap where the spacing between two upright dominos "
    "is visibly wider than the others. "
    "The last fallen domino is circled in green as the answer."
)

PROMPT_PARAMS = {
    "default": {}
}


def get_prompt(task_type: str = "default") -> str:
    """
    Get unified prompt for the given task type.

    Args:
        task_type: Type of task - "default"

    Returns:
        Formatted prompt string
    """
    return PROMPT_TEMPLATE


def get_all_prompts(task_type: str = "default") -> list[str]:
    """Get all prompts for a given task type (returns single prompt in a list for compatibility)."""
    return [get_prompt(task_type)]
