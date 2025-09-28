from __future__ import annotations
import pygame
import math
from . import config

class Player:
    def __init__(self, terrain):
        # World position references the player's feet (x, y at ground contact)
        self.x = 0.0
        self.y = config.BASELINE
        self.vx = 0.0
        self.vy = 0.0
        self.terrain = terrain
        self.on_ground = False
        # Particles
        self.particles = []  # list of dicts
        self._was_on_ground = False
        # Cached visuals
        self._body_cache = None
        self._shadow_cache = None
        self._last_size_key = None
        # Sprite sheet animation assets
        self.sprite_frames = []  # list of pygame.Surface
        self.sprite_loaded = False
        self.anim_time = 0.0
        self.facing = 1  # 1 right, -1 left
        if getattr(config, 'PLAYER_SPRITES_ENABLED', False):
            self._load_spritesheet()

    @property
    def width(self):
        return config.PLAYER_WIDTH

    @property
    def height(self):
        return config.PLAYER_HEIGHT

    def handle_input(self):
        keys = pygame.key.get_pressed()
        move = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            move -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            move += 1
        self.vx = move * config.PLAYER_MOVE_SPEED
        if (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]) and self.on_ground:
            self.vy = config.PLAYER_JUMP_VELOCITY
            self.on_ground = False
            if getattr(config, 'JUMP_DUST_ENABLED', False):
                self._spawn_dust_burst()

    def physics(self, dt: float):
        # Apply gravity
        self.vy += config.GRAVITY * dt
        # Integrate
        self.x += self.vx * dt
        self.y += self.vy * dt
        # Ground collision using terrain height at player's x
        ground_y = self.terrain.sample_height(self.x)
        if self.y > ground_y:
            self.y = ground_y
            self.vy = 0.0
            self.on_ground = True
        else:
            self.on_ground = False

    def update(self, dt: float):
        self.handle_input()
        self.physics(dt)
        self._update_particles(dt)
        self._was_on_ground = self.on_ground
        # Track facing based on last non-zero vx
        if self.vx < -1e-3:
            self.facing = -1
        elif self.vx > 1e-3:
            self.facing = 1
        # Advance animation clock if sprites active
        if self.sprite_loaded:
            self.anim_time += dt

    # --- Sprite sheet handling ---
    def _load_spritesheet(self):
        """Load external player spritesheet and slice frames using JSON meta.

        Expected JSON (TexturePacker style) with structure:
        {
            "frames": {"FrameName.png": {"frame": {"x":...,"y":...,"w":...,"h":...}, ...}},
            "meta": {"image": "spritesheet.png", ...}
        }
        Only the frame rects are used; frame order determined by sorted frame names.
        """
        import os, json
        try:
            meta_path = getattr(config, 'PLAYER_SPRITESHEET_META', '')
            sheet_path = getattr(config, 'PLAYER_SPRITESHEET_PATH', '')
            if not meta_path or not sheet_path:
                return
            if not (os.path.exists(meta_path) and os.path.exists(sheet_path)):
                return
            with open(meta_path, 'r') as f:
                data = json.load(f)
            sheet_image = pygame.image.load(sheet_path).convert_alpha()
            frames_dict = data.get('frames', {})
            # Sort frame names to establish deterministic order (e.g., RunRight01, 02, ...)
            for name in sorted(frames_dict.keys()):
                frame_info = frames_dict[name]
                fr = frame_info.get('frame') or {}
                x = fr.get('x', 0)
                y = fr.get('y', 0)
                w = fr.get('w', 0)
                h = fr.get('h', 0)
                if w <= 0 or h <= 0:
                    continue
                sub = pygame.Surface((w, h), pygame.SRCALPHA)
                sub.blit(sheet_image, (0,0), pygame.Rect(x, y, w, h))
                self.sprite_frames.append(sub)
            if self.sprite_frames:
                self.sprite_loaded = True
        except Exception:
            # Silently fail; fallback to capsule
            self.sprite_frames = []
            self.sprite_loaded = False

    # Particle system helpers
    def _spawn_dust_burst(self):
        import random
        rng = random.Random()
        count = getattr(config, 'DUST_PARTICLE_COUNT', 8)
        size_min, size_max = getattr(config, 'DUST_PARTICLE_SIZE_RANGE', (4, 10))
        life = getattr(config, 'DUST_PARTICLE_LIFETIME', 0.5)
        base_col = getattr(config, 'DUST_PARTICLE_COLOR', (230, 225, 215))
        for _ in range(count):
            ang = rng.uniform(-math.pi * 0.9, -math.pi * 0.1)
            speed = rng.uniform(60, 180)
            vx = math.cos(ang) * speed
            vy = math.sin(ang) * speed * 0.6
            size = rng.uniform(size_min, size_max)
            self.particles.append({
                'x': self.x + rng.uniform(-self.width * 0.3, self.width * 0.3),
                'y': self.y - 4,
                'vx': vx,
                'vy': vy,
                'life': life,
                'age': 0.0,
                'size': size,
                'color': base_col,
            })

    def _update_particles(self, dt: float):
        if not self.particles:
            return
        gravity = getattr(config, 'GRAVITY', 1500) * 0.25
        for p in self.particles:
            p['age'] += dt
            t = p['age'] / p['life'] if p['life'] > 0 else 1
            p['x'] += p['vx'] * dt
            p['y'] += p['vy'] * dt
            p['vy'] += gravity * dt * 0.2  # light gravity
            # Slight horizontal drag
            p['vx'] *= (1 - 1.4 * dt)
            # Expand slightly
            p['size'] *= (1 + 0.4 * dt)
        # Cull dead
        self.particles = [p for p in self.particles if p['age'] < p['life']]

    def draw(self, surface: pygame.Surface, camera_x: float, day_t: float | None = None):
        screen_x = self.x - camera_x - self.width / 2
        screen_y = self.y - self.height
        # Prefer sprite rendering if enabled & loaded
        if self.sprite_loaded and getattr(config, 'PLAYER_SPRITES_ENABLED', False):
            # Determine animation state (simple: idle vs run). Later can add jump/fall.
            speed = abs(self.vx)
            run_thresh = config.PLAYER_MOVE_SPEED * 0.15
            if speed > run_thresh and self.on_ground:
                # Run cycle
                fps = getattr(config, 'PLAYER_ANIM_FPS', 10)
                frame_count = len(self.sprite_frames)
                if frame_count > 0:
                    idx = int(self.anim_time * fps) % frame_count
                else:
                    idx = 0
            else:
                # Idle: pick first frame
                idx = 0
            frame = self.sprite_frames[idx]
            draw_frame = frame
            if self.facing < 0:
                draw_frame = pygame.transform.flip(frame, True, False)
            # Scale sprite to configured player dimensions (maintain aspect ratio based on height)
            target_h = int(self.height)
            scale = target_h / draw_frame.get_height()
            target_w = max(1, int(draw_frame.get_width() * scale))
            if draw_frame.get_height() != target_h:
                draw_frame = pygame.transform.smoothscale(draw_frame, (target_w, target_h))
            # Shadow (reuse capsule logic if cache exists, else build lightweight ellipse)
            if not self._shadow_cache:
                alpha = getattr(config, 'PLAYER_SHADOW_ALPHA', 70)
                shadow_w = int(self.width * 1.2)
                shadow_h = int(self.height * 0.28)
                shadow = pygame.Surface((shadow_w, shadow_h), pygame.SRCALPHA)
                rw = shadow_w / 2
                rh = shadow_h / 2
                for yy in range(shadow_h):
                    for xx in range(shadow_w):
                        nx = (xx - rw) / rw
                        ny = (yy - rh) / rh
                        d = nx * nx + ny * ny
                        if d <= 1.0:
                            a = int(alpha * (1 - d) ** 1.5)
                            shadow.set_at((xx, yy), (0,0,0,a))
                self._shadow_cache = shadow
            # Draw shadow first
            if self._shadow_cache:
                shadow_x = self.x - camera_x - self._shadow_cache.get_width() / 2
                shadow_y = self.y - self._shadow_cache.get_height() * 0.45
                surface.blit(self._shadow_cache, (shadow_x, shadow_y))
            # Draw sprite frame
            sprite_x = self.x - camera_x - target_w / 2
            sprite_y = self.y - target_h
            # Apply optional day-night tint
            if getattr(config, 'PLAYER_TINT_ENABLED', False) and day_t is not None:
                draw_frame = self._apply_day_tint(draw_frame, day_t)
            surface.blit(draw_frame, (int(sprite_x), int(sprite_y)))
        elif getattr(config, 'PLAYER_CAPSULE_ENABLED', True):
            size_key = (self.width, self.height, config.COLOR_PLAYER)
            if size_key != self._last_size_key or self._body_cache is None:
                self._last_size_key = size_key
                w = int(self.width)
                h = int(self.height)
                body = pygame.Surface((w, h), pygame.SRCALPHA)
                # Base skin tone (derive from config color but ensure warm tone)
                base = config.COLOR_PLAYER
                top_col = (min(255, int(base[0] * 1.1)), min(255, int(base[1] * 1.05)), min(255, int(base[2] * 0.95)))
                bot_col = (int(base[0] * 0.75), int(base[1] * 0.7), int(base[2] * 0.65))
                for yy in range(h):
                    t = yy / (h - 1)
                    r = int(top_col[0] * (1 - t) + bot_col[0] * t)
                    g = int(top_col[1] * (1 - t) + bot_col[1] * t)
                    b = int(top_col[2] * (1 - t) + bot_col[2] * t)
                    pygame.draw.line(body, (r, g, b), (0, yy), (w, yy))
                radius = min(int(w / 2), int(h / 2))
                # Mask corners to create capsule using alpha circle cuts
                mask = pygame.Surface((w, h), pygame.SRCALPHA)
                pygame.draw.rect(mask, (255, 255, 255, 255), (0, radius, w, h - 2 * radius))
                pygame.draw.circle(mask, (255, 255, 255, 255), (radius, radius), radius)
                pygame.draw.circle(mask, (255, 255, 255, 255), (w - radius, radius), radius)
                pygame.draw.circle(mask, (255, 255, 255, 255), (radius, h - radius), radius)
                pygame.draw.circle(mask, (255, 255, 255, 255), (w - radius, h - radius), radius)
                body.blit(mask, (0,0), special_flags=pygame.BLEND_RGBA_MULT)
                # Outline
                outline = pygame.Surface((w, h), pygame.SRCALPHA)
                pygame.draw.rect(outline, (0,0,0,130), (0,0,w,h), border_radius=radius)
                body.blit(outline, (0,0), special_flags=pygame.BLEND_RGBA_MIN)
                # Simple highlight ellipse near top-left
                hl = pygame.Surface((w, h), pygame.SRCALPHA)
                pygame.draw.ellipse(hl, (255,255,255,60), (w*0.25, h*0.15, w*0.5, h*0.35))
                body.blit(hl, (0,0), special_flags=pygame.BLEND_RGBA_ADD)
                # Face (eyes + mouth)
                if getattr(config, 'PLAYER_FACE_ENABLED', True):
                    face = pygame.Surface((w, h), pygame.SRCALPHA)
                    eye_col = getattr(config, 'PLAYER_EYE_COLOR', (30,30,35))
                    eye_high = getattr(config, 'PLAYER_EYE_HIGHLIGHT', (255,255,255))
                    mouth_col = getattr(config, 'PLAYER_MOUTH_COLOR', (60,40,40))
                    eye_r = max(2, w//9)
                    eye_y = int(h*0.38)
                    eye_offset_x = int(w*0.22)
                    cx = w//2
                    # Eyes
                    pygame.draw.circle(face, eye_col, (cx - eye_offset_x, eye_y), eye_r)
                    pygame.draw.circle(face, eye_col, (cx + eye_offset_x, eye_y), eye_r)
                    # Eye highlights
                    pygame.draw.circle(face, eye_high, (cx - eye_offset_x - eye_r//2 +1, eye_y - eye_r//2), max(1, eye_r//3))
                    pygame.draw.circle(face, eye_high, (cx + eye_offset_x - eye_r//2 +1, eye_y - eye_r//2), max(1, eye_r//3))
                    # Mouth (simple arc / line)
                    mouth_w = int(w*0.32)
                    mouth_y = int(h*0.60)
                    mouth_rect = pygame.Rect(cx - mouth_w//2, mouth_y, mouth_w, eye_r*2)
                    pygame.draw.arc(face, mouth_col, mouth_rect, math.pi*0.1, math.pi*0.9, 2)
                    body.blit(face, (0,0))
                self._body_cache = body
                # Shadow cache
                alpha = getattr(config, 'PLAYER_SHADOW_ALPHA', 70)
                shadow_w = int(self.width * 1.2)
                shadow_h = int(self.height * 0.28)
                shadow = pygame.Surface((shadow_w, shadow_h), pygame.SRCALPHA)
                rw = shadow_w / 2
                rh = shadow_h / 2
                for yy in range(shadow_h):
                    for xx in range(shadow_w):
                        nx = (xx - rw) / rw
                        ny = (yy - rh) / rh
                        d = nx * nx + ny * ny
                        if d <= 1.0:
                            a = int(alpha * (1 - d) ** 1.5)
                            shadow.set_at((xx, yy), (0,0,0,a))
                self._shadow_cache = shadow
            frame_to_draw = self._body_cache
            if getattr(config, 'PLAYER_TINT_ENABLED', False) and day_t is not None:
                frame_to_draw = self._apply_day_tint(self._body_cache, day_t)
            surface.blit(frame_to_draw, (int(screen_x), int(screen_y)))
            if self._shadow_cache:
                shadow_x = self.x - camera_x - self._shadow_cache.get_width() / 2
                shadow_y = self.y - self._shadow_cache.get_height() * 0.45
                surface.blit(self._shadow_cache, (shadow_x, shadow_y))
        else:
            pygame.draw.rect(surface, config.COLOR_PLAYER, pygame.Rect(screen_x, screen_y, self.width, self.height))
        # Draw particles after player so they appear in front of shadow but behind future effects
        if self.particles:
            for p in self.particles:
                t = p['age'] / p['life'] if p['life'] > 0 else 1
                fade = max(0.0, 1 - t)
                a = int(255 * (fade ** 1.5))
                r, g, b = p['color']
                size = max(1, int(p['size']))
                surf = pygame.Surface((size, size), pygame.SRCALPHA)
                pygame.draw.circle(surf, (r, g, b, a), (size // 2, size // 2), size // 2)
                surface.blit(surf, (p['x'] - camera_x - size / 2, p['y'] - size / 2))

    def _apply_day_tint(self, frame: pygame.Surface, day_t: float) -> pygame.Surface:
        """Return a tinted copy of the frame according to day-night cycle.

        day_t: 0 night -> 1 day
        - Warm tint near dawn/dusk edges (within PLAYER_TINT_DAWN_SPAN)
        - Cool tint at deep night (scaled by PLAYER_TINT_NIGHT_STRENGTH)
        - Neutral at midday.
        """
        span = getattr(config, 'PLAYER_TINT_DAWN_SPAN', 0.1)
        warm_col = getattr(config, 'PLAYER_TINT_WARM', (255, 210, 160))
        cool_col = getattr(config, 'PLAYER_TINT_COOL', (160, 190, 255))
        day_col = getattr(config, 'PLAYER_TINT_DAY', (255, 255, 255))
        night_strength = getattr(config, 'PLAYER_TINT_NIGHT_STRENGTH', 0.5)
        # Determine blend target color multiplier
        edge_t = min(day_t, 1 - day_t)
        if edge_t < span:
            k = 1 - (edge_t / span)  # 1 at exact dawn/dusk, 0 away
            target = (
                int(day_col[0] * (1 - k) + warm_col[0] * k),
                int(day_col[1] * (1 - k) + warm_col[1] * k),
                int(day_col[2] * (1 - k) + warm_col[2] * k),
            )
        else:
            # Either broad day or night; night_t factor
            night_t = 1 - day_t
            k = max(0.0, night_t) * night_strength
            target = (
                int(day_col[0] * (1 - k) + cool_col[0] * k),
                int(day_col[1] * (1 - k) + cool_col[1] * k),
                int(day_col[2] * (1 - k) + cool_col[2] * k),
            )
        # Multiply original frame by target color normalized to 255
        r_mul = target[0] / 255.0
        g_mul = target[1] / 255.0
        b_mul = target[2] / 255.0
        tinted = frame.copy()
        # Fast per-pixel multiply via BLEND_RGBA_MULT using a solid surface
        mul = pygame.Surface(frame.get_size(), pygame.SRCALPHA)
        mul.fill((int(255 * r_mul), int(255 * g_mul), int(255 * b_mul), 255))
        tinted.blit(mul, (0,0), special_flags=pygame.BLEND_RGBA_MULT)
        return tinted
