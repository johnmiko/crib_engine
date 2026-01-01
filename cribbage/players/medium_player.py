
from itertools import combinations
import sqlite3
import pandas as pd
from typing import List, Tuple
from cribbage.constants import DB_PATH
from cribbage.crib_strategies import calc_crib_ranges_fast_given_6_cards
from cribbage.database import normalize_hand_to_str
from cribbage.players.beginner_player import BeginnerPlayer
from cribbage.players.rule_based_player import get_full_deck
from cribbage.playingcards import Card, build_hand
import logging

from scripts.generate_all_possible_crib_hand_scores import process_dealt_hand_exact, process_dealt_hand_only_exact

logger = logging.getLogger(__name__)

# Fastest, but need to check if I introduced a bug or not
# _HAND_STATS_DF = None
# _CRIB_STATS_DF = None

# def _load_stats_dfs():
#     global _HAND_STATS_DF, _CRIB_STATS_DF
#     if _HAND_STATS_DF is not None:
#         return

#     conn = sqlite3.connect(DB_PATH)

#     _HAND_STATS_DF = pd.read_sql_query(
#         "SELECT hand_key, min_score, max_score, avg_score FROM hand_stats_approx",
#         conn
#     ).rename(columns={
#         "min_score": "min_score_hand",
#         "max_score": "max_score_hand",
#         "avg_score": "avg_score_hand",
#     })

#     _CRIB_STATS_DF = pd.read_sql_query(
#         "SELECT hand_key, min_score, max_score, avg_score FROM crib_stats_approx",
#         conn
#     ).rename(columns={
#         "hand_key": "crib_key",
#         "min_score": "min_score_crib",
#         "max_score": "max_score_crib",
#         "avg_score": "avg_score_crib",
#     })

#     conn.close()

# def get_6_card_stats_df(hand, dealer_is_self):
#     _load_stats_dfs()
    
#     # Build all combinations at once without iterative DataFrame concatenation
#     hands_and_cribs = []
#     for keep in combinations(hand, 4):
#         discard = tuple(c for c in hand if c not in keep)
#         hands_and_cribs.append({
#             "hand_key": normalize_hand_to_str(keep),
#             "crib_key": normalize_hand_to_str(discard)
#         })
    
#     # Create DataFrame once from list of dicts
#     df = pd.DataFrame(hands_and_cribs)
    
#     # Merge operations (already efficient)
#     df2 = df.merge(_CRIB_STATS_DF, on="crib_key", how="left")
#     df3 = df2.merge(_HAND_STATS_DF, on="hand_key", how="left")
    
#     # Vectorized operations for scoring
#     if dealer_is_self:
#         df3["min_score"] = df3["min_score_hand"] + df3["min_score_crib"]
#         df3["max_score"] = df3["max_score_hand"] + df3["min_score_crib"]
#         df3["avg_score"] = df3["avg_score_hand"] + df3["avg_score_crib"]
#     else:
#         df3["min_score"] = df3["min_score_hand"] - df3["avg_score_crib"]
#         df3["max_score"] = df3["max_score_hand"] - df3["avg_score_crib"]
#         df3["avg_score"] = df3["avg_score_hand"] - df3["avg_score_crib"]    
#     logger.info("\n" + df3[["hand_key", "crib_key", "min_score_hand", "max_score_hand", "avg_score_hand", "avg_score_crib", "avg_score"]].sort_values(by="avg_score", ascending=False).to_string())
#     return df3

# def get_6_card_stats_df_from_db(hand, dealer_is_self): 
#     hand_keys = []
#     crib_keys = []
#     df = pd.DataFrame(columns=["key", "hand_key","crib_key","min_score", "max_score", "avg_score_approx"])
#     for keep in combinations(hand, 4):
#         discard = tuple(c for c in hand if c not in keep)
#         crib_key = normalize_hand_to_str(discard)
#         crib_keys.append(crib_key)
#         # canonical key, must match DB format exactly
#         hand_key = normalize_hand_to_str(keep)
#         hand_keys.append(hand_key)
#         df = pd.concat([df, pd.DataFrame([{"hand_key": hand_key, "crib_key": crib_key}])], ignore_index=True)

