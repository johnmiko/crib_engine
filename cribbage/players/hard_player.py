from __future__ import annotations

import sqlite3
from itertools import combinations
from typing import List, Optional, Tuple
from pathlib import Path

from cribbage.constants import HAND_CRIB_DB_PATH
from cribbage.database import normalize_hand_to_str
from cribbage.players.beginner_player import BeginnerPlayer
from cribbage.players.medium_player import MediumPlayer
from cribbage.playingcards import Card
from cribbage.strategies.pegging_strategies import medium_pegging_strategy

_HAND_STATS: dict[str, float] | None = None
_CRIB_STATS: dict[str, float] | None = None


def _load_db_stats() -> tuple[dict[str, float], dict[str, float]]:
    global _HAND_STATS, _CRIB_STATS
    if _HAND_STATS is not None and _CRIB_STATS is not None:
        return _HAND_STATS, _CRIB_STATS

    if not HAND_CRIB_DB_PATH or not Path(HAND_CRIB_DB_PATH).exists():
        raise FileNotFoundError(
            f"Missing hand/crib stats DB at {HAND_CRIB_DB_PATH}. "
            "Run scripts/build_hand_crib_db.py to create it."
        )

    hand_stats: dict[str, float] = {}
    crib_stats: dict[str, float] = {}

    conn = sqlite3.connect(HAND_CRIB_DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT hand_key, avg_score FROM hand1")
    for hand_key, avg_score in cur.fetchall():
        hand_stats[str(hand_key)] = float(avg_score)

    cur.execute("SELECT hand_key, avg_score FROM crib1")
    for crib_key, avg_score in cur.fetchall():
        crib_stats[str(crib_key)] = float(avg_score)

    conn.close()
    _HAND_STATS = hand_stats
    _CRIB_STATS = crib_stats
    return hand_stats, crib_stats


class HardPlayer(BeginnerPlayer):
    def __init__(self, name: str = "hard"):
        super().__init__(name=name)
        self.description = (
            "Picks highest average scoring hand crib combo from average estimates. "
            "Pegs points, tries to set self up for points and not set opponent up for points (same as medium)"
        )
        self._fallback = MediumPlayer(name=f"{name}_fallback")
        self._hand_stats, self._crib_stats = _load_db_stats()

    def play_pegging(self, playable: List[Card], count: int, history_since_reset: List[Card]) -> Optional[Card]:
        return medium_pegging_strategy(playable, count, history_since_reset)

    def select_crib_cards(self, player_state, round_state) -> Tuple[Card, Card]:
        hand = player_state.hand
        dealer_is_self = player_state.is_dealer

        best_discards: Tuple[Card, Card] | None = None
        best_score = float("-inf")

        for kept in combinations(hand, 4):
            kept_list = list(kept)
            discards_list = [c for c in hand if c not in kept_list]

            hand_key = normalize_hand_to_str(kept_list)
            crib_key = normalize_hand_to_str(discards_list)

            hand_avg = self._hand_stats.get(hand_key)
            crib_avg = self._crib_stats.get(crib_key)
            if hand_avg is None or crib_avg is None:
                raise KeyError(f"Missing DB stats for hand={hand_key} crib={crib_key}")

            score = hand_avg + (crib_avg if dealer_is_self else -crib_avg)
            if score > best_score:
                best_score = score
                best_discards = (discards_list[0], discards_list[1])

        if best_discards is None:
            raise RuntimeError("No discard choice found from DB stats.")
        return best_discards
