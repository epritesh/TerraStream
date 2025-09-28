"""Minimal 1D gradient noise (Perlin-like) with fractal octaves.

We keep it lightweight: no external dependencies. The implementation
produces deterministic results given a seed. Values are in [-1, 1].

Usage:
    noise = Noise1D(seed=1337)
    val = noise.noise(x)                   # single octave
    val2 = noise.fractal(x, octaves=4)     # multi-octave fractal noise

Approach:
- Create a permutation table (hash) of size 256 duplicated to avoid wrapping logic.
- For a given x: find unit segment (x0, x1), compute gradients g0, g1 from hashed indices.
- Fade the fractional component (Perlin fade curve) for smooth interpolation.
- Dot product simplifies to gradient * fractional offset since 1D.
- Interpolate (LERP) between contributions.

Fractal layering (aka FBM):
value = sum( noise(x * freq) * amp ) / sum(amp)
where freq *= lacunarity (default 2.0) and amp *= persistence (default 0.5).
"""
from __future__ import annotations
import random
from typing import List

_FADE = lambda t: t * t * t * (t * (t * 6 - 15) + 10)  # 6t^5 - 15t^4 + 10t^3
_LERP = lambda a, b, t: a + (b - a) * t

class Noise1D:
    def __init__(self, seed: int = 0):
        rnd = random.Random(seed)
        p = list(range(256))
        rnd.shuffle(p)
        # Duplicate for overflow-less index wrap
        self.perm: List[int] = p + p

    def _grad(self, hash_val: int) -> float:
        # In 1D gradients are just +1 or -1 (could add more variety if desired)
        return 1.0 if (hash_val & 1) == 0 else -1.0

    def noise(self, x: float) -> float:
        # Find unit grid cell containing x
        x0 = int(x) & 255
        x_rel = x - int(x)
        x1 = (x0 + 1) & 255

        # Gradients
        g0 = self._grad(self.perm[x0])
        g1 = self._grad(self.perm[x1])

        # Dot products (in 1D this is gradient * distance)
        d0 = g0 * x_rel
        d1 = g1 * (x_rel - 1.0)

        # Smooth interpolation
        t = _FADE(x_rel)
        return _LERP(d0, d1, t)

    def fractal(self, x: float, octaves: int = 4, lacunarity: float = 2.0, persistence: float = 0.5) -> float:
        total = 0.0
        amplitude = 1.0
        max_amp = 0.0
        freq = 1.0
        for _ in range(octaves):
            total += self.noise(x * freq) * amplitude
            max_amp += amplitude
            amplitude *= persistence
            freq *= lacunarity
        return total / max_amp if max_amp else 0.0

# Convenience singleton (can be replaced later if seed changes)
_default_noise = Noise1D(seed=1337)

def noise1(x: float) -> float:
    return _default_noise.noise(x)

def fractal_noise1(x: float, octaves: int = 4, lacunarity: float = 2.0, persistence: float = 0.5) -> float:
    return _default_noise.fractal(x, octaves=octaves, lacunarity=lacunarity, persistence=persistence)

if __name__ == "__main__":  # simple manual test
    n = Noise1D(42)
    for i in range(0, 10):
        print(i, n.fractal(i * 0.25, octaves=5))
