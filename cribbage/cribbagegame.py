"""Cribbage game."""

from copy import deepcopy
import random
import logging
from shutil import copy

from cribbage.board import CribbageBoard
from cribbage.state import GameState, RoundState
from . import scoring
from cribbage.scoring import score_hand, score_play
from .players.base_player import HumanPlayer
from .players.random_player import RandomPlayer
from .playingcards import Deck
from cribbage.cribbageround import CribbageRound

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



class CribbageGame:
    """
    Main cribbage game class
    Dealer deals 6 cards, non-dealer cuts the deck
    If jack dealer pegs 2 points
    Crib belongs to the dealer
    """
    
    # Class-level constants
    MAX_SCORE = 121  # game ends at this score
    CRIB_SIZE = 4  # size of the crib
    N_GO = 31  # round sequence ends at this card point total

    def __init__(self, players, seed: int | None = None, copy_players: bool = True):
        # self.players = players  #: the two players
        if copy_players:
            self.players = [deepcopy(p) for p in players]
        else:
            self.players = players
        assert self.players[0].name != self.players[1].name, "Players must have unique names." # todo: need to improve
        self.players_dict = {self.players[0].name: self.players[0], self.players[1].name: self.players[1]}
        self.board = CribbageBoard(self.players, self.MAX_SCORE)  #: the cribbage board for scoring
        self.seed = seed
        self._rng = random.Random(seed)    
        # self._rng = random.Random(self.seed)
        assert len(players) == 2, "Currently, only 2-player games are supported."
        for p in self.players:
            if isinstance(p, RandomPlayer):
                p.reset_rng()
        self.game_state = GameState(self.players, seed=seed)
        self.round_scores = []
        self.history = []
        self.round_seed = None

    def _alternate_players(self, start_idx=0):
        """Generator to alternate which player dealers, with an arbitrary starting player.

        :param start_idx: Index of player who deals initially.
        :return: Generator primed for the start_idx player to deal.
        """
        if start_idx == 1:
            yield self.players[1]
        while True:
            yield self.players[0]
            yield self.players[1]

    def start(self):
        """Initiate game.

        :return: None
        """        
        game_score = [0 for _ in self.players]
        while max(game_score) < self.MAX_SCORE:            
            self.round_seed = self._rng.randint(0, 2**32 - 1) if self.seed is not None else None
            game_score = self.play_round(game_score, seed=self.round_seed)     
        return game_score # list of player 1's final peg vs player 2's final peg

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
        r = CribbageRound(self, dealer=dealer, seed=seed)
        r.play()
        game_score = [self.board.get_score(p) for p in self.players]
        logger.debug(f"{game_score=}")
        logger.debug(self.board)
        self.round_scores.append(game_score)
        self.history.append(r)
        return game_score # list of player 1's final peg vs player 2's final peg




def main():
    players = [RandomPlayer("Player1"), RandomPlayer("Player2")]
    game = CribbageGame(players=players)
    game.start()


if __name__ == '__main__':
    main()
