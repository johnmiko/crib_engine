from typing import List, Tuple, Optional
import random
from logging import getLogger
from cribbage.players.base_player import BasePlayer
from cribbage.playingcards import Card

logger = getLogger(__name__)

class PlayFirstCardPlayer(BasePlayer):
    def __init__(self, name: str = "play first card", seed: int | None = None):
        super().__init__(name=name)
        self.name = name
        self.description = "Discards first 2 cards in hand. Plays first card in hand"

    def select_crib_cards(self, player_state, round_state) -> Tuple[Card, Card]:
        return tuple(player_state.hand[:2])  # type: ignore

    def play_pegging(self, playable: List[Card], count: int, history_since_reset: List[Card]) -> Optional[Card]:
        return playable[0] if playable else None
    
    def select_card_to_play(self, player_state, round_state) -> Optional[Card]:
        # Get playable cards
        playable_cards = [c for c in player_state.hand if c + round_state.count <= 31]
        if not playable_cards:
            return None
        return self.play_pegging(playable_cards, round_state.count, round_state.table_cards)