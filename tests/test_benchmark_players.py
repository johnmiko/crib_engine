import logging
from cribbage.players.random_player import RandomPlayer
from cribbage.players.play_first_card_player import PlayFirstCardPlayer
from cribbage.players.beginner_player import BeginnerPlayer
from cribbage.players.medium_player import MediumPlayer

from cribbage.utils import play_multiple_games
from cribbage.cribbagegame import CribbageGame
import sqlite3

logger = logging.getLogger(__name__)

def test_random_vs_first_card_player_seeded_results_are_always_the_same():
    # both players are random so we expect about 50% win rate
    num_games = 1
    random_player = RandomPlayer(name="RandomPlayer", seed=42)
    first_card_player = PlayFirstCardPlayer(name="PlayFirstCardPlayer")
    results = play_multiple_games(num_games, p0=random_player, p1=first_card_player, seed=42)        
    assert results == {'wins': 1, 'diffs': [62], 'winrate': 1.0, 'ci_lo': 0.2065432914738929, 'ci_hi': 1.0}

def test_random_vs_first_card_player():
    # both players are random so we expect about 50% win rate
    num_games = 500
    random_player = RandomPlayer(name="RandomPlayer", seed=42)
    first_card_player = PlayFirstCardPlayer(name="PlayFirstCardPlayer")
    results = play_multiple_games(num_games, p0=random_player, p1=first_card_player, seed=42)    
    wins, diffs, winrate, lo, hi = results["wins"], results["diffs"], results["winrate"], results["ci_lo"], results["ci_hi"]    
    win_rate = wins / num_games
    logger.info(f"RandomPlayer wins: {wins}/{num_games} ({win_rate:.2%})")
    assert win_rate > 0.4, "RandomPlayer should win at least 40% of the time against PlayFirstCardPlayer"    
    assert win_rate < 0.6, "RandomPlayer should not win more than 60% of the time against PlayFirstCardPlayer"

def test_random_vs_beginner_player():
    num_games = 500
    random_player = BeginnerPlayer(name="BeginnerPlayer")
    first_card_player = PlayFirstCardPlayer(name="PlayFirstCardPlayer")
    results = play_multiple_games(num_games, p0=random_player, p1=first_card_player)    
    wins, diffs, winrate, lo, hi = results["wins"], results["diffs"], results["winrate"], results["ci_lo"], results["ci_hi"]    
    win_rate = wins / num_games
    logger.info(f"BeginnerPlayer wins: {wins}/{num_games} ({win_rate:.2%})")
    assert win_rate > 0.98, "BeginnerPlayer should win at least 98% of the time against PlayFirstCardPlayer"        

def test_beginner_vs_medium_player():
    num_games = 500
    beginner_player = BeginnerPlayer(name="BeginnerPlayer")
    medium_player = MediumPlayer(name="MediumPlayer")    
    results = play_multiple_games(num_games, p0=medium_player, p1=beginner_player)    
    wins, diffs, winrate, lo, hi = results["wins"], results["diffs"], results["winrate"], results["ci_lo"], results["ci_hi"]    
    win_rate = wins / num_games
    logger.info(f"diffs: {diffs}")
    logger.info(f"medium_player wins: {wins}/{num_games} ({win_rate:.2%})")
    assert win_rate > 0.63, "medium_player should win at least 63% of the time against BeginnerPlayer"    

# def test_beginner_vs_medium_player_single_discards():
#     from cribbage.playingcards import Deck
#     deck = Deck()
#     deck.shuffle()
#     hand = deck.cards[:6]
#     logger.info(f"Hand: {hand}")
#     beginner_player = BeginnerPlayer(name="BeginnerPlayer")
#     medium_player = MediumPlayer(name="MediumPlayer")    
#     beginner_crib = beginner_player.select_crib_cards(hand, dealer_is_self=False)
#     medium_crib = medium_player.select_crib_cards(hand, dealer_is_self=False)
#     a = 1
