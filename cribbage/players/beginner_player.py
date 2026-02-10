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
        self.description = (
            "Discard - Picks highest scoring hand. "
            "Pegging - Pegs points when possible. Does not use statistics."
        )

    def select_crib_cards(self, player_state, round_state) -> Tuple[Card, Card]:
        return basic_crib_strategy(player_state.hand, player_state.is_dealer)

    def play_pegging(self, playable: List[Card], count: int, history_since_reset: List[Card]) -> Optional[Card]:
        return basic_pegging_strategy(playable, count, history_since_reset)

    def select_card_to_play(self, player_state, round_state) -> Optional[Card]:
        # Get playable cards
        playable_cards = [c for c in player_state.hand if c + round_state.count <= 31]
        if not playable_cards:
            return None
        return self.play_pegging(playable_cards, round_state.count, round_state.table_cards)
