"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                        DOMINO CHAIN GAP GENERATOR                             ║
║                                                                               ║
║  Generates domino chain gap analysis tasks.                                   ║
║  Task: Find where the chain reaction stops due to a gap.                      ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import random
import math
import tempfile
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from PIL import Image, ImageDraw, ImageFont

from core import BaseGenerator, TaskPair, ImageRenderer
from core.video_utils import VideoGenerator
from .config import TaskConfig
from .prompts import get_prompt


class TaskGenerator(BaseGenerator):
    """
    Domino Chain Gap Analysis generator.

    Generates tasks where a chain of dominos has one gap that's too wide,
    stopping the chain reaction. The task is to identify which domino
    is the last to fall.
    """

    def __init__(self, config: TaskConfig):
        super().__init__(config)
        self.renderer = ImageRenderer(image_size=config.image_size)

        # Initialize video generator if enabled
        self.video_generator = None
        if config.generate_videos and VideoGenerator.is_available():
            self.video_generator = VideoGenerator(fps=config.video_fps, output_format="mp4")

        # Calculate fall reach threshold
        self.fall_reach = config.domino_height * config.fall_reach_ratio

    def generate_task_pair(self, task_id: str) -> TaskPair:
        """Generate one domino chain gap analysis task."""

        # Generate domino chain data with randomized visual properties
        task_data = self._generate_chain_data()
        
        # Randomize visual properties for scaling
        visual_props = self._randomize_visual_properties()
        task_data['visual_props'] = visual_props
        
        # Finalize chain data with positions
        task_data = self._finalize_chain_data(task_data)

        # Render images
        first_image = self._render_initial_state(task_data)
        final_image = self._render_final_state(task_data)

        # Generate video (optional)
        video_path = None
        if self.config.generate_videos and self.video_generator:
            video_path = self._generate_video(task_data, task_id)

        # Select prompt
        prompt = get_prompt("default")

        # Build objects metadata
        objects = self._build_objects_metadata(task_data)
        
        # Build task_data with object-centric metadata
        optimized_task_data = {
            "gap_after": task_data["gap_after"],
            "answer": task_data["answer"],
            "last_fallen_index": task_data["last_fallen_index"],
            "objects": objects
        }
        
        metadata = self._build_metadata(task_id, optimized_task_data)
        
        
        
        return TaskPair(
            task_id=task_id,
            domain=self.config.domain,
            prompt=prompt,
            first_image=first_image,
            final_image=final_image,
            ground_truth_video=video_path,
            metadata=metadata
        )

    # ══════════════════════════════════════════════════════════════════════════
    #  METADATA BUILDING
    # ══════════════════════════════════════════════════════════════════════════

    def _build_objects_metadata(self, task_data: dict) -> List[Dict[str, Any]]:
        """
        Build objects metadata with all dominos as objects.
        
        Args:
            task_data: Task data dictionary containing domino information
        
        Returns:
            List of domino objects with their properties
        """
        objects = []
        visual_props = task_data['visual_props']
        ground_y = visual_props['ground_y']
        
        for i in range(task_data["num_dominos"]):
            x = task_data["positions"][i]
            is_fallen = i <= task_data["last_fallen_index"]
            
            objects.append({
                "symbol": "domino",
                "index": i + 1,  # 1-indexed for display
                "center": [round(x, 2), round(ground_y - visual_props['domino_height'] / 2, 2)],
                "position": round(x, 2),
                "color": list(visual_props['domino_color'] if not is_fallen else visual_props['fallen_domino_color']),
                "is_fallen": is_fallen,
                "is_last_fallen": (i == task_data["last_fallen_index"])
            })
        
        return objects

    # ══════════════════════════════════════════════════════════════════════════
    #  CHAIN GENERATION
    # ══════════════════════════════════════════════════════════════════════════

    def _randomize_visual_properties(self) -> dict:
        """Randomize visual properties for scaling."""
        return {
            # Color randomization
            'domino_color': random.choice(self.config.DOMINO_COLORS),
            'fallen_domino_color': (231, 76, 60),  # Fixed red color for fallen dominos
            'background_color': (255, 255, 255),  # Fixed white background
            'ground_color': random.choice(self.config.GROUND_COLORS),
            
            # Size randomization (±12.5% variation)
            'domino_width': random.randint(35, 45),
            'domino_height': random.randint(130, 150),
            
            # Layout randomization
            'margin_left': random.randint(150, 200),  # Increased to ensure PUSH arrow is in scene
            'ground_y': random.randint(650, 750),
            
            # Spacing randomization (slightly wider ranges)
            'normal_spacing_min': random.randint(55, 65),
            'normal_spacing_max': random.randint(85, 95),
            'gap_spacing_min': random.randint(170, 190),
            'gap_spacing_max': random.randint(230, 250),
        }

    def _generate_chain_data(self) -> dict:
        """Generate domino chain with one gap."""
        # Random number of dominos
        num_dominos = random.randint(self.config.min_dominos, self.config.max_dominos)

        # Choose gap position (not first, not last - somewhere in middle)
        # Gap is AFTER this domino index (0-indexed)
        gap_after = random.randint(1, num_dominos - 3)

        # Note: Spacing generation will be done in a second pass after visual_props are available
        return {
            "num_dominos": num_dominos,
            "gap_after": gap_after,  # 0-indexed
        }
    
    def _finalize_chain_data(self, task_data: dict) -> dict:
        """Finalize chain data with positions based on visual properties."""
        visual_props = task_data['visual_props']
        num_dominos = task_data['num_dominos']
        gap_after = task_data['gap_after']

        # Generate spacings with explicit contact physics:
        # normal spacing must be reachable, gap spacing must be unreachable.
        max_trigger_spacing = self._max_trigger_spacing(visual_props)
        normal_max_allowed = max(40, max_trigger_spacing - 6)
        # Keep normal spacing tighter so collisions are visually believable.
        normal_max_allowed = min(normal_max_allowed, int(visual_props["domino_height"] * 0.55))
        normal_min_allowed = max(30, normal_max_allowed - 28)
        gap_min_required = max_trigger_spacing + 22

        spacings = []
        for i in range(num_dominos - 1):
            if i == gap_after:
                # This is the gap - guaranteed too far for contact.
                low = max(visual_props["gap_spacing_min"], gap_min_required)
                high = max(visual_props["gap_spacing_max"], low + 18)
                spacing = random.randint(
                    low,
                    high,
                )
            else:
                # Normal spacings are reachable so chain can continue.
                low = min(visual_props["normal_spacing_min"], normal_max_allowed)
                high = min(visual_props["normal_spacing_max"], normal_max_allowed)
                if high < low:
                    low = normal_min_allowed
                    high = normal_max_allowed
                spacing = random.randint(
                    low,
                    high,
                )
            spacings.append(spacing)

        # Calculate x positions
        positions = []
        x = visual_props['margin_left']
        for i in range(num_dominos):
            positions.append(x)
            if i < len(spacings):
                x += spacings[i]

        # Simulate chain trigger physically: next domino falls only if spacing is reachable.
        last_fallen_index = 0
        for i, spacing in enumerate(spacings):
            if spacing <= max_trigger_spacing:
                last_fallen_index = i + 1
            else:
                break
        answer = last_fallen_index + 1  # 1-indexed for display
        contact_angles = self._compute_contact_angles(spacings, visual_props)
        rest_angles = self._compute_rest_angles(last_fallen_index, contact_angles)

        task_data.update({
            "positions": positions,
            "spacings": spacings,
            "answer": answer,  # 1-indexed (domino number)
            "last_fallen_index": last_fallen_index,  # 0-indexed
            "contact_angles": contact_angles,
            "rest_angles": rest_angles,
        })
        
        return task_data

    def _max_trigger_spacing(self, visual_props: dict) -> int:
        """
        Maximum center-to-center spacing where a fallen domino still reaches the next one.
        Reach model (rigid rectangle): max horizontal reach of top-front corner.
        """
        w = visual_props["domino_width"]
        h = visual_props["domino_height"]
        # Max of h*sin(theta) + w*cos(theta) over theta in [0, 90) is sqrt(h^2 + w^2).
        return int(math.hypot(h, w))

    def _compute_contact_angles(self, spacings: List[int], visual_props: dict) -> List[Optional[float]]:
        """Angle (from vertical) where domino i first touches domino i+1."""
        w = visual_props["domino_width"]
        h = visual_props["domino_height"]
        max_reach = math.hypot(h, w)
        phase = math.atan2(w, h)  # h*sin(t) + w*cos(t) = R*sin(t + phase)

        out: List[Optional[float]] = []
        for spacing in spacings:
            if spacing > max_reach:
                out.append(None)
                continue
            ratio = spacing / max(max_reach, 1e-6)
            ratio = max(0.0, min(1.0, ratio))
            theta = math.asin(ratio) - phase
            out.append(max(0.0, math.degrees(theta)))
        return out

    def _compute_rest_angles(self, last_fallen_index: int, contact_angles: List[Optional[float]]) -> List[float]:
        """
        Stable final tilt angles for fallen dominos.
        Dominos keep falling after contact; use larger rest angles for natural settling.
        """
        rest: List[float] = []
        for i in range(last_fallen_index + 1):
            if i < last_fallen_index and contact_angles[i] is not None:
                rest.append(max(50.0, min(74.0, contact_angles[i] + 20.0)))
            else:
                rest.append(75.0)
        return rest

    # ══════════════════════════════════════════════════════════════════════════
    #  RENDERING
    # ══════════════════════════════════════════════════════════════════════════

    def _render_initial_state(self, task_data: dict) -> Image.Image:
        """Render initial state with all dominos standing."""
        visual_props = task_data['visual_props']
        img = Image.new('RGB', self.config.image_size, visual_props['background_color'])
        draw = ImageDraw.Draw(img)

        # Draw ground
        self._draw_ground(draw, visual_props)

        # Draw all dominos standing
        for i in range(task_data["num_dominos"]):
            x = task_data["positions"][i]
            self._draw_domino_standing(draw, x, i + 1, visual_props['domino_color'], visual_props)

        # Draw "PUSH" arrow at first domino
        self._draw_push_indicator(draw, task_data["positions"][0], visual_props)

        return img

    def _render_final_state(self, task_data: dict) -> Image.Image:
        """Render final state with fallen and standing dominos."""
        visual_props = task_data['visual_props']
        img = Image.new('RGB', self.config.image_size, visual_props['background_color'])
        draw = ImageDraw.Draw(img)
        final_state = self._simulate_domino_angles(task_data, max_frames=220)[-1]
        final_angles = final_state["angles"]
        final_xs = final_state["xs"]

        # Draw ground
        self._draw_ground(draw, visual_props)

        # Draw dominos in two passes to avoid clipping issues:
        # Pass 1: Draw all fallen dominos first (they should be behind standing ones)
        for i in range(task_data["num_dominos"]):
            if i <= task_data["last_fallen_index"]:
                x = final_xs[i]
                self._draw_domino_at_angle(
                    draw, x, i + 1, final_angles[i], visual_props['fallen_domino_color'], visual_props
                )
        
        # Pass 2: Draw all standing dominos on top
        for i in range(task_data["num_dominos"]):
            if i > task_data["last_fallen_index"]:
                x = final_xs[i]
                self._draw_domino_at_angle(draw, x, i + 1, final_angles[i], visual_props['domino_color'], visual_props)

        return img

    def _draw_ground(self, draw: ImageDraw.Draw, visual_props: dict) -> None:
        """Draw ground line."""
        y = visual_props['ground_y']
        width = self.config.image_size[0]
        draw.line([(0, y), (width, y)], fill=visual_props['ground_color'], width=4)

        # Draw some texture lines
        for i in range(0, width, 40):
            draw.line([(i, y + 2), (i + 20, y + 2)], fill=visual_props['ground_color'], width=2)

    def _draw_domino_standing(
        self,
        draw: ImageDraw.Draw,
        x: int,
        number: int,
        color: Tuple[int, int, int],
        visual_props: dict
    ) -> None:
        """Draw a standing domino at position x."""
        w = visual_props['domino_width']
        h = visual_props['domino_height']
        ground_y = visual_props['ground_y']

        # Rectangle from ground up
        left = x - w // 2
        top = ground_y - h
        right = x + w // 2
        bottom = ground_y

        # Draw domino body
        draw.rectangle([left, top, right, bottom], fill=color, outline=(20, 20, 20), width=2)

        # Draw number
        font = self._get_font(32)
        text = str(number)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        text_x = x - text_w // 2
        text_y = ground_y - h // 2 - text_h // 2
        draw.text((text_x, text_y), text, fill=(255, 255, 255), font=font)

    def _draw_domino_fallen(
        self,
        draw: ImageDraw.Draw,
        x: int,
        number: int,
        color: Tuple[int, int, int],
        visual_props: dict
    ) -> None:
        """Draw a fallen domino (tilted right, bottom edge on ground)."""
        poly, _ = self._domino_polygon(x, 75, visual_props)

        # Draw as polygon
        draw.polygon(poly, fill=color, outline=(20, 20, 20))

        # Draw number at center of fallen domino
        center_x = sum(pt[0] for pt in poly) / 4
        center_y = sum(pt[1] for pt in poly) / 4
        font = self._get_font(28)
        text = str(number)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        draw.text((center_x - text_w // 2, center_y - text_h // 2), text, fill=(255, 255, 255), font=font)

    def _draw_push_indicator(self, draw: ImageDraw.Draw, x: int, visual_props: dict) -> None:
        """Draw PUSH arrow pointing at first domino."""
        arrow_y = visual_props['ground_y'] - visual_props['domino_height'] - 40
        arrow_end_x = x - visual_props['domino_width'] // 2 - 5
        
        # Calculate PUSH text width to ensure everything fits
        font = self._get_font(28)
        text = "PUSH"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        
        # Ensure arrow starts at least 20px from left edge
        min_arrow_start_x = text_w + 40  # text width + margins
        arrow_start_x = max(min_arrow_start_x, x - 80)
        
        # If arrow would be too short, adjust the arrow_start further left within bounds
        if arrow_end_x - arrow_start_x < 30:
            arrow_start_x = max(20 + text_w + 10, arrow_end_x - 50)

        # Draw arrow line
        draw.line(
            [(arrow_start_x, arrow_y), (arrow_end_x, arrow_y)],
            fill=self.config.text_color,
            width=3
        )

        # Draw arrowhead
        draw.polygon([
            (arrow_end_x, arrow_y),
            (arrow_end_x - 10, arrow_y - 6),
            (arrow_end_x - 10, arrow_y + 6)
        ], fill=self.config.text_color)

        # Draw "PUSH" text - ensure it's within bounds
        text_x = max(20, arrow_start_x - text_w - 10)
        draw.text(
            (text_x, arrow_y - 10),
            text,
            fill=self.config.text_color,
            font=font
        )

    def _draw_question_marker(self, draw: ImageDraw.Draw) -> None:
        """Draw prominent ? marker."""
        # Position in upper right area
        x = self.config.image_size[0] - 80
        y = 60

        # Draw circle background
        radius = 30
        draw.ellipse(
            [x - radius, y - radius, x + radius, y + radius],
            fill=(255, 193, 7),  # Yellow
            outline=self.config.text_color,
            width=3
        )

        # Draw ?
        font = self._get_font(36)
        text = "?"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        draw.text(
            (x - text_w // 2, y - text_h // 2 - 2),
            text,
            fill=self.config.text_color,
            font=font
        )

    def _draw_gap_indicator(self, draw: ImageDraw.Draw, x1: int, x2: int, visual_props: dict) -> None:
        """Draw TOO FAR indicator between two positions."""
        y = visual_props['ground_y'] + 25

        # Draw bracket
        bracket_top = y - 5
        bracket_bottom = y + 5

        # Left bracket
        draw.line([(x1, bracket_top), (x1, bracket_bottom)], fill=self.config.gap_indicator_color, width=2)
        # Right bracket
        draw.line([(x2, bracket_top), (x2, bracket_bottom)], fill=self.config.gap_indicator_color, width=2)
        # Connecting line (no on-image caption; gap is visible from spacing + bracket)
        draw.line([(x1, y), (x2, y)], fill=self.config.gap_indicator_color, width=2)

    def _draw_answer_circle(self, draw: ImageDraw.Draw, x: float, angle_deg: float, visual_props: dict) -> None:
        """Draw an enclosing highlight around the full last fallen domino."""
        poly, _ = self._domino_polygon(x, angle_deg, visual_props)
        min_x = min(px for px, _ in poly)
        max_x = max(px for px, _ in poly)
        min_y = min(py for _, py in poly)
        max_y = max(py for _, py in poly)

        # Padding keeps the full domino body comfortably inside the circle.
        pad = max(14, visual_props["domino_width"] // 3)
        draw.ellipse(
            [min_x - pad, min_y - pad, max_x + pad, max_y + pad],
            outline=self.config.highlight_color,
            width=4,
        )

    def _draw_title(self, draw: ImageDraw.Draw, text: str) -> None:
        """Draw title text at top of image."""
        font = self._get_font(42)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        x = (self.config.image_size[0] - text_w) // 2
        y = 20
        draw.text((x, y), text, fill=self.config.text_color, font=font)

    def _get_font(self, size: int) -> ImageFont.FreeTypeFont:
        """Get a font of specified size."""
        font_names = [
            "arial.ttf",
            "Arial.ttf",
            "DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "C:/Windows/Fonts/arial.ttf",
        ]

        for font_name in font_names:
            try:
                return ImageFont.truetype(font_name, size)
            except (OSError, IOError):
                continue

        return ImageFont.load_default()

    # ══════════════════════════════════════════════════════════════════════════
    #  VIDEO GENERATION
    # ══════════════════════════════════════════════════════════════════════════

    def _generate_video(self, task_data: dict, task_id: str) -> Optional[str]:
        """Generate animation video showing chain reaction."""
        temp_dir = Path(tempfile.gettempdir()) / f"{self.config.domain}_videos"
        temp_dir.mkdir(parents=True, exist_ok=True)
        video_path = temp_dir / f"{task_id}_ground_truth.mp4"

        frames = self._create_animation_frames(task_data)

        result = self.video_generator.create_video_from_frames(frames, video_path)

        return str(result) if result else None

    def _create_animation_frames(self, task_data: dict) -> List[Image.Image]:
        """Create animation frames using contact-triggered simplified domino physics."""
        frames = []

        # Phase 1: Hold initial state (reduced for 5-second target)
        initial_frame = self._render_initial_state(task_data)
        for _ in range(10):  # Reduced from 15 to 10
            frames.append(initial_frame)

        # Phase 2: Contact-driven chain simulation
        snapshots = self._simulate_domino_angles(task_data, max_frames=220)
        for state in snapshots:
            frames.append(self._render_simulation_frame(task_data, state))

        # Phase 3: End shortly after the chain settles.
        settle_state = snapshots[-1]
        settled_frame = self._render_simulation_frame(task_data, settle_state)
        for _ in range(4):
            frames.append(settled_frame)

        return frames

    def _simulate_domino_angles(self, task_data: dict, max_frames: int = 220) -> List[Dict[str, List[float]]]:
        """
        Simulate domino motion with a real rigid-body physics engine (pymunk).
        Each domino is a non-deforming rectangle; collisions and gravity drive
        chain propagation.
        """
        import pymunk

        visual_props = task_data["visual_props"]
        positions = task_data["positions"]
        n = task_data["num_dominos"]
        w = float(visual_props["domino_width"])
        h = float(visual_props["domino_height"])

        space = pymunk.Space()
        space.gravity = (0.0, -3200.0)
        space.damping = 0.999

        # Ground as a static segment in physics world (y=0).
        left = float(min(positions) - 250)
        right = float(max(positions) + 350)
        ground = pymunk.Segment(space.static_body, (left, 0.0), (right, 0.0), 2.0)
        ground.friction = 1.0
        ground.elasticity = 0.0
        space.add(ground)

        bodies: List[pymunk.Body] = []
        mass = 2.2
        for x in positions:
            moment = pymunk.moment_for_box(mass, (w, h))
            body = pymunk.Body(mass, moment)
            body.position = (float(x), h / 2.0)
            body.angle = 0.0
            shape = pymunk.Poly.create_box(body, (w, h))
            shape.friction = 0.88
            shape.elasticity = 0.0
            # Keep the domino foot on ground (realistic pivot, avoids unrealistic sliding/stacking).
            pivot = pymunk.PivotJoint(
                space.static_body,
                body,
                (float(x), 0.0),
                (0.0, -h / 2.0),
            )
            pivot.collide_bodies = False
            limiter = pymunk.RotaryLimitJoint(space.static_body, body, -math.radians(89.0), math.radians(2.0))
            space.add(body, shape, pivot, limiter)
            bodies.append(body)

        # Kick the first domino near its top edge to the right.
        if bodies:
            bodies[0].apply_impulse_at_local_point((950.0, 0.0), (0.0, h * 0.45))

        dt = 1.0 / 240.0
        substeps = 6
        snapshots: List[Dict[str, List[float]]] = []
        settled_runs = 0

        for _ in range(max_frames):
            for _ in range(substeps):
                space.step(dt)

            angles: List[float] = []
            total_omega = 0.0
            total_speed = 0.0
            for body in bodies:
                # body.angle is CCW in a y-up world. Right-fall is negative angle.
                deg_from_vertical = math.degrees(-body.angle)
                deg_from_vertical = max(0.0, min(89.0, deg_from_vertical))
                angles.append(deg_from_vertical)
                total_omega += abs(body.angular_velocity)
                total_speed += body.velocity.length

            xs: List[float] = []
            for body, angle in zip(bodies, angles):
                pivot_x = float(body.position.x) - (h * 0.5) * math.sin(math.radians(angle))
                xs.append(pivot_x)
            snapshots.append({
                "angles": angles,
                "xs": xs,
            })

            # Stop once motion is nearly settled for multiple frames.
            if total_omega < 0.22 and total_speed < 4.0:
                settled_runs += 1
                if settled_runs >= 12 and len(snapshots) > 35:
                    break
            else:
                settled_runs = 0

        if not snapshots:
            snapshots = [{"angles": [0.0] * n, "xs": [float(x) for x in positions]}]

        final_angles = snapshots[-1]["angles"]
        fallen_threshold = 16.0
        last_fallen_index = 0
        for i, angle in enumerate(final_angles):
            if angle >= fallen_threshold:
                last_fallen_index = i
            else:
                break

        task_data["last_fallen_index"] = last_fallen_index
        task_data["answer"] = last_fallen_index + 1

        return snapshots

    def _render_simulation_frame(
        self,
        task_data: dict,
        state: Dict[str, List[float]],
        show_measurement: bool = False,
        show_gap_indicator: bool = False,
    ) -> Image.Image:
        """Render one frame from current per-domino angles."""
        visual_props = task_data['visual_props']
        angles = state["angles"]
        xs = state["xs"]
        img = Image.new('RGB', self.config.image_size, visual_props['background_color'])
        draw = ImageDraw.Draw(img)

        self._draw_ground(draw, visual_props)

        for i in range(task_data["num_dominos"]):
            x = xs[i]
            angle = angles[i]
            is_fallen = i <= task_data["last_fallen_index"]
            color = visual_props['fallen_domino_color'] if is_fallen and angle > 0.5 else visual_props['domino_color']
            self._draw_domino_at_angle(draw, x, i + 1, angle, color, visual_props)

        if show_measurement:
            self._draw_distance_measurement(
                draw,
                task_data,
                visual_props,
                angles[task_data["last_fallen_index"]],
                x_override=xs[task_data["gap_after"]],
            )

        if show_gap_indicator:
            gap_x1 = task_data["positions"][task_data["gap_after"]]
            gap_x2 = task_data["positions"][task_data["gap_after"] + 1]
            self._draw_gap_indicator(draw, gap_x1, gap_x2, visual_props)

        return img

    def _render_animation_frame(
        self,
        task_data: dict,
        falling_up_to: int,
        current_angle: float,
        show_measurement: bool = False,
        show_gap_indicator: bool = False
    ) -> Image.Image:
        """Render a single animation frame."""
        visual_props = task_data['visual_props']
        img = Image.new('RGB', self.config.image_size, visual_props['background_color'])
        draw = ImageDraw.Draw(img)

        # Draw ground
        self._draw_ground(draw, visual_props)

        # Draw dominos
        for i in range(task_data["num_dominos"]):
            x = task_data["positions"][i]

            if i < falling_up_to:
                # Already fully fallen
                self._draw_domino_fallen(draw, x, i + 1, visual_props['fallen_domino_color'], visual_props)
            elif i == falling_up_to:
                # Currently falling - draw at current angle
                self._draw_domino_at_angle(draw, x, i + 1, current_angle, visual_props['fallen_domino_color'], visual_props)
            else:
                # Still standing
                self._draw_domino_standing(draw, x, i + 1, visual_props['domino_color'], visual_props)

        # Show measurement if requested
        if show_measurement:
            self._draw_distance_measurement(draw, task_data, visual_props)

        # Show gap indicator if requested
        if show_gap_indicator:
            gap_x1 = task_data["positions"][task_data["gap_after"]]
            gap_x2 = task_data["positions"][task_data["gap_after"] + 1]
            self._draw_gap_indicator(draw, gap_x1, gap_x2, visual_props)

        return img

    def _draw_domino_at_angle(
        self,
        draw: ImageDraw.Draw,
        x: float,
        number: int,
        angle: float,
        color: Tuple[int, int, int],
        visual_props: dict
    ) -> None:
        """Draw a domino at a specific angle (0 = standing, 90 = flat)."""
        if angle <= 0:
            self._draw_domino_standing(draw, x, number, color, visual_props)
            return
        angle = min(89.0, angle)

        poly, _ = self._domino_polygon(x, angle, visual_props)
        draw.polygon(poly, fill=color, outline=(20, 20, 20))

        # Draw number
        center_x = sum(pt[0] for pt in poly) / 4
        center_y = sum(pt[1] for pt in poly) / 4
        font = self._get_font(28)
        text = str(number)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        draw.text((center_x - text_w // 2, center_y - text_h // 2), text, fill=(255, 255, 255), font=font)

    def _domino_polygon(
        self,
        x: float,
        angle_deg: float,
        visual_props: dict,
    ) -> Tuple[List[Tuple[float, float]], float]:
        """
        Build a domino polygon at a given angle from vertical.
        Uses rigid-body rotation (no deformation), then lifts polygon so its lowest point
        sits on the ground line to avoid visual suspension.
        Returns (polygon_points, tip_x).
        """
        w = visual_props["domino_width"]
        h = visual_props["domino_height"]
        ground_y = visual_props["ground_y"]
        angle = math.radians(angle_deg)

        # Rotate rigid rectangle clockwise around bottom-center pivot (x, ground_y).
        # Local standing coordinates:
        #   bl(-w/2,0), tl(-w/2,-h), tr(w/2,-h), br(w/2,0)
        def rot(lx: float, ly: float) -> Tuple[float, float]:
            # In image space (x right, y down), clockwise-positive rotation:
            # x' = x*cos(a) - y*sin(a), y' = x*sin(a) + y*cos(a)
            xr = lx * math.cos(angle) - ly * math.sin(angle)
            yr = lx * math.sin(angle) + ly * math.cos(angle)
            return x + xr, ground_y + yr

        p1 = rot(-w / 2.0, 0.0)   # bottom-left
        p2 = rot(-w / 2.0, -h)    # top-left
        p3 = rot(w / 2.0, -h)     # top-right
        p4 = rot(w / 2.0, 0.0)    # bottom-right
        poly = [p1, p2, p3, p4]

        max_y = max(pt[1] for pt in poly)
        if max_y > ground_y:
            lift = max_y - ground_y
            poly = [(px, py - lift) for (px, py) in poly]

        tip_x = poly[2][0]
        return poly, tip_x

    def _draw_distance_measurement(
        self,
        draw: ImageDraw.Draw,
        task_data: dict,
        visual_props: dict,
        angle_deg: float = 75.0,
        x_override: Optional[float] = None,
    ) -> None:
        """Draw distance measurement between last fallen and next domino."""
        gap_idx = task_data["gap_after"]
        x1 = task_data["positions"][gap_idx]
        x2 = task_data["positions"][gap_idx + 1]

        # For fallen domino, tip is further right
        _, tip_x = self._domino_polygon(x_override if x_override is not None else x1, angle_deg, visual_props)

        y = visual_props['ground_y'] - visual_props['domino_height'] // 2

        # Draw measurement line
        draw.line([(tip_x, y), (x2, y)], fill=(255, 165, 0), width=2)

        # Draw end markers
        draw.line([(tip_x, y - 10), (tip_x, y + 10)], fill=(255, 165, 0), width=2)
        draw.line([(x2, y - 10), (x2, y + 10)], fill=(255, 165, 0), width=2)
