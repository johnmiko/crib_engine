from typing import List, Tuple, Optional
import random
from logging import getLogger
from cribbage.players.base_player import BasePlayer
from cribbage.playingcards import Card

logger = getLogger(__name__)

class RandomPlayer(BasePlayer):
    def __init__(self, name: str = "random", seed: int | None = None):
        super().__init__(name=name)
        self.name = name
        self.seed = seed
        self._rng = random.Random(seed)
        self.description = "Plays randomly"
    
    def reset_rng(self):
        self._rng = random.Random(self.seed)

    def select_crib_cards(self, player_state, round_state) -> Tuple[Card, Card]:        
        return tuple(self._rng.sample(player_state.hand, 2))  # type: ignore

    def play_pegging(self, playable: List[Card], count: int, history_since_reset: List[Card]) -> Optional[Card]:
        return self._rng.choice(playable) if playable else None

    def select_card_to_play(self, player_state, round_state) -> Optional[Card]:
        # Get playable cards
        playable_cards = [c for c in player_state.hand if c + round_state.count <= 31]
        if not playable_cards:
            return None
        return self.play_pegging(playable_cards, round_state.count, round_state.table_cards)
