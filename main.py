from game.loop import Game
import argparse
from game import config
import os

if __name__ == "__main__":
    # Skip launching interactive loop when under pytest
    if 'PYTEST_CURRENT_TEST' in os.environ or os.environ.get('PYTEST_RUNNING') == '1':
        raise SystemExit(0)
    parser = argparse.ArgumentParser(description="Run Terrastream infinite terrain prototype.")
    parser.add_argument("--seed", type=int, default=config.SEED, help="Noise seed (default: config.SEED)")
    args = parser.parse_args()
    Game(seed=args.seed).run()
