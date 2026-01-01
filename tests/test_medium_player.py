from collections import defaultdict
import itertools
import numpy as np
from cribbage.database import normalize_hand_to_str
from cribbage.players.medium_player import MediumPlayer, get_6_card_stats_df_from_db
from cribbage.players.rule_based_player import get_full_deck
from cribbage.playingcards import build_hand
import pandas as pd

from cribbage.scoring import score_hand
from cribbage.scoring import score_hand
from itertools import combinations
from typing import List, Tuple
from cribbage.playingcards import Card
import pandas as pd
import logging

from scripts.generate_all_possible_crib_hand_scores_old import calc_crib_ranges_exact, process_dealt_hand_exact, process_dealt_hand_only_exact


logger = logging.getLogger(__name__)

RUN_NO_FLUSH_HAND = ["3h","4c","5d","6h","7h","8d"]
RUN_FLUSH_HAND = ["3h","4h","5h","6h","7h","8h"]

pd.set_option("display.width", None)

# def test_get_6_card_stats_df():
#     # couple hands that have an extra 2 points in them, check that this is correct in the lookup
#     hand = build_hand(RUN_NO_FLUSH_HAND)
#     df = get_6_card_stats_df_from_db(hand, dealer_is_self=True)
#     df2 = df.sort_values(by="avg_score_hand_approx", ascending=False)
#     kept_key = "3H|4C|5D|6H"
#     assert df2.loc[df2["hand_key"] == kept_key, "min_score_hand"].values[0] == 8
#     assert df2.loc[df2["hand_key"] == kept_key, "avg_score_approx"].values[0] == 16.53
#     # exact is 15.57
#     assert score_hand(build_hand(kept_key), is_crib=False) == 6
#     kept_key = "5D|6H|7H|8D"
#     assert df2.loc[df2["hand_key"] == kept_key, "min_score_hand"].values[0] == 8
#     assert score_hand(build_hand(kept_key), is_crib=False) == 6
#     assert df2.loc[df2["hand_key"] == kept_key, "avg_score_approx"].values[0] == 15.05
#     # exact is 14.08
#     hand = build_hand(["5h","6c","7d","9h","2h","10d"])
#     df = get_6_card_stats_df_from_db(hand, dealer_is_self=False)
#     df2 = df.sort_values(by="avg_score_hand_approx", ascending=False)
#     kept_key = "2H|5H|6C|7D"
#     a = 1
#     assert df2.loc[df2["hand_key"] == kept_key, "min_score_hand"].values[0] == 7
#     assert df2.loc[df2["hand_key"] == kept_key, "avg_score_approx"].values[0] == 3.58
#     # exact is 4.66
#     assert score_hand(build_hand(kept_key), is_crib=False) == 5
#     kept_key = "5H|6C|7D|9H"
#     assert df2.loc[df2["hand_key"] == kept_key, "min_score_hand"].values[0] == 7
#     assert score_hand(build_hand(kept_key), is_crib=False) == 5
#     assert round(df2.loc[df2["hand_key"] == kept_key, "avg_score_approx"].values[0],2) == 4.01
#     row = df2.loc[df2["hand_key"] == kept_key].iloc[0]

#     avg_hand = row["avg_score_hand_approx"]
#     avg_crib = row["avg_score_crib_approx"]

#     assert abs(avg_hand - 8.11) < 0.1
#     assert round(avg_crib, 2) == 4.05
#     # exact is 8.11 - 3.03 = 5.08
#     # This is returning 8 because I'm not doing my shit correctly, but it's stored in the table incorrectly
#     # So I cannot just look up the score in the table
#     hand = build_hand(RUN_FLUSH_HAND)
#     df = get_6_card_stats_df_from_db(hand, dealer_is_self=True)
#     df2 = df.sort_values(by="avg_score_hand_approx", ascending=False)
#     kept_key = "3H|4H|5H|6H"
#     assert df2.loc[df2["hand_key"] == kept_key, "min_score_hand"].values[0] == 12
#     assert score_hand(build_hand(kept_key), is_crib=False) == 10
#     kept_key = "5H|6H|7H|8H"
#     assert df2.loc[df2["hand_key"] == kept_key, "min_score_hand"].values[0] == 12
#     assert score_hand(build_hand(kept_key), is_crib=False) == 10    


