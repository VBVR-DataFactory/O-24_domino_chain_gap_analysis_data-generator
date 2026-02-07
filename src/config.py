"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                           DOMINO CHAIN CONFIGURATION                          ║
║                                                                               ║
║  Configuration for Domino Chain Gap Analysis task.                            ║
║  Inherits common settings from core.GenerationConfig                          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from pydantic import Field
from typing import Tuple
from core import GenerationConfig


class TaskConfig(GenerationConfig):
    """
    Domino Chain Gap Analysis configuration.

    Inherited from GenerationConfig:
        - num_samples: int          # Number of samples to generate
        - domain: str               # Task domain name
        - difficulty: Optional[str] # Difficulty level
        - random_seed: Optional[int] # For reproducibility
        - output_dir: Path          # Where to save outputs
        - image_size: tuple[int, int] # Image dimensions
    """

    # ══════════════════════════════════════════════════════════════════════════
    #  OVERRIDE DEFAULTS
    # ══════════════════════════════════════════════════════════════════════════

    domain: str = Field(default="domino_chain_gap_analysis")
    image_size: Tuple[int, int] = Field(default=(1024, 1024))  # Standard 1:1 aspect ratio

    # ══════════════════════════════════════════════════════════════════════════
    #  VIDEO SETTINGS
    # ══════════════════════════════════════════════════════════════════════════

    generate_videos: bool = Field(
        default=True,
        description="Whether to generate ground truth videos"
    )

    video_fps: int = Field(
        default=16,
        description="Video frame rate"
    )

    # ══════════════════════════════════════════════════════════════════════════
    #  DOMINO CHAIN SETTINGS
    # ══════════════════════════════════════════════════════════════════════════

    # Domino dimensions (side view) - scaled for 1024x1024
    domino_width: int = Field(
        default=20,
        description="Width of each domino in pixels"
    )

    domino_height: int = Field(
        default=90,
        description="Height of each domino in pixels"
    )

    # Chain parameters
    min_dominos: int = Field(
        default=7,
        description="Minimum number of dominos in chain"
    )

    max_dominos: int = Field(
        default=12,
        description="Maximum number of dominos in chain"
    )

    # Spacing parameters - scaled for 1024x1024
    normal_spacing_min: int = Field(
        default=38,
        description="Minimum normal spacing between dominos"
    )

    normal_spacing_max: int = Field(
        default=56,
        description="Maximum normal spacing between dominos"
    )

    gap_spacing_min: int = Field(
        default=115,
        description="Minimum gap spacing (too far)"
    )

    gap_spacing_max: int = Field(
        default=150,
        description="Maximum gap spacing (too far)"
    )

    # Physics threshold (domino can reach up to this fraction of its height)
    fall_reach_ratio: float = Field(
        default=0.9,
        description="Fraction of domino height that determines max reach"
    )

    # Visual settings - adjusted for 1024x1024 (centered vertically)
    ground_y: int = Field(
        default=650,
        description="Y position of ground line"
    )

    margin_left: int = Field(
        default=100,
        description="Left margin for first domino"
    )

    # Colors (RGB tuples)
    domino_color: Tuple[int, int, int] = Field(
        default=(41, 128, 185),
        description="Color of standing dominos (blue)"
    )

    fallen_domino_color: Tuple[int, int, int] = Field(
        default=(231, 76, 60),
        description="Color of fallen dominos (red)"
    )

    ground_color: Tuple[int, int, int] = Field(
        default=(139, 90, 43),
        description="Color of ground line (brown)"
    )

    background_color: Tuple[int, int, int] = Field(
        default=(245, 245, 245),
        description="Background color (light gray)"
    )

    text_color: Tuple[int, int, int] = Field(
        default=(33, 33, 33),
        description="Text color (dark gray)"
    )

    highlight_color: Tuple[int, int, int] = Field(
        default=(46, 204, 113),
        description="Highlight/answer color (green)"
    )

    gap_indicator_color: Tuple[int, int, int] = Field(
        default=(192, 57, 43),
        description="Gap indicator color (dark red)"
    )
