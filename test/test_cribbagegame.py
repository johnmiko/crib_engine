import unittest

import pytest

from cribbage import cribbagegame
from cribbage.players.play_first_card_player import PlayFirstCardPlayer
from cribbage.players.random_player import RandomPlayer
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



if __name__ == '__main__':
    unittest.main()