# def test_avg_score_approx_is_reasonable():
#     # check that my approx average scores are reasonable vs exact values (brute force calculated)
#     tolerance = 0.1    
#     hand = build_hand(["5h","6c","7d","9h","2h","10d"])
#     df = get_6_card_stats_df_from_db(hand, dealer_is_self=False)
#     df2 = df.sort_values(by="avg_score_approx", ascending=False)
#     df_exact = pd.DataFrame({"hand_key":['5H|6C|7D|9H', '5H|6C|7D|TD', '2H|5H|6C|7D','5H|6C|9H|TD', '2H|5H|6C|9H', '5H|7D|9H|TD', '2H|5H|6C|TD', '2H|5H|9H|TD', '2H|5H|7D|9H', '2H|6C|7D|9H', '2H|5H|7D|TD', '6C|7D|9H|TD', '2H|6C|7D|TD', '2H|6C|9H|TD', '2H|7D|9H|TD'],
#                              "avg_hand_score_exact": [8.11, 7.85, 8.46, 6.89, 4.85, 4.76, 4.67, 4.65, 2.93, 6.07, 4.5, 4.11, 3.98, 3.91, 2.04],
#                              "avg_crib_score_exact": [4.10, 4.17, 4.84, 4.24, 3.67, 4.21, 4.31, 5.37, 3.60, 7.21, 5.53, 5.94, 5.76, 6.43, 7.10]})
#     df2 = pd.merge(df2, df_exact, left_on="hand_key", right_on="hand_key")
#     df2["avg_hand_score_diff"] = df2["avg_score_hand_approx"] - df2["avg_hand_score_exact"]
#     df2["avg_crib_score_diff"] = df2["avg_score_crib_approx"] - df2["avg_crib_score_exact"]
#     bad_hand_approxes = df2.loc[~df2["avg_hand_score_diff"].between(0, 0.1), "avg_hand_score_diff"]
#     bad_crib_approxes = df2.loc[~df2["avg_crib_score_diff"].between(0, 0.1), "avg_crib_score_diff"]
#     df3 = df2.loc[~df2["avg_hand_score_diff"].between(0, 0.1) | ~df2["avg_crib_score_diff"].between(0, 0.1)]
#     if not bad_hand_approxes.empty or not bad_crib_approxes.empty:
#         pd.set_option("display.width", None)
#         logger.error("Bad approximations found:\n " + df3[["hand_key","crib_key", "avg_score_hand_approx","avg_hand_score_exact","avg_hand_score_diff", "avg_score_crib_approx","avg_crib_score_exact", "avg_crib_score_diff"]].to_string())
#     assert bad_hand_approxes.empty, f"Bad hand approximations: {bad_hand_approxes.to_string()}"
#     assert bad_crib_approxes.empty, f"Bad crib approximations: {bad_crib_approxes.to_string()}"

    

def test_medium_player_chooses_correct_discard_simple_hand():
    player = MediumPlayer()
    hand = build_hand(["ac","ad","ah","as","2h","2d"])
    crib_cards = player.select_crib_cards(hand, dealer_is_self=True)
    assert crib_cards == tuple(build_hand(["2d","2h"]))


def test_medium_player_chooses_correct_discard():
    player = MediumPlayer()
    hand = build_hand(RUN_FLUSH_HAND)
    crib_cards = player.select_crib_cards(hand, dealer_is_self=True)
    assert crib_cards == tuple(build_hand(["7h","8h"]))

# def test_min_hand_calc_is_correct():
#     hand = build_hand(["3h","4h","5h","6h"])
#     full_deck = get_full_deck()
#     remaining = [c for c in full_deck if c not in hand]
#     scores = []
#     records = []
#     for starter in remaining:                
#         score = score_hand(hand, is_crib=False, starter_card=starter)
#         scores.append(score)

