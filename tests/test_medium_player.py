from cribbage.players.medium_player import MediumPlayer, get_hand_stats_df
from cribbage.playingcards import build_hand
import pandas as pd

def test_get_hand_stats_df():
    hand = build_hand(["3h","4h","5h","6h","7h","8h"])
    df = get_hand_stats_df(hand, dealer_is_self=True)
    assert df.empty

def test_medium_player_chooses_correct_discard_simple_hand():
    player = MediumPlayer()
    hand = build_hand(["ac","ad","ah","as","2h","2d"])
    crib_cards = player.select_crib_cards(hand, dealer_is_self=True)
    assert crib_cards == build_hand(["2d","2h"])


def test_medium_player_chooses_correct_discard():
    player = MediumPlayer()
    hand = build_hand(["3h","4h","5h","6h","7h","8h"])
    crib_cards = player.select_crib_cards(hand, dealer_is_self=True)
    assert crib_cards == build_hand(["7h","8h"])