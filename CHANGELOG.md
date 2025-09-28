# Changelog

All notable changes to this project will be documented in this file.

The format roughly follows Keep a Changelog (https://keepachangelog.com/) and Semantic Versioning.

## [Unreleased]
_No changes yet._

## [0.2.1] - 2025-09-28
### Added
- Foreground grass silhouette system with caching, smoothing, and tuning parameters.
- Player external sprite sheet support (run cycle) with idle fallback.
- Player day/night tint (warm dawn/dusk, cool night) with configurable spans.
- Atmospheric enhancements: haze bands, lightning flashes, fog twilight tint, star twinkle.
- Fireflies: ambient night wandering glow particles with flicker & lightning flash boost.
- Screenshot hotkey (F12) with timestamped PNG output.

### Changed
- Terrain ridge shading (highlight noise + slope-based shadow attenuation).
- Grass silhouette parameters lowered for calmer profile.
- Firefly glow rendering optimized (cached brightness buckets, smoothing, respawn logic) for consistent motion.

### Removed
- Experimental god rays (visual artifacts + performance costs).

### Performance
- Caching for sky blend, fog gradients, clouds, foreground silhouettes, player body capsule, and firefly glow buckets.

## [0.2.0] - 2025-09-27
### Added
- Combined features listed above (silhouettes, sprites, tint, haze bands, lightning polish) baseline release.

## [0.1.0] - 2025-09-27
### Added
- Initial procedural terrain generation with smoothing & spike filtering.
- Day/night cycle with sky gradient blending.
- Basic player movement & physics with capsule rendering and jump dust.
- Parallax background layers and clouds.
- Base lightning system.

[Unreleased]: https://github.com/youruser/terrastream/compare/v0.2.1...HEAD
[0.2.1]: https://github.com/youruser/terrastream/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/youruser/terrastream/compare/v0.1.0...v0.2.0
