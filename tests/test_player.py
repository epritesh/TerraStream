import math
from game.player import Player
from game.terrain import TerrainManager
from game import config

class DummyKeys:
    def __init__(self, pressed):
        self.pressed = set(pressed)
    def __getitem__(self, key):
        return key in self.pressed

def test_player_ground_clamp(monkeypatch):
    terrain = TerrainManager(seed=1)
    player = Player(terrain)
    player.y = terrain.sample_height(player.x) - 200
    player.vy = 0
    monkeypatch.setattr("pygame.key.get_pressed", lambda: DummyKeys([]))
    # Simulate up to 120 frames or until grounded
    for _ in range(120):
        player.update(1/60)
        if player.on_ground:
            break
    ground = terrain.sample_height(player.x)
    assert player.on_ground, "Player failed to land within expected frames"
    assert abs(player.y - ground) < 1e-3

def test_player_jump(monkeypatch):
    terrain = TerrainManager(seed=2)
    player = Player(terrain)
    player.y = terrain.sample_height(player.x)
    player.on_ground = True
    monkeypatch.setattr("pygame.key.get_pressed", lambda: DummyKeys([]))
    # Directly trigger jump (avoid depending on real key constants in headless test)
    player.vy = config.PLAYER_JUMP_VELOCITY
    player.on_ground = False
    start_y = player.y
    player.update(1/60)
    # After one frame of upward velocity, player should have moved upward (smaller y because y increasing means falling)
    assert player.y < start_y, "Player should move upward after jump impulse"
