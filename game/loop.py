import pygame
from . import config
from .terrain import TerrainManager
from .player import Player
from .background import ParallaxBackground
import math

class Game:
    def __init__(self, seed: int | None = None):
        pygame.init()
        self.screen = pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
        pygame.display.set_caption(config.GAME_TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.time = 0.0
        self.camera_x = 0.0
        self.seed = seed if seed is not None else config.SEED
        self.terrain = TerrainManager(seed=self.seed)
        self.player = Player(self.terrain)
        self.parallax = ParallaxBackground(self.seed)
        self.camera_bob_offset = 0.0
        self._bob_phase = 0.0
        # Gradient surfaces for day and night; we blend each frame
        self._bg_day = self._build_gradient(getattr(config, 'DAY_COLOR_TOP', config.COLOR_BG_TOP),
                                            getattr(config, 'DAY_COLOR_BOTTOM', config.COLOR_BG_BOTTOM))
        self._bg_night = self._build_gradient(getattr(config, 'NIGHT_COLOR_TOP', config.COLOR_BG_TOP),
                                              getattr(config, 'NIGHT_COLOR_BOTTOM', config.COLOR_BG_BOTTOM))
        self._bg_surface = pygame.Surface((config.WINDOW_WIDTH, config.WINDOW_HEIGHT)).convert()
        # Precompute per-row color tuples for faster blending
        self._bg_day_rows = [self._bg_day.get_at((0, y)) for y in range(config.WINDOW_HEIGHT)]
        self._bg_night_rows = [self._bg_night.get_at((0, y)) for y in range(config.WINDOW_HEIGHT)]
        # Sky blend caching
        self._sky_cache = {}
        self._sky_last_bucket = None
        # Stars (static positions + twinkle phase/speed)
        import random
        self._stars = []
        if hasattr(config, 'STAR_COUNT'):
            rng = random.Random(self.seed * 9991)
            for _ in range(config.STAR_COUNT):
                x = rng.randint(0, config.WINDOW_WIDTH - 1)
                y = rng.randint(0, int(config.WINDOW_HEIGHT * 0.6))
                a = rng.randint(getattr(config, 'STAR_MIN_ALPHA', 40), getattr(config, 'STAR_MAX_ALPHA', 160))
                phase = rng.random() * math.tau
                speed = 0.6 + rng.random() * 0.8
                self._stars.append((x, y, a, phase, speed))
        self.font = pygame.font.SysFont("consolas", 16)
        # Pre-generate initial left-side terrain if enabled
        if config.ALLOW_NEGATIVE_CHUNKS and getattr(config, "INITIAL_LEFT_CHUNKS", 0) > 0:
            for neg in range(1, config.INITIAL_LEFT_CHUNKS + 1):
                self.terrain.generate_chunk(-neg)
        # Lightning state
        self._lightning_time = 0.0
        self._next_lightning = self._schedule_lightning()
        self._active_flash = 0.0  # time remaining of current flash
        self._bolt_points = []
        # Sun glow cache
        self._sun_glow_cache = {}

    def _schedule_lightning(self):
        import random
        return random.uniform(getattr(config, 'LIGHTNING_MIN_INTERVAL', 16.0),
                              getattr(config, 'LIGHTNING_MAX_INTERVAL', 32.0))

    def _spawn_lightning(self):
        # Build a jagged bolt path from top to horizon/fog baseline
        import random
        if not getattr(config, 'LIGHTNING_ENABLED', False):
            return
        # Only at night (after day factor threshold)
        if self._day_night_factor() > 0.35:
            return
        w = config.WINDOW_WIDTH
        h = config.WINDOW_HEIGHT
        base_y = h * getattr(config, 'FOG_HEIGHT_FRACTION', 0.55)
        x = random.randint(int(self.camera_x) - 200, int(self.camera_x) + w + 200)
        segs = random.randint(6, 10)
        points = []
        cur_y = 0
        cur_x = x
        lateral_span = 140
        for i in range(segs):
            ny = cur_y + (base_y / segs) * (0.8 + random.random() * 0.4)
            nx = cur_x + random.uniform(-lateral_span, lateral_span)
            points.append((nx, ny))
            cur_x, cur_y = nx, ny
            lateral_span *= 0.6
        self._bolt_points = points
        self._active_flash = getattr(config, 'LIGHTNING_FLASH_DURATION', 0.35)
        self._lightning_time = 0.0
        self._next_lightning = self._schedule_lightning()

    def _build_gradient(self, top, bottom) -> pygame.Surface:
        surf = pygame.Surface((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
        h = config.WINDOW_HEIGHT
        # Draw vertical gradient once
        for y in range(h):
            t = y / h
            r = int(top[0] * (1 - t) + bottom[0] * t)
            g = int(top[1] * (1 - t) + bottom[1] * t)
            b = int(top[2] * (1 - t) + bottom[2] * t)
            # Single line fill
            pygame.draw.line(surf, (r, g, b), (0, y), (config.WINDOW_WIDTH, y))
        return surf.convert()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.running = False

    def update_camera(self, dt: float):
        # Desired camera keeps player at anchor fraction of screen width
        anchor_px = config.WINDOW_WIDTH * config.CAMERA_ANCHOR_X
        desired = self.player.x - anchor_px
        self.camera_x += (desired - self.camera_x) * config.CAMERA_LERP

    def update(self, dt):
        self.time += dt
        self.player.update(dt)
        self.update_camera(dt)
        # Lightning timing
        if getattr(config, 'LIGHTNING_ENABLED', False):
            self._lightning_time += dt
            if self._lightning_time >= self._next_lightning:
                self._spawn_lightning()
            if self._active_flash > 0:
                self._active_flash -= dt
        # Camera bob (visual only)
        if getattr(config, 'CAMERA_BOB_ENABLED', False):
            speed = abs(self.player.vx)
            norm = min(1.0, speed / max(1.0, config.PLAYER_MOVE_SPEED))
            self._bob_phase += dt * getattr(config, 'CAMERA_BOB_SPEED', 1.2) * (0.3 + 0.7 * norm)
            amp = getattr(config, 'CAMERA_BOB_AMPLITUDE', 6.0) * norm
            self.camera_bob_offset = math.sin(self._bob_phase * math.tau) * amp
        else:
            self.camera_bob_offset = 0.0

    def _day_night_factor(self) -> float:
        if not getattr(config, 'DAY_NIGHT_ENABLED', False):
            return 0.0
        period = getattr(config, 'DAY_NIGHT_DURATION', 60.0)
        phase = (self.time / period) * math.tau  # 0..2pi
        # sin gives -1..1; map to 0..1 (0 = night, 1 = day) or invert? choose (sin+1)/2
        return (math.sin(phase) + 1.0) * 0.5

    def draw_background(self):
        t = self._day_night_factor()
        # Sky blend caching with quantization
        steps = max(1, getattr(config, 'SKY_BLEND_CACHE_STEPS', 240))
        bucket = int(t * (steps - 1))
        if bucket != self._sky_last_bucket:
            day_rows = self._bg_day_rows
            night_rows = self._bg_night_rows
            draw_line = pygame.draw.line
            w = config.WINDOW_WIDTH
            for y in range(config.WINDOW_HEIGHT):
                d = day_rows[y]
                n = night_rows[y]
                r = (n.r * (1 - t) + d.r * t)
                g = (n.g * (1 - t) + d.g * t)
                b = (n.b * (1 - t) + d.b * t)
                draw_line(self._bg_surface, (int(r), int(g), int(b)), (0, y), (w, y))
            self._sky_cache[bucket] = self._bg_surface.copy()
            self._sky_last_bucket = bucket
        else:
            cached = self._sky_cache.get(bucket)
            if cached:
                self._bg_surface.blit(cached, (0, 0))
        self.screen.blit(self._bg_surface, (0, 0))
        # (God rays removed due to visual artifacts and performance impact. Keeping code out for clarity.)
        # Stars (fade in at night)
        if self._stars:
            night_factor = 1.0 - t  # 1 at night
            power = getattr(config, 'STAR_NIGHT_POWER', 1.5)
            nf = night_factor ** power
            star_color = getattr(config, 'STAR_COLOR', (240, 240, 255))
            tw_amp = getattr(config, 'STAR_TWINKLE_AMPLITUDE', 0.3)
            tw_speed = getattr(config, 'STAR_TWINKLE_SPEED', 0.4)
            for x, y, base_a, phase, speed in self._stars:
                # Twinkle factor (0..1)
                tw = (math.sin(phase + self.time * speed * tw_speed) + 1) * 0.5
                a = int(base_a * nf * (1.0 + tw_amp * (tw - 0.5)))
                if a <= 2:
                    continue
                star_surf = pygame.Surface((2, 2), pygame.SRCALPHA)
                star_surf.fill((*star_color, a))
                self.screen.blit(star_surf, (x, y))
        # Sun & Moon positions (on a simple arc)
        cx = config.WINDOW_WIDTH * 0.5
        cy = config.WINDOW_HEIGHT * 0.15
        arc_radius = config.WINDOW_HEIGHT * 0.55
        angle = (t) * math.pi  # 0..pi across sky for sun
        sun_x = cx + math.cos(angle - math.pi) * arc_radius
        sun_y = cy + math.sin(angle - math.pi) * arc_radius * 0.35
        moon_angle = angle + math.pi
        moon_x = cx + math.cos(moon_angle - math.pi) * arc_radius
        moon_y = cy + math.sin(moon_angle - math.pi) * arc_radius * 0.35
        # Radial sun glow (cheap, cached by radius & day factor bucket)
        if hasattr(config, 'SUN_RADIUS') and getattr(config, 'SUN_GLOW_ENABLED', True):
            glow_scale = getattr(config, 'SUN_GLOW_SCALE', 1.8)
            max_alpha = getattr(config, 'SUN_GLOW_MAX_ALPHA', 65)
            glow_outer = int(config.SUN_RADIUS * glow_scale)
            # Quantize brightness to reduce cache size
            glow_steps = 48
            sun_brightness = int(t * (glow_steps - 1))
            key = (glow_outer, sun_brightness)
            glow = self._sun_glow_cache.get(key)
            if glow is None:
                glow = pygame.Surface((glow_outer * 2, glow_outer * 2), pygame.SRCALPHA)
                center = glow_outer
                # Base color slightly warm
                base_col = getattr(config, 'SUN_COLOR', (255, 245, 200))
                for r in range(glow_outer, 0, -1):
                    k = r / glow_outer
                    # Outer falloff steeper for edge softness
                    a = int(max_alpha * (k ** 1.9) * (0.55 + 0.45 * t))
                    if a <= 0:
                        continue
                    pygame.draw.circle(glow, (*base_col, a), (center, center), r)
                self._sun_glow_cache[key] = glow
            self.screen.blit(glow, (sun_x - glow.get_width() / 2, sun_y - glow.get_height() / 2), special_flags=pygame.BLEND_PREMULTIPLIED)
        if hasattr(config, 'SUN_RADIUS'):
            pygame.draw.circle(self.screen, config.SUN_COLOR, (int(sun_x), int(sun_y)), config.SUN_RADIUS)
        if hasattr(config, 'MOON_RADIUS'):
            night_alpha = int(255 * (1 - t))
            if night_alpha > 5:
                moon_surface = pygame.Surface((config.MOON_RADIUS * 2, config.MOON_RADIUS * 2), pygame.SRCALPHA)
                pygame.draw.circle(moon_surface, (*config.MOON_COLOR, night_alpha), (config.MOON_RADIUS, config.MOON_RADIUS), config.MOON_RADIUS)
                self.screen.blit(moon_surface, (moon_x - config.MOON_RADIUS, moon_y - config.MOON_RADIUS))
        self.parallax.draw(self.screen, self.camera_x, t)
        # Lightning bolt & flash overlay (after parallax, before terrain to illuminate ridge edges; simple approach)
        if self._active_flash > 0 and self._bolt_points:
            fade = max(0.0, self._active_flash / getattr(config, 'LIGHTNING_FLASH_DURATION', 0.35))
            alpha = int(getattr(config, 'LIGHTNING_FLASH_ALPHA', 120) * (fade ** 0.6))
            # Bolt path in screen space
            bolt_color = (255, 255, 255)
            # Draw on temp surface for alpha
            bolt_surf = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
            last = None
            cam = self.camera_x
            for pt in self._bolt_points:
                sx = pt[0] - cam
                sy = pt[1]
                if last is not None:
                    pygame.draw.line(bolt_surf, (*bolt_color, alpha), last, (sx, sy), 2)
                last = (sx, sy)
            # Global flash overlay (tinted slightly blue-white)
            flash = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
            flash.fill((210, 230, 255, int(alpha * 0.55)))
            self.screen.blit(bolt_surf, (0, 0))
            self.screen.blit(flash, (0, 0))

    def draw_hud(self):
        if not config.HUD_ENABLED:
            return
        fps = self.clock.get_fps()
        dist = int(self.player.x)
        lines = [
            f"FPS: {fps:5.1f}",
            f"Dist: {dist}",
            f"Seed: {self.seed}",
        ]
        x = 10
        y = 8
        for line in lines:
            surf = self.font.render(line, True, config.COLOR_HUD)
            self.screen.blit(surf, (x, y))
            y += surf.get_height() + 2

    def draw(self):
        self.draw_background()
        # Draw terrain
        # Apply bob via a temporary surface if offset non-zero
        if self.camera_bob_offset != 0.0:
            temp = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
            day_t = self._day_night_factor()
            self.terrain.draw(temp, self.camera_x, day_t)
            if hasattr(self.parallax, 'draw_foreground'):
                self.parallax.draw_foreground(temp, self.camera_x, day_t)
            self.player.draw(temp, self.camera_x, day_t)
            self.screen.blit(temp, (0, self.camera_bob_offset))
        else:
            day_t = self._day_night_factor()
            self.terrain.draw(self.screen, self.camera_x, day_t)
            if hasattr(self.parallax, 'draw_foreground'):
                self.parallax.draw_foreground(self.screen, self.camera_x, day_t)
            self.player.draw(self.screen, self.camera_x, day_t)
        self.draw_hud()
        pygame.display.flip()

    def run(self):
        import os
        max_frames = None
        if os.environ.get('SMOKE_TEST_FRAMES'):
            try:
                max_frames = int(os.environ['SMOKE_TEST_FRAMES'])
            except ValueError:
                max_frames = 120
        frame = 0
        while self.running:
            dt = self.clock.tick(config.FPS) / 1000.0
            self.handle_events()
            self.update(dt)
            self.draw()
            if max_frames is not None:
                frame += 1
                if frame >= max_frames:
                    self.running = False
        pygame.quit()
