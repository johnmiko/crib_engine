import math
import sqlite3
import itertools
import numpy as np
# You said this exists already:
# from your_module import get_full_deck, score_hand
# For example:
import sys

sys.path.insert(0, ".")
sys.path.insert(0, '..')
from cribbage.database import normalize_hand_to_str, normalize_hand_to_tuple
from cribbage.players.rule_based_player import get_full_deck
from cribbage.cribbagegame import score_hand
import multiprocessing as mp

DB_PATH = "crib_cache.db"

def process_dealt_hand(args):
    # proper 6 card analysis, 20358520 combinations
    dealt_hand, full_deck, hand_score_cache = args
    dealt_hand = list(dealt_hand)

    results = []

    # all 2-card discards from the 6-card dealt hand
    discard_combos = itertools.combinations(range(6), 2)

    for discard_idx in discard_combos:
        kept_hand = [dealt_hand[i] for i in range(6) if i not in discard_idx]
        discarded_cards = [dealt_hand[i] for i in discard_idx]

        hand_key = normalize_hand_to_str(kept_hand)

        # starter cannot be any of the discarded cards
        starter_pool = [c for c in full_deck if c not in kept_hand and c not in discarded_cards]

        scores = np.array([
            hand_score_cache[normalize_hand_to_tuple(kept_hand + [starter])]
            for starter in starter_pool
        ], dtype=np.float32)

        results.append((
            hand_key,
            float(scores.min()),
            float(scores.max()),
            round(float(scores.mean()), 2),
        ))

    return results


def build_hand_stats_parallel(full_deck, hand_score_cache, n_workers=8, batch_size=2000):
    # proper 6 card analysis, 20358520 combinations
    setup_hand_stats_table(sqlite3.connect(DB_PATH))  # ensure table exists

    all_dealt_hands = itertools.combinations(full_deck, 6)
    total_iterations = math.comb(len(full_deck), 6) 
    args_iter = ((hand, full_deck, hand_score_cache) for hand in all_dealt_hands)

    pool = mp.Pool(n_workers)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    batch = []
    for idx, res in enumerate(pool.imap_unordered(process_dealt_hand, args_iter, chunksize=100), 1):
        batch.extend(res)

        if idx % 1000 == 0:
            print(f"Processing dealt hand {idx} / {total_iterations}")

        if len(batch) >= batch_size:
            cur.executemany(
                """
                INSERT OR REPLACE INTO hand_stats
                (hand_key, min_score, max_score, avg_score)
                VALUES (?, ?, ?, ?)
                """,
                batch,
            )
            conn.commit()
            batch.clear()
    
    # insert remaining
    if batch:
        cur.executemany(
            """
            INSERT OR REPLACE INTO hand_stats
            (hand_key, min_score, max_score, avg_score)
            VALUES (?, ?, ?, ?)
            """,
            batch,
        )
        conn.commit()

    pool.close()
    pool.join()
    conn.close()
    print("Done building hand stats.")

    

def process_kept_hand(args):
    kept_hand, full_deck, hand_score_cache = args
    remaining_cards = [c for c in full_deck if c not in kept_hand]

    scores = np.array([
        hand_score_cache[normalize_hand_to_tuple(list(kept_hand) + [starter])]
        for starter in remaining_cards
    ], dtype=np.float32)

    hand_key = normalize_hand_to_str(kept_hand)
    return [(hand_key, float(scores.min()), float(scores.max()), round(float(scores.mean()), 2))]


