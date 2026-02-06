"""Time Medium vs Medium and Hard vs Hard game speed."""
from __future__ import annotations

import argparse
import time

from cribbage.players.medium_player import MediumPlayer
from cribbage.players.hard_player import HardPlayer
from cribbage.utils import play_multiple_games


def _time_matchup(label: str, p0, p1, games: int, seed: int | None, fast_mode: bool) -> None:
    start = time.perf_counter()
    play_multiple_games(games, p0, p1, seed=seed, fast_mode=fast_mode, copy_players=True)
    elapsed = time.perf_counter() - start
    per_game = elapsed / games if games > 0 else 0.0
    print(f"{label}: {elapsed:.3f}s total, {per_game:.4f}s/game ({games} games)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=int, default=50, help="Number of games per matchup.")
    ap.add_argument("--seed", type=int, default=67, help="Base seed for repeatability.")
    ap.add_argument("--fast_mode", action=argparse.BooleanOptionalAction, default=False)
    args = ap.parse_args()

    if args.games < 1:
        raise SystemExit("--games must be >= 1")

    _time_matchup(
        "Medium vs Medium",
        MediumPlayer(name="medium0"),
        MediumPlayer(name="medium1"),
        args.games,
        args.seed,
        args.fast_mode,
    )
    _time_matchup(
        "Hard vs Hard",
        HardPlayer(name="hard0"),
        HardPlayer(name="hard1"),
        args.games,
        args.seed,
        args.fast_mode,
    )


if __name__ == "__main__":
    main()
