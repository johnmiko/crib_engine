from cribbage.players.base_player import BasePlayer
from cribbage.scoring_old import score_play


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

def basic_crib_strategy(hand: List[Card], dealer_is_self: bool) -> Tuple[Card, Card]:
    # Counts points in hand and then adds/subtracts points in crib to decide
    best_discards: List[Tuple[Card, Card]] = []
    best_score = float("-inf")

    for kept in combinations(hand, 4):  # all 6-choose-4 possible hands
        kept = list(kept)
        starter = kept[0]  # same "neutral starter" hack as before

        # the 2 not in kept are the discards
        discards = [c for c in hand if c not in kept]
        assert len(discards) == 2

        kept_score = score_hand(kept, is_crib=False)
        crib_score = score_hand(discards, is_crib=True)

        # if you want to actually use dealer_is_self:
        score = kept_score + crib_score if dealer_is_self else kept_score - crib_score
        if score > best_score:
            best_score = score
            best_discards = [tuple(discards)]
        elif score == best_score:
            best_discards.append(tuple(discards))

    return best_discards[0]  # type: ignore


class BeginnerPlayer(BasePlayer):
    def __init__(self, name: str = "beginner"):
        self.name = name

    def select_crib_cards(self, hand: List[Card], dealer_is_self: bool) -> Tuple[Card, Card]:
        return basic_crib_strategy(hand, dealer_is_self)

    def play_pegging(self, playable: List[Card], count: int, history_since_reset: List[Card]) -> Optional[Card]:
        return basic_pegging_strategy(playable, count, history_since_reset)

    def select_card_to_play(self, hand: List[Card], table, crib, count: int):
        # table is the list of cards currently on the table
        playable_cards = [c for c in hand if c + count <= 31]
        if not playable_cards:
            return None
        return self.play_pegging(playable_cards, count, table)