WINDOW_WIDTH = 960
WINDOW_HEIGHT = 540
FPS = 60

# Game meta
GAME_TITLE = "Terrastream"

# Terrain generation
CHUNK_WIDTH = 256            # pixels per chunk
POINT_SPACING = 16            # distance between sampled noise points
NOISE_OCTAVES = 4
NOISE_SCALE = 0.005           # base frequency scale
NOISE_AMPLITUDE = 140         # vertical scale of terrain
BASELINE = WINDOW_HEIGHT * 0.55  # base y level around which hills vary
SEED = 1337
ALLOW_NEGATIVE_CHUNKS = True   # allow terrain generation to the left of x=0
INITIAL_LEFT_CHUNKS = 3        # how many negative chunks to guarantee at start (if allowed)
PREFETCH_CHUNKS_AHEAD = 12     # how many chunks beyond right edge of screen to keep generated
PREFETCH_CHUNKS_BEHIND = 2     # how many chunks behind camera to retain (>=1 for safety)
ASYNC_TERRAIN_THREAD = False   # future option: generate terrain in background thread
MAX_CHUNKS_PER_FRAME = 3       # cap synchronous chunk generations per frame to avoid spikes

# Terrain smoothing (Catmull-Rom on ridge)
TERRAIN_SMOOTHING_ENABLED = True
TERRAIN_SMOOTH_SUBDIVS = 4   # extra points between source samples (>=1)
TERRAIN_SMOOTH_MIN_POINTS = 8  # minimum raw points before smoothing
TERRAIN_SMOOTH_VERTICAL_CLAMP = 220  # max vertical deviation from original sample envelope

# Player
PLAYER_MOVE_SPEED = 240       # pixels / second
PLAYER_JUMP_VELOCITY = -520
GRAVITY = 1500
PLAYER_WIDTH = 32
PLAYER_HEIGHT = 48

# Camera
CAMERA_LERP = 0.15
CAMERA_ANCHOR_X = 0.75  # fraction of screen width where player is kept horizontally

# Parallax layers
PARALLAX_LAYERS = [
    {"scale": 0.25, "amplitude": 40, "color": (35, 80, 50), "speed_factor": 0.3},
    {"scale": 0.12, "amplitude": 25, "color": (25, 60, 40), "speed_factor": 0.15},
]
PARALLAX_POINT_SPACING = 48

# Foreground silhouettes (close decorative grass/foliage bands for depth)
FOREGROUND_SILHOUETTES_ENABLED = True
FOREGROUND_LAYER_COUNT = 2            # number of silhouette bands
FOREGROUND_BASE_COLOR = (15, 40, 25)  # darkest layer base color
FOREGROUND_COLOR_VARIATION = 0.22     # lighten factor progression front->back
FOREGROUND_NOISE_SCALE = 0.55         # horizontal frequency (higher = more detail)
FOREGROUND_AMPLITUDE = 18             # vertical amplitude of noise contour (lower = calmer)
FOREGROUND_POINT_SPACING = 22         # horizontal spacing between generated points (slightly wider = fewer points)
FOREGROUND_HEIGHT = 70                # max vertical height of silhouettes above terrain baseline (lowered)
FOREGROUND_PARALLAX = 0.75            # movement factor relative to camera ( <1 slower than terrain )
FOREGROUND_ALPHA = 185                # overall alpha (0-255)
FOREGROUND_GRASS_JITTER = 0.22        # per-point vertical jitter fraction (reduced jitter)
FOREGROUND_GRASS_BLADE_CHANCE = 0.12  # probability per segment to add a blade tuft (fewer spikes)
FOREGROUND_GRASS_COLOR_BOOST = 1.35   # saturation/light boost for blade tips
FOREGROUND_SMOOTH_STEPS = 1           # fewer smoothing subdivision passes
FOREGROUND_CACHE_STRIDE = 48          # pixels per cache bucket for silhouettes
FOREGROUND_TOP_GRADIENT_ALPHA = 95    # max extra highlight alpha at crest
FOREGROUND_MAX_FPS_IMPACT = True      # if True, skip redraw when camera moved < 1 px within frame
FOREGROUND_ALPHA = 165                # (override earlier) final fill alpha; slightly lower for subtlety

