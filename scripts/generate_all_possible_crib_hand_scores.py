from collections import defaultdict
import math
import sqlite3
import itertools
import numpy as np
import pandas as pd
# You said this exists already:
# from your_module import get_full_deck, score_hand
# For example:
import sys

from cribbage.crib_strategies import calc_crib_ranges_exact_and_slow
from cribbage.playingcards import Card

sys.path.insert(0, ".")
sys.path.insert(0, '..')
from cribbage.database import normalize_hand_to_str, normalize_hand_to_tuple
from cribbage.players.rule_based_player import get_full_deck
from cribbage.cribbagegame import score_hand
import multiprocessing as mp

DB_PATH = "crib_cache.db"

def process_dealt_hand_old(args):
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

def calc_hand_ranges_exact(rank_to_suits, kept_hand, flush_suit, flush_base, nobs_suits, hand_score_cache):
    # Compute scores
    scores = []
    for rank, avail_suits in rank_to_suits.items():
        if not avail_suits:
            continue
        # Dummy for base (suit 'C' arbitrary)
        # dummy_starter = Card(rank + 'c')
        # calculate runs, 15s, pairs since these don't care about suit
        dummy_suit = list(avail_suits)[0]
        dummy_starter = Card(rank + dummy_suit)
        dummy_hand = kept_hand + [dummy_starter]
        dummy_tuple = normalize_hand_to_tuple(dummy_hand)
        runs_15s_pairs_score = hand_score_cache.get(dummy_tuple, None)  # Fallback if missing
        if runs_15s_pairs_score is None:
            runs_15s_pairs_score = score_hand(dummy_hand, is_crib=False)

        # Extras dummy triggered
        dummy_flush_bonus = 1 if flush_suit == dummy_suit else 0
        dummy_nobs = 1 if dummy_suit in nobs_suits else 0
        dummy_flush = flush_base + dummy_flush_bonus
        # Since we mocked the starter cards suit, we need to remove its contributions
        # could simplify by not calculatin the full hand score
        base = runs_15s_pairs_score - dummy_flush - dummy_nobs

        # Per real suit
        for avail_suit in avail_suits:
            flush_bonus = 1 if flush_suit == avail_suit else 0
            nobs = 1 if avail_suit in nobs_suits else 0
            score = base + flush_base + flush_bonus + nobs
            scores.append(score)
    return scores

def process_dealt_hand_only_exact(args):
    dealt_hand, full_deck, hand_score_cache = args
    # currently forcing hand score cache to none because there is bugs in it
    hand_score_cache = {}
    dealt_hand = list(dealt_hand)
    results = []
    discard_combos = itertools.combinations(range(6), 2)
    for discard_idx in discard_combos:
        kept_hand = [dealt_hand[i] for i in range(6) if i not in discard_idx]
        discarded_cards = [dealt_hand[i] for i in discard_idx]
        hand_key = normalize_hand_to_str(kept_hand)
        starter_pool = [c for c in full_deck if c not in dealt_hand]  # 46 cards

        # Flush setup
        suits = [c.suit for c in kept_hand]
        flush_potential = len(set(suits)) == 1
        flush_suit = suits[0] if flush_potential else None
        flush_base = 4 if flush_potential else 0

        # Nobs setup
        nobs_suits = set(c.suit for c in kept_hand if c.rank.lower() == 'j')

        # Group starters by rank -> set of available suits
        from collections import defaultdict
        # ranks to suits is a dict of rank -> set of suits available of the remaining 46 cards
        rank_to_suits = defaultdict(set)
        for starter in starter_pool:
            rank = starter.rank
            suit = starter.suit
            rank_to_suits[rank].add(suit)

        scores = calc_hand_ranges_exact(rank_to_suits, kept_hand, flush_suit, flush_base, nobs_suits, hand_score_cache)

        scores_np = np.array(scores, dtype=np.float32)
        results.append((
            hand_key,
            float(scores_np.min()),
            float(scores_np.max()),
            round(float(scores_np.mean()), 2),
        ))
    return results


def update_table(hand_key, crib_key, hand_ranges=None, crib_ranges=None, conn=None):
    if conn is None:
        conn = sqlite3.connect(DB_PATH)
    table_name = "hand_stats"
    cur = conn.cursor()
    cur.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            hand_key TEXT,
            crib_key TEXT,
            min_hand_score INTEGER,
            max_hand_score INTEGER,
            avg_hand_score REAL,
            min_crib_score INTEGER,
            avg_crib_score REAL,
            PRIMARY KEY (hand_key, crib_key)
        )
        """
    )
    conn.commit()
    # check if key already exists
    cur.execute(f"SELECT 1 FROM {table_name} WHERE hand_key = ? AND crib_key = ?", (hand_key, crib_key))
    row = cur.fetchone()
    if row:
        if crib_ranges is not None: 
            cur.execute(
                f"""
                UPDATE {table_name}
                SET min_crib_score = ?,
                    avg_crib_score = ?
                WHERE hand_key = ? AND crib_key = ?
                """,
                (crib_ranges[0], crib_ranges[1], hand_key, crib_key)
            )
        elif hand_ranges is not None:
            cur.execute(
                f"""
                UPDATE {table_name}
                SET min_hand_score = ?,
                    max_hand_score = ?,
                    avg_hand_score = ?,
                WHERE hand_key = ? AND crib_key = ?
                """,
                (hand_ranges[0], hand_ranges[1], hand_ranges[2], hand_key, crib_key)
            )

    else:
        if (crib_ranges is not None) and (hand_ranges is not None):
            cur.execute(
            f"""
            INSERT INTO {table_name}
            (hand_key, crib_key,
            min_hand_score, max_hand_score, avg_hand_score,
            min_crib_score, avg_crib_score)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (hand_key, crib_key,
            hand_ranges[0], hand_ranges[1], hand_ranges[2],
            crib_ranges[0], crib_ranges[1])
        )
        elif crib_ranges is not None:
            cur.execute(
            f"""
            INSERT INTO {table_name}
            (hand_key, crib_key,
            min_crib_score, avg_crib_score)
            VALUES (?, ?, ?, ?)
            """,
            (hand_key, crib_key,            
            crib_ranges[0], crib_ranges[1])
        )
        elif hand_ranges is not None:
            cur.execute(
            f"""
            INSERT INTO {table_name}
            (hand_key, crib_key,
            min_hand_score, max_hand_score, avg_hand_score)
            VALUES (?, ?, ?, ?, ?)
            """,
            (hand_key, crib_key,
            hand_ranges[0], hand_ranges[1], hand_ranges[2])
        )

        