#         # hand_key = "|".join(str(c) for c in key_cards)
#     conn = sqlite3.connect(DB_PATH)    
#     hand_keys_str = [hk for hk in hand_keys]
#     hand_placeholders = ",".join(["?"] * len(hand_keys_str))
#     hand_query = f"""
#     SELECT hand_key, min_score, max_score, avg_score
#     FROM hand_stats_approx
#     WHERE hand_key IN ({hand_placeholders})
#     """

#     df_hands = pd.read_sql_query(hand_query, conn, params=hand_keys_str)
#     df_hands = df_hands.rename(columns={"min_score": "min_score_hand",
#                                 "max_score": "max_score_hand",
#                                 "avg_score": "avg_score_hand_approx"})
#     crib_keys_str = [ck for ck in crib_keys]
#     crib_placeholders = ",".join(["?"] * len(crib_keys_str))
#     crib_query = f"""
#     SELECT hand_key, min_score, max_score, avg_score
#     FROM crib_stats_approx
#     WHERE hand_key IN ({crib_placeholders})
#     """
#     df_crib = pd.read_sql_query(crib_query, conn, params=crib_keys_str)
#     df_crib = df_crib.rename(columns={"min_score": "min_score_crib",
#                                         "max_score": "max_score_crib",
#                                         "avg_score": "avg_score_crib_approx",
#                                         "hand_key": "crib_key"})
#     df2 = pd.merge(df, df_crib, left_on="crib_key", right_on="crib_key")
#     df3 = pd.merge(df2, df_hands, left_on="hand_key", right_on="hand_key")
#     df3["min_score"] = df3["min_score_hand"] + (df3["min_score_crib"] if dealer_is_self else -df3["max_score_crib"])
#     df3["max_score"] = df3["max_score_hand"] + (df3["max_score_crib"] if dealer_is_self else -df3["min_score_crib"])
#     df3["avg_score_approx"] = df3["avg_score_hand_approx"] + (df3["avg_score_crib_approx"] if dealer_is_self else -df3["avg_score_crib_approx"])
#     return df3

class MediumPlayer(BeginnerPlayer):
    def __init__(self, name: str = "medium"):
        super().__init__(name=name)

    def select_crib_cards(self, hand, dealer_is_self):                
        # df3 = get_6_card_stats_df_from_db(hand, dealer_is_self)
        full_deck = get_full_deck()
        hand_score_cache = {}
        crib_score_cache = {}        
        hand_results = process_dealt_hand_only_exact([hand, full_deck, hand_score_cache])
        df_hand = pd.DataFrame(hand_results, columns=["hand_key","min_hand_score","max_hand_score","avg_hand_score"])
        crib_results = calc_crib_ranges_fast_given_6_cards(hand)
        df_crib = pd.DataFrame(crib_results, columns=["hand_key","crib_key","min_crib_score","avg_crib_score"])
        df3 = pd.merge(df_hand, df_crib, on=["hand_key"])        
        df3["avg_total_score"] = df3["avg_hand_score"] + (df3["avg_crib_score"] if dealer_is_self else -df3["avg_crib_score"])
    #     logger.debug(f"\n {df3[['hand_key', 'max_hand_score',
    #    'avg_hand_score', 'min_crib_score', 'avg_crib_score',
    #    'avg_total_score']].sort_values(by='avg_total_score', ascending=False)}")
        best_discards_str = df3.loc[df3["avg_total_score"] == df3["avg_total_score"].max()]["crib_key"].values[0]
        best_discards = best_discards_str.lower().replace("t", "10").split("|")
        best_discards_cards = build_hand(best_discards)
        return tuple(best_discards_cards)