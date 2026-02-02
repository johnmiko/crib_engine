import sys
from pathlib import Path
import pandas as pd
from cribbage.state import PlayerState, RoundState
from typing import List

# look in this directory first when importing modules
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
pd.set_option("display.width", None)


def make_player_state(hand: List, is_dealer: bool = False, score: int = 0, known_cards: List = None, opponent_known_hand: List = None):
    """Helper to create PlayerState for tests."""
    return PlayerState(
        hand=hand,
        score=score,
        is_dealer=is_dealer,
        known_cards=known_cards if known_cards is not None else [],
        opponent_known_hand=opponent_known_hand if opponent_known_hand is not None else []
    )


def make_round_state(starter_card=None, count: int = 0, table_cards: List = None, all_played_cards: List = None, crib: List = None, dealer_name: str = "dealer"):
    """Helper to create RoundState for tests."""
    return RoundState(
        starter_card=starter_card,
        count=count,
        table_cards=table_cards if table_cards is not None else [],
        all_played_cards=all_played_cards if all_played_cards is not None else [],
        crib=crib if crib is not None else [],
        dealer_name=dealer_name
    )