def build_kept_stats_parallel(full_deck, hand_score_cache, n_workers=8, batch_size=2000):
    setup_hand_stats_table(sqlite3.connect(DB_PATH))

    all_kept_hands = itertools.combinations(full_deck, 4)
    total_iterations = math.comb(len(full_deck), 4)  
    args_iter = ((hand, full_deck, hand_score_cache) for hand in all_kept_hands)

    pool = mp.Pool(n_workers)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS hand_stats_approx (
            hand_key TEXT PRIMARY KEY,
            min_score INTEGER,
            max_score INTEGER,
            avg_score REAL
        )
        """
    )

    batch = []
    for idx, res in enumerate(pool.imap_unordered(process_kept_hand, args_iter, chunksize=100), 1):
        batch.extend(res)

        if idx % 1000 == 0:
            print(f"Processing dealt hand {idx} / {total_iterations}")
        if len(batch) >= batch_size:
            cur.executemany(
                """
                INSERT OR REPLACE INTO hand_stats_approx
                (hand_key, min_score, max_score, avg_score)
                VALUES (?, ?, ?, ?)
                """,
                batch,
            )
            conn.commit()
            batch.clear()

    if batch:
        cur.executemany(
            """
            INSERT OR REPLACE INTO hand_stats_approx
            (hand_key, min_score, max_score, avg_score)
            VALUES (?, ?, ?, ?)
            """,
            batch,
        )
        conn.commit()

    pool.close()
    pool.join()
    conn.close()
    print("Done building hand stats.")




def setup_db(conn):
    cur = conn.cursor()

    # Hand lookup table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS hand_scores (
            hand_key TEXT PRIMARY KEY,
            score INTEGER
        )
        """
    )

    # Placeholder for future crib averages
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS crib_averages (
            context_key TEXT PRIMARY KEY,
            avg_value REAL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS hand_stats (
            hand_key TEXT PRIMARY KEY,
            min_score INTEGER,
            max_score INTEGER,
            avg_score REAL,
            avg_crib REAL
        )
        """
    )
    conn.commit()

def setup_hand_stats_table(conn):
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS hand_stats (
            hand_key TEXT PRIMARY KEY,
            min_score INTEGER,
            max_score INTEGER,
            avg_score REAL
        )
        """
    )
    conn.commit()

def setup_crib_stats_table(conn):
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS crib_stats (
            hand_key TEXT PRIMARY KEY,
            avg_crib REAL
        )
        """
    )
    conn.commit()

def load_all_5_card_scores(conn):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT hand_key, score FROM hand_scores")
    hand_score_cache = {
        tuple(row[0].split("|")): row[1]
        for row in cur.fetchall()
    }
    conn.close()
    return hand_score_cache


def load_all_5_card_crib_scores(conn):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT hand_key, score FROM crib_scores")
    hand_score_cache = {
        tuple(row[0].split("|")): row[1]
        for row in cur.fetchall()
    }
    conn.close()
    return hand_score_cache


def build_5_card_crib_score_table(full_deck):
    # create table containing the score of all possible specific cribs
    # almost exact same as hand scores minus the flush logic
    conn = sqlite3.connect(DB_PATH)
    setup_db(conn)
    cur = conn.cursor()
    table_name = "crib_scores"
    cur = conn.cursor()
    cur.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            hand_key TEXT PRIMARY KEY,
            score INTEGER
        )
        """
    )
    conn.commit()
    total = 0    
    all_dealt_hands = itertools.combinations(full_deck, 5)    
    for combo in all_dealt_hands:
        hand_key = normalize_hand_to_str(combo)
        # Skip if already stored
        cur.execute(
            f"SELECT 1 FROM {table_name} WHERE hand_key = ?",
            (hand_key,),
        )
        if cur.fetchone():
            continue
        score = score_hand(list(combo), is_crib=True)
        cur.execute(
            f"INSERT INTO {table_name} (hand_key, score) VALUES (?, ?)",
            (hand_key, score),
        )
        total += 1
        if total % 10000 == 0:
            conn.commit()
            print(f"Saved {total} / 3 000 000ish hands...")

    conn.commit()
    conn.close()
    print("Done.")




def build_5_card_hand_score_table(full_deck):
    # create table of 5 card scores
    conn = sqlite3.connect(DB_PATH)
    setup_db(conn)
    cur = conn.cursor()

    total = 0    
    all_dealt_hands = itertools.combinations(full_deck, 5)    
    for combo in all_dealt_hands:
        hand_key = normalize_hand_to_str(combo)

        # Skip if already stored
        cur.execute(
            "SELECT 1 FROM hand_scores WHERE hand_key = ?",
            (hand_key,),
        )
        if cur.fetchone():
            continue

        score = score_hand(list(combo))

        cur.execute(
            "INSERT INTO hand_scores (hand_key, score) VALUES (?, ?)",
            (hand_key, score),
        )

        total += 1
        if total % 10000 == 0:
            conn.commit()
            print(f"Saved {total} / 3 000 000ish hands...")

    conn.commit()
    conn.close()
    print("Done.")



