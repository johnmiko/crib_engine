import sqlite3
from cribbage.constants import DB_PATH
from cribbage.players.medium_player import MediumPlayer, get_hand_stats_df
from cribbage.playingcards import build_hand
from cribbage.scoring import score_hand
from scripts.generate_all_possible_crib_hand_scores import load_all_5_card_crib_scores, lload_all_5_card_crib_scores, oad_all_5_card_scores


def test_medium_player_chooses_correct_discard():
import os
import sys

import pandas as pd

sys.path.insert(0, ".")
# sys.path.insert(0, "..")
# sys.path.insert(0, "...")
from cribbage.scoring import score_hand
from cribbage.cribbagegame import CribbageGame
from cribbage.cribbageround import CribbageRound
from cribbage.players.beginner_player import BeginnerPlayer
from cribbage.players.medium_player import MediumPlayer
from cribbage.utils import play_multiple_games

import logging

logger = logging.getLogger(__name__)


# def test_max_score_vs_statistic_discard_strategy():
    # to test the strategy strength, I want to deal both players the same cards, then check which cards they discard
    # then deal a random starter card, and score both hands + cribs to see which strategy is better
    # when they are both dealt the same hand, we want to see how the strategies change
    # I can manually look at them, but what about the crib? If they have the same hand, the crib doesn't make any sense
    # I will put 2 random cards in the crib I guess? But that's assuming they have the same discards
def test_using_statistics_performs_better_than_4_card_scoring_discard_strategy_on_average():
    num_hands = 100    
    beginner_player = BeginnerPlayer(name="BeginnerPlayer")
    medium_player = MediumPlayer(name="MediumPlayer")
    header = "dealt,starter,beginner_discard,medium_discard,beginner_crib,medium_crib,beginner_hand,beginner_score,medium_hand,medium_score,dealer_is_self\n"
    rows = []    
    for hand_num in range(num_hands): 
        if hand_num % 2 == 0:
            dealer_is_self = True
        else:
            dealer_is_self = False
        game = CribbageGame(players=[medium_player, beginner_player], seed=None)
        round = CribbageRound(game, dealer=medium_player, seed=None)
        cards = round.deck.cards[:6]
        beginner_discards = beginner_player.select_crib_cards(cards, dealer_is_self=dealer_is_self)
        medium_discards = medium_player.select_crib_cards(cards, dealer_is_self=dealer_is_self)                  
        starter = round.deck.cards[6]
        beginner_hand = [c for c in cards if c not in beginner_discards]
        medium_hand = [c for c in cards if c not in medium_discards]
        beginner_crib = list(beginner_discards) + [round.deck.cards[7], round.deck.cards[8]]
        medium_crib = list(medium_discards) + [round.deck.cards[7], round.deck.cards[8]]
        beginner_hand_score = score_hand(beginner_hand, is_crib=False, starter_card=starter)
        beginner_crib_score = score_hand(beginner_crib, is_crib=True, starter_card=starter)
        medium_hand_score = score_hand(medium_hand, is_crib=False, starter_card=starter)
        medium_crib_score = score_hand(medium_crib, is_crib=True, starter_card=starter)
        if dealer_is_self:
            beginner_score = beginner_hand_score + beginner_crib_score
            medium_score = medium_hand_score + medium_crib_score
        else:
            beginner_score = beginner_hand_score - beginner_crib_score
            medium_score = medium_hand_score - medium_crib_score
        rows.append(f'"{",".join(str(c) for c in cards)}","{starter}","{",".join(str(c) for c in beginner_discards)}","{",".join(str(c) for c in medium_discards)}","{",".join(str(c) for c in beginner_crib)}","{",".join(str(c) for c in medium_crib)}","{",".join(str(c) for c in beginner_hand)}",{beginner_score},"{",".join(str(c) for c in medium_hand)}",{medium_score},{dealer_is_self}\n')
        df = pd.DataFrame([row.strip().split(",") for row in rows], columns=header.split(","))
        logger.info(f"Score difference when different discards were selected (medium - beginner)")
        df2 = df.drop_duplicates("dealt")
        df2["score_dif"] = df2["medium_score"] - df2["beginner_score"]
        total_score_dif = df2["score_dif"].sum()
        average_score_dif = df2["score_dif"].mean()
        logger.info(f"Total score difference over {len(df2)} hands: {total_score_dif}")
        assert total_score_dif > 0, "medium_player should have a higher total score than BeginnerPlayer when different discards are chosen"
        assert average_score_dif > 0, "medium_player should have a higher average score than BeginnerPlayer when different discards are chosen"