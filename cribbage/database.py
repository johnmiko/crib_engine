from cribbage.playingcards import Card

RANK_ORDER = {r: i for i, r in enumerate("A23456789TJQK")}
SUIT_ORDER = {s: i for i, s in enumerate("CDHS")}

def card_to_code(card):
    rank = card.rank.upper()
    if rank == "10":
        rank = "T"
    suit = card.suit.upper()
    return f"{rank}{suit}"


def normalize_hand_to_str(cards):
    codes = [card_to_code(c) for c in cards]
    codes.sort(key=lambda c: (RANK_ORDER[c[0]], SUIT_ORDER[c[1]]))
    return "|".join(codes)

def normalize_hand_to_tuple(cards):
    codes = [card_to_code(c) for c in cards]
    codes.sort(key=lambda c: (RANK_ORDER[c[0]], SUIT_ORDER[c[1]]))
    return tuple(codes)