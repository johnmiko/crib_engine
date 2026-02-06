from __future__ import annotations

import json
from pathlib import Path
from itertools import combinations
from typing import List, Optional, Tuple

import numpy as np

from cribbage.playingcards import Card
from cribbage.players.beginner_player import BeginnerPlayer
from cribbage.players.rule_based_player import get_full_deck
from cribbage.scoring import HasPairTripleQuad, HasStraight_DuringPlay
from cribbage.cribbagegame import score_play

RANKS = ["a", "2", "3", "4", "5", "6", "7", "8", "9", "10", "j", "q", "k"]
RANK_TO_I = {r: i for i, r in enumerate(RANKS)}
TENS_RANKS = {"10", "j", "q", "k"}

# Base discard features (52 discards + 52 kept + 1 dealer flag)
BASE_DISCARD_FEATURE_DIM = 105

# Engineered discard features count:
# 13 kept rank counts + 13 discard rank counts +
# 2 value sums + 2 tens counts + 2 fives counts +
# 3 kept pair/trip/quad + 3 discard pair/trip/quad +
# 3 run counts (3/4/5) + 1 run max +
# 2 flush flags (kept/discard) + 1 nobs + 2 fifteen counts +
# 2 scores + 1 score margin + 3 endgame flags
ENGINEERED_DISCARD_NO_SCORE_DIM = 47
ENGINEERED_DISCARD_SCORE_DIM = 6
ENGINEERED_DISCARD_FEATURE_DIM = ENGINEERED_DISCARD_NO_SCORE_DIM + ENGINEERED_DISCARD_SCORE_DIM
DISCARD_FEATURE_DIM = BASE_DISCARD_FEATURE_DIM + ENGINEERED_DISCARD_FEATURE_DIM

# Pegging features
PEGGING_BASE_FEATURE_DIM = 240  # hand(52) + table(52) + count(32) + candidate(52) + known(52)
PEGGING_ENGINEERED_NO_SCORE_DIM = 20
PEGGING_ENGINEERED_SCORE_DIM = 5
PEGGING_ENGINEERED_FEATURE_DIM = PEGGING_ENGINEERED_NO_SCORE_DIM + PEGGING_ENGINEERED_SCORE_DIM
PEGGING_FULL_FEATURE_DIM = PEGGING_BASE_FEATURE_DIM + 52 + 52 + PEGGING_ENGINEERED_FEATURE_DIM  # + opp_played + all_played


def get_discard_feature_indices(feature_set: str) -> np.ndarray:
    if feature_set == "base":
        return np.arange(BASE_DISCARD_FEATURE_DIM, dtype=np.int64)
    if feature_set == "engineered_no_scores":
        end = BASE_DISCARD_FEATURE_DIM + ENGINEERED_DISCARD_NO_SCORE_DIM
        return np.arange(end, dtype=np.int64)
    if feature_set == "full":
        return np.arange(DISCARD_FEATURE_DIM, dtype=np.int64)
    raise ValueError(f"Unknown discard feature_set: {feature_set}")


def get_pegging_feature_indices(feature_set: str) -> np.ndarray:
    if feature_set == "base":
        return np.arange(PEGGING_BASE_FEATURE_DIM, dtype=np.int64)
    if feature_set == "full_no_scores":
        end = PEGGING_BASE_FEATURE_DIM + 52 + 52 + PEGGING_ENGINEERED_NO_SCORE_DIM
        return np.arange(end, dtype=np.int64)
    if feature_set == "full":
        return np.arange(PEGGING_FULL_FEATURE_DIM, dtype=np.int64)
    raise ValueError(f"Unknown pegging feature_set: {feature_set}")


def multi_hot_cards(cards: List[Card]) -> np.ndarray:
    v = np.zeros(52, dtype=np.float32)
    for c in cards:
        v[c.to_index()] = 1.0
    return v


def _rank_counts(cards: List[Card]) -> np.ndarray:
    counts = np.zeros(13, dtype=np.float32)
    for c in cards:
        counts[RANK_TO_I[c.get_rank().lower()]] += 1.0
    return counts


def _value_sum(cards: List[Card]) -> float:
    return float(sum(c.get_value() for c in cards))


def _count_tens(cards: List[Card]) -> float:
    return float(sum(1 for c in cards if c.get_rank().lower() in TENS_RANKS))


def _count_fives(cards: List[Card]) -> float:
    return float(sum(1 for c in cards if c.get_rank().lower() == "5"))


