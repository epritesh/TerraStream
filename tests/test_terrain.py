from game.terrain import TerrainManager
from game import config


def test_chunk_generation_and_boundary_continuity():
    tm = TerrainManager(seed=777)
    # Force generate two adjacent chunks (0 and 1)
    tm.generate_chunk(0)
    tm.generate_chunk(1)
    # Last point of chunk 0
    last_point_chunk0 = tm.chunks[0][-1]
    # First point inside chunk1 with same x (should exist due to overlap sampling pattern)
    same_x = last_point_chunk0[0]
    # Find matching x in chunk1
    match = [p for p in tm.chunks[1] if p[0] == same_x]
    assert match, "Expected overlapping x sample in chunk 1"
    y0 = last_point_chunk0[1]
    y1 = match[0][1]
    # After blending we expect small difference (slope continuity attempt) but allow some tolerance
    assert abs(y0 - y1) < config.NOISE_AMPLITUDE * 0.25, "Boundary discontinuity too large"


def test_sample_height_interpolation():
    tm = TerrainManager(seed=1)
    tm.generate_chunk(0)
    # Pick two adjacent sample points
    p0, p1 = tm.chunks[0][0], tm.chunks[0][1]
    mid_x = (p0[0] + p1[0]) / 2
    mid_y = tm.sample_height(mid_x)
    # For linear interpolation midpoint should be average of endpoints if function between samples is linear; noise curve may not be linear but our interpolation is
    expected_mid = (p0[1] + p1[1]) / 2
    assert abs(mid_y - expected_mid) < config.NOISE_AMPLITUDE * 0.51, "Interpolation midpoint deviates excessively"