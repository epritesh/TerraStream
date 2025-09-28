from __future__ import annotations
import math
from typing import Dict, List, Tuple
import pygame

from . import config
from .noise import Noise1D  # use class directly

Point = Tuple[float, float]

class TerrainManager:
    """Generates and caches terrain chunks.

    Each chunk spans CHUNK_WIDTH pixels and stores sampled points spaced by POINT_SPACING.
    To reduce visible seams at chunk boundaries we 'peek' one point beyond the boundary,
    then when the adjacent chunk is generated we blend a small overlap region so the slope
    transitions smoothly.
    """
    def __init__(self, seed: int = config.SEED):
        self.seed = seed  # store local seed
        self.noise = Noise1D(seed=seed)  # dedicated noise instance
        self.chunks: Dict[int, List[Point]] = {}
        self.overlap = config.POINT_SPACING * 2  # pixels to blend at boundaries

    def world_x_range_for_chunk(self, chunk_idx: int) -> Tuple[int, int]:
        start_x = chunk_idx * config.CHUNK_WIDTH
        end_x = start_x + config.CHUNK_WIDTH
        return start_x, end_x

    def _sample_height(self, x: float) -> float:
        # Use fractal noise through the instance for determinism per seed
        n = self.noise.fractal(x * config.NOISE_SCALE, octaves=config.NOISE_OCTAVES)
        return config.BASELINE - n * config.NOISE_AMPLITUDE

    def generate_chunk(self, chunk_idx: int) -> None:
        if (not config.ALLOW_NEGATIVE_CHUNKS) and chunk_idx < 0:
            return
        if chunk_idx in self.chunks:
            return
        start_x, end_x = self.world_x_range_for_chunk(chunk_idx)
        points: List[Point] = []

        # Include one extra sample beyond end for smoothing with next chunk
        for sx in range(start_x, end_x + config.POINT_SPACING, config.POINT_SPACING):
            y = self._sample_height(sx)
            points.append((float(sx), y))

        self.chunks[chunk_idx] = points

        # If previous exists, blend overlap region between previous tail and this head
        prev_idx = chunk_idx - 1
        if prev_idx in self.chunks:
            self._blend_boundary(prev_idx, chunk_idx)

    def _blend_boundary(self, left_idx: int, right_idx: int) -> None:
        left_points = self.chunks[left_idx]
        right_points = self.chunks[right_idx]
        # Determine overlapping x range to blend
        blend_start = left_points[-1][0] - self.overlap
        blend_end = left_points[-1][0]
        # Build mapping for right points for quick replacement
        rp_index = {p[0]: i for i, p in enumerate(right_points)}
        # Gather points in left chunk in blend zone (excluding final duplicate maybe)
        left_zone = [p for p in left_points if blend_start <= p[0] <= blend_end]
        if not left_zone:
            return
        # Compute slope at boundary using last two left points
        if len(left_points) >= 2:
            (x1, y1), (x2, y2) = left_points[-2], left_points[-1]
            boundary_slope = (y2 - y1) / (x2 - x1) if x2 != x1 else 0.0
        else:
            boundary_slope = 0.0
        # Adjust the first few right points so first derivative feels continuous
        for p in right_points:
            x = p[0]
            if x > blend_end + self.overlap:
                break
            if x in rp_index and x <= blend_end + self.overlap:
                t = (x - (blend_end)) / (self.overlap + config.POINT_SPACING)
                t = max(0.0, min(1.0, t))
                # predicted y continuing slope from boundary
                predicted = left_points[-1][1] + boundary_slope * (x - left_points[-1][0])
                # current procedural y (original)
                original = p[1]
                blended_y = predicted * (1 - t) + original * t
                right_points[rp_index[x]] = (x, blended_y)

    def ensure_chunks(self, camera_x: float, screen_width: int) -> None:
        # Prefetch based on configurable window so terrain appears instantly when revealed
        current_idx = int(math.floor(camera_x / config.CHUNK_WIDTH))
        left_keep = current_idx - config.PREFETCH_CHUNKS_BEHIND
        right_target = current_idx + config.PREFETCH_CHUNKS_AHEAD
        # Cap chunk generations per frame to avoid frame spikes
        budget = config.MAX_CHUNKS_PER_FRAME
        # Iterate forward first (player typically moves right)
        for idx in range(current_idx - 1, right_target + 1):
            if budget <= 0:
                break
            if (not config.ALLOW_NEGATIVE_CHUNKS) and idx < 0:
                continue
            if idx not in self.chunks:
                self.generate_chunk(idx)
                budget -= 1
        # Then ensure minimal behind chunks
        if budget > 0:
            for idx in range(current_idx - 2, left_keep - 1, -1):
                if budget <= 0:
                    break
                if idx not in self.chunks:
                    if (not config.ALLOW_NEGATIVE_CHUNKS) and idx < 0:
                        continue
                    self.generate_chunk(idx)
                    budget -= 1
        # Prune chunks far behind window (keep those ahead even if offscreen)
        prune = [ci for ci in self.chunks.keys() if ci < left_keep]
        for ci in prune:
            del self.chunks[ci]

    def sample_height(self, x: float) -> float:
        # Find chunk
        chunk_idx = int(math.floor(x / config.CHUNK_WIDTH))
        if chunk_idx not in self.chunks:
            self.generate_chunk(chunk_idx)
        points = self.chunks[chunk_idx]
        # Binary search or linear walk (few points so linear is fine)
        for i in range(len(points) - 1):
            x0, y0 = points[i]
            x1, y1 = points[i + 1]
            if x0 <= x <= x1:
                t = (x - x0) / (x1 - x0) if x1 != x0 else 0.0
                return y0 + (y1 - y0) * t
        return points[-1][1]

    def _catmull_rom(self, pts: List[Point], subdivs: int) -> List[Point]:
        if len(pts) < config.TERRAIN_SMOOTH_MIN_POINTS or subdivs <= 1:
            return pts
        # Break the ridge into segments where slope or vertical delta is extreme to avoid huge spikes
        max_dy = config.NOISE_AMPLITUDE * 1.2  # treat anything larger than this between raw samples as a boundary
        max_slope = max_dy / config.POINT_SPACING * 0.8
        segments: List[List[Point]] = []
        cur: List[Point] = [pts[0]]
        for i in range(1, len(pts)):
            x0, y0 = pts[i - 1]
            x1, y1 = pts[i]
            dy = abs(y1 - y0)
            slope = dy / max(1e-6, (x1 - x0))
            if dy > max_dy or slope > max_slope:
                # start new segment, push current
                if len(cur) >= 2:
                    segments.append(cur)
                cur = [pts[i]]
            else:
                cur.append(pts[i])
        if len(cur) >= 2:
            segments.append(cur)

        def smooth_segment(seg: List[Point]) -> List[Point]:
            if len(seg) < config.TERRAIN_SMOOTH_MIN_POINTS:
                return seg
            out: List[Point] = []
            ext = [seg[0]] + seg + [seg[-1]]
            for j in range(1, len(ext) - 2):
                p0 = ext[j - 1]
                p1 = ext[j]
                p2 = ext[j + 1]
                p3 = ext[j + 2]
                for s in range(subdivs):
                    t = s / subdivs
                    t2 = t * t
                    t3 = t2 * t
                    x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + (2*p0[0] - 5*p1[0] + 4*p2[0] - p3[0]) * t2 + (-p0[0] + 3*p1[0] - 3*p2[0] + p3[0]) * t3)
                    y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + (2*p0[1] - 5*p1[1] + 4*p2[1] - p3[1]) * t2 + (-p0[1] + 3*p1[1] - 3*p2[1] + p3[1]) * t3)
                    out.append((x, y))
            out.append(seg[-1])
            return out

        smoothed: List[Point] = []
        for seg in segments:
            smoothed.extend(smooth_segment(seg))
        if not smoothed:
            return pts
        if config.TERRAIN_SMOOTH_VERTICAL_CLAMP:
            raw_min = min(p[1] for p in pts)
            raw_max = max(p[1] for p in pts)
            band_min = raw_min - config.TERRAIN_SMOOTH_VERTICAL_CLAMP
            band_max = raw_max + config.TERRAIN_SMOOTH_VERTICAL_CLAMP
            smoothed = [(x, max(band_min, min(band_max, y))) for x, y in smoothed]
        # Optional spike filter pass to relax sharp isolated upward spikes
        if getattr(config, 'SPIKE_FILTER_ENABLED', False):
            threshold = getattr(config, 'SPIKE_FILTER_THRESHOLD', 18.0)
            relax = getattr(config, 'SPIKE_RELAX_FACTOR', 0.5)
            passes = getattr(config, 'SPIKE_FILTER_PASSES', 1)
            for _ in range(passes):
                changed = False
                new_pts: List[Point] = list(smoothed)
                for i in range(2, len(smoothed) - 2):
                    x, y = smoothed[i]
                    # average of two neighbors on each side for stability
                    y_prev = (smoothed[i - 1][1] + smoothed[i - 2][1]) * 0.5
                    y_next = (smoothed[i + 1][1] + smoothed[i + 2][1]) * 0.5
                    avg = 0.5 * (y_prev + y_next)
                    diff = y - avg
                    if diff < -threshold:  # negative diff => point significantly above surrounding (smaller y is higher visually)
                        new_y = y - diff * relax  # move toward average
                        new_pts[i] = (x, new_y)
                        changed = True
                smoothed = new_pts
                if not changed:
                    break
        return smoothed

    def draw(self, surface: pygame.Surface, camera_x: float, day_t: float = 1.0):
        screen_w = surface.get_width()
        screen_h = surface.get_height()
        self.ensure_chunks(camera_x, screen_w)
        left_bound = camera_x - 50
        right_bound = camera_x + screen_w + 50
        draw_points: List[Point] = []
        # Gather points from any chunk overlapping
        for pts in self.chunks.values():
            for x, y in pts:
                if x < 0 and not config.ALLOW_NEGATIVE_CHUNKS:
                    continue
                if left_bound <= x <= right_bound:
                    draw_points.append((x, y))
        if not draw_points:
            return
        # Sort by x to ensure polygon continuity
        draw_points.sort(key=lambda p: p[0])
        ridge = draw_points
        if config.TERRAIN_SMOOTHING_ENABLED:
            ridge = self._catmull_rom(ridge, config.TERRAIN_SMOOTH_SUBDIVS)
        # Convert to screen space (camera_x centers player; here simple offset)
        poly = [(x - camera_x, y) for x, y in ridge]
        # Close polygon down to bottom
        poly.append((poly[-1][0], screen_h))
        poly.append((poly[0][0], screen_h))
        # Biome modulation by large-scale band index
        def lerp(a, b, t):
            return int(a + (b - a) * t)
        biome_colors = getattr(config, 'BIOME_COLOR_VARIANTS', [config.COLOR_TERRAIN])
        band_w = getattr(config, 'BIOME_BAND_WIDTH', config.CHUNK_WIDTH * 8)
        # Determine dominant biome color in visible window via average of band indices
        if biome_colors:
            avg_x = sum(p[0] for p in ridge) / len(ridge)
            band_idx = int(avg_x // band_w) % len(biome_colors)
            base_col = biome_colors[band_idx]
        else:
            base_col = config.COLOR_TERRAIN
        # Day-night blended terrain base
        day_col = getattr(config, 'TERRAIN_DAY_COLOR', base_col)
        night_col = getattr(config, 'TERRAIN_NIGHT_COLOR', base_col)
        terrain_col = (lerp(night_col[0], day_col[0], day_t),
                       lerp(night_col[1], day_col[1], day_t),
                       lerp(night_col[2], day_col[2], day_t))
        # Modulate toward biome base
        mix = 0.5
        terrain_col = (lerp(terrain_col[0], base_col[0], mix),
                        lerp(terrain_col[1], base_col[1], mix),
                        lerp(terrain_col[2], base_col[2], mix))
        pygame.draw.polygon(surface, terrain_col, poly)
        # Ridge highlight
        highlight = getattr(config, 'RIDGE_HIGHLIGHT_COLOR', (255, 255, 255))
        hl_alpha = getattr(config, 'RIDGE_HIGHLIGHT_ALPHA', 120)
        shadow_alpha = getattr(config, 'RIDGE_SHADOW_ALPHA', 60)
        # Build a temporary surface for highlight/edge with per-pixel alpha
        edge_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        sun_dir_x = 0.0
        sun_dir_y = -1.0
        # Optional highlight noise
        noise_mod = None
        if getattr(config, 'HIGHLIGHT_NOISE_ENABLED', False):
            noise_mod = Noise1D(seed=self.seed + 777)
            h_noise_scale = getattr(config, 'HIGHLIGHT_NOISE_SCALE', 0.0015)
            h_noise_amp = getattr(config, 'HIGHLIGHT_NOISE_AMPLITUDE', 0.35)
        if getattr(config, 'SLOPE_LIGHTING_ENABLED', False):
            # Slight forward bias so slopes facing up-left get a bit more light
            sun_dir_x = -0.3
            length = math.hypot(sun_dir_x, sun_dir_y)
            sun_dir_x /= length
            sun_dir_y /= length
        for i in range(len(ridge) - 1):
            (x0, y0), (x1, y1) = ridge[i], ridge[i + 1]
            seg_dx = x1 - x0
            seg_dy = y1 - y0
            if seg_dx == 0:
                normal = (0.0, -1.0)
            else:
                # 2D normal ( -dy, dx ) then normalize; we want upward component
                nx = -seg_dy
                ny = seg_dx
                nl = math.hypot(nx, ny)
                if nl != 0:
                    nx /= nl
                    ny /= nl
                # Ensure upward facing
                if ny > 0:
                    nx = -nx
                    ny = -ny
                normal = (nx, ny)
            if getattr(config, 'SLOPE_LIGHTING_ENABLED', False):
                dot = normal[0] * sun_dir_x + normal[1] * sun_dir_y
                dot = max(0.0, dot + getattr(config, 'SUN_NORMAL_BIAS', 0.3))
                intensity = min(1.0, dot * getattr(config, 'SUN_HIGHLIGHT_STRENGTH', 1.0))
            else:
                intensity = 1.0
            alpha = int(hl_alpha * intensity)
            if noise_mod is not None:
                # Sample highlight noise at midpoint x
                mx = (x0 + x1) * 0.5
                nval = noise_mod.fractal(mx * h_noise_scale, octaves=2)
                alpha = int(alpha * (1.0 + h_noise_amp * nval))
                alpha = max(0, min(255, alpha))
            pygame.draw.line(edge_surf, (*highlight, alpha), (x0 - camera_x, y0 - 1), (x1 - camera_x, y1 - 1), 2)
        # Subtle shadow just below ridge
        for i in range(len(ridge) - 1):
            (x0, y0), (x1, y1) = ridge[i], ridge[i + 1]
            if getattr(config, 'RIDGE_SHADOW_SLOPE_ATTEN', 0.0) > 0:
                slope = abs(y1 - y0) / max(1e-6, (x1 - x0)) if x1 != x0 else 0.0
                atten = 1.0 - min(1.0, slope * 0.25) * getattr(config, 'RIDGE_SHADOW_SLOPE_ATTEN', 0.6)
                sa = int(shadow_alpha * atten)
            else:
                sa = shadow_alpha
            pygame.draw.line(edge_surf, (0, 0, 0, sa), (x0 - camera_x, y0 + 2), (x1 - camera_x, y1 + 2), 2)
        surface.blit(edge_surf, (0, 0))