#         records.append({
#             "hand_key": "3H|4H|5H|6H" + f"|{starter}",
#             "min_score": min(scores),
#             "max_score": max(scores),
#             "avg_score": round(sum(scores) / len(scores), 2)
#         })
        
#     df = pd.DataFrame(records)
#     assert df["min_score"].min() == 12
#     hand = build_hand(["3h","4c","5s","6d"])
#     full_deck = get_full_deck()
#     remaining = [c for c in full_deck if c not in hand]
#     scores = []
#     records = []
#     for starter in remaining:                
#         score = score_hand(hand, is_crib=False, starter_card=starter)
#         scores.append(score)

#         records.append({
#             "hand_key": "3H|4H|5H|6H" + f"|{starter}",
#             "min_score": min(scores),
#             "max_score": max(scores),
#             "avg_score": round(sum(scores) / len(scores), 2)
#         })
        
#     df = pd.DataFrame(records)
#     assert df["min_score"].min() == 8
    # df = get_6_card_stats_df(hand, dealer_is_self=True)
    # df2 = df.sort_values(by="avg_score_hand_approx", ascending=False)
    # kept_key = "3H|4H|5H|6H"
    # assert df2.loc[df2["hand_key"] == kept_key, "min_score_hand"].values[0] == 12
    # kept_key = "5H|6H|7H|8H"
    # assert df2.loc[df2["hand_key"] == kept_key, "min_score_hand"].values[0] == 12

def test_process_dealt_hand_only_works_correctly():
    # hand = build_hand(RUN_FLUSH_HAND)
    full_deck = get_full_deck()
    hand_score_cache = {}    
    # results = process_dealt_hand([hand, full_deck, hand_score_cache])
    # a = 1 
    tolerance = 0.1 
    hand = build_hand(["5h","6c","7d","9h","2h","10d"])
    results = process_dealt_hand_only_exact([hand, full_deck, hand_score_cache])
    df_processed = pd.DataFrame(results, columns=["hand_key","min_score","max_score","avg_hand_score"])
    # df_processed = pd.DataFrame(results, columns=["hand_key","crib_key","min_score","max_score","avg_hand_score"])
    # df = get_6_card_stats_df_from_db(hand, dealer_is_self=False)
    # df2 = df.sort_values(by="avg_score_approx", ascending=False)
    df_expected = pd.DataFrame({"hand_key":['5H|6C|7D|9H', '5H|6C|7D|TD', '2H|5H|6C|7D','5H|6C|9H|TD', '2H|5H|6C|9H', '5H|7D|9H|TD', '2H|5H|6C|TD', '2H|5H|9H|TD', '2H|5H|7D|9H', '2H|6C|7D|9H', '2H|5H|7D|TD', '6C|7D|9H|TD', '2H|6C|7D|TD', '2H|6C|9H|TD', '2H|7D|9H|TD'],
                             "avg_hand_score_exact": [8.11, 7.85, 8.46, 6.89, 4.85, 4.76, 4.67, 4.65, 2.93, 6.07, 4.5, 4.11, 3.98, 3.91, 2.04]})
    df2 = pd.merge(df_processed, df_expected, left_on="hand_key", right_on="hand_key")    
    df2["avg_hand_score_diff"] = df2["avg_hand_score"] - df2["avg_hand_score_exact"]
    incorrect_hand_calcs = df2.loc[df2["avg_hand_score_diff"] != 0, "avg_hand_score_diff"]
    df3 = df2.loc[~df2["avg_hand_score_diff"].between(0, tolerance)]
    if not incorrect_hand_calcs.empty:
        pd.set_option("display.width", None)
        logger.error("Bad approximations found:\n " + df3[["hand_key","crib_key", "avg_score_hand_approx","avg_hand_score_exact","avg_hand_score_diff"]].to_string())
    assert incorrect_hand_calcs.empty, f"Bad hand approximations: {incorrect_hand_calcs.to_string()}"    
    

