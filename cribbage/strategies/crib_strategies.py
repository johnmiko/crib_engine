
from collections import defaultdict
import itertools
import math
from cribbage.database import normalize_hand_to_str, normalize_hand_to_tuple
from cribbage.players.rule_based_player import get_full_deck
from cribbage.scoring import score_hand
from itertools import combinations
from typing import List, Tuple
from cribbage.playingcards import Card
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def basic_crib_strategy(hand: List[Card], dealer_is_self: bool) -> Tuple[Card, Card]:
    """
    For each 4 cards, calculate the score of keeping them then +/- the score of discarding the other 2 into the crib    
    """
    best_discards: List[Tuple[Card, Card]] = []
    best_score = float("-inf")
    df = pd.DataFrame(columns=["kept", "discarded", "kept_score", "crib_score", "total_score"])    

    for kept in combinations(hand, 4):  # all 6-choose-4 possible hands
        kept = list(kept)

        # the 2 not in kept are the discards
        discards = [c for c in hand if c not in kept]
        assert len(discards) == 2

        kept_score = score_hand(kept, is_crib=False)
        crib_score = score_hand(discards, is_crib=True)

        # if you want to actually use dealer_is_self:
        score = kept_score + crib_score if dealer_is_self else kept_score - crib_score
        df_new = pd.DataFrame({"kept": [kept],
                "discarded": [discards],
                "kept_score": [kept_score],
                "crib_score": [crib_score],
                "total_score": [score]
                })
        df = pd.concat([df, df_new], ignore_index=True)
        if score > best_score:
            best_score = score
            best_discards = [tuple(discards)]
        elif score == best_score:
            best_discards.append(tuple(discards))

    df = df.sort_values(by="total_score", ascending=False)
    logger.debug("Beginner player discard logic\n" + df.to_string())
    return best_discards[0]  # type: ignore


def calc_crib_ranges_exact_and_slow(rank_list, starter_pool, suits_list, discarded_cards, crib_score_cache):
    """
    Calculate expected crib score by considering all possible opponent discards and starters.
    We need to average over all possible suit combinations for each rank partition.
    """
    # Build mapping of which suits are available for each rank
    rank_to_cards = {r: [] for r in rank_list}
    for c in starter_pool:
        rank_to_cards[c.rank].append(c)

    # Total ways = C(46, 2) * 44 for choosing 2 opponent discards and 1 starter
    total_ways = math.comb(len(starter_pool), 2) * (len(starter_pool) - 2)
    total_score_sum = 0.0
    min_crib = float('inf')

    for ri1 in range(13):
        for ri2 in range(ri1, 13):
            for ri3 in range(ri2, 13):
                r1, r2, r3 = rank_list[ri1], rank_list[ri2], rank_list[ri3]
                cards_r1 = rank_to_cards[r1]
                cards_r2 = rank_to_cards[r2]
                cards_r3 = rank_to_cards[r3]
                
                n1 = len(cards_r1)
                n2 = len(cards_r2)
                n3 = len(cards_r3)

                # Need to partition (r1, r2, r3) into "2 for opponent + 1 for starter"
                # Each partition has different number of ways and potentially different score
                
                partitions = []  # List of (opp_rank_indices, starter_rank_index)
                
                if r1 == r2 == r3:
                    # All same rank: opp gets (r1, r1), starter is r1
                    if n1 >= 3:
                        # Enumerate all specific card combinations
                        for i in range(n1):
                            for j in range(i+1, n1):
                                for k in range(n1):
                                    if k != i and k != j:
                                        partitions.append((
                                            [cards_r1[i], cards_r1[j]], 
                                            cards_r1[k]
                                        ))
                        
                elif r1 == r2 != r3:
                    # Two r1, one r3
                    # Partition A: opp gets (r1, r1), starter is r3
                    if n1 >= 2 and n3 >= 1:
                        for i in range(n1):
                            for j in range(i+1, n1):
                                for k in range(n3):
                                    partitions.append((
                                        [cards_r1[i], cards_r1[j]], 
                                        cards_r3[k]
                                    ))
                    # Partition B: opp gets (r1, r3), starter is r1
                    if n1 >= 2 and n3 >= 1:
                        for i in range(n1):
                            for j in range(n3):
                                for k in range(n1):
                                    if k != i:
                                        partitions.append((
                                            [cards_r1[i], cards_r3[j]], 
                                            cards_r1[k]
                                        ))
                        
                elif r2 == r3 != r1:
                    # One r1, two r2
                    # Partition A: opp gets (r2, r2), starter is r1
                    if n2 >= 2 and n1 >= 1:
                        for i in range(n2):
                            for j in range(i+1, n2):
                                for k in range(n1):
                                    partitions.append((
                                        [cards_r2[i], cards_r2[j]], 
                                        cards_r1[k]
                                    ))
                    # Partition B: opp gets (r1, r2), starter is r2
                    if n1 >= 1 and n2 >= 2:
                        for i in range(n1):
                            for j in range(n2):
                                for k in range(n2):
                                    if k != j:
                                        partitions.append((
                                            [cards_r1[i], cards_r2[j]], 
                                            cards_r2[k]
                                        ))
                        
                else:
                    # All different ranks
                    if n1 >= 1 and n2 >= 1 and n3 >= 1:
                        # Partition A: opp gets (r1, r2), starter is r3
                        for i in range(n1):
                            for j in range(n2):
                                for k in range(n3):
                                    partitions.append((
                                        [cards_r1[i], cards_r2[j]], 
                                        cards_r3[k]
                                    ))
                        # Partition B: opp gets (r1, r3), starter is r2
                        for i in range(n1):
                            for j in range(n3):
                                for k in range(n2):
                                    partitions.append((
                                        [cards_r1[i], cards_r3[j]], 
                                        cards_r2[k]
                                    ))
                        # Partition C: opp gets (r2, r3), starter is r1
                        for i in range(n2):
                            for j in range(n3):
                                for k in range(n1):
                                    partitions.append((
                                        [cards_r2[i], cards_r3[j]], 
                                        cards_r1[k]
                                    ))

                # Process each partition (now with specific cards/suits)
                for opp_cards, starter_card in partitions:
                    crib_hand = list(discarded_cards) + opp_cards
                    
                    # Score the crib with the starter
                    dummy_tuple = normalize_hand_to_tuple(crib_hand + [starter_card])
                    score = crib_score_cache.get(dummy_tuple, None)
                    if score is None:
                        score = score_hand(crib_hand, is_crib=True, starter_card=starter_card)
                        # update_table(hand_key, crib_key, None, score, conn)
                    
                    total_score_sum += score
                    min_crib = min(min_crib, score)

    crib_avg = 0.0
    if total_ways > 0:
        crib_avg = total_score_sum / total_ways
    return min_crib, crib_avg

