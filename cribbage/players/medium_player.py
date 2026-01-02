
from itertools import combinations
import sqlite3
import pandas as pd
from typing import List, Tuple
from cribbage.constants import DB_PATH
from cribbage.strategies.crib_strategies import calc_crib_ranges_fast_given_6_cards
from cribbage.database import normalize_hand_to_str
from cribbage.strategies.hand_strategies import exact_hand_and_fast_crib, exact_hand_and_min_crib
from cribbage.players.beginner_player import BeginnerPlayer
from cribbage.players.rule_based_player import get_full_deck
from cribbage.playingcards import Card, build_hand
import logging

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

    def select_crib_cards(self, hand, dealer_is_self, your_score=None, opponent_score=None) -> Tuple[Card, Card]:                
        # best_discards = exact_hand_and_fast_crib(hand, dealer_is_self)
        best_discards = exact_hand_and_min_crib(hand, dealer_is_self, your_score=your_score, opponent_score=opponent_score)
        return best_discards