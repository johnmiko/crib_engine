from itertools import combinations
from typing import List, Tuple, Optional
from logging import getLogger
from cribbage.playingcards import Card
from itertools import combinations

import numpy as np
from cribbage import cribbagegame
from cribbage.training_game import TrainingGame

logger = getLogger(__name__)

# def fill_hand(possible_hands: list[tuple[list[Card], list[Card]]]) -> list[tuple[list[Card], list[Card]]]:
#     """
#     Given a list of (hand, crib) pairs, return all possible 5-card hands for each hand and crib.
#     Returns a list of tuples: (hand_5, crib_5)
#     """    
#     from crib_ai_trainer.constants import SUITES
#     filled = []
#     deck = [Card(suit, rank) for suit in SUITES for rank in range(1, 14)]
#     for hand, crib in possible_hands:
#         hand_set = set(hand + crib)
#         remaining = [card for card in deck if card not in hand_set]
#         # For each 4-card hand, add each remaining card to make a 5-card hand
#         hand_5s = [list(hand) + [card] for card in remaining] if len(hand) == 4 else []
#         crib_5s = [list(crib) + [card] for card in remaining] if len(crib) == 4 else []
#         for h5 in hand_5s:
#             for c5 in crib_5s:
#                 filled.append((h5, c5))
#     return filled


# def get_possible_hands(hand: list[Card]) -> list[tuple[list[Card], list[Card]]]:
#     """
#     Given a 6-card hand, return all possible (cards_to_keep, crib_cards) pairs,
#     where cards_to_keep is a list of 4 cards and crib_cards is the 2 cards put in the crib.
#     """
#     if len(hand) != 6:
#         raise ValueError("Hand must have exactly 6 cards")
#     all_combos = []
#     for kept in combinations(hand, 4):
#         crib = [c for c in hand if c not in kept]
#         all_combos.append((list(kept), crib))
#     return all_combos

def play_game(
    p0,
    p1,
    seed=None,
    *,
    fast_mode: bool = False,
    copy_players: bool = True,
    training_mode: str = "full",
) -> tuple[int, int]:
    if training_mode == "full":
        game = cribbagegame.CribbageGame(
            players=[p0, p1],
            seed=seed,
            copy_players=copy_players,
            fast_mode=fast_mode,
        )
    else:
        game = TrainingGame(
            players=[p0, p1],
            seed=seed,
            copy_players=copy_players,
            fast_mode=fast_mode,
            training_mode=training_mode,
        )
    final_pegging_scores = game.start()
    return (final_pegging_scores[0], final_pegging_scores[1])
    # return get_scores(game)


def wilson_ci(wins: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    phat = wins / n
    denom = 1 + z * z / n
    center = (phat + z * z / (2 * n)) / denom
    half = (z / denom) * np.sqrt((phat * (1 - phat) / n) + (z * z / (4 * n * n)))
    return float(center - half), float(center + half)

def mean_ci(values: list[float], z: float = 1.96) -> tuple[float, float]:
    if not values:
        return (0.0, 0.0)
    arr = np.array(values, dtype=np.float32)
    n = int(arr.shape[0])
    if n <= 1:
        mean = float(arr.mean())
        return (mean, mean)
    mean = float(arr.mean())
    std = float(arr.std(ddof=1))
    half = z * (std / np.sqrt(n))
    return (mean - half, mean + half)
    

def play_multiple_games_old(num_games, p0, p1, seed=None) -> dict:
    wins = 0
    diffs = []
    for i in range(num_games):
        if (i % 100) == 0:
            logger.debug(f"Playing game {i}/{num_games}")
        # Alternate seats because cribbage has dealer advantage
        if i % 2 == 0:
            s0, s1 = play_game(p0, p1, seed=seed)
            diff = s0 - s1
            if diff > 0:
                wins += 1
        else:
            s0, s1 = play_game(p1, p0, seed=seed)
            diff = s1 - s0
            if diff > 0:
                wins += 1
        diffs.append(diff)
    winrate = wins / num_games
    lo, hi = wilson_ci(wins, num_games)    
    return {"wins":wins, "diffs": diffs, "winrate": winrate, "ci_lo": lo, "ci_hi": hi}

def play_multiple_games(
    num_games,
    p0,
    p1,
    seed=None,
    *,
    fast_mode: bool = False,
    copy_players: bool = True,
    training_mode: str = "full",
) -> dict:
    wins = 0
    ties = 0
    diffs = []
    for i in range(num_games):
        if (i % (num_games / 10)) == 0:
            logger.debug(f"Playing game {i}/{num_games}")
        game_seed = None if seed is None else int(seed) + i
        # Alternate seats because cribbage has dealer advantage
        if i % 2 == 0:
            s0, s1 = play_game(
                p0,
                p1,
                seed=game_seed,
                fast_mode=fast_mode,
                copy_players=copy_players,
                training_mode=training_mode,
            )
            diff = s0 - s1
        else:
            s0, s1 = play_game(
                p1,
                p0,
                seed=game_seed,
                fast_mode=fast_mode,
                copy_players=copy_players,
                training_mode=training_mode,
            )
            diff = s1 - s0
        if diff > 0:
            wins += 1
        elif diff == 0:             
             ties += 1
        diffs.append(diff)
    winrate = wins / (num_games - ties)
    win_lo, win_hi = wilson_ci(wins, (num_games - ties))
    diff_lo, diff_hi = mean_ci(diffs)
    return {
        "wins": wins,
        "diffs": diffs,
        "winrate": winrate,
        "ci_lo": win_lo,
        "ci_hi": win_hi,
        "diff_ci_lo": diff_lo,
        "diff_ci_hi": diff_hi,
        "ties": ties,
    }