def calc_crib_ranges_almost_exact(rank_list, starter_pool, suits_list, discarded_cards, crib_score_cache):
    """
    Exact takes about 13 seconds
    Almost exact takes about 8 seconds and is within +/- 0.03 points
    """
    # Build mapping of available cards by rank  
    rank_to_cards = {r: [] for r in rank_list}
    for c in starter_pool:
        rank_to_cards[c.rank].append(c)

    # Check properties of discarded cards
    disc_suits = [c.suit for c in discarded_cards]
    disc_ranks = [c.rank for c in discarded_cards]
    
    # Total ways = C(46, 2) * 44 for choosing 2 opponent discards and 1 starter
    total_ways = math.comb(len(starter_pool), 2) * (len(starter_pool) - 2)
    total_score_sum = 0.0
    min_crib = float('inf')

    for ri1 in range(13):
        for ri2 in range(ri1, 13):
            for ri3 in range(ri2, 13):
                r1, r2, r3 = rank_list[ri1], rank_list[ri2], rank_list[ri3]
                cards_r1 = rank_to_cards[r1]
                cards_r2 = rank_to_cards[r2]
                cards_r3 = rank_to_cards[r3]
                
                n1 = len(cards_r1)
                n2 = len(cards_r2)
                n3 = len(cards_r3)

                # Build partitions with specific cards, but group by suit patterns
                # to avoid redundant scoring
                partitions = []  # List of (opp_cards_list, starter_card_list, weight)
                
                if r1 == r2 == r3:
                    # All same rank
                    if n1 >= 3:
                        # Group by suit patterns instead of enumerating all combinations
                        for i in range(n1):
                            for j in range(i+1, n1):
                                # For this pair of opponent cards, check all starters
                                for k in range(n1):
                                    if k != i and k != j:
                                        partitions.append((
                                            [cards_r1[i], cards_r1[j]], 
                                            cards_r1[k],
                                            1  # Each specific combination has weight 1
                                        ))
                        
                elif r1 == r2 != r3:
                    # Two r1, one r3
                    if n1 >= 2 and n3 >= 1:
                        # Partition A: opp gets (r1, r1), starter is r3
                        for i in range(n1):
                            for j in range(i+1, n1):
                                for k in range(n3):
                                    partitions.append((
                                        [cards_r1[i], cards_r1[j]], 
                                        cards_r3[k],
                                        1
                                    ))
                        # Partition B: opp gets (r1, r3), starter is r1
                        for i in range(n1):
                            for j in range(n3):
                                for k in range(n1):
                                    if k != i:
                                        partitions.append((
                                            [cards_r1[i], cards_r3[j]], 
                                            cards_r1[k],
                                            1
                                        ))
                        
                elif r2 == r3 != r1:
                    # One r1, two r2
                    if n2 >= 2 and n1 >= 1:
                        # Partition A: opp gets (r2, r2), starter is r1
                        for i in range(n2):
                            for j in range(i+1, n2):
                                for k in range(n1):
                                    partitions.append((
                                        [cards_r2[i], cards_r2[j]], 
                                        cards_r1[k],
                                        1
                                    ))
                        # Partition B: opp gets (r1, r2), starter is r2
                        for i in range(n1):
                            for j in range(n2):
                                for k in range(n2):
                                    if k != j:
                                        partitions.append((
                                            [cards_r1[i], cards_r2[j]], 
                                            cards_r2[k],
                                            1
                                        ))
                        
                else:
                    # All different ranks - this is where we can optimize most
                    if n1 >= 1 and n2 >= 1 and n3 >= 1:
                        # For all-different ranks, group by suit patterns
                        # Partition A: opp gets (r1, r2), starter is r3
                        for i in range(n1):
                            for j in range(n2):
                                for k in range(n3):
                                    partitions.append((
                                        [cards_r1[i], cards_r2[j]], 
                                        cards_r3[k],
                                        1
                                    ))
                        # Partition B: opp gets (r1, r3), starter is r2
                        for i in range(n1):
                            for j in range(n3):
                                for k in range(n2):
                                    partitions.append((
                                        [cards_r1[i], cards_r3[j]], 
                                        cards_r2[k],
                                        1
                                    ))
                        # Partition C: opp gets (r2, r3), starter is r1
                        for i in range(n2):
                            for j in range(n3):
                                for k in range(n1):
                                    partitions.append((
                                        [cards_r2[i], cards_r3[j]], 
                                        cards_r1[k],
                                        1
                                    ))

                # Process each partition
                for opp_cards, starter_card, weight in partitions:
                    crib_hand = list(discarded_cards) + opp_cards
                    
                    # Score the crib with the starter
                    dummy_tuple = normalize_hand_to_tuple(crib_hand + [starter_card])
                    score = crib_score_cache.get(dummy_tuple, None)
                    if score is None:
                        score = score_hand(crib_hand, is_crib=True, starter_card=starter_card)
                        crib_score_cache[dummy_tuple] = score
                    
                    total_score_sum += score * weight
                    min_crib = min(min_crib, score)

    crib_avg = 0.0
    if total_ways > 0:
        crib_avg = total_score_sum / total_ways
    return min_crib, crib_avg


