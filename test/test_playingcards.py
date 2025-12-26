import unittest
from cribbage.playingcards import Card, Deck


class TestCardClass(unittest.TestCase):
    def setUp(self):
        rank_ace = Deck.RANKS['ace']
        rank_two = Deck.RANKS['two']
        self.card = Card(rank=Deck.RANKS['ace'], suit=Deck.SUITS['hearts'])
        self.acecard = Card(rank=rank_ace, suit=Deck.SUITS['hearts'])
        self.twocard = Card(rank=rank_two, suit=Deck.SUITS['hearts'])

    def test_to_str(self):
        self.assertEqual(str(self.card), 'A\u2665')

    def test_lt(self):
        self.assertEqual(self.twocard < self.acecard, False)
        self.assertEqual(self.acecard < self.twocard, True)
        self.assertEqual(self.acecard < self.acecard, False)
        self.assertEqual(self.twocard < 3, True)
        self.assertEqual(self.twocard < 2, False)
        self.assertEqual(self.twocard < -2, False)

    def test_gt(self):
        self.assertEqual(self.twocard > self.acecard, True)
        self.assertEqual(self.acecard > self.twocard, False)
        self.assertEqual(self.acecard > self.acecard, False)
        self.assertEqual(self.twocard > 3, False)
        self.assertEqual(self.twocard > 2, False)
        self.assertEqual(self.twocard > -2, True)

    def test_eq(self):
        self.assertEqual(self.twocard == self.acecard, False)
        self.assertEqual(self.acecard == self.twocard, False)
        self.assertEqual(self.acecard == self.acecard, True)
        self.assertEqual(self.twocard == 3, False)
        self.assertEqual(self.twocard == 2, True)
        self.assertEqual(self.twocard == -2, False)

    def test_add(self):
        self.assertEqual(self.twocard + self.acecard, 3)
        self.assertEqual(self.acecard + self.twocard, 3)
        self.assertEqual(self.acecard + self.acecard, 2)
        self.assertEqual(self.twocard + self.twocard, 4)
        self.assertEqual(self.twocard + 3, 5)


class TestDeckClass(unittest.TestCase):
    def setUp(self):
        self.deck = Deck()

    def test_deck_size(self):
        self.assertEqual(len(self.deck.cards), 52)

    def test_to_str(self):
        self.assertEqual(str(self.deck),
                         'A\u2665 2\u2665 3\u2665 4\u2665 5\u2665 6\u2665 7\u2665 8\u2665 9\u2665 10\u2665 J\u2665 Q\u2665 K\u2665 '
                         'A\u2666 2\u2666 3\u2666 4\u2666 5\u2666 6\u2666 7\u2666 8\u2666 9\u2666 10\u2666 J\u2666 Q\u2666 K\u2666 '
                         'A\u2663 2\u2663 3\u2663 4\u2663 5\u2663 6\u2663 7\u2663 8\u2663 9\u2663 10\u2663 J\u2663 Q\u2663 K\u2663 '
                         'A\u2660 2\u2660 3\u2660 4\u2660 5\u2660 6\u2660 7\u2660 8\u2660 9\u2660 10\u2660 J\u2660 Q\u2660 K\u2660 ')

    def test_shuffle(self):
        preshuffle = str(self.deck.cards)
        self.assertEqual(preshuffle, str(self.deck.cards))
        self.deck.shuffle()
        self.assertNotEqual(preshuffle, str(self.deck.cards))


if __name__ == '__main__':
    unittest.main()
