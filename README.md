# Terrastream

"A flowing horizon of generated hills."  
Terrastream is an infinite side-scrolling terrain prototype using procedural 1D gradient (Perlin-like) noise to create natural rolling hills on the fly. Built with Python and Pygame.

## Features (Current) *(v0.2.1)*
- Procedural terrain generated chunk-by-chunk (infinite scrolling)
- Multi-octave fractal gradient noise (deterministic via seed)
- Seam smoothing between chunks (slope-based blending of boundaries)
- Optional Catmull-Rom ridge smoothing with spike segmentation + vertical clamp
- Cached dual (day/night) gradient sky with per-row blend (fast day-night transition)
- Sky blend caching (quantized buckets) reduces per-frame line draws
- Dynamic day-night cycle (sky, terrain, parallax brightness)
- Sun & moon orbital arc with progressive night starfield fade-in
- Procedural starfield with power-law fade + subtle twinkle
- Layered parallax distant hills (noise-driven contours + atmospheric depth fade + optional vertical fade mask)
- Procedural multi-layer cloud system (cached ellipse blobs, scale, speed, density, day/night tint)
- Horizon fog / depth haze gradient (thicker at night) for added depth separation
- Biome-based terrain color bands with smooth modulation
- Slope-based ridge lighting (per-segment normal & biased sun direction) + highlight & subtle shadow
- Player entity (movement, jump, gravity, ground collision)
- External player sprite run cycle (with fallback capsule) & day/night tinting
- Anchored smoothing camera (configurable horizontal anchor fraction)
- Configurable terrain prefetch & pruning window (ahead/behind) with per-frame generation budget
- HUD overlay (FPS, distance traveled, seed)
- Foreground silhouette grass layers (noise-driven, cached, smoothed) for depth
- Atmospheric haze bands, lightning flashes, twilight fog warm tint, star twinkle
- Fireflies (night-only ambient wandering glow with flicker & lightning flash boost)
- Screenshot hotkey (F12) saves timestamped PNG to `screenshots/`

## Planned (Next Targets)
- Landing squash/stretch animation & jump/fall state sprites
- Collectibles / scoring prototype
- Performance auto-scaler (dynamic density / quality)
- Optional threaded terrain generation (`ASYNC_TERRAIN_THREAD` future)
- Additional weather FX (rain, drifting pollen, distant lightning variations)
- Ambient audio / subtle wind layer

## Stretch Ideas
- Underground caves when terrain dips below threshold
- Procedural structures / trees
- Saveable seeds & replays

## Getting Started
```
pip install -r requirements.txt
python main.py --seed 1337   # optional seed override
```

### Command Line Options
```
--seed <int>   Noise seed (deterministic world); defaults to value in config.py
```

## Controls
- Left / Right Arrows or A / D: Move horizontally
- Space / W / Up Arrow: Jump (when on ground)
- Esc: Quit
- F12: Screenshot (if `SCREENSHOT_ENABLED`)

## Configuration Highlights (`game/config.py`)
- Core terrain: `CHUNK_WIDTH`, `POINT_SPACING`, `NOISE_*`, `BASELINE`, `SEED`
- Streaming window: `PREFETCH_CHUNKS_AHEAD`, `PREFETCH_CHUNKS_BEHIND`, `MAX_CHUNKS_PER_FRAME`
- Negative world start: `ALLOW_NEGATIVE_CHUNKS`, `INITIAL_LEFT_CHUNKS`
- Smoothing: `TERRAIN_SMOOTHING_ENABLED`, `TERRAIN_SMOOTH_SUBDIVS`, `TERRAIN_SMOOTH_VERTICAL_CLAMP`
- Parallax: `PARALLAX_LAYERS`, `PARALLAX_POINT_SPACING`
- Camera: `CAMERA_ANCHOR_X`, `CAMERA_LERP`
- Day/Night: `DAY_NIGHT_ENABLED`, `DAY_NIGHT_DURATION`, `DAY_COLOR_*`, `NIGHT_COLOR_*`
- Terrain tinting: `TERRAIN_DAY_COLOR`, `TERRAIN_NIGHT_COLOR`
- Biomes: `BIOME_BAND_WIDTH`, `BIOME_COLOR_VARIANTS`
- Ridge & lighting: `RIDGE_HIGHLIGHT_COLOR`, `RIDGE_HIGHLIGHT_ALPHA`, `RIDGE_SHADOW_ALPHA`, `SLOPE_LIGHTING_ENABLED`, `SUN_NORMAL_BIAS`, `SUN_HIGHLIGHT_STRENGTH`
- Celestial / stars: `SUN_COLOR`, `MOON_COLOR`, `SUN_RADIUS`, `MOON_RADIUS`, `STAR_COUNT`, `STAR_MIN_ALPHA`, `STAR_MAX_ALPHA`, `STAR_NIGHT_POWER`
- Clouds: `CLOUD_ENABLED`, `CLOUD_LAYER_COUNT`, `CLOUD_COLOR`, `CLOUD_ALPHA`, `CLOUD_SCALE_RANGE`, `CLOUD_DENSITY`
- Celestial / stars: `SUN_COLOR`, `MOON_COLOR`, `SUN_RADIUS`, `MOON_RADIUS`, `STAR_COUNT`, `STAR_MIN_ALPHA`, `STAR_MAX_ALPHA`, `STAR_NIGHT_POWER`, `STAR_TWINKLE_SPEED`, `STAR_TWINKLE_AMPLITUDE`
- Clouds: `CLOUD_ENABLED`, `CLOUD_LAYER_COUNT`, `CLOUD_COLOR`, `CLOUD_ALPHA`, `CLOUD_SCALE_RANGE`, `CLOUD_DENSITY`, `CLOUD_TINT_DAY`, `CLOUD_TINT_NIGHT`
- Fog / depth haze: `FOG_ENABLED`, `FOG_ALPHA_TOP`, `FOG_ALPHA_BOTTOM`, `FOG_HEIGHT_FRACTION`, `FOG_COLOR`
- Parallax fade & caching: `PARALLAX_VERTICAL_FADE_ENABLED`, `PARALLAX_VERTICAL_FADE_POWER`, `SKY_BLEND_CACHE_STEPS`
- HUD: `HUD_ENABLED`
- Future placeholder: `ASYNC_TERRAIN_THREAD`

## Project Structure
```
project_root/
  main.py
  requirements.txt
  README.md
  game/
    __init__.py
    config.py
    loop.py
    terrain.py
    noise.py
    player.py
    background.py
  tests/
    test_noise.py
    test_terrain.py
    test_player.py
  pytest.ini
```

## Running Tests
```
pip install pytest
pytest -q
```

## Performance Notes
- Gradient background cached
- Ridge smoothing adds CPU cost; reduce `TERRAIN_SMOOTH_SUBDIVS` or disable if needed
- Parallax layers use sparse sampling (spacing configurable) to stay light
 - Prefetch keeps a large buffer of future chunks so reveal is instant; adjust `PREFETCH_CHUNKS_AHEAD` for memory vs. smoothness tradeoff.
- Fireflies: glow surfaces cached per brightness bucket; adjust `FIREFLY_BASE_COUNT` & `FIREFLY_GLOW_RADIUS` for performance.
- Screenshot overhead is negligible (single PNG encode) but avoid spamming F12 every frame.

## Version
Current package version: imported as:
```python
from game import __version__
print(__version__)
```

## License
MIT (you may adapt freely).
