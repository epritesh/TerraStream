# Changelog

All notable changes to this project will be documented in this file.

The format roughly follows Keep a Changelog (https://keepachangelog.com/) and Semantic Versioning.

## [Unreleased]
### Added
- Foreground grass silhouette system with caching, smoothing, and tuning parameters.
- Player external sprite sheet support (run cycle) with idle fallback.
- Player day/night tint (warm dawn/dusk, cool night) with configurable spans.
- Atmospheric enhancements: haze bands, lightning flashes, fog twilight tint, star twinkle.

### Changed
- Terrain ridge shading (highlight noise + slope-based shadow attenuation).
- Grass silhouette parameters lowered for calmer profile.

### Removed
- Experimental god rays (visual artifacts + performance costs).

### Performance
- Caching for sky blend, fog gradients, clouds, foreground silhouettes, and player body capsule.

## [0.1.0] - 2025-09-27
### Added
- Initial procedural terrain generation with smoothing & spike filtering.
- Day/night cycle with sky gradient blending.
- Basic player movement & physics with capsule rendering and jump dust.
- Parallax background layers and clouds.
- Base lightning system.

[Unreleased]: https://github.com/youruser/terrastream/compare/v0.1.0...HEAD
