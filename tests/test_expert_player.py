import json
from pathlib import Path

from cribbage.cribbagegame import CribbageGame
from cribbage.playingcards import Card
from cribbage.players.beginner_player import BeginnerPlayer
from cribbage.players.expert_player import ExpertPlayer
from cribbage.players.ai_player import featurize_pegging, get_pegging_feature_indices


def test_expert_pegging_feature_dim_matches_meta():
    model_dir = Path(__file__).resolve().parent.parent / "cribbage" / "players" / "expert_player"
    meta = json.loads((model_dir / "model_meta.json").read_text(encoding="utf-8"))
    feature_set = meta["pegging_feature_set"]
    expected_dim = int(meta["pegging_feature_dim"])

    hand = [Card("ah"), Card("2h"), Card("3d"), Card("5c")]
    table = [Card("7s"), Card("9d")]
    candidate = hand[0]
    x = featurize_pegging(
        hand=hand,
        table=table,
        count=16,
        candidate=candidate,
        known_cards=None,
        opponent_known_hand=None,
        all_played_cards=None,
        player_score=0,
        opponent_score=0,
        feature_set=feature_set,
    )
    assert x.shape[0] == expected_dim
    idx = get_pegging_feature_indices(feature_set)
    assert idx.shape[0] == expected_dim


def test_expert_player_single_round_does_not_crash():
    expert = ExpertPlayer(name="Expert")
    beginner = BeginnerPlayer(name="Beginner")
    game = CribbageGame(players=[expert, beginner], seed=123, copy_players=False, fast_mode=True)
    scores = game.play_round(seed=123)
    assert isinstance(scores, list)
    assert len(scores) == 2


def test_pegging_does_not_cheat():
    expert = ExpertPlayer(name="Expert")
    beginner = BeginnerPlayer(name="Beginner")
    game = CribbageGame(players=[expert, beginner], seed=123, copy_players=False, fast_mode=True)
    round_scores = game.play_round(seed=123)
    assert len(round_scores) == 2

    last_round = game.history[-1]
    expert_name = expert.name
    opponent = beginner
    opponent_name = opponent.name

    known_cards = last_round.hands[expert_name][:] + last_round.table[:]
    if last_round.starter:
        known_cards.append(last_round.starter)

    opponent_hidden = [
        c for c in last_round.hands[opponent_name]
        if c not in last_round.table
    ]
    assert all(c not in known_cards for c in opponent_hidden)