def calc_crib_ranges_fast(starter_pool, discarded_cards, crib_score_cache):
    """
    Exact takes about 13 seconds
    Almost exact takes about 8 seconds and is within +/- 0.03 points
    """
    # Build mapping of available cards by rank  
    rank_list = ['a', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'j', 'q', 'k']
    suits_list = ['c', 'd', 'h', 's']
    rank_to_cards = {r: [] for r in rank_list}
    for c in starter_pool:
        rank_to_cards[c.rank].append(c)

    # Check properties of discarded cards
    disc_suits = [c.suit for c in discarded_cards]
    disc_ranks = [c.rank for c in discarded_cards]
    
    # Total ways = C(46, 2) * 44 for choosing 2 opponent discards and 1 starter
    total_ways = math.comb(len(starter_pool), 2) * (len(starter_pool) - 2)
    total_score_sum = 0.0
    min_crib = float('inf')
    scores = []

    for ri1 in range(13):
        for ri2 in range(ri1, 13):
            for ri3 in range(ri2, 13):
                r1, r2, r3 = rank_list[ri1], rank_list[ri2], rank_list[ri3]
                # cards_r1 = rank_to_cards[r1]
                # cards_r2 = rank_to_cards[r2]
                # cards_r3 = rank_to_cards[r3]              
                                

                # Process each partition
                opp_cards = [Card(r1 + "c"), Card(r2 + "d"), Card(r3 + "h")]
                # dummy_tuple = normalize_hand_to_tuple(crib_hand + [starter_card])
                # score = crib_score_cache.get(dummy_tuple, None)
                score = None
                if score is None:
                    score = score_hand(discarded_cards + opp_cards, is_crib=True)                                    
                scores.append(score)
    crib_avg = 0.0    
    crib_avg = sum(scores) / len(scores) if scores else 0.0
    min_crib = score_hand(discarded_cards, is_crib=True)
    return min_crib, crib_avg

def calc_crib_ranges_fast_given_6_cards(dealt_hand):        
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
        min_crib, crib_avg = calc_crib_ranges_fast(starter_pool, discarded_cards, crib_score_cache)
        results.append((
            hand_key,
            crib_key,
            float(min_crib),
            round(float(crib_avg), 2),
        ))
    return results

def calc_crib_min_only_given_6_cards(dealt_hand):        
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
        kept_hand = [dealt_hand[i] for i in range(6) if i not in discard_idx]
        discarded_cards = [dealt_hand[i] for i in discard_idx]

        hand_key = normalize_hand_to_str(kept_hand)
        crib_key = normalize_hand_to_str(discarded_cards)
        # starter cannot be any of the discarded cards
        min_crib = score_hand(discarded_cards, is_crib=True)
        avg_crib = min_crib
        if "j" in crib_key.lower():
            avg_crib += 0.25
        results.append((
            hand_key,
            crib_key,
            float(min_crib),
            float(avg_crib),
        ))
    return results