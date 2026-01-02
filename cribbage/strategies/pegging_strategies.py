
from typing import List, Optional
from cribbage.playingcards import Card
from cribbage.scoring import score_play


import logging

logger = logging.getLogger(__name__)

def basic_pegging_strategy(playable: List[Card], count: int, history_since_reset: List[Card]) -> Optional[Card]:
    # always take points if available; else play highest card
    best = None
    best_pts = -1
    for c in playable:
        sequence = history_since_reset + [c]
        pts = score_play(sequence)
        if (pts > best_pts) and (c + count <= 31):
            best_pts = pts
            best = c
    if best is not None:
        return best
    # otherwise play highest value        
    highest_card = playable[0]
    for c in playable:
        if c > highest_card:
            highest_card = c
    return highest_card
