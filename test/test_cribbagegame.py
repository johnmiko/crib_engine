import unittest

import pytest

from cribbage import cribbagegame
from cribbage.player import RandomPlayer
from cribbage.playingcards import Card, Deck


class TestCribbageBoard(unittest.TestCase):
    def setUp(self):
        self.players = [RandomPlayer("Player1"), RandomPlayer("Player2")]
        self.board = cribbagegame.CribbageBoard(players=self.players, max_score=121)

    def test_peg(self):
        self.board.peg(self.players[0], 100)
        self.assertEqual(self.board.pegs[self.players[0]]['front'], 100)
        self.assertEqual(self.board.pegs[self.players[0]]['rear'], 0)

    def test_peg_leapfrog(self):
        self.board.peg(self.players[0], 100)
        self.board.peg(self.players[0], 5)
        self.assertEqual(self.board.pegs[self.players[0]]['front'], 105)
        self.assertEqual(self.board.pegs[self.players[0]]['rear'], 100)


@pytest.fixture
def setUp():
        players = [RandomPlayer("Player1"), RandomPlayer("Player2")]
        game = cribbagegame.CribbageGame(players=players)
        round = cribbagegame.CribbageRound(game, dealer=game.players[0])
        return game, round

class TestCribbageRound():    
    def test_get_crib(self, setUp):
        game, round = setUp
        round._deal()
        round._populate_crib()

    def test_cut(self, setUp):
        game, round = setUp
        round._cut()

    def test_get_table_value(self, setUp):
        game, round = setUp
        round.table = []
        total = round.get_table_value(0)
        assert total == 0
        round.table = [Card(Deck.RANKS['seven'], Deck.SUITS['hearts'])]
        total = round.get_table_value(0)
        assert total == 7



if __name__ == '__main__':
    unittest.main()