def get_remaining_cards(full_deck, dealt_hand):    
    return list(set(full_deck) - set(dealt_hand))        


# ---------------- crib stats ----------------
def build_crib_stats(full_deck):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    setup_crib_stats_table(conn)

    all_dealt_hands = itertools.combinations(full_deck, 6)
    len_all_dealt_hands = len(list(all_dealt_hands))
    for idx, dealt_hand in enumerate(all_dealt_hands, 1):
        dealt_hand = list(dealt_hand)
        remaining_cards = [c for c in full_deck if c not in dealt_hand]
        my_discards = list(itertools.combinations(dealt_hand, 2))

        crib_scores = []

        for starter in remaining_cards:
            remaining_for_opp = [c for c in remaining_cards if c != starter]
            opponent_discards = itertools.combinations(remaining_for_opp, 2)

            for my_discard in my_discards:
                for opp_discard in opponent_discards:
                    crib_hand = list(my_discard) + list(opp_discard) + [starter]
                    crib_scores.append(score_hand(crib_hand, is_crib=True))

        avg_crib = sum(crib_scores) / len(crib_scores)
        hand_key = normalize_hand_to_str(dealt_hand)
        cur.execute(
            """
            INSERT OR REPLACE INTO crib_stats
            (hand_key, avg_crib)
            VALUES (?, ?)
            """,
            (hand_key, avg_crib),
        )

        if idx % 100 == 0:
            conn.commit()
            print(f"Processed {idx} / {len_all_dealt_hands} dealt hands for crib...")

    conn.commit()
    conn.close()
    print("Done building crib stats.")

import pandas as pd

def build_kept_stats_pandas(hand_scores):
    """
    hand_scores: dict with keys = 5-card tuples, values = score
    Computes min, max, average score for each 4-card kept hand.
    """

    # Convert to DataFrame
    df = pd.DataFrame([
        (*hand, score) for hand, score in hand_scores.items()
    ], columns=["c1","c2","c3","c4","c5","score"])

    # Sort cards in each hand to ensure consistency
    df[["c1","c2","c3","c4","c5"]] = pd.DataFrame(
        df[["c1","c2","c3","c4","c5"]].apply(lambda row: sorted(row), axis=1).tolist()
    )

    # Generate 4-card kept hands
    def kept_keys(row):
        return [tuple(sorted(k)) for k in itertools.combinations(row[["c1","c2","c3","c4","c5"]], 4)]

    df["kept_keys"] = df.apply(kept_keys, axis=1)

    # Explode so each row = 1 kept hand
    df_exploded = df.explode("kept_keys")

    # Group by kept hand key
    kept_stats = df_exploded.groupby("kept_keys")["score"].agg(
        min_score="min",
        max_score="max",
        avg_score="mean"
    ).reset_index()

    # Optional: round average
    kept_stats["avg_score"] = kept_stats["avg_score"].round(2)

    # Insert into SQLite
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS hand_stats_approx (
            hand_key TEXT PRIMARY KEY,
            min_score INTEGER,
            max_score INTEGER,
            avg_score REAL
        )
        """
    )
    # Convert tuple keys to string
    kept_stats["hand_key"] = kept_stats["kept_keys"].apply(lambda x: "|".join(x))
    cur.executemany(
        """
        INSERT OR REPLACE INTO hand_stats_approx 
        (hand_key, min_score, max_score, avg_score)
        VALUES (?, ?, ?, ?)
        """,
        kept_stats[["hand_key","min_score","max_score","avg_score"]].values.tolist()
    )
    conn.commit()
    conn.close()
    print(f"Inserted {len(kept_stats)} 4-card kept hands into hand_stats_approx.")


def build_exact_full_hand_stats_pandas(full_deck, hand_score_cache, db_path=DB_PATH, batch_size=5000):
    import pandas as pd
    import itertools
    import sqlite3

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    table_name = "hand_stats_exact" 

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            dealt_hand_key TEXT,
            kept_hand_key TEXT,
            min_score INTEGER,
            max_score INTEGER,
            avg_score REAL,
            PRIMARY KEY (dealt_hand_key, kept_hand_key)
        )
    """)
    conn.commit()

    records = []
    total_hands = itertools.combinations(full_deck, 6)
    len_total_hands = "20358520"  # precomputed

    for idx, dealt_hand in enumerate(total_hands, 1):
        dealt_hand = list(dealt_hand)
        remaining_cards = [c for c in full_deck if c not in dealt_hand]

        dealt_hand_key = normalize_hand_to_str(dealt_hand)

        for kept in itertools.combinations(dealt_hand, 4):
            kept_hand_key = normalize_hand_to_str(kept)
            scores = [
                hand_score_cache[normalize_hand_to_tuple(list(kept) + [starter])]
                for starter in remaining_cards
            ]

            records.append({
                "dealt_hand_key": dealt_hand_key,
                "kept_hand_key": kept_hand_key,
                "min_score": min(scores),
                "max_score": max(scores),
                "avg_score": round(sum(scores)/len(scores), 2)
            })

        if len(records) >= batch_size:
            df = pd.DataFrame(records)
            try:  
                df.to_sql(table_name, conn, if_exists="append", index=False)
                records.clear()
            except Exception as e:
                print(f"Error inserting batch at dealt hand {idx}: {e}")
                breakpoint()            
            print(f"Processed {idx} / {len_total_hands} dealt hands...")

    if records:
        df = pd.DataFrame(records)
        df.to_sql(table_name, conn, if_exists="append", index=False)

    conn.close()
    print("Done building exact full hand stats.")



