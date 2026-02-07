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
        default=40,
        description="Width of each domino in pixels"
    )

    domino_height: int = Field(
        default=140,
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
        default=60,
        description="Minimum normal spacing between dominos"
    )

    normal_spacing_max: int = Field(
        default=90,
        description="Maximum normal spacing between dominos"
    )

    gap_spacing_min: int = Field(
        default=180,
        description="Minimum gap spacing (too far)"
    )

    gap_spacing_max: int = Field(
        default=240,
        description="Maximum gap spacing (too far)"
    )

    # Physics threshold (domino can reach up to this fraction of its height)
    fall_reach_ratio: float = Field(
        default=0.9,
        description="Fraction of domino height that determines max reach"
    )

    # Visual settings - adjusted for 1024x1024 (centered vertically)
    ground_y: int = Field(
        default=700,
        description="Y position of ground line"
    )

    margin_left: int = Field(
        default=120,
        description="Left margin for first domino"
    )

    # ══════════════════════════════════════════════════════════════════════════
    #  COLOR POOLS FOR SCALING
    # ══════════════════════════════════════════════════════════════════════════

    # Standing domino color pool - expanded to 30 colors for better scaling
    DOMINO_COLORS: list = [
        # Blues
        (41, 128, 185),   # Blue
        (52, 152, 219),   # Light blue
        (46, 134, 193),   # Medium blue
        (30, 144, 255),   # Dodger blue
        (65, 105, 225),   # Royal blue
        
        # Greens
        (46, 204, 113),   # Green
        (26, 188, 156),   # Teal
        (22, 160, 133),   # Dark teal
        (34, 153, 84),    # Medium green
        (40, 180, 99),    # Light green
        (16, 172, 132),   # Ocean green
        
        # Purples
        (155, 89, 182),   # Purple
        (142, 68, 173),   # Dark purple
        (136, 78, 160),   # Medium purple
        (165, 105, 189),  # Light purple
        (147, 51, 234),   # Vivid purple
        (123, 104, 238),  # Medium slate blue
        
        # Oranges/Browns
        (230, 126, 34),   # Orange
        (211, 84, 0),     # Dark orange
        (243, 156, 18),   # Amber
        (235, 152, 78),   # Light orange
        (255, 140, 0),    # Dark orange 2
        
        # Yellows/Golds
        (241, 196, 15),   # Yellow
        (255, 215, 0),    # Gold
        (218, 165, 32),   # Goldenrod
        
        # Pinks/Magentas
        (219, 10, 91),    # Pink
        (255, 20, 147),   # Deep pink
        (199, 21, 133),   # Medium violet red
        
        # Cyans
        (0, 206, 209),    # Dark cyan
        (64, 224, 208),   # Turquoise
    ]

    # Fallen domino color pool
    FALLEN_COLORS: list = [
        (231, 76, 60),    # Red
        (230, 126, 34),   # Orange
        (241, 196, 15),   # Yellow
        (192, 57, 43),    # Dark red
        (211, 84, 0),     # Dark orange
        (243, 156, 18),   # Amber
        (235, 152, 78),   # Light orange
    ]

    # Background color pool
    BACKGROUND_COLORS: list = [
        (245, 245, 245),  # Light gray
        (250, 250, 250),  # Almost white
        (240, 248, 255),  # Alice blue
        (255, 250, 240),  # Floral white
        (248, 248, 255),  # Ghost white
        (245, 255, 250),  # Mint cream
        (255, 248, 240),  # Seashell
    ]

    # Ground color pool
    GROUND_COLORS: list = [
        (139, 90, 43),    # Brown
        (160, 82, 45),    # Sienna
        (101, 67, 33),    # Dark brown
        (139, 115, 85),   # Tan
        (118, 85, 43),    # Medium brown
    ]

    # Colors (RGB tuples) - defaults for backward compatibility
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
