
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