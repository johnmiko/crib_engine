
from itertools import combinations
import sqlite3
from typing import List, Tuple
from cribbage.constants import DB_PATH
from cribbage.database import normalize_hand_to_str
from cribbage.players.beginner_player import BeginnerPlayer
from cribbage.playingcards import Card

# def 

class HardPlayer(BeginnerPlayer):
    def __init__(self, name: str = "difficult"):
        super().__init__(name=name)

    def select_crib_cards(self, hand, dealer_is_self):
        best_score = float("-inf")
        best_discard = None
        # build_kept_stats_pandas(hand_score_cache)

        hand_keys = []
        for keep in combinations(hand, 4):
            discard = tuple(c for c in hand if c not in keep)

            # canonical key, must match DB format exactly
            hand_key = normalize_hand_to_str(keep)
            hand_keys.append(hand_key)
            # hand_key = "|".join(str(c) for c in key_cards)
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        table_name = "hand_stats_approx"
        hand_keys_str = [hk for hk in hand_keys]
        # query = f"SELECT * FROM hand_stats_approx WHERE hand_key IN ({','.join(['?']*len(hand_keys_str))})"        
        # cur.execute(query, hand_keys_str)
        # rows = cur.fetchall()
        import pandas as pd

        placeholders = ",".join(["?"] * len(hand_keys_str))
        query = f"""
        SELECT hand_key, min_score, max_score, avg_score
        FROM hand_stats_approx
        WHERE hand_key IN ({placeholders})
        """

        df = pd.read_sql_query(query, conn, params=hand_keys_str)
        highest_average_hand = df.loc[df["avg_score"] == df["avg_score"].max()]["hand_key"].values[0]
        return df
        hand_scores = {
            tuple(row.hand_key.split("|")): row.avg_score
            for row in df.itertuples(index=False)
        }
        hand_scores = {
            tuple(row[0].split("|")): row[1]
            for row in cur.fetchall()
        }
        conn.close()
        return hand_scores
        #     score = row.avg_score

        #     # if opponent's crib, discarding good cards is bad
        #     if not dealer_is_self:
        #         score = -score

        #     if score > best_score:
        #         best_score = score
        #         best_discard = discard

        # return best_discard