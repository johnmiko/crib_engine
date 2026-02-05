from cribbage.cribbagegame import CribbageGame
from cribbage.cribbageround import CribbageRound
from cribbage.players.beginner_player import BeginnerPlayer
from cribbage.players.medium_player import MediumPlayer
from cribbage.utils import play_multiple_games, play_game


def test_play_multiple_games_uses_incrementing_seeds():
    p0 = BeginnerPlayer("b0")
    p1 = MediumPlayer("m1")
    seed = 67
    results = play_multiple_games(2, p0, p1, seed=seed)

    s0, s1 = play_game(p0, p1, seed=seed)
    diff0 = s0 - s1
    s0, s1 = play_game(p1, p0, seed=seed + 1)
    diff1 = s1 - s0

    assert results["diffs"] == [diff0, diff1]


def _round_signature(seed: int) -> tuple:
    players = [BeginnerPlayer("b0"), MediumPlayer("m1")]
    game = CribbageGame(players=players, seed=seed, copy_players=False)
    dealer = game.players[0]
    round_ = CribbageRound(game, dealer=dealer, seed=seed)
    round_.setup_deal_phase()
    round_.setup_crib_phase()

    p0_hand = tuple(str(c) for c in round_.hands[game.players[0].name])
    p1_hand = tuple(str(c) for c in round_.hands[game.players[1].name])
    starter = str(round_.starter)
    crib = tuple(str(c) for c in round_.crib)
    return (p0_hand, p1_hand, starter, crib)


def test_round_one_differs_for_next_game_seed():
    sig_a = _round_signature(67)
    sig_b = _round_signature(68)
    assert sig_a != sig_b