def test_calc_crib_ranges_exact_works_correctly():    
    dealt_hand = build_hand(["5h","6c","7d","9h","2h","10d"])
    full_deck = get_full_deck()    
    # caches are wrong, force to empty for now
    hand_score_cache = {}
    crib_score_cache = {}
    rank_list = ['a', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'j', 'q', 'k']
    suits_list = ['c', 'd', 'h', 's']
    results = []

    # all 2-card discards from the 6-card dealt hand
    discard_combos = itertools.combinations(range(6), 2)
    
    for discard_idx in discard_combos:
        logger.info(f"Processing discard idx: {discard_idx}")
        kept_hand = [dealt_hand[i] for i in range(6) if i not in discard_idx]
        discarded_cards = [dealt_hand[i] for i in discard_idx]

        hand_key = normalize_hand_to_str(kept_hand)
        crib_key = normalize_hand_to_str(discarded_cards)
        # starter cannot be any of the discarded cards
        starter_pool = [c for c in full_deck if c not in dealt_hand]  # 46 cards

        # Group starters by rank -> set of available suits
        rank_to_suits = defaultdict(set)
        for starter in starter_pool:
            rank = starter.rank
            suit = starter.suit
            rank_to_suits[rank].add(suit)


        # CRIB SCORES (new optimized calc)
        min_crib, crib_avg = calc_crib_ranges_exact(rank_list, starter_pool, suits_list, discarded_cards, crib_score_cache)
        results.append((
            hand_key,
            crib_key,
            float(min_crib),
            round(float(crib_avg), 2),
        ))
    df_processed = pd.DataFrame(results, columns=["hand_key","crib_key", "min_crib_score","avg_crib_score"])      
    # the exact crib scores were calculated using the script calculate_exact_crib_values_by_brute_force.py
    df_expected = pd.DataFrame({"hand_key":['2H|5H|6C|7D', '2H|5H|6C|9H', '2H|5H|6C|TD', '2H|5H|7D|9H', '2H|5H|7D|TD', '2H|5H|9H|TD', '2H|6C|7D|9H', '2H|6C|7D|TD', '2H|6C|9H|TD', '2H|7D|9H|TD', '5H|6C|7D|9H', '5H|6C|7D|TD', '5H|6C|9H|TD', '5H|7D|9H|TD', '6C|7D|9H|TD'],
                             "avg_crib_score_exact": [4.84, 3.67, 4.31, 3.6, 5.53, 5.37, 7.21, 5.76, 6.43, 7.1, 4.1, 4.17, 4.24, 4.21, 5.94]})
    df2 = pd.merge(df_processed, df_expected, left_on="hand_key", right_on="hand_key")    
    df2["avg_crib_score_diff"] = df2["avg_crib_score"] - df2["avg_crib_score_exact"]    
    bad_crib_approxes = df2.loc[~df2["avg_crib_score_diff"].between(-0.01, 0.01), "avg_crib_score_diff"]
    df3 = df2.loc[~df2["avg_crib_score_diff"].between(0, 0.01)]    
    df3 = df3.sort_values(by="avg_crib_score_exact", ascending=False)
    logger.info(f"\n{df3[["hand_key","crib_key", "avg_crib_score","avg_crib_score_exact", "avg_crib_score_diff"]]}")
    if not bad_crib_approxes.empty:        
        logger.error("Bad approximations found:\n " + df3[["hand_key", "avg_crib_score","avg_crib_score_exact", "avg_crib_score_diff"]].to_string())
    assert bad_crib_approxes.empty, f"Bad crib approximations: {bad_crib_approxes.to_string()}"

    
