import unittest
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

class TestDeckClass(unittest.TestCase):
    def setUp(self):
        self.deck = Deck()

    def test_deck_size(self):
        self.assertEqual(len(self.deck.cards), 52)

    def test_shuffle(self):
        preshuffle = str(self.deck.cards)
        self.assertEqual(preshuffle, str(self.deck.cards))
        self.deck.shuffle()
        self.assertNotEqual(preshuffle, str(self.deck.cards))

def test_card_creation_invalid():    
    try:
        card = Card(Deck.SUITS['hearts'], Deck.RANKS['ace'])  # Incorrect order
    except ValueError as e:
        assert str(e) == "Card is created with rank then suit, passed in suit first"
    else:
        assert False, "ValueError not raised for invalid card creation"

if __name__ == '__main__':
    unittest.main()