def _pair_trip_quad_counts(cards: List[Card]) -> Tuple[float, float, float]:
    counts = _rank_counts(cards)
    pair_count = float(np.sum(counts * (counts - 1.0) / 2.0))
    trip_count = float(np.sum(counts * (counts - 1.0) * (counts - 2.0) / 6.0))
    quad_count = float(np.sum(counts * (counts - 1.0) * (counts - 2.0) * (counts - 3.0) / 24.0))
    return pair_count, trip_count, quad_count


def _run_counts(cards: List[Card]) -> Tuple[float, float, float, float]:
    counts = _rank_counts(cards)
    run3 = 0.0
    run4 = 0.0
    run5 = 0.0
    run_max = 0.0
    for start in range(0, 13):
        if start + 3 <= 13:
            c = counts[start:start + 3]
            if np.all(c > 0):
                run3 += float(np.prod(c))
                run_max = max(run_max, 3.0)
        if start + 4 <= 13:
            c = counts[start:start + 4]
            if np.all(c > 0):
                run4 += float(np.prod(c))
                run_max = max(run_max, 4.0)
        if start + 5 <= 13:
            c = counts[start:start + 5]
            if np.all(c > 0):
                run5 += float(np.prod(c))
                run_max = max(run_max, 5.0)
    return run3, run4, run5, run_max


def _count_fifteens(cards: List[Card]) -> float:
    values = [c.get_value() for c in cards]
    total = 0
    for r in range(2, len(values) + 1):
        for combo in combinations(values, r):
            if sum(combo) == 15:
                total += 1
    return float(total)


def _all_same_suit(cards: List[Card]) -> float:
    if not cards:
        return 0.0
    suit = cards[0].get_suit()
    return 1.0 if all(c.get_suit() == suit for c in cards) else 0.0


def _has_nobs(cards: List[Card]) -> float:
    return 1.0 if any(c.get_rank().lower() == "j" for c in cards) else 0.0


def _score_context_features(player_score: int | None, opponent_score: int | None) -> np.ndarray:
    if player_score is None:
        player_score = 0
    if opponent_score is None:
        opponent_score = 0
    score_margin = float(player_score - opponent_score)
    endgame_self = 1.0 if player_score >= 110 else 0.0
    endgame_opp = 1.0 if opponent_score >= 110 else 0.0
    endgame_any = 1.0 if max(player_score, opponent_score) >= 110 else 0.0
    return np.array(
        [
            float(player_score),
            float(opponent_score),
            score_margin,
            endgame_self,
            endgame_opp,
            endgame_any,
        ],
        dtype=np.float32,
    )


def featurize_discard(
    kept: List[Card],
    discards: List[Card],
    dealer_is_self: bool,
    player_score: int | None = None,
    opponent_score: int | None = None,
) -> np.ndarray:
    disc_vec = multi_hot_cards(discards)
    kept_vec = multi_hot_cards(kept)
    dealer_vec = np.array([1.0 if dealer_is_self else 0.0], dtype=np.float32)

    score_context = _score_context_features(player_score, opponent_score)

    engineered = np.concatenate(
        [
            _rank_counts(kept),
            _rank_counts(discards),
            np.array([_value_sum(kept)], dtype=np.float32),
            np.array([_value_sum(discards)], dtype=np.float32),
            np.array([_count_tens(kept)], dtype=np.float32),
            np.array([_count_tens(discards)], dtype=np.float32),
            np.array([_count_fives(kept)], dtype=np.float32),
            np.array([_count_fives(discards)], dtype=np.float32),
            np.array(_pair_trip_quad_counts(kept), dtype=np.float32),
            np.array(_pair_trip_quad_counts(discards), dtype=np.float32),
            np.array(_run_counts(kept), dtype=np.float32),
            np.array([_all_same_suit(kept)], dtype=np.float32),
            np.array([_all_same_suit(discards)], dtype=np.float32),
            np.array([_has_nobs(kept)], dtype=np.float32),
            np.array([_count_fifteens(kept)], dtype=np.float32),
            np.array([_count_fifteens(discards)], dtype=np.float32),
            score_context,
        ]
    )

    out = np.concatenate([disc_vec, kept_vec, dealer_vec, engineered])
    assert out.shape[0] == DISCARD_FEATURE_DIM, f"discard features dim {out.shape[0]} != {DISCARD_FEATURE_DIM}"
    return out


def one_hot_count(count: int) -> np.ndarray:
    v = np.zeros(32, dtype=np.float32)
    if 0 <= count < 32:
        v[count] = 1.0
    return v


