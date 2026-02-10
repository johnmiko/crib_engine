from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

import numpy as np

from cribbage.players.ai_player import (
    AIPlayer,
    featurize_pegging,
    get_pegging_feature_indices,
)
from cribbage.players.hard_player import HardPlayer
from cribbage.playingcards import Card


class PolicyMLP:
    def __init__(self, input_dim: int, hidden_sizes: tuple[int, ...]):
        import torch
        import torch.nn as nn

        layers: list[nn.Module] = []
        prev = int(input_dim)
        for h in hidden_sizes:
            layers.append(nn.Linear(prev, int(h)))
            layers.append(nn.ReLU())
            prev = int(h)
        layers.append(nn.Linear(prev, 1))
        self.model = nn.Sequential(*layers)
        self.input_dim = int(input_dim)
        self.hidden_sizes = tuple(int(h) for h in hidden_sizes)

    def load_state(self, state: dict) -> None:
        self.model.load_state_dict(state["state_dict"])
        self.model.eval()

    def logits(self, X: np.ndarray) -> np.ndarray:
        import torch

        with torch.no_grad():
            t = torch.tensor(X, dtype=torch.float32)
            return self.model(t).squeeze(1).cpu().numpy()


class ExpertPlayer(AIPlayer, HardPlayer):
    """Hard discard strategy + PPO pegging policy."""

    def __init__(self, name: str = "expert", model_dir: Path | None = None):
        HardPlayer.__init__(self, name=name)
        self.description = "Hard discard + PPO pegging policy. Beats beginner 68% of the time"

        if model_dir is None:
            model_dir = Path(__file__).resolve().parent / "expert_player"
        meta_path = model_dir / "model_meta.json"
        if not meta_path.exists():
            raise FileNotFoundError(f"Missing model metadata: {meta_path}")
        meta = json.loads(meta_path.read_text(encoding="utf-8"))

        self.pegging_feature_set = meta.get("pegging_feature_set", "full")
        self.pegging_feature_indices = get_pegging_feature_indices(self.pegging_feature_set)

        policy_file = meta.get("pegging_model_file", "pegging_policy.pt")
        policy_path = model_dir / policy_file
        if not policy_path.exists():
            raise FileNotFoundError(f"Missing pegging policy: {policy_path}")

        import torch

        state = torch.load(str(policy_path), map_location="cpu")
        input_dim = int(state["input_dim"])
        hidden_sizes = tuple(int(h) for h in state["hidden_sizes"])
        self.pegging_policy = PolicyMLP(input_dim, hidden_sizes)
        self.pegging_policy.load_state(state)

    def select_crib_cards(self, player_state, round_state):
        return HardPlayer.select_crib_cards(self, player_state, round_state)

    def play_pegging(self, playable: List[Card], count: int, history_since_reset: List[Card]) -> Optional[Card]:
        if not playable:
            return None
        logits = []
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
            logits.append(x)
        X = np.stack(logits, axis=0)
        scores = self.pegging_policy.logits(X)
        best_idx = int(np.argmax(scores))
        return playable[best_idx]

    def select_card_to_play(self, player_state, round_state) -> Optional[Card]:
        playable_cards = [c for c in player_state.hand if c + round_state.count <= 31]
        if not playable_cards:
            return None
        logits = []
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
            logits.append(x)
        X = np.stack(logits, axis=0)
        scores = self.pegging_policy.logits(X)
        best_idx = int(np.argmax(scores))
        return playable_cards[best_idx]
