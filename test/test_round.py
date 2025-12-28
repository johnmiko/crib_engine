from cribbage.cribbagegame import CribbageGame, CribbageRound
from cribbage.players.play_first_card_player import PlayFirstCardPlayer
import pytest

from cribbage.players.random_player import RandomPlayer
from cribbage.playingcards import Card

@pytest.fixture
def game_and_cribround():
        players = [RandomPlayer("Player1"), RandomPlayer("Player2")]
        game = CribbageGame(players=players)
        cribround = CribbageRound(game, dealer=game.players[0])
        return game, cribround

class TestCribbagecribround():    
    def test_get_crib(self, game_and_cribround):
        game, cribround = game_and_cribround
        cribround._deal()
        cribround._populate_crib()

    def test_cut(self, game_and_cribround):
        game, cribround = game_and_cribround
        cribround._cut()

    def test_get_table_value(self, game_and_cribround):
        game, cribround = game_and_cribround
        cribround.table = []
        total = cribround.get_table_value(0)
        assert total == 0
        cribround.table = [Card('7h')]
        total = cribround.get_table_value(0)
        assert total == 7

def test_cribbage_game_is_exactly_repeatable():
    p0 = PlayFirstCardPlayer(name="Player1")
    p1 = PlayFirstCardPlayer(name="Player2")
    game1 = CribbageGame(players=[p0, p1], seed=123)
    peg_dif1 = game1.start()
    game2 = CribbageGame(players=[p0, p1], seed=123)
    peg_dif2 = game2.start()
    assert peg_dif1 == peg_dif2