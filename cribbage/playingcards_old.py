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


# class CardFactory:
#     # Create a card factory to more lazily create cards in tests    
#     @staticmethod
#     def create_hand_from_strs(card_strs: List[str]):
#         return [CardFactory.create_from_str(s) for s in card_strs]     
    
#     @staticmethod
#     def create_from_str(card_str: str):
#         if len(card_str) != 2:
#             raise ValueError(f"Card string needs to be 2 characters: {card_str}")
#         rank_shorthand = card_str[0]
#         suit_letter = card_str[1]
#         return CardFactory.create(rank_shorthand, suit_letter)

#     @staticmethod
#     def create(rank_shorthand: str, suit_letter: str):
#         rank = Deck.RANKS[rank_name_map[rank_shorthand.lower()]]
#         suit = Deck.SUITS[suit_name_map[suit_letter.lower()]]
#         return Card(rank, suit)

    

def build_hand(card_str_list: List[str]):
    hand = []
    for card_str in card_str_list:
        hand.append(Card(card_str))
    return hand

class Card:
    def __init__(self, rank_and_suit):
        self.rank = rank_and_suit[0]
        self.suit = rank_and_suit[1]
        # Need the if statement or else int(self.rank) fails on face cards
        self.value = value_map.get(self.rank.lower(),int(self.rank) if self.rank.isdigit() else None)
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
        print(self)
        print(self.rank)
        return self.rank['value']

    def get_suit(self):
        return self.suit['name']

    def get_rank(self):
        return self.rank['name']

    def __hash__(self):
        return hash(self.tupl)
    
    def to_index(self) -> int:
        suit_indices = {suit: idx for idx, suit in enumerate(Deck.SUITS)}
        rank_indices = {rank: idx for idx, rank in enumerate(Deck.RANKS)}
        return suit_indices[self.suit['name']] * 13 + rank_indices[self.rank['name']]
