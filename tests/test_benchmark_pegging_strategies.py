import logging

import pytest
from cribbage import cribbagegame
from cribbage.cribbageround import CribbageRound
from cribbage.players.random_player import RandomPlayer
from cribbage.players.play_first_card_player import PlayFirstCardPlayer
from cribbage.players.beginner_player import BeginnerPlayer
from cribbage.players.medium_player import MediumPlayer

from cribbage.utils import play_game, play_multiple_games, wilson_ci
from cribbage.cribbagegame import CribbageGame
import sqlite3
import pandas as pd

logger = logging.getLogger(__name__)


def play_first_round(p0, p1, seed=None):
    # game = cribbagegame.CribbageGame(players=[p0, p1], seed=seed)
    # final_pegging_scores = game.start()
    # return (final_pegging_scores[0], final_pegging_scores[1])
    game1 = CribbageGame(players=[p0, p1], seed=seed)
    round1 = CribbageRound(game=game1, dealer=p0)
    round1.play()
    return round1.history.score_after_pegging

def play_multiple_hands(num_games, p0, p1, seed=None) -> dict:
    wins = 0
    ties = 0
    diffs = []
    for i in range(num_games):
        # if (i % 100) == 0:
        logger.info(f"Playing hand {i}/{num_games}")
        # Alternate seats because cribbage has dealer advantage
        if i % 2 == 0:
            p0_peg_score, p1_peg_score = play_first_round(p0, p1, seed=seed)
            diff = p0_peg_score - p1_peg_score
        else:
            p0_peg_score, p1_peg_score = play_first_round(p1, p0, seed=seed)
            diff = p1_peg_score - p0_peg_score            
        if diff > 0:
                wins += 1
        elif diff == 0:
             ties += 1 
        diffs.append(diff)
    winrate = wins / (num_games - ties)
    lo, hi = wilson_ci(wins, (num_games - ties))    
    return {"wins":wins, "diffs": diffs, "winrate": winrate, "ci_lo": lo, "ci_hi": hi, "ties": ties}

# @pytest.mark.slow
def test_beginner_vs_medium_player_pegging_strategies():
# Not sure why this fails, guessing it's because of endgame strategies differ
    num_games = 300
    beginner_player = BeginnerPlayer(name="BeginnerPlayer")
    medium_player = MediumPlayer(name="MediumPlayer")    
    results = play_multiple_hands(num_games, p0=medium_player, p1=beginner_player)    
    wins, diffs, win_rate, lo, hi, ties = results["wins"], results["diffs"], results["winrate"], results["ci_lo"], results["ci_hi"], results["ties"]
    # win_rate = wins / num_games
    non_tie_games = num_games - ties
    average_peg_dif = sum(diffs) / num_games
    total_difs = sum(diffs)
    logger.info(f"Ties after pegging: {ties}/{num_games}")    
    logger.info(f"Average pegging score difference per hand (medium - beginner): {average_peg_dif:.2f}")    
    logger.info(f"Total pegging difference after {num_games} games (medium - beginner): {total_difs:.2f}")    
    logger.info(f"medium_player wins: {wins}/{non_tie_games} ({win_rate:.2%} CI: {lo:.2%}-{hi:.2%})")
    assert win_rate > 0.5, "medium_player should win at least 50% of the time against BeginnerPlayer"    