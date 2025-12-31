import numpy as np
from cribbage.players.medium_player import MediumPlayer, get_6_card_stats_df
from cribbage.playingcards import build_hand
import pandas as pd

from cribbage.scoring import score_hand
from cribbage.scoring import score_hand
from itertools import combinations
from typing import List, Tuple
from cribbage.playingcards import Card
import pandas as pd
import logging


logger = logging.getLogger(__name__)

def test_get_6_card_stats_df():
    # couple hands that have an extra 2 points in them, check that this is correct in the lookup
    hand = build_hand(["3h","4c","5d","6h","7h","8d"])
    df = get_6_card_stats_df(hand, dealer_is_self=True)
    df2 = df.sort_values(by="avg_score_hand_approx", ascending=False)
    kept_key = "3H|4C|5D|6H"
    assert df2.loc[df2["hand_key"] == kept_key, "min_score_hand"].values[0] == 8
    assert df2.loc[df2["hand_key"] == kept_key, "avg_score_approx"].values[0] == 16.53
    # exact is 15.57
    assert score_hand(build_hand(kept_key), is_crib=False) == 6
    kept_key = "5D|6H|7H|8D"
    assert df2.loc[df2["hand_key"] == kept_key, "min_score_hand"].values[0] == 8
    assert score_hand(build_hand(kept_key), is_crib=False) == 6
    assert df2.loc[df2["hand_key"] == kept_key, "avg_score_approx"].values[0] == 15.05
    # exact is 14.08
    hand = build_hand(["5h","6c","7d","9h","2h","10d"])
    df = get_6_card_stats_df(hand, dealer_is_self=False)
    df2 = df.sort_values(by="avg_score_hand_approx", ascending=False)
    kept_key = "2H|5H|6C|7D"
    a = 1
    assert df2.loc[df2["hand_key"] == kept_key, "min_score_hand"].values[0] == 7
    assert df2.loc[df2["hand_key"] == kept_key, "avg_score_approx"].values[0] == 3.58
    # exact is 4.66
    assert score_hand(build_hand(kept_key), is_crib=False) == 5
    kept_key = "5H|6C|7D|9H"
    assert df2.loc[df2["hand_key"] == kept_key, "min_score_hand"].values[0] == 7
    assert score_hand(build_hand(kept_key), is_crib=False) == 5
    assert round(df2.loc[df2["hand_key"] == kept_key, "avg_score_approx"].values[0],2) == 4.01
    row = df2.loc[df2["hand_key"] == kept_key].iloc[0]

    avg_hand = row["avg_score_hand_approx"]
    avg_crib = row["avg_score_crib_approx"]

    assert abs(avg_hand - 8.11) < 0.1
    assert round(avg_crib, 2) == 4.05
    # exact is 8.11 - 3.03 = 5.08
    hand = build_hand(["3h","4h","5h","6h","7h","8h"])
    df = get_6_card_stats_df(hand, dealer_is_self=True)
    df2 = df.sort_values(by="avg_score_hand_approx", ascending=False)
    kept_key = "3H|4H|5H|6H"
    assert df2.loc[df2["hand_key"] == kept_key, "min_score_hand"].values[0] == 12
    assert score_hand(build_hand(kept_key), is_crib=False) == 10
    kept_key = "5H|6H|7H|8H"
    assert df2.loc[df2["hand_key"] == kept_key, "min_score_hand"].values[0] == 12
    assert score_hand(build_hand(kept_key), is_crib=False) == 10    


def test_avg_score_approx_is_reasonable():
    # check that my approx average scores are reasonable vs exact values according to crib app
    tolerance = 0.1    
    hand = build_hand(["5h","6c","7d","9h","2h","10d"])
    df = get_6_card_stats_df(hand, dealer_is_self=False)
    df2 = df.sort_values(by="avg_score_approx", ascending=False)
    df_exact = pd.DataFrame({"hand_key":['5H|6C|7D|9H', '5H|6C|7D|TD', '2H|5H|6C|7D','5H|6C|9H|TD', '2H|5H|6C|9H', '5H|7D|9H|TD', '2H|5H|6C|TD', '2H|5H|9H|TD', '2H|5H|7D|9H', '2H|6C|7D|9H', '2H|5H|7D|TD', '6C|7D|9H|TD', '2H|6C|7D|TD', '2H|6C|9H|TD', '2H|7D|9H|TD'],
                             "avg_hand_score_exact": [8.11, 7.85, 8.46, 6.89, 4.85, 4.76, 4.67, 4.65, 2.93, 6.07, 4.5, 4.11, 3.98, 3.91, 2.04],
                             "avg_crib_score_exact": [3.03, 3.13, 3.80, 3.24, 2.73, 3.32, 3.31, 4.50, 2.80, 5.98, 4.53, 4.76, 4.73, 5.37, 6.05]})
    df2 = pd.merge(df2, df_exact, left_on="hand_key", right_on="hand_key")
    df2["avg_hand_score_diff"] = df2["avg_score_hand_approx"] - df2["avg_hand_score_exact"]
    df2["avg_crib_score_diff"] = df2["avg_score_crib_approx"] - df2["avg_crib_score_exact"]
    bad_hand_approxes = df2.loc[~df2["avg_hand_score_diff"].between(0, 0.1), "avg_hand_score_diff"]
    bad_crib_approxes = df2.loc[~df2["avg_crib_score_diff"].between(0, 0.1), "avg_crib_score_diff"]
    df3 = df2.loc[~df2["avg_hand_score_diff"].between(0, 0.1) | ~df2["avg_crib_score_diff"].between(0, 0.1)]
    if not bad_hand_approxes.empty or not bad_crib_approxes.empty:
        pd.set_option("display.width", None)
        logger.error("Bad approximations found:\n " + df3[["hand_key","crib_key", "avg_score_hand_approx","avg_hand_score_exact","avg_hand_score_diff", "avg_score_crib_approx","avg_crib_score_exact", "avg_crib_score_diff"]].to_string())
    assert bad_hand_approxes.empty, f"Bad hand approximations: {bad_hand_approxes.to_string()}"
    assert bad_crib_approxes.empty, f"Bad crib approximations: {bad_crib_approxes.to_string()}"

    

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
