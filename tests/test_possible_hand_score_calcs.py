# generate_all_possible_crib_hand_scores
import math
import sqlite3
import itertools
import numpy as np
import pandas as pd
# You said this exists already:
# from your_module import get_full_deck, score_hand
# For example:
import sys

sys.path.insert(0, ".")
sys.path.insert(0, '..')
from cribbage.constants import DB_PATH
from cribbage.database import normalize_hand_to_str, normalize_hand_to_tuple
from cribbage.players.rule_based_player import get_full_deck
from cribbage.cribbagegame import score_hand
import multiprocessing as mp

def get_4_card_hand_stats(hand_score_cache, full_deck, db_path=DB_PATH, batch_size=5000):

    # doesn't account for the starter card not being in the 6 cards we were dealt
    table_name = "hand_stats_approx"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    possible_hands = list(itertools.combinations(full_deck, 4))
    df = pd.DataFrame(possible_hands, columns=["c1", "c2", "c3", "c4"])
    df["hand_key"] = df.apply(lambda r: normalize_hand_to_str(r), axis=1)
    len_df = len(df)
    records = []
    i = 0
    for _, row in df.iterrows():
        i += 1 
        print(f"Processing hand {i} / {len_df}")
        hand = [row.c1, row.c2, row.c3, row.c4]
        remaining = [c for c in full_deck if c not in hand]
        scores = []

        # opponent contributes 2 cards + starter
        for starter in remaining:            
            five = normalize_hand_to_tuple(hand + [starter])
            scores.append(hand_score_cache[five])

        records.append({
            "hand_key": row.hand_key,
            "min_score": min(scores),
            "max_score": max(scores),
            "avg_score": round(sum(scores) / len(scores), 2)
        })

        if len(records) >= batch_size:
            pd.DataFrame(records).to_sql(
                table_name, conn, if_exists="append", index=False
            )
            records.clear()

    if records:
        pd.DataFrame(records).to_sql(
            table_name, conn, if_exists="append", index=False
        )

    conn.close()
    print(f"Done building {table_name}")



def test_implicit_plus_2_hands():
    pass