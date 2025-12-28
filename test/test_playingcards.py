import unittest

from pytest import raises
from cribbage.playingcards import Card, Deck


def test_face_cards_are_created_correctly():    
    card = Card('ah')
    assert card.rank == 'a'
    assert card.suit == 'h'
    assert card.value == 1
    card = Card('jd')
    assert card.rank == 'j'
    assert card.suit == 'd'
    assert card.value == 10
    card = Card('qs')
    assert card.rank == 'q'
    assert card.suit == 's'
    assert card.value == 10
    card = Card('ks')
    assert card.rank == 'k'
    assert card.suit == 's'
    assert card.value == 10

def test_cards_add_correctly():
    card1 = Card('5h')
    card2 = Card('7d')
    assert card1 + card2 == 12
    assert card1 + 3 == 8

def test_default_deck_is_random():
    deck1 = Deck()
    deck2 = Deck()
    assert deck1.cards != deck2.cards
    deck1 = Deck(seed=42)
    deck2 = Deck(seed=43)
    assert deck1.cards != deck2.cards

def test_seeded_deck_is_deterministic():
    deck1 = Deck(seed=42)
    deck2 = Deck(seed=42)
    deck1_pre_shuffle = deck1.cards.copy()
    assert deck1.cards == deck2.cards
    deck1.cut()
    deck2.cut()
    assert deck1.cards == deck2.cards
    deck1.shuffle()
    deck2.shuffle()
    assert deck1.cards == deck2.cards
    assert deck1.cards != deck1_pre_shuffle


def test_card_creation_invalid():    
    with raises(ValueError) as context:
        Card("h5")  # Incorrect order
    assert str(context.value) == "Card is created with rank then suit, passed in suit first"


if __name__ == '__main__':
    unittest.main()