def build_crib_stats_approx_table(
    full_deck,
    crib_score_cache,
    db_path=DB_PATH,
    batch_size=5000,
):
    import itertools
    import sqlite3
    import pandas as pd
    # doesn't account for the starter card not being in the 6 cards we were dealt
    table_name = "crib_stats_approx"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS {}".format(table_name))
    conn.commit()
    cur.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            hand_key TEXT PRIMARY KEY,
            min_score INTEGER,
            max_score INTEGER,
            avg_score REAL
        )
        """
    )

    possible_crib_hands = list(itertools.combinations(full_deck, 2))
    df = pd.DataFrame(possible_crib_hands, columns=["c1", "c2"])
    df["hand_key"] = df.apply(lambda r: normalize_hand_to_str(r), axis=1)
    
    records = []
    i = 0
    for _, row in df.iterrows():
        i += 1 
        print(f"Processing crib hand {i} / 1326")
        crib = [row.c1, row.c2]
        remaining = [c for c in full_deck if c not in crib]

        scores = []

        # opponent contributes 2 cards + starter
        for opp2 in itertools.combinations(remaining, 3):
            rest = [c for c in remaining if c not in opp2]
            five = normalize_hand_to_tuple(crib + list(opp2))
            scores.append(crib_score_cache[five])

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
    print("Done building crib_stats_approx")





if __name__ == "__main__":
    full_deck = get_full_deck()
    # done - build_5_card_hand_score_table(full_deck)
    # done - hand_score_cache = load_all_5_card_scores(sqlite3.connect(DB_PATH))  # keys as sorted tuples    
    # done - build_kept_stats_pandas(hand_score_cache)
    # done - build_exact_full_hand_stats_pandas(full_deck, hand_score_cache, db_path=DB_PATH, batch_size=5000)


    # donebuild_5_card_crib_score_table(full_deck)    
    crib_score_cache = load_all_5_card_crib_scores(sqlite3.connect(DB_PATH))  # keys as sorted tuples    
    build_crib_stats_approx_table(full_deck, crib_score_cache, db_path=DB_PATH)
    # build_kept_stats_parallel(full_deck, hand_score_cache, n_workers=8)
    # build_crib_stats(full_deck)