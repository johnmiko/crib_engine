import unittest

import pytest

from cribbage import cribbagegame
from cribbage.players.play_first_card_player import PlayFirstCardPlayer
from cribbage.players.random_player import RandomPlayer
from cribbage.playingcards import Card, Deck




def test_cribbage_game_is_exactly_repeatable():
    p0 = PlayFirstCardPlayer(name="Player1")
    p1 = PlayFirstCardPlayer(name="Player2")
    game1 = cribbagegame.CribbageGame(players=[p0, p1], seed=123)
    peg_dif1 = game1.start()
    game2 = cribbagegame.CribbageGame(players=[p0, p1], seed=123)
    peg_dif2 = game2.start()
    assert peg_dif1 == peg_dif2