def featurize_pegging(
    hand: List[Card],
    table: List[Card],
    count: int,
    candidate: Card,
    known_cards: List[Card] = None,
    opponent_known_hand: List[Card] = None,
    all_played_cards: List[Card] = None,
    player_score: int | None = None,
    opponent_score: int | None = None,
    feature_set: str = "full_no_scores",
) -> np.ndarray:
    if known_cards is None:
        known_cards = []
    if opponent_known_hand is None:
        opponent_known_hand = []
    if all_played_cards is None:
        all_played_cards = []
    if player_score is None:
        player_score = 0
    if opponent_score is None:
        opponent_score = 0

    hand_vec = multi_hot_cards(hand)
    table_vec = multi_hot_cards(table)
    count_vec = one_hot_count(count)
    known_vec = multi_hot_cards(known_cards)
    opp_played_vec = multi_hot_cards(opponent_known_hand)
    all_played_vec = multi_hot_cards(all_played_cards)

    cand_vec = np.zeros(52, dtype=np.float32)
    cand_vec[candidate.to_index()] = 1.0

    new_count = count + candidate.get_value()
    remaining_to_31 = 31 - new_count
    makes_15 = 1.0 if new_count == 15 else 0.0
    makes_31 = 1.0 if new_count == 31 else 0.0

    seq_after = table + [candidate]
    immediate_points = float(score_play(seq_after)[0])
    pair_points = float(HasPairTripleQuad().check(seq_after)[0])
    run_length = float(HasStraight_DuringPlay().check(seq_after)[0])

    run_setup_gap1 = 0.0
    run_setup_gap2 = 0.0
    run_setup_any = 0.0
    opponent_pair_setup = 0.0

    if len(seq_after) >= 1:
        last_rank = seq_after[-1].get_rank().lower()
        same_rank_card = Card(f"{last_rank}h")
        if new_count + same_rank_card.get_value() <= 31:
            opponent_pair_setup = 1.0

    if len(seq_after) >= 2:
        r1 = RANK_TO_I[seq_after[-1].get_rank().lower()] + 1
        r2 = RANK_TO_I[seq_after[-2].get_rank().lower()] + 1
        gap = abs(r1 - r2)
        if gap == 1:
            candidates = []
            low = min(r1, r2) - 1
            high = max(r1, r2) + 1
            if 1 <= low <= 13:
                candidates.append(low)
            if 1 <= high <= 13:
                candidates.append(high)
            for rv in candidates:
                rank_str = RANKS[rv - 1]
                c = Card(f"{rank_str}h")
                if new_count + c.get_value() <= 31:
                    run_setup_gap1 += 1.0
        elif gap == 2:
            mid = min(r1, r2) + 1
            rank_str = RANKS[mid - 1]
            c = Card(f"{rank_str}h")
            if new_count + c.get_value() <= 31:
                run_setup_gap2 = 1.0

    for rv in range(1, 14):
        rank_str = RANKS[rv - 1]
        c = Card(f"{rank_str}h")
        if new_count + c.get_value() > 31:
            continue
        run_len = HasStraight_DuringPlay().check(seq_after + [c])[0]
        if run_len >= 3:
            run_setup_any += 1.0

    our_hand_count = float(len(hand))
    opp_hand_count_est = float(max(0, 4 - len(opponent_known_hand)))
    table_len = float(len(table))
    opp_played_count = float(len(opponent_known_hand))
    known_cards_count = float(len(known_cards))

    full_deck = get_full_deck()
    known_set = set(known_cards) | set(all_played_cards) | set(hand)
    unseen = [c for c in full_deck if c not in known_set]
    playable_unseen = [c for c in unseen if c.get_value() <= remaining_to_31]
    opp_can_play_prob = float(len(playable_unseen) / max(1, len(unseen)))
    opp_playable_count = float(len(playable_unseen))
    unseen_count = float(len(unseen))

    score_context = _score_context_features(player_score, opponent_score)

    engineered = np.array(
        [
            float(new_count),
            float(remaining_to_31),
            makes_15,
            makes_31,
            immediate_points,
            pair_points,
            run_length,
            run_setup_gap1,
            run_setup_gap2,
            run_setup_any,
            opponent_pair_setup,
            our_hand_count,
            opp_hand_count_est,
            table_len,
            opp_played_count,
            known_cards_count,
            opp_can_play_prob,
            opp_playable_count,
            unseen_count,
        ],
        dtype=np.float32,
    )
    engineered = np.concatenate([engineered, score_context])

    base = np.concatenate([hand_vec, table_vec, count_vec, cand_vec, known_vec])
    if feature_set == "basic":
        assert base.shape[0] == PEGGING_BASE_FEATURE_DIM, f"pegging features dim {base.shape[0]} != {PEGGING_BASE_FEATURE_DIM}"
        return base
    if feature_set == "full_no_scores":
        engineered_no_scores = engineered[:PEGGING_ENGINEERED_NO_SCORE_DIM]
        out = np.concatenate([base, opp_played_vec, all_played_vec, engineered_no_scores])
        expected = PEGGING_BASE_FEATURE_DIM + 52 + 52 + PEGGING_ENGINEERED_NO_SCORE_DIM
        assert out.shape[0] == expected, f"pegging features dim {out.shape[0]} != {expected}"
        return out
    if feature_set == "full":
        out = np.concatenate([base, opp_played_vec, all_played_vec, engineered])
        assert out.shape[0] == PEGGING_FULL_FEATURE_DIM, f"pegging features dim {out.shape[0]} != {PEGGING_FULL_FEATURE_DIM}"
        return out
    raise ValueError(f"Unknown pegging feature_set: {feature_set}")