def test_process_dealt_hand_and_crib_works_correctly():
    # hand = build_hand(RUN_FLUSH_HAND)
    full_deck = get_full_deck()
    hand_score_cache = {}    
    crib_score_cache = {}
    # results = process_dealt_hand([hand, full_deck, hand_score_cache])
    # a = 1 
    tolerance = 0.1 
    hand = build_hand(["5h","6c","7d","9h","2h","10d"])
    results = process_dealt_hand_exact([hand, full_deck, hand_score_cache, crib_score_cache])
    df_processed = pd.DataFrame(results, columns=["hand_key","crib_key","min_score","max_score","avg_hand_score", "min_crib_score","avg_crib_score"])
    # df_processed = pd.DataFrame(results, columns=["hand_key","crib_key","min_score","max_score","avg_hand_score"])
    # df = get_6_card_stats_df_from_db(hand, dealer_is_self=False)
    # df2 = df.sort_values(by="avg_score_approx", ascending=False)
    df_hand_expected = pd.DataFrame({"hand_key":['5H|6C|7D|9H', '5H|6C|7D|TD', '2H|5H|6C|7D','5H|6C|9H|TD', '2H|5H|6C|9H', '5H|7D|9H|TD', '2H|5H|6C|TD', '2H|5H|9H|TD', '2H|5H|7D|9H', '2H|6C|7D|9H', '2H|5H|7D|TD', '6C|7D|9H|TD', '2H|6C|7D|TD', '2H|6C|9H|TD', '2H|7D|9H|TD'],
                             "avg_hand_score_exact": [8.11, 7.85, 8.46, 6.89, 4.85, 4.76, 4.67, 4.65, 2.93, 6.07, 4.5, 4.11, 3.98, 3.91, 2.04],
                             })
    df_crib_expected = pd.DataFrame({"hand_key":['2H|5H|6C|7D', '2H|5H|6C|9H', '2H|5H|6C|TD', '2H|5H|7D|9H', '2H|5H|7D|TD', '2H|5H|9H|TD', '2H|6C|7D|9H', '2H|6C|7D|TD', '2H|6C|9H|TD', '2H|7D|9H|TD', '5H|6C|7D|9H', '5H|6C|7D|TD', '5H|6C|9H|TD', '5H|7D|9H|TD', '6C|7D|9H|TD'],
                             "avg_crib_score_exact": [4.84, 3.67, 4.31, 3.6, 5.53, 5.37, 7.21, 5.76, 6.43, 7.1, 4.1, 4.17, 4.24, 4.21, 5.94]})
    df_expected = pd.merge(df_hand_expected, df_crib_expected, left_on="hand_key", right_on="hand_key")
    df2 = pd.merge(df_processed, df_expected, left_on="hand_key", right_on="hand_key")    
    df2["avg_hand_score_diff"] = df2["avg_hand_score"] - df2["avg_hand_score_exact"]    
    df2["avg_crib_score_diff"] = df2["avg_crib_score"] - df2["avg_crib_score_exact"]
    bad_hand_approxes = df2.loc[~df2["avg_hand_score_diff"].between(0, 0.01), "avg_hand_score_diff"]
    bad_crib_approxes = df2.loc[~df2["avg_crib_score_diff"].between(0, 0.01), "avg_crib_score_diff"]    
    df3 = df2.loc[~df2["avg_hand_score_diff"].between(0, 0.1) | ~df2["avg_crib_score_diff"].between(0, 0.1)]    
    df3["avg_score_exact"] = df3["avg_hand_score_exact"] + df3["avg_crib_score_exact"]
    df3 = df3.sort_values(by="avg_score_exact", ascending=False)
    logger.info(f"\n{df3[["hand_key","crib_key", "avg_crib_score","avg_crib_score_exact", "avg_crib_score_diff"]]}")
    if not bad_hand_approxes.empty or not bad_crib_approxes.empty:        
        logger.error("Bad approximations found:\n " + df3[["hand_key","avg_hand_score","avg_hand_score_exact","avg_hand_score_diff", "avg_crib_score","avg_crib_score_exact", "avg_crib_score_diff"]].to_string())
    assert bad_hand_approxes.empty, f"Bad hand approximations: {bad_hand_approxes.to_string()}"
    assert bad_crib_approxes.empty, f"Bad crib approximations: {bad_crib_approxes.to_string()}"
    