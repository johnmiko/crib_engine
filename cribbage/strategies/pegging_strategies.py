
from typing import List, Optional
from cribbage.playingcards import Card, rank_order_map
from cribbage.scoring import score_play


import logging

logger = logging.getLogger(__name__)

def basic_pegging_strategy(playable: List[Card], count: int, history_since_reset: List[Card]) -> Optional[Card]:
    # always take points if available; else play highest card
    best_card_choices = []
    best_pts = 1
    for c in playable:
        sequence = history_since_reset + [c]
        pts = score_play(sequence)
        if (pts >= best_pts) and (c + count <= 31):
            best_pts = pts
            best_card_choices.append(c)
    if best_card_choices:
        good_choices = best_card_choices
    else:
        good_choices = playable    
    # If there is multiple cards that score the same points, play the highest value card
    best_choice = good_choices[0]
    for card_choice in good_choices:
        if card_choice.rank_order > best_choice.rank_order:
            best_choice = card_choice
    return best_choice
