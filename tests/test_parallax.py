from game.background import ParallaxBackground


def test_parallax_relative_motion():
    bg = ParallaxBackground(seed=123)
    cam_a = 100.0
    cam_b = 400.0
    # Internal helper: retrieve raw layer points (speed_factor, points)
    layer_data_a = []
    layer_data_b = []
    for layer in bg.layers:
        pts_a, sf = bg._layer_points(layer, cam_a, 800, 600)
        pts_b, _ = bg._layer_points(layer, cam_b, 800, 600)
        layer_data_a.append((sf, pts_a))
        layer_data_b.append((sf, pts_b))

    deltas = {}
    for (sf_a, pts_a), (sf_b, pts_b) in zip(layer_data_a, layer_data_b):
        assert sf_a == sf_b
        if not pts_a or not pts_b:
            continue
        mid_idx_a = len(pts_a) // 2
        mid_idx_b = min(mid_idx_a, len(pts_b) - 1)
        x_a = pts_a[mid_idx_a][0]
        x_b = pts_b[mid_idx_b][0]
        delta = x_b - x_a
        deltas[sf_a] = delta

    items = sorted(deltas.items(), key=lambda t: t[0])
    # For increasing speed factor, expect more negative (faster left movement) or at least not more positive
    for i in range(len(items) - 1):
        sf0, d0 = items[i]
        sf1, d1 = items[i + 1]
        # Allow small tolerance due to bucket shifts
        assert d1 <= d0 + 10.0, f"Parallax ordering unexpected: layer {sf1} delta {d1} vs {sf0} delta {d0}"