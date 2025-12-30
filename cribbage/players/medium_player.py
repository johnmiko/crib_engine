
from itertools import combinations
import sqlite3
import pandas as pd
from typing import List, Tuple
from cribbage.constants import DB_PATH
from cribbage.database import normalize_hand_to_str
from cribbage.players.beginner_player import BeginnerPlayer
from cribbage.playingcards import Card, build_hand

_HAND_STATS_DF = None
_CRIB_STATS_DF = None

def _load_stats_dfs():
    global _HAND_STATS_DF, _CRIB_STATS_DF
    if _HAND_STATS_DF is not None:
        return

    conn = sqlite3.connect(DB_PATH)

    _HAND_STATS_DF = pd.read_sql_query(
        "SELECT hand_key, min_score, max_score, avg_score FROM hand_stats_approx",
        conn
    ).rename(columns={
        "min_score": "min_score_hand",
        "max_score": "max_score_hand",
        "avg_score": "avg_score_hand",
    })

    _CRIB_STATS_DF = pd.read_sql_query(
        "SELECT hand_key, min_score, max_score, avg_score FROM crib_stats_approx",
        conn
    ).rename(columns={
        "hand_key": "crib_key",
        "min_score": "min_score_crib",
        "max_score": "max_score_crib",
        "avg_score": "avg_score_crib",
    })

    conn.close()

def get_hand_stats_df(hand, dealer_is_self):
    _load_stats_dfs()
    
    # Build all combinations at once without iterative DataFrame concatenation
    hands_and_cribs = []
    for keep in combinations(hand, 4):
        discard = tuple(c for c in hand if c not in keep)
        hands_and_cribs.append({
            "hand_key": normalize_hand_to_str(keep),
            "crib_key": normalize_hand_to_str(discard)
        })
    
    # Create DataFrame once from list of dicts
    df = pd.DataFrame(hands_and_cribs)
    
    # Merge operations (already efficient)
    df2 = df.merge(_CRIB_STATS_DF, on="crib_key", how="left")
    df3 = df2.merge(_HAND_STATS_DF, on="hand_key", how="left")
    
    # Vectorized operations for scoring
    if dealer_is_self:
        df3["min_score"] = df3["min_score_hand"] + df3["min_score_crib"]
        df3["max_score"] = df3["max_score_hand"] + df3["max_score_crib"]
        df3["avg_score"] = df3["avg_score_hand"] + df3["avg_score_crib"]
    else:
        df3["min_score"] = df3["min_score_hand"] - df3["max_score_crib"]
        df3["max_score"] = df3["max_score_hand"] - df3["min_score_crib"]
        df3["avg_score"] = df3["avg_score_hand"] - df3["avg_score_crib"]    
    return df3

class MediumPlayer(BeginnerPlayer):
    def __init__(self, name: str = "medium"):
        super().__init__(name=name)

    def select_crib_cards(self, hand, dealer_is_self):                
        df3 = get_hand_stats_df(hand, dealer_is_self)
        best_discards_str = df3.loc[df3["avg_score"] == df3["avg_score"].max()]["crib_key"].values[0]
        best_discards = best_discards_str.lower().replace("t", "10").split("|")
        best_discards_cards = build_hand(best_discards)
        return best_discards_cards