def process_dealt_hand_exact(args):
    dealt_hand, full_deck, hand_score_cache, crib_score_cache = args
    # caches are wrong, force to empty for now
    hand_score_cache = {}
    crib_score_cache = {}
    dealt_hand = list(dealt_hand)
    rank_list = ['a', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'j', 'q', 'k']
    suits_list = ['c', 'd', 'h', 's']
    results = []

    # all 2-card discards from the 6-card dealt hand
    discard_combos = itertools.combinations(range(6), 2)

    for discard_idx in discard_combos:
        kept_hand = [dealt_hand[i] for i in range(6) if i not in discard_idx]
        discarded_cards = [dealt_hand[i] for i in discard_idx]

        hand_key = normalize_hand_to_str(kept_hand)
        crib_key = normalize_hand_to_str(discarded_cards)

        # starter cannot be any of the discarded cards
        starter_pool = [c for c in full_deck if c not in dealt_hand]  # 46 cards

        # HAND SCORES (existing optimized code)
        # Flush setup
        suits = [c.suit for c in kept_hand]
        flush_potential = len(set(suits)) == 1
        flush_suit = suits[0] if flush_potential else None
        flush_base = 4 if flush_potential else 0

        # Nobs setup
        nobs_suits = set(c.suit for c in kept_hand if c.rank.lower() == 'j')

        # Group starters by rank -> set of available suits
        rank_to_suits = defaultdict(set)
        for starter in starter_pool:
            rank = starter.rank
            suit = starter.suit
            rank_to_suits[rank].add(suit)

        # Compute scores
        scores = calc_hand_ranges_exact(rank_to_suits, kept_hand, flush_suit, flush_base, nobs_suits, hand_score_cache)
        scores_np = np.array(scores, dtype=np.float32)

        # CRIB SCORES (new optimized calc)
        min_crib, crib_avg = calc_crib_ranges_exact_and_slow(rank_list, starter_pool, suits_list, discarded_cards, crib_score_cache)
        results.append((
            hand_key,
            crib_key,
            float(scores_np.min()),
            float(scores_np.max()),
            round(float(scores_np.mean()), 2),
            float(min_crib),
            round(float(crib_avg), 2),
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
    for idx, res in enumerate(pool.imap_unordered(process_dealt_hand_exact, args_iter, chunksize=100), 1):
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
            min_crib INTEGER,
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
    table_name = "hand_scores"
    delete_table(table_name, conn)
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

        score = score_hand(list(combo))

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



def get_remaining_cards(full_deck, dealt_hand):    
    return list(set(full_deck) - set(dealt_hand))        


def build_hand_stats_approx_table(full_deck, db_path=DB_PATH, batch_size=5000):

    # doesn't account for the starter card not being in the 6 cards we were dealt
    table_name = "hand_stats_approx"
    conn = sqlite3.connect(db_path)
    delete_table(table_name, conn)

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
            # TODO: this step is incorrect because it changes which card is the starter
            # raise ValueError("This function is incorrect, needs fixing")
            score = score_hand(hand, is_crib=False, starter_card=starter)
            scores.append(score)

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


def delete_table(table_name, conn=None):
    if conn is None:
        db_path = DB_PATH
        conn = sqlite3.connect(db_path)        
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS {}".format(table_name))
    conn.commit()

def build_crib_stats_approx_table(
    full_deck,    
    db_path=DB_PATH,
    batch_size=5000,
):
    # doesn't account for the starter card not being in the 6 cards we were dealt
    table_name = "crib_stats_approx"
    conn = sqlite3.connect(db_path)
    delete_table(table_name, conn)

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
        for opp2 in itertools.combinations(remaining, 2):
            rest = [c for c in remaining if c not in opp2]
            for starter in rest:                
                scores.append(score_hand(crib + list(opp2), is_crib=True, starter_card=starter))

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
    build_hand_stats_approx_table(full_deck, db_path=DB_PATH)
    # build_crib_stats_approx_table(full_deck, db_path=DB_PATH)


    # build_5_card_hand_score_table(full_deck) # done   
    # build_kept_stats_pandas(hand_score_cache) # done
    # hand_score_cache = load_all_5_card_scores(sqlite3.connect(DB_PATH)) # done    
    # done - build_exact_full_hand_stats_pandas(full_deck, hand_score_cache, db_path=DB_PATH, batch_size=5000)


    # build_5_card_crib_score_table(full_deck) # done
    # crib_score_cache = load_all_5_card_crib_scores(sqlite3.connect(DB_PATH)) # done
    # build_crib_stats_approx_table(full_deck, crib_score_cache, db_path=DB_PATH)
    # build_kept_stats_parallel(full_deck, hand_score_cache, n_workers=8)
    # build_crib_stats(full_deck)