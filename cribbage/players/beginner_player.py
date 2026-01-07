from typing import List, Optional, Tuple
from cribbage.strategies.crib_strategies import basic_crib_strategy
from cribbage.strategies.pegging_strategies import basic_pegging_strategy
from cribbage.players.base_player import BasePlayer
from cribbage.playingcards import Card
from cribbage.scoring import score_play, score_hand
from itertools import combinations

import logging

logger = logging.getLogger(__name__)



class BeginnerPlayer(BasePlayer):
    def __init__(self, name: str = "beginner"):
        self.name = name

    def select_crib_cards(self, hand: List[Card], dealer_is_self: bool, your_score=None, opponent_score=None) -> Tuple[Card, Card]:
        return basic_crib_strategy(hand, dealer_is_self)

    def play_pegging(self, playable: List[Card], count: int, history_since_reset: List[Card]) -> Optional[Card]:
        return basic_pegging_strategy(playable, count, history_since_reset)

    def select_card_to_play(self, hand: List[Card], table, count: int, crib=None):
        # table is the list of cards currently on the table
        playable_cards = [c for c in hand if c + count <= 31]
        if not playable_cards:
            return None
        return self.play_pegging(playable_cards, count, table)