from cribbage.cribbagegame import CribbageGame
from cribbage.cribbageround import CribbageRound
from cribbage.players.play_first_card_player import PlayFirstCardPlayer
import pytest

from cribbage.players.random_player import RandomPlayer
from cribbage.playingcards import Card, build_hand
from logging import getLogger

logger = getLogger(__name__)

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
    assert round1.table == round2.table, "Tables should be the same for same seed"
    assert round1.most_recent_player.name == round2.most_recent_player.name, f"most recent player not the same after round {round1.most_recent_player} vs {round2.most_recent_player}" # type: ignore
    assert [hand for hand in round1.player_hand_after_discard.values()] == [hand for hand in round2.player_hand_after_discard.values()], "Player hands after discard should be the same for same seed"
    game1_score = [game1.board.get_score(p) for p in [p0, p1]]
    game2_score = [game2.board.get_score(p) for p in [p0, p1]]
    logger.debug(f"Game1 score: {game1_score}, Game2 score: {game2_score}")
    logger.debug(str(round1))
    assert game1_score == [11,11]
    assert game2_score == [11, 11]
    assert game1_score == game2_score, "Game scores should be the same for same seed"

def test_cribbage_round_is_exactly_repeatable_with_play_first_card_player_and_set_seed():
    # test potentially redundant
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
    assert game1_score == [11, 11]
    assert game2_score == [11, 11]
    assert game1_score == game2_score, "Game scores should be the same for same seed"

def test_cribbage_round_scores_and_pegs_are_correct():
    # manually checking a round of crib, that it's scored correctly and pegs correctly
    p0 = PlayFirstCardPlayer(name="Player1")
    p1 = PlayFirstCardPlayer(name="Player2")
    game1 = CribbageGame(players=[p0, p1], seed=123)
    round1 = CribbageRound(game=game1, dealer=p0, seed=123)
    round1.hands = {
        p0.name: build_hand(['ah','2h','5h', '5d', '5s', '5c']),
        p1.name: build_hand(['3h','4h','jc', 'jd', 'jh', 'js'])
    }
    round1.play()
    round1.starter = Card("qc")
    game1_score = [game1.board.get_score(p) for p in [p0, p1]]
    assert round1.table == build_hand(["jc", "5h", "jd", "5d", "5s", "jh", "5c", "js"])
    assert round1.crib == build_hand(["ah", "2h", "3h", "4h"])    
    logger.debug(round1)
    assert game1_score == [39, 16]


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
    assert game1_score == [11, 4]
    assert game2_score == [11, 4]
    assert game1_score == game2_score, "Game scores should be the same for same seed"

def test_cribbage_round_1_and_2_are_different_when_game_is_seeded():
    # can't assign same player instances to different games otherwise their RNG state gets messed up
    game1 = CribbageGame(players=[RandomPlayer(name="Random1", seed=42), RandomPlayer(name="Random2", seed=42)], seed=123)
    round1 = CribbageRound(game=game1, dealer=game1.players[0], seed=game1._rng.randint(0, 2**32 - 1))        
    round1.play()
    logger.info(f"round1.table: {round1.table}")
    round1_score = [game1.board.get_score(p) for p in game1.players]
    round2 = CribbageRound(game=game1, dealer=game1.players[0],seed=game1._rng.randint(0, 2**32 - 1))
    round2.play()
    round2_score = [game1.board.get_score(p) for p in game1.players]
    logger.info(f"round2.table: {round2.table}")
    round1_hand_values = [hand for hand in round1.player_hand_after_discard.values()]
    round2_hand_values = [hand for hand in round2.player_hand_after_discard.values()]
    assert round1_hand_values == ([build_hand(["4c", "qd", "9c", "2s"]), build_hand(["jc", "3d", "7s", "qs"])])
    assert round2_hand_values == ([build_hand(["6d", "7h", "ah", "kd"]), build_hand(["9h", "8c", "4h", "5d"])])
    assert round1_hand_values != round2_hand_values    
    assert round1_score == [14, 5]
    assert round2_score == [24, 8]
    for round1_player_score, round2_player_score in zip(round1_score, round2_score):
        assert round2_player_score > round1_player_score

def test_play_round_works_as_expected():
    game1 = CribbageGame(players=[RandomPlayer(name="Random1", seed=42), RandomPlayer(name="Random2", seed=42)], seed=123)        
    game1.play_round()
    logger.info(game1.history[0])
    assert game1.round_scores == [[13, 8]], str(game1.history[0])
    game1.play_round()
    assert game1.round_scores == [[13, 8], [19, 21]], str(game1.history[1])
