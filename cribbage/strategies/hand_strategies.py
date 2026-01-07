import itertools

import numpy as np
import pandas as pd

from cribbage.strategies.crib_strategies import calc_crib_min_only_given_6_cards, calc_crib_ranges_fast_given_6_cards
from cribbage.database import normalize_hand_to_str, normalize_hand_to_tuple
from cribbage.players.rule_based_player import get_full_deck
from cribbage.playingcards import Card, build_hand
from cribbage.scoring import score_hand


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
    # need to check how fast this is, so far might only need this
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

def exact_hand_and_fast_crib(hand, dealer_is_self):
    # won 46/100 times against beginner player
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

def exact_hand_and_min_crib(hand, dealer_is_self, your_score=None, opponent_score=None):
    # don't analyze crib, just calculate min value of the crib and use that
    full_deck = get_full_deck()
    hand_score_cache = {}
    crib_score_cache = {}        
    hand_results = process_dealt_hand_only_exact([hand, full_deck, hand_score_cache])
    df_hand = pd.DataFrame(hand_results, columns=["hand_key","min_hand_score","max_hand_score","avg_hand_score"])
    crib_results = calc_crib_min_only_given_6_cards(hand)
    df_crib = pd.DataFrame(crib_results, columns=["hand_key","crib_key","min_crib_score","avg_crib_score"])
    df3 = pd.merge(df_hand, df_crib, on=["hand_key"])        
    df3["avg_total_score"] = df3["avg_hand_score"] + (df3["avg_crib_score"] if dealer_is_self else -df3["avg_crib_score"])
    df3["min_total_score"] = df3["min_hand_score"] + (df3["min_crib_score"] if dealer_is_self else -df3["min_crib_score"])
    import logging
    logger = logging.getLogger(__name__)
#     logger.info(f"\n {df3[['hand_key', 'max_hand_score',
#    'avg_hand_score', 'min_crib_score', 'avg_crib_score',
#    'avg_total_score']].sort_values(by='avg_total_score', ascending=False)}")
    # think there's a small bug here, your_score and opponent_score are initialized to None instead of 0
    # if your_score is not None and opponent_score is not None:
        # if we are behind, try to maximize avg score
        # if your_score > 90 or opponent_score > 90:
        #     df3 = df3.sort_values(by=["min_total_score", "avg_total_score"], ascending=False)
        #     df4 = df3.loc[df3["min_total_score"] == df3["min_total_score"].max()]
        #     # if len(df4) > 1:
        #     #     logger.info(f"\n {df3[['hand_key', 'crib_key','min_total_score', 'avg_total_score']]}")                
        #     best_discards_str = df4.iloc[0]["crib_key"]            
        # else:
    best_discards_str = df3.loc[df3["avg_total_score"] == df3["avg_total_score"].max()]["crib_key"].values[0]
    # best_discards_str = df3.loc[df3["avg_total_score"] == df3["avg_total_score"].max()]["crib_key"].values[0]
    best_discards = best_discards_str.lower().replace("t", "10").split("|")
    best_discards_cards = build_hand(best_discards)
    return tuple(best_discards_cards)