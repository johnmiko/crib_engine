"""Training game variants that can isolate discard-only or pegging-only play."""

from __future__ import annotations

from cribbage.cribbagegame import CribbageGame
from cribbage.cribbageround import CribbageRound, IllegalCardChoiceError


class TrainingRound(CribbageRound):
    def __init__(self, game, dealer, seed: int | None = None, fast_mode: bool = False, training_mode: str = "full"):
        super().__init__(game, dealer=dealer, seed=seed, fast_mode=fast_mode)
        self.training_mode = training_mode

    def _play_pegging(self) -> None:
        loser = None
        active_players = [self.nondealer, self.dealer]
        players_said_go = []
        any_player_has_at_least_1_card = any(len(hand) > 0 for hand in self.hands.values())
        while any_player_has_at_least_1_card and self.game_winner is None:
            sequence_start_idx = len(self.table)
            while any_player_has_at_least_1_card and self.game_winner is None:
                players_to_check = list(active_players)
                for player in players_to_check:
                    if player in players_said_go:
                        continue

                    player_state = self._build_player_state(player, sequence_start_idx)
                    round_state = self._build_round_state(sequence_start_idx)
                    card = player.select_card_to_play(player_state, round_state)

                    if card is None or card.get_value() + round_state.count > 31:
                        self._record_non_scoring_event(player, "Go", card=None, sequence_start_idx=sequence_start_idx)
                        loser = loser if loser else player
                        players_said_go.append(player)
                    else:
                        self._record_non_scoring_event(
                            player,
                            f"Plays {str(card)}",
                            card=card,
                            sequence_start_idx=sequence_start_idx,
                        )
                        self.table.append(card)

                        if self.get_table_value(sequence_start_idx) == 31:
                            winner = self._record_and_peg(player, 1, "31 for 1", card=None, sequence_start_idx=sequence_start_idx)
                            if winner is not None:
                                self.game_winner = winner
                                return

                        self.most_recent_player = player
                        self.hands[player.name].remove(card)
                        sequence = self.table[sequence_start_idx:]
                        score, description = self._score_play(sequence)
                        if score:
                            winner = self._record_and_peg(player, score, description, card=None, sequence_start_idx=sequence_start_idx)
                            if winner is not None:
                                self.game_winner = winner
                                return

                    if self.game_winner is None:
                        if len(players_said_go) == 2:
                            players_to_check = self.go_or_31_reached(players_said_go, self.table[sequence_start_idx:])
                            players_said_go = []
                            sequence_start_idx = len(self.table)
                        any_player_has_at_least_1_card = any(len(hand) > 0 for hand in self.hands.values())
                        if not any_player_has_at_least_1_card:
                            self.game_winner = self._record_and_peg(player, 1, "Last card for 1", card=None, sequence_start_idx=0)
                            if self.history is not None:
                                self.history.score_after_pegging = [self.game.board.get_score(p) for p in self.game.players]
                            break

    def _populate_crib(self):
        if self.training_mode != "pegging_only":
            return super()._populate_crib()

        # For pegging-only training, use each player's normal discard logic.
        for pi, player in self.game.players_dict.items():
            player_state = self._build_player_state(player)
            round_state = self._build_round_state()
            cards_to_crib = player.select_crib_cards(player_state, round_state)

            if not set(cards_to_crib).issubset(set(self.hands[pi])):
                raise IllegalCardChoiceError("Crib cards selected are not part of player's hand.")
            if len(cards_to_crib) != 2:
                raise IllegalCardChoiceError("Wrong number of cards sent to crib.")
            self.crib += cards_to_crib
            for card in cards_to_crib:
                self.hands[pi].remove(card)
            self.player_hand_after_discard[pi] = self.hands[pi][:]

    def play(self):
        self.setup_deal_phase()
        self.setup_crib_phase()

        if self.training_mode != "pegging_only":
            winner = self.setup_starter_scoring()
            if winner is not None:
                return
        else:
            if self.history is not None:
                self.history.starter = str(self.starter) if self.starter else None

        if self.training_mode != "discard_only":
            self._play_pegging()
        else:
            if self.history is not None:
                self.history.score_after_pegging = [self.game.board.get_score(p) for p in self.game.players]

        if self.training_mode != "pegging_only":
            self.score_hands_phase()
        else:
            if self.history is not None:
                self.history.score_after_hands = [self.game.board.get_score(p) for p in self.game.players]
                self.history.play_record = self.play_record


class TrainingGame(CribbageGame):
    """CribbageGame variant that can isolate discard-only or pegging-only outcomes."""

    def __init__(
        self,
        players,
        seed: int | None = None,
        copy_players: bool = True,
        dealer=None,
        fast_mode: bool = False,
        training_mode: str = "full",
    ):
        super().__init__(players, seed=seed, copy_players=copy_players, dealer=dealer, fast_mode=fast_mode)
        if training_mode not in {"full", "discard_only", "pegging_only"}:
            raise ValueError("training_mode must be one of: full, discard_only, pegging_only")
        self.training_mode = training_mode

    def play_round(self, game_score=None, seed=None):
        if game_score is None:
            game_score = self.round_scores[-1] if self.round_scores else [0 for _ in self.players]
        if seed is not None:
            round_seed = seed
        if self.round_seed is not None:
            round_seed = self.round_seed
        else:
            round_seed = None
        starting_player = self._rng.choice([0, 1])
        seed = self._rng.randint(0, 2**32 - 1) if self.seed is not None else None
        player_gen = self._alternate_players(starting_player)
        dealer = next(player_gen)
        r = TrainingRound(self, dealer=dealer, seed=seed, fast_mode=self.fast_mode, training_mode=self.training_mode)
        r.play()
        game_score = [self.board.get_score(p) for p in self.players]
        if game_score == [121, 121]:
            raise ValueError("tie should not be possible")
        self.round_scores.append(game_score)
        self.history.append(r)
        return game_score