# HUD
HUD_ENABLED = True

# Colors
COLOR_BG_TOP = (20, 30, 55)
COLOR_BG_BOTTOM = (40, 65, 100)
COLOR_TERRAIN = (60, 150, 80)
COLOR_TERRAIN_EDGE = (30, 90, 45)
COLOR_PLAYER = (250, 240, 230)
COLOR_HUD = (235, 235, 235)

# Day/Night cycle & biomes
DAY_NIGHT_ENABLED = True
DAY_NIGHT_DURATION = 60.0   # seconds for full cycle day->night->day (one period of sin based blend)
DAY_COLOR_TOP = (90, 150, 210)
DAY_COLOR_BOTTOM = (170, 200, 240)
NIGHT_COLOR_TOP = (10, 15, 30)
NIGHT_COLOR_BOTTOM = (25, 35, 60)
TERRAIN_DAY_COLOR = (60, 150, 80)
TERRAIN_NIGHT_COLOR = (30, 90, 70)
RIDGE_HIGHLIGHT_COLOR = (180, 225, 170)
RIDGE_HIGHLIGHT_ALPHA = 110
RIDGE_SHADOW_ALPHA = 70
BIOME_BAND_WIDTH = 8 * CHUNK_WIDTH  # distance over which biome color shifts
BIOME_COLOR_VARIANTS = [
    (60, 150, 80),
    (75, 155, 90),
    (55, 140, 95),
    (70, 160, 70),
]

# Advanced sky & atmosphere
SUN_COLOR = (255, 245, 200)
MOON_COLOR = (200, 220, 255)
SUN_RADIUS = 36
MOON_RADIUS = 28
STAR_COUNT = 140
STAR_COLOR = (240, 240, 255)
STAR_MIN_ALPHA = 30
STAR_MAX_ALPHA = 180
STAR_NIGHT_POWER = 1.6  # how sharply stars fade in (higher = later)

# Clouds
CLOUD_ENABLED = True
CLOUD_LAYER_COUNT = 2
CLOUD_COLOR = (255, 255, 255)
CLOUD_ALPHA = 60
CLOUD_SPEEDS = [12, 25]
CLOUD_SCALE_RANGE = (0.6, 1.4)
CLOUD_DENSITY = 9

# Fog / horizon depth
FOG_ENABLED = True
FOG_ALPHA_TOP = 0
FOG_ALPHA_BOTTOM = 120
FOG_HEIGHT_FRACTION = 0.55  # start fog around baseline
FOG_COLOR = (170, 200, 215)

# Lighting
SLOPE_LIGHTING_ENABLED = True
SUN_NORMAL_BIAS = 0.35  # bias for highlight intensity
SUN_HIGHLIGHT_STRENGTH = 0.9

# Performance / visual caching
SKY_BLEND_CACHE_STEPS = 240  # number of discrete cached sky blend states per full day-night cycle

# Star twinkle
STAR_TWINKLE_SPEED = 0.4      # base speed multiplier for twinkle animation
STAR_TWINKLE_AMPLITUDE = 0.35 # max additional brightness fraction

# Parallax vertical fade
PARALLAX_VERTICAL_FADE_ENABLED = True
PARALLAX_VERTICAL_FADE_POWER = 1.4  # exponent shaping fade curve

# Cloud tinting (day/night modulation factors)
CLOUD_TINT_DAY = (1.0, 1.0, 1.0)
CLOUD_TINT_NIGHT = (0.8, 0.85, 1.05)

# Fog twilight warm tint (sunrise/sunset blend)
FOG_TWILIGHT_ENABLED = True
FOG_TWILIGHT_WARM = (225, 190, 150)  # warm hue near horizon at sunrise/sunset
FOG_TWILIGHT_SPAN = 0.18  # fraction of day_t near 0 and 1 edges (wrap) to apply warm blend

