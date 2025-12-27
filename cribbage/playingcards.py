import random
from typing import List


SUIT_SYMBOLS = {
    'h': '\u2665',
    'd': '\u2666',
    'c': '\u2663',
    's': '\u2660'
}

suit_name_map = {
    'h': 'hearts',
    'd': 'diamonds',
    'c': 'clubs',
    's': 'spades'
}
rank_name_map = {
    'a': 'ace',    
    '2': 'two',
    '3': 'three',
    '4': 'four',
    '5': 'five',
    '6': 'six',    
    '7': 'seven',    
    '8': 'eight',
    '9': 'nine',    
    '10': 'ten',    
    'j': 'jack',    
    'q': 'queen',
    'k': 'king'}

value_map = {
    'a': 1,
    'j': 10,
    'q': 10,
    'k': 10
}

class Deck:
    RANKS = ['a','2','3','4','5','6','7','8','9','10','j','q','k']
    SUITS = ['h','d','c','s']  # hearts, diamonds, clubs, spades

    def __init__(self, seed: int | None = None):
        self._rng = random.Random(seed)
        self.cards = [Card(f"{r}{s}") for r in self.RANKS for s in self.SUITS]
        self.shuffle()

    def __len__(self):
        return len(self.cards)

    def draw(self):
        return self.cards.pop() if self.cards else None

    def shuffle(self):
        self._rng.shuffle(self.cards)

    def cut(self, cut_point=None):
        len_precut = len(self.cards)
        if cut_point is None:
            cut_point = self._rng.randrange(len(self.cards))
        self.cards = self.cards[cut_point:] + self.cards[:cut_point]
        assert len(self.cards) == len_precut, "Cards lost in cut."

def get_random_hand(num_cards: int = 6, seed: int | None = None):
    deck = Deck(seed=seed)
    hand = []
    for _ in range(num_cards):
        hand.append(deck.draw())
    return hand    

def build_hand(card_str_list: List[str]):
    hand = []
    for card_str in card_str_list:
        hand.append(Card(card_str))
    return hand

class Card:
    def __init__(self, rank_and_suit):
        # Support both single and double character ranks (e.g., '10h')
        if len(rank_and_suit) == 3:
            self.rank = rank_and_suit[:2]
            self.suit = rank_and_suit[2]
        else:
            self.rank = rank_and_suit[0]
            self.suit = rank_and_suit[1]
        if self.rank not in rank_name_map:
            raise ValueError("Card is created with rank then suit, passed in suit first")
        self.value = value_map.get(self.rank.lower(), int(self.rank) if self.rank.isdigit() else None)
        self.tupl = (self.rank, self.suit)
    
    def __add__(self, other):
        if isinstance(other, Card):
            return self.value + other.value # type: ignore        
        return self.value + other        

    def __str__(self):
        return str(self.rank + self.suit)
    
    def pretty(self):
        return self.rank.upper() + SUIT_SYMBOLS[self.suit]

    def __repr__(self):
        return str(self)

    def __lt__(self, other):
        if type(other) == Card:
            return self.rank['value'] < other.rank['value']
        elif type(other) == int:
            return self.rank['value'] < other
        else:
            raise NotImplementedError

    def __gt__(self, other):
        if type(other) == Card:
            return self.rank['value'] > other.rank['value']
        elif type(other) == int:
            return self.rank['value'] > other
        else:
            raise NotImplementedError

    def __eq__(self, other):
        if type(other) == Card:
            # Cards are equal only if both rank and suit match
            return (
                self.rank == other.rank and
                self.suit == other.suit
            )
        elif type(other) == int:
            return self.value == other
        else:
            raise NotImplementedError



    def get_value(self):
        # Return the value of the card (face cards 10, ace 1, others as int)
        return value_map.get(self.rank.lower(), int(self.rank) if self.rank.isdigit() else None)

    def get_suit(self):
        return self.suit

    def get_rank(self):
        return self.rank

    def __hash__(self):
        return hash(self.tupl)
    
    def to_index(self) -> int:
        suit_indices = {suit: idx for idx, suit in enumerate(Deck.SUITS)}
        rank_indices = {rank: idx for idx, rank in enumerate(Deck.RANKS)}
        return suit_indices[self.suit['name']] * 13 + rank_indices[self.rank['name']]
