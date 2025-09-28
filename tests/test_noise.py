import math
from game.noise import Noise1D

def test_noise_determinism():
    n1 = Noise1D(seed=1234)
    n2 = Noise1D(seed=1234)
    samples1 = [n1.noise(i * 0.137) for i in range(50)]
    samples2 = [n2.noise(i * 0.137) for i in range(50)]
    assert samples1 == samples2, "Noise with same seed should be deterministic"


def test_noise_range_single_octave():
    n = Noise1D(seed=42)
    vals = [n.noise(i * 0.111) for i in range(100)]
    assert all(-1.1 <= v <= 1.1 for v in vals), "Single octave noise out of expected range"


def test_fractal_range_and_mean():
    n = Noise1D(seed=99)
    vals = [n.fractal(i * 0.091, octaves=5) for i in range(300)]
    # Fractal should still be in roughly [-1,1]
    assert all(-1.05 <= v <= 1.05 for v in vals), "Fractal noise out of range"
    mean = sum(vals) / len(vals)
    assert abs(mean) < 0.1, f"Mean should be near zero, got {mean}"