# Cloud soft edges
CLOUD_SOFT_EDGES = True
CLOUD_EDGE_FALLOFF_POWER = 2.2

# Camera bob
CAMERA_BOB_ENABLED = True
CAMERA_BOB_AMPLITUDE = 6.0  # pixels
CAMERA_BOB_SPEED = 1.2

# Ridge shadow gradient & highlight noise
RIDGE_SHADOW_SLOPE_ATTEN = 0.6  # reduce shadow on gentle slopes
HIGHLIGHT_NOISE_ENABLED = True
HIGHLIGHT_NOISE_SCALE = 0.0015
HIGHLIGHT_NOISE_AMPLITUDE = 0.35

# Terrain spike filter (post smoothing)
SPIKE_FILTER_ENABLED = True
SPIKE_MAX_SLOPE = 3.8   # above this local slope difference considered spike
SPIKE_RELAX_FACTOR = 0.55

# Ambient haze bands
HAZE_BANDS_ENABLED = True
HAZE_BAND_COUNT = 3
HAZE_BAND_ALPHA = 18
HAZE_BAND_NOISE_SCALE = 0.002

# Fog gradient caching
FOG_CACHE_STEPS = 160

# Player visual style
PLAYER_CAPSULE_ENABLED = True
PLAYER_SHADOW_ALPHA = 70
PLAYER_FACE_ENABLED = True
PLAYER_EYE_COLOR = (35, 35, 40)
PLAYER_EYE_HIGHLIGHT = (255, 255, 255)
PLAYER_MOUTH_COLOR = (60, 40, 35)

# Player external sprite sheet
PLAYER_SPRITES_ENABLED = True
PLAYER_SPRITESHEET_PATH = "game/assets/player_spritesheet.png"
PLAYER_SPRITESHEET_META = "game/assets/player_spritesheet.json"
PLAYER_ANIM_FPS = 10  # frames per second for run cycle

# Player day-night ambient tint
PLAYER_TINT_ENABLED = True
PLAYER_TINT_WARM = (255, 210, 160)   # dawn/dusk warm tint multiplier target
PLAYER_TINT_COOL = (160, 190, 255)   # deep night cool tint multiplier target
PLAYER_TINT_DAY = (255, 255, 255)    # midday neutral
PLAYER_TINT_DAWN_SPAN = 0.12         # fraction of day_t near 0/1 for warm blend
PLAYER_TINT_NIGHT_STRENGTH = 0.55    # strength of cool tint at deepest night (0..1)

# Jump dust particles
JUMP_DUST_ENABLED = True
DUST_PARTICLE_COUNT = 10
DUST_PARTICLE_LIFETIME = 0.45
DUST_PARTICLE_SIZE_RANGE = (4, 10)
DUST_PARTICLE_COLOR = (230, 225, 215)

# Lightning flash (night)
LIGHTNING_ENABLED = True
LIGHTNING_MIN_INTERVAL = 18.0
LIGHTNING_MAX_INTERVAL = 38.0
LIGHTNING_FLASH_DURATION = 0.35
LIGHTNING_FLASH_ALPHA = 120

# God rays (sunrise beams)
GOD_RAYS_ENABLED = True
GOD_RAY_COUNT = 5
GOD_RAY_ALPHA = 60
GOD_RAY_WIDTH = 180
GOD_RAY_TILT = -18  # degrees
GOD_RAY_SPAN_DAYT = 0.08  # fraction of day_t window around sunrise (near 0.0)

# Sun glow tuning
SUN_GLOW_SCALE = 1.8        # multiplier of sun radius for outer glow radius
SUN_GLOW_MAX_ALPHA = 65     # peak per-ring alpha factor (lower => subtler glow)
SUN_GLOW_ENABLED = False    # disable if visual style unwanted