class MLPValueModel:
    def __init__(self, path: Path):
        import torch

        data = torch.load(str(path), map_location="cpu")
        self.input_dim = int(data["input_dim"])
        self.hidden_sizes = tuple(int(h) for h in data["hidden_sizes"])
        layers = []
        prev = self.input_dim
        for h in self.hidden_sizes:
            layers.append(torch.nn.Linear(prev, h))
            layers.append(torch.nn.ReLU())
            prev = h
        layers.append(torch.nn.Linear(prev, 1))
        self.model = torch.nn.Sequential(*layers)
        self.model.load_state_dict(data["state_dict"])
        self.model.eval()

    def predict(self, x: np.ndarray) -> float:
        import torch

        with torch.no_grad():
            t = torch.tensor(x, dtype=torch.float32).unsqueeze(0)
            y = self.model(t).squeeze(0).squeeze(0).item()
        return float(y)


class AIPlayer(BeginnerPlayer):
    def __init__(self, name: str = "ai"):
        super().__init__(name=name)
        self.description = (
            "Picks highest model-predicted hand and pegging value using learned value models."
        )
        model_dir = Path(__file__).resolve().parent / "hard_model"
        meta_path = model_dir / "model_meta.json"
        if not meta_path.exists():
            raise FileNotFoundError(f"Missing model metadata: {meta_path}")
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        self.discard_feature_set = meta.get("discard_feature_set", "engineered_no_scores")
        self.pegging_feature_set = meta.get("pegging_feature_set", "full_no_scores")
        self.discard_feature_indices = get_discard_feature_indices(self.discard_feature_set)
        self.pegging_feature_indices = get_pegging_feature_indices(self.pegging_feature_set)
        self.discard_model = MLPValueModel(model_dir / "discard_mlp.pt")
        self.pegging_model = MLPValueModel(model_dir / "pegging_mlp.pt")

    def select_crib_cards(self, player_state, round_state) -> Tuple[Card, Card]:
        hand = player_state.hand
        dealer_is_self = player_state.is_dealer
        best, best_v = None, float("-inf")
        for kept in combinations(hand, 4):
            kept = list(kept)
            discards = [c for c in hand if c not in kept]
            x = featurize_discard(
                kept,
                discards,
                dealer_is_self,
                player_score=player_state.score,
                opponent_score=player_state.opponent_score,
            )
            x = x[self.discard_feature_indices]
            v = self.discard_model.predict(x)
            if v > best_v:
                best_v, best = v, tuple(discards)
        return best

    def play_pegging(self, playable: List[Card], count: int, history_since_reset: List[Card]) -> Optional[Card]:
        if not playable:
            return None
        best, best_v = None, float("-inf")
        for card in playable:
            x = featurize_pegging(
                hand=playable,
                table=history_since_reset,
                count=count,
                candidate=card,
                known_cards=None,
                opponent_known_hand=None,
                all_played_cards=None,
                player_score=None,
                opponent_score=None,
                feature_set=self.pegging_feature_set,
            )
            x = x[self.pegging_feature_indices]
            v = self.pegging_model.predict(x)
            if v > best_v:
                best_v, best = v, card
        return best

    def select_card_to_play(self, player_state, round_state) -> Optional[Card]:
        playable_cards = [c for c in player_state.hand if c + round_state.count <= 31]
        if not playable_cards:
            return None
        best, best_v = None, float("-inf")
        for card in playable_cards:
            x = featurize_pegging(
                hand=player_state.hand,
                table=round_state.table_cards,
                count=round_state.count,
                candidate=card,
                known_cards=player_state.known_cards,
                opponent_known_hand=player_state.opponent_known_hand,
                all_played_cards=round_state.all_played_cards,
                player_score=player_state.score,
                opponent_score=player_state.opponent_score,
                feature_set=self.pegging_feature_set,
            )
            x = x[self.pegging_feature_indices]
            v = self.pegging_model.predict(x)
            if v > best_v:
                best_v, best = v, card
        return best
