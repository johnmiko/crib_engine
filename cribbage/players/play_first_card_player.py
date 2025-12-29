from typing import List, Tuple, Optional
import random
from logging import getLogger
from cribbage.players.base_player import BasePlayer
from cribbage.playingcards import Card

logger = getLogger(__name__)

class PlayFirstCardPlayer(BasePlayer):
    def __init__(self, name: str = "play first card", seed: int | None = None):
        self.name = name

    def select_crib_cards(self, hand: List[Card], dealer_is_self: bool) -> Tuple[Card, Card]:
        return tuple(hand[:2])  # type: ignore

    def play_pegging(self, playable: List[Card], count: int, history_since_reset: List[Card]) -> Optional[Card]:
        return playable[0] if playable else None
    
    def select_card_to_play(self, hand: List[Card], table, crib, count: int):
        # table is the list of cards currently on the table
        playable_cards = [c for c in hand if c + count <= 31]
        if not playable_cards:
            return None
        return self.play_pegging(playable_cards, count, table)
