from __future__ import annotations
import pygame
import math
from . import config
from .noise import Noise1D

class ParallaxBackground:
    def __init__(self, seed: int):
        self.layers = []
        # Separate noise generator per layer for variety (offset seed) 
        for i, layer in enumerate(config.PARALLAX_LAYERS):
            noise = Noise1D(seed=seed + i * 101)
            self.layers.append({"cfg": layer, "noise": noise})
        # Foreground silhouettes (close grass/foliage bands)
        self.fg_layers = []  # each: {noise, offset_seed}
        if getattr(config, 'FOREGROUND_SILHOUETTES_ENABLED', False):
            import random
            count = max(1, getattr(config, 'FOREGROUND_LAYER_COUNT', 1))
            for i in range(count):
                n = Noise1D(seed=seed + 5000 + i * 137)
                self.fg_layers.append({"noise": n, "rng": random.Random(seed + 7000 + i * 977)})
        # Foreground cache (per bucket camera position)
        self._fg_cache = {}
        self._fg_last_key = None
        self._fg_surface = None
        self._last_camera_px = None
        # Cloud blobs (generated once)
        self.clouds = []  # each entry: {speed, blobs:[(cx,cy,scale,surface)]}
        if getattr(config, 'CLOUD_ENABLED', False):
            import random
            rng = random.Random(seed * 17 + 42)
            count = getattr(config, 'CLOUD_LAYER_COUNT', 2)
            density = getattr(config, 'CLOUD_DENSITY', 6)
            for layer_idx in range(count):
                layer_speed = 0.05 + 0.1 * (layer_idx / max(1, count - 1))
                blobs = []
                for _ in range(density):
                    cx = rng.uniform(-500, 1500)
                    cy = rng.uniform(40, 160 + layer_idx * 40)
                    scale = rng.uniform(*getattr(config, 'CLOUD_SCALE_RANGE', (0.7, 1.3)))
                    # Prebuild ellipse surface (un-tinted white alpha = 255; tint & alpha applied on blit)
                    bw = int(140 * scale)
                    bh = int(60 * scale)
                    surf = pygame.Surface((bw, bh), pygame.SRCALPHA)
                    if getattr(config, 'CLOUD_SOFT_EDGES', True):
                        # Radial falloff inside ellipse
                        power = getattr(config, 'CLOUD_EDGE_FALLOFF_POWER', 2.0)
                        rw = bw / 2.0
                        rh = bh / 2.0
                        cxp = rw
                        cyp = rh
                        for yy in range(bh):
                            for xx in range(bw):
                                nx = (xx - cxp) / rw
                                ny = (yy - cyp) / rh
                                d = nx * nx + ny * ny
                                if d <= 1.0:
                                    # inner intensity (1 at center -> 0 at edge)
                                    inner = (1 - d) ** power
                                    a = int(255 * inner)
                                    surf.set_at((xx, yy), (255, 255, 255, a))
                    else:
                        pygame.draw.ellipse(surf, (255, 255, 255, 255), surf.get_rect())
                    blobs.append((cx, cy, scale, surf))
                self.clouds.append({"speed": layer_speed, "blobs": blobs})
        # Parallax vertical fade mask (single column scaled) if enabled
        self._parallax_fade_mask = None
        if getattr(config, 'PARALLAX_VERTICAL_FADE_ENABLED', False):
            h = config.WINDOW_HEIGHT
            col = pygame.Surface((1, h), pygame.SRCALPHA)
            power = getattr(config, 'PARALLAX_VERTICAL_FADE_POWER', 1.4)
            for y in range(h):
                t = y / (h - 1)
                # Inverse fade: top opaque, lower portion fades allowing fog to dominate
                a = int(255 * (1 - (t ** power)))
                col.set_at((0, y), (255, 255, 255, a))
            self._parallax_fade_mask = pygame.transform.scale(col, (config.WINDOW_WIDTH, h))
        # Haze bands (soft horizontal atmospheric layers)
        self.haze_band_template = None
        self.haze_noise = None
        if getattr(config, 'HAZE_BANDS_ENABLED', False):
            band_h = max(10, int(config.WINDOW_HEIGHT * 0.12))
            template = pygame.Surface((config.WINDOW_WIDTH, band_h), pygame.SRCALPHA)
            mid_alpha = getattr(config, 'HAZE_BAND_ALPHA', 18)
            # Build vertical bell-curve alpha falloff (cosine)
            for yy in range(band_h):
                t = yy / (band_h - 1)
                fade = math.sin(t * math.pi)  # 0 at edges -> 1 at center
                a = int(mid_alpha * fade)
                template.fill((255, 255, 255, a), pygame.Rect(0, yy, config.WINDOW_WIDTH, 1))
            self.haze_band_template = template
            from math import floor  # silence potential linter about unused import if removed later
            self.haze_noise = Noise1D(seed=seed + 999)
        # Fog cache
        self._fog_cache = {}
        self._fog_last_bucket = None

    def _layer_points(self, layer, camera_x: float, width: int, height: int):
        cfg = layer["cfg"]
        noise = layer["noise"]
        scale = cfg["scale"]
        amp = cfg["amplitude"]
        speed_factor = cfg.get("speed_factor", 0.5)
        spacing = config.PARALLAX_POINT_SPACING
        # World-space window for this layer (camera scaled by speed_factor)
        layer_cam = camera_x * speed_factor
        left_world = layer_cam - 100
        right_world = layer_cam + width + 200
        points = []
        x = int(left_world // spacing * spacing)
        while x <= right_world:
            n = noise.fractal(x * scale, octaves=3)
            y = height * 0.4 - n * amp
            # Convert layer world x to screen: subtract layer_cam, NOT full camera_x
            screen_x = x - layer_cam
            points.append((screen_x, y))
            x += spacing
        return points, speed_factor

    def get_sample_points(self, camera_x: float, width: int, height: int):
        """Return list of (speed_factor, first_point_x) for testing relative motion."""
        out = []
        for layer in self.layers:
            pts, sf = self._layer_points(layer, camera_x, width, height)
            if pts:
                out.append((sf, pts[0][0]))
        return out

    def draw(self, surface: pygame.Surface, camera_x: float, day_t: float = 1.0):
        w = surface.get_width()
        h = surface.get_height()
        fog_enabled = getattr(config, 'FOG_ENABLED', False)
        fog_start_y = int(h * getattr(config, 'FOG_HEIGHT_FRACTION', 0.55)) if fog_enabled else h
        # Draw parallax layers (closed to bottom; fog overlays later). Avoid per-layer full-surface allocations.
        for layer in self.layers:
            points, _ = self._layer_points(layer, camera_x, w, h)
            if len(points) < 2:
                continue
            base = layer["cfg"]["color"]
            depth = layer["cfg"].get("speed_factor", 0.5)
            # Atmospheric fade: deeper layers (smaller speed_factor) blend more with sky
            fade = 1.0 - min(1.0, depth * 1.5)
            # Day-night tint: lerp between night-dim and full color
            night_dim = 0.35
            brightness = night_dim + (1 - night_dim) * day_t
            # Lighten base color a bit so combined with fog doesn't become a solid band
            r = int(base[0] * brightness * (0.55 + 0.45 * fade))
            g = int(base[1] * brightness * (0.55 + 0.45 * fade))
            b = int(base[2] * brightness * (0.55 + 0.45 * fade))
            color = (min(255, r), min(255, g), min(255, b))
            poly = points.copy()
            poly.append((points[-1][0], h))
            poly.append((points[0][0], h))
            pygame.draw.polygon(surface, color, poly, 0)
        # Haze bands (draw after parallax, before clouds, so clouds sit above them)
        if self.haze_band_template is not None:
            count = max(1, getattr(config, 'HAZE_BAND_COUNT', 3))
            noise_scale = getattr(config, 'HAZE_BAND_NOISE_SCALE', 0.002)
            base_col = getattr(config, 'FOG_COLOR', (170, 200, 215))
            # Day-night modulation (fade out at deep night a bit)
            dn = 0.55 + 0.45 * day_t
            tint = (int(base_col[0] * dn), int(base_col[1] * dn), int(base_col[2] * dn))
            baseline = getattr(config, 'BASELINE', h * 0.55)
            vertical_span = baseline * 0.55  # region above baseline for haze distribution
            for i in range(count):
                f = (i + 1) / (count + 1)
                center_y = baseline - vertical_span * f
                # gentle undulation using noise based on world camera position
                n = self.haze_noise.fractal((camera_x * 0.25 + i * 311) * noise_scale, octaves=2)
                offset = n * 28
                y = int(center_y + offset - self.haze_band_template.get_height() / 2)
                # Create a tinted copy (alpha already encoded in template)
                band = self.haze_band_template.copy()
                band.fill((*tint, 255), special_flags=pygame.BLEND_RGBA_MULT)
                # Clip within screen
                surface.blit(band, (0, y))
        # Clouds drawn after parallax layer shapes (so they sit above distant hills) but before fog so fog mists them
        if self.clouds:
            cloud_alpha = getattr(config, 'CLOUD_ALPHA', 70)
            base_col = getattr(config, 'CLOUD_COLOR', (255, 255, 255))
            # Apply additional tint interpolation
            dt_day = getattr(config, 'CLOUD_TINT_DAY', (1, 1, 1))
            dt_night = getattr(config, 'CLOUD_TINT_NIGHT', (0.8, 0.85, 1.05))
            tint = (
                dt_night[0] + (dt_day[0] - dt_night[0]) * day_t,
                dt_night[1] + (dt_day[1] - dt_night[1]) * day_t,
                dt_night[2] + (dt_day[2] - dt_night[2]) * day_t,
            )
            for layer in self.clouds:
                speed = layer['speed']
                for cx, cy, sc, blob_surface in layer['blobs']:
                    world_x = cx + camera_x * speed
                    sx = (world_x % (w + 800)) - 400
                    # Create a tinted copy with target alpha (reuse size)
                    surf = blob_surface.copy()
                    # Multiply color (approximate by filling with blend) then apply alpha
                    r = max(0, min(255, int(base_col[0] * tint[0])))
                    g = max(0, min(255, int(base_col[1] * tint[1])))
                    b = max(0, min(255, int(base_col[2] * tint[2])))
                    # For BLEND_RGBA_MULT color alpha channel is also multiplied; keep 255 then blit alpha separately
                    surf.fill((r, g, b, 255), special_flags=pygame.BLEND_RGBA_MULT)
                    if cloud_alpha < 255:
                        # Apply desired final alpha by modulating overall surface alpha
                        surf.set_alpha(cloud_alpha)
                    surface.blit(surf, (sx, cy))
        # Apply parallax vertical fade mask (multiplies lower part) BEFORE fog to preserve layering
        if self._parallax_fade_mask is not None:
            surface.blit(self._parallax_fade_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        # Fog overlay last for proper depth fade over clouds & layers
        if fog_enabled:
            fog_top_alpha = getattr(config, 'FOG_ALPHA_TOP', 0)
            fog_bottom_alpha = getattr(config, 'FOG_ALPHA_BOTTOM', 140)
            start_y = fog_start_y
            day_fade = 0.65 + 0.35 * (1 - day_t)
            base_fog = getattr(config, 'FOG_COLOR', (170, 200, 215))
            # Twilight warm blend
            if getattr(config, 'FOG_TWILIGHT_ENABLED', False):
                span = getattr(config, 'FOG_TWILIGHT_SPAN', 0.18)
                warm = getattr(config, 'FOG_TWILIGHT_WARM', (225, 190, 150))
                edge_t = min(day_t, 1 - day_t)
                if edge_t < span:
                    k = 1 - (edge_t / span)  # 1 at exact edge (sunrise/sunset), 0 outside span
                    base_fog = (
                        int(base_fog[0] * (1 - k) + warm[0] * k),
                        int(base_fog[1] * (1 - k) + warm[1] * k),
                        int(base_fog[2] * (1 - k) + warm[2] * k),
                    )
            fog_height = h - start_y
            if fog_height > 0:
                steps = max(1, getattr(config, 'FOG_CACHE_STEPS', 160))
                bucket = int(day_t * (steps - 1))
                cache_key = (bucket, base_fog)
                grad_scaled = self._fog_cache.get(cache_key)
                if grad_scaled is None:
                    grad = pygame.Surface((1, fog_height), pygame.SRCALPHA)
                    for yy in range(fog_height):
                        trow = yy / (fog_height - 1) if fog_height > 1 else 1.0
                        a = int((fog_top_alpha * (1 - trow) + fog_bottom_alpha * trow) * day_fade)
                        grad.set_at((0, yy), (*base_fog, a))
                    grad_scaled = pygame.transform.scale(grad, (w, fog_height))
                    self._fog_cache[cache_key] = grad_scaled
                surface.blit(grad_scaled, (0, start_y))

    def draw_foreground(self, surface: pygame.Surface, camera_x: float, day_t: float):
        """Draw foreground silhouette grass layers for extra depth.

        Draw AFTER terrain but BEFORE player so player appears in front of silhouettes.
        """
        if not self.fg_layers:
            return
        # Skip recompute for tiny camera movement to reduce cost
        if getattr(config, 'FOREGROUND_MAX_FPS_IMPACT', True):
            if self._last_camera_px is not None and abs(camera_x - self._last_camera_px) < 0.8 and self._fg_surface is not None:
                surface.blit(self._fg_surface, (0,0))
                return
            self._last_camera_px = camera_x
        stride = max(8, getattr(config, 'FOREGROUND_CACHE_STRIDE', 64))
        bucket = int(camera_x // stride)
        key = (bucket, int(day_t * 50))  # quantize day_t
        cached = self._fg_cache.get(key)
        if cached is not None:
            self._fg_surface = cached
            surface.blit(cached, (0,0))
            return
        # Rebuild
        fg_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        baseline = getattr(config, 'BASELINE', surface.get_height() * 0.55)
        height_max = getattr(config, 'FOREGROUND_HEIGHT', 100)
        spacing = getattr(config, 'FOREGROUND_POINT_SPACING', 20)
        amplitude = getattr(config, 'FOREGROUND_AMPLITUDE', 30)
        parallax = getattr(config, 'FOREGROUND_PARALLAX', 0.8)
        base_col = getattr(config, 'FOREGROUND_BASE_COLOR', (20, 50, 30))
        variation = getattr(config, 'FOREGROUND_COLOR_VARIATION', 0.25)
        alpha = getattr(config, 'FOREGROUND_ALPHA', 180)
        grass_jitter = getattr(config, 'FOREGROUND_GRASS_JITTER', 0.3)
        blade_chance = getattr(config, 'FOREGROUND_GRASS_BLADE_CHANCE', 0.2)
        blade_boost = getattr(config, 'FOREGROUND_GRASS_COLOR_BOOST', 1.25)
        noise_scale = getattr(config, 'FOREGROUND_NOISE_SCALE', 0.5)
        w = surface.get_width()
        # Day-night color modulation (slightly brighter at day, cooler/darker at night)
        night_dim = 0.55
        brightness = night_dim + (1 - night_dim) * day_t
        layer_count = len(self.fg_layers)
        for idx, layer in enumerate(self.fg_layers):
            noise = layer['noise']
            rng = layer['rng']
            # Color progression: back layers lighter, front darker or vice versa? Choose front darkest for depth.
            depth_t = idx / max(1, layer_count - 1) if layer_count > 1 else 0
            dark_factor = 1 - variation * (1 - depth_t)
            r = int(base_col[0] * dark_factor * brightness)
            g = int(base_col[1] * dark_factor * brightness)
            b = int(base_col[2] * dark_factor * brightness)
            color = (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))
            local_cam = camera_x * parallax
            left_world = local_cam - 50
            right_world = local_cam + w + 50
            x = int(left_world // spacing * spacing)
            pts = []
            while x <= right_world:
                n = noise.fractal(x * noise_scale, octaves=3)
                y = baseline - n * amplitude - (height_max * 0.15)
                # vertical jitter for natural edge
                y -= rng.uniform(-height_max * grass_jitter, height_max * grass_jitter)
                sx = x - local_cam
                pts.append((sx, y))
                # Occasional blade tuft (small spike) by inserting an extra point
                if blade_chance > 0 and rng.random() < blade_chance:
                    # Clamp spike to softer range relative to lowered height_max
                    spike_h = rng.uniform(height_max * 0.08, height_max * 0.25)
                    pts.append((sx + spacing * 0.35, y - spike_h))
                x += spacing
            if len(pts) < 2:
                continue
            # Optional smoothing iterations to soften jagged spikes
            smooth_steps = max(0, getattr(config, 'FOREGROUND_SMOOTH_STEPS', 0))
            for _ in range(smooth_steps):
                new_pts = [pts[0]]
                for a, b in zip(pts, pts[1:]):
                    mx = (a[0] + b[0]) * 0.5
                    my = (a[1] + b[1]) * 0.5
                    new_pts.append((mx, my))
                    new_pts.append(b)
                pts = new_pts
            poly = pts.copy()
            poly.append((pts[-1][0], baseline + 12))
            poly.append((pts[0][0], baseline + 12))
            pygame.draw.polygon(fg_surf, (*color, alpha), poly, 0)
            # Gradient highlight along top crest (sample max y among pts)
            if getattr(config, 'FOREGROUND_TOP_GRADIENT_ALPHA', 0) > 0:
                grad_alpha = getattr(config, 'FOREGROUND_TOP_GRADIENT_ALPHA', 80)
                for i in range(len(pts) - 1):
                    p1 = pts[i]
                    p2 = pts[i + 1]
                    # Light line
                    pygame.draw.line(fg_surf, (int(color[0] * blade_boost), int(color[1] * blade_boost), int(color[2] * blade_boost), int(grad_alpha * 0.55)), p1, p2, 1)
        surface.blit(fg_surf, (0,0))
        self._fg_surface = fg_surf
        self._fg_cache[key] = fg_surf
