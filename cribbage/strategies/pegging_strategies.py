
from typing import List, Optional
from cribbage.playingcards import Card, rank_order_map
from cribbage.scoring import score_play


import logging

logger = logging.getLogger(__name__)

def get_highest_rank_card(cards: List[Card]) -> Card:
    highest_rank_card = cards[0]
    for card_choice in cards:
        if card_choice.rank_order > highest_rank_card.rank_order:
            highest_rank_card = card_choice
    return highest_rank_card

def basic_pegging_strategy(playable: List[Card], count: int, history_since_reset: List[Card]) -> Optional[Card]:
    # always take points if available; else play highest card
    best_card_choices = []
    best_pts = 1
    for c in playable:
        sequence = history_since_reset + [c]
        pts, _ = score_play(sequence)  # Unpack tuple (score, description)
        if (pts >= best_pts) and (c + count <= 31):
            best_pts = pts
            best_card_choices.append(c)
    if best_card_choices:
        good_choices = best_card_choices
    else:
        good_choices = playable    
    # If there is multiple cards that score the same points, play the highest value card
    best_choice = get_highest_rank_card(good_choices)
    return best_choice

def medium_pegging_strategy(playable: List[Card], count: int, history_since_reset: List[Card]) -> Optional[Card]:
    """
    play card that pegs the most points
    if not, more complicated scoring
    if card sets count to 
      1-4 = -0.05 points (safe but wasteful for scoring last card or 31) = 0
      5 = (likely to have a 10) 4/13 * -2 = -8/13 = -0.615
      6-14 = -1/13 = -0.077
      16-20 = give positive score of 0.1 points (safe)
      21 = (likely to have a 10) = -0.615
      do not set opponent up for a run = -0.5, 2/13 * -3 = -6/13 = -0.462
      else play highest card
    does not account for
        have a pair, play first card of pair if getting a triple is under 31
        likely cards opponent has based on what they have already played
        because opponent is going to keep cards that score points
        example, if they play a 5, they are more likely to have a 10 and/or 4,6
        if they play 3 cards that are the same suit, they likely have a flush
    """
    # First priority: find cards that score points
    best_card_choices = []
    best_pts = 1
    for c in playable:
        if c.get_value() + count > 31:
            continue  # Skip cards that would bust
        sequence = history_since_reset + [c]
        pts, _ = score_play(sequence)  # Unpack tuple (score, description)
        if pts >= best_pts:
            if pts > best_pts:
                best_pts = pts
                best_card_choices = [c]
            else:
                best_card_choices.append(c)
    
    if best_card_choices:
        # If we have scoring options, pick the highest-value card among them
        return get_highest_rank_card(best_card_choices)
    
    best_card_choice = set_self_up_for_points(playable, count, history_since_reset)
    if best_card_choice:
        return best_card_choice

    # No scoring available, use strategic scoring system
    card_scores = []
    
    for c in playable:
        if c.get_value() + count > 31:
            continue  # Skip cards that would bust
        
        new_count = count + c.get_value()
        score = 0.0
        
        # Count-based scoring (probability-based)
        if 1 <= new_count <= 4:
            score -= 0.05  # Safe but wasteful for scoring last card or 31
        elif new_count == 5:
            score -= 0.615  # 4/13 * -2 = -8/13 (likely opponent has 10)
        elif 6 <= new_count <= 14:
            score -= 0.077  # -1/13 (slightly unsafe)
        elif new_count == 15:
            score += 2.0  # This scores points, but shouldn't reach here
        elif 16 <= new_count <= 20:
            score += 0.1  # Safe
        elif new_count == 21:
            score -= 0.615  # Same as 5 (likely opponent has 10)
        if count == 0 and c.get_value() == 10:
            # Not sure what the exact probability is but we should not play a 10 first if possible
            score -= 0.1
        
        # Check if this sets up a run for opponent
        if len(history_since_reset) > 0:
            if _sets_up_run(history_since_reset, c):
                # opponent has approx 2/13 chance of having the needed card to score 3 points
                score -= 0.462  # 2/13 * -3 = -6/13
        
        # Add card value as tiebreaker (prefer higher cards when equal)
        # score += c.rank_order * 0.01
        
        card_scores.append((c, score))
    
    if not card_scores:
        return None  # No playable cards
    
    # Return card with highest score
    card_scores.sort(key=lambda x: x[1], reverse=True)
    max_points = max(v for _, v in card_scores)
    highest_scoring_cards_list = [k for k, v in card_scores if v == max_points]
    highest_scoring_card = get_highest_rank_card(highest_scoring_cards_list)
    return highest_scoring_card


def _sets_up_run(history: List[Card], new_card: Card) -> bool:
    """
    Check if playing this card sets up opponent for a run.
    A run is set up if the last 1-2 cards + new card form consecutive ranks.
    Does not account for single value run cards (if opponent plays 7 and we play 5, they can play 6 for run)
    """
    if not history:
        return False
    
    # Check last card + new card
    last_card = history[-1]
    rank_diff = abs(new_card.rank_order - last_card.rank_order)
    
    # If consecutive (diff of 1), it sets up a potential run
    if rank_diff == 1:
        return True
    
    # If we have at least 2 cards in history, check if new card + last 2 could be a run
    if len(history) >= 2:
        second_last = history[-2]
        ranks = sorted([second_last.rank_order, last_card.rank_order, new_card.rank_order])
        # Check if they form consecutive sequence
        if ranks[1] - ranks[0] == 1 and ranks[2] - ranks[1] == 1:
            return True
    
    return False

def set_self_up_for_points(playable, count, history_since_reset):
    """
    Try to set self up for future points when starting a new sequence (count == 0).
    Returns the card to play, or None if no strategic setup is found.
    """
    # Only apply this strategy when starting a new sequence
    if count != 0:
        return None
    
    # Group cards by rank to find pairs/triples
    rank_groups = {}
    for card in playable:
        rank = card.rank_order
        if rank not in rank_groups:
            rank_groups[rank] = []
        rank_groups[rank].append(card)
    
    # Priority 1: Pairs/triples of rank 1-9 (play one to set up for triple)
    for rank, cards in rank_groups.items():
        if len(cards) >= 2 and rank <= 9:
            return cards[0]
    
    # Priority 2: Specific rank combinations to set up 15s or pairs
    playable_ranks = set(c.rank_order for c in playable)
    
    # If we have 2 and 3, play 3 (opponent plays 10 → we play 2 for 15)
    if 2 in playable_ranks and 3 in playable_ranks:
        return next(c for c in playable if c.rank_order == 3)
    
    # If we have A (1) and 4, play 4 (opponent plays 10 → we play A for 15)
    if 1 in playable_ranks and 4 in playable_ranks:
        return next(c for c in playable if c.rank_order == 4)
    
    # If we have 7 and 8, play 8 (opponent plays 7 → we pair for 2)
    if 7 in playable_ranks and 8 in playable_ranks:
        return next(c for c in playable if c.rank_order == 8)
    
    # If we have 6 and 9, play 6 (opponent plays 9 → we pair for 2)
    if 6 in playable_ranks and 9 in playable_ranks:
        return next(c for c in playable if c.rank_order == 6)
    
    if 5 in playable_ranks and ((10 in playable_ranks) or (11 in playable_ranks) or (12 in playable_ranks) or (13 in playable_ranks)):
        return next(c for c in playable if c.rank_order > 9)
    
    # Priority 3: Pairs/triples of rank 10+ (play one to set up for triple)
    for rank, cards in rank_groups.items():
        if len(cards) >= 2 and rank >= 10:
            return cards[0]
    
    # No strategic play found
    return None    