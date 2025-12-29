from cribbage.cribbagegame import CribbageGame, CribbageRound
from cribbage.players.play_first_card_player import PlayFirstCardPlayer
import pytest

from cribbage.players.random_player import RandomPlayer
from cribbage.playingcards import Card, build_hand

@pytest.fixture
def game_and_cribround():
        players = [RandomPlayer("Player1"), RandomPlayer("Player2")]
        game = CribbageGame(players=players)
        cribround = CribbageRound(game, dealer=game.players[0])
        return game, cribround

class TestCribRound():    
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

def test_cribbage_round_attributes_are_the_same_with_set_seed():
    p0 = PlayFirstCardPlayer(name="Player1")
    p1 = PlayFirstCardPlayer(name="Player2")
    game1 = CribbageGame(players=[p0, p1], seed=123)
    game2 = CribbageGame(players=[p0, p1], seed=123)
    round1 = CribbageRound(game=game1, dealer=p0, seed=123)
    round2 = CribbageRound(game=game2, dealer=p0, seed=123) 
    assert round1.deck.cards == round2.deck.cards, "Decks should be the same for same seed"
    assert [hand for hand in round1.hands.values()] == [hand for hand in round2.hands.values()], "Hands should be the same for same seed"
    assert round1.crib == round2.crib, "Cribs should be the same for same seed" 
    assert round1.dealer == round2.dealer, "Dealers should be the same for same seed"
    assert round1.most_recent_player == round2.most_recent_player, "Most recent players should be the same for same seed"
    assert [hand for hand in round1.player_hand_after_discard.values()] == [hand for hand in round2.player_hand_after_discard.values()], "Player hands after discard should be the same for same seed"
    round1.play()
    round2.play()
    assert round1.deck.cards == round2.deck.cards, "Decks should be the same for same seed"
    assert [hand for hand in round1.hands.values()] == [hand for hand in round2.hands.values()], "Hands should be the same for same seed"
    assert round1.crib == round2.crib, "Cribs should be the same for same seed" 
    assert round1.dealer == round2.dealer, "Dealers should be the same for same seed"
    assert round1.most_recent_player == round2.most_recent_player, "Most recent players should be the same for same seed"
    assert [hand for hand in round1.player_hand_after_discard.values()] == [hand for hand in round2.player_hand_after_discard.values()], "Player hands after discard should be the same for same seed"
    game1_score = [game1.board.get_score(p) for p in [p0, p1]]
    game2_score = [game2.board.get_score(p) for p in [p0, p1]]
    assert game1_score == [21, 18]
    assert game2_score == [21, 18]
    assert game1_score == game2_score, "Game scores should be the same for same seed"

def test_cribbage_round_is_exactly_repeatable_with_play_first_card_player_and_set_seed():
    p0 = PlayFirstCardPlayer(name="Player1")
    p1 = PlayFirstCardPlayer(name="Player2")
    game1 = CribbageGame(players=[p0, p1], seed=123)
    game2 = CribbageGame(players=[p0, p1], seed=123)
    round1 = CribbageRound(game=game1, dealer=p0, seed=123)
    round2 = CribbageRound(game=game2, dealer=p0, seed=123)    
    round1.play()
    round2.play()
    game1_score = [game1.board.get_score(p) for p in [p0, p1]]
    game2_score = [game2.board.get_score(p) for p in [p0, p1]]
    assert game1_score == [21, 18]
    assert game2_score == [21, 18]
    assert game1_score == game2_score, "Game scores should be the same for same seed"


def test_cribbage_round_is_exactly_repeatable_with_random_player_and_set_seed():
    # can't assign same player instances to different games otherwise their RNG state gets messed up
    game1 = CribbageGame(players=[RandomPlayer(name="Random1", seed=42), RandomPlayer(name="Random2", seed=42)], seed=123)
    game2 = CribbageGame(players=[RandomPlayer(name="Random1", seed=42), RandomPlayer(name="Random2", seed=42)], seed=123)    
    round1 = CribbageRound(game=game1, dealer=game1.players[0], seed=123)
    round2 = CribbageRound(game=game2, dealer=game2.players[0], seed=123)
    # round1.set_up_round_and_deal_cards()
    # round2.set_up_round_and_deal_cards()
    round1.play()
    round2.play()
    # {Random1: [kc, 6h, 4h, 7s], Random2: [6c, 4d, 2h, 2d]}
    # assert round1.hands.values() == dict_values([[kc, 6h, 4h, 7s], [6c, 4d, 2h, 2d]])
    round1_hand_values = [hand for hand in round1.player_hand_after_discard.values()]
    round2_hand_values = [hand for hand in round2.player_hand_after_discard.values()]
    assert round1_hand_values == ([build_hand(["kc", "6h", "4h", "7s"]), build_hand(["6c", "4d", "2h", "2d"])])
    assert round2_hand_values == ([build_hand(["kc", "6h", "4h", "7s"]), build_hand(["6c", "4d", "2h", "2d"])])
    assert round1_hand_values == round2_hand_values
    game1_score = [game1.board.get_score(p) for p in game1.players]
    game2_score = [game2.board.get_score(p) for p in game2.players]
    assert game1_score == [16, 14]
    assert game2_score == [16, 14]
    assert game1_score == game2_score, "Game scores should be the same for same seed"