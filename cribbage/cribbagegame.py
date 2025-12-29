"""Cribbage game."""

from copy import deepcopy
import random
import logging
from shutil import copy

from cribbage.board import CribbageBoard
from cribbage.state import GameState, RoundState
from . import scoring
from .players.base_player import HumanPlayer
from .players.random_player import RandomPlayer
from .playingcards import Deck

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



def score_play(card_seq):
    """Return score for latest move in an active play sequence.

    :param card_seq: List of all cards played (oldest to newest).
    :return: Points earned by player of latest card played in the sequence.
    """
    score = 0
    score_scenarios = [scoring.ExactlyEqualsN(n=15), scoring.ExactlyEqualsN(n=31),
                        scoring.HasPairTripleQuad(), scoring.HasStraight_DuringPlay()]
    for scenario in score_scenarios:
        s, desc = scenario.check(card_seq[:])
        score += s
        if desc:
            logger.debug("[SCORE] " + desc)
    return score

def score_hand(cards, is_crib: bool = False):
    """Score a hand at the end of a round.

    :param cards: Cards in a single player's hand.
    :return: Points earned by player.
    """
    score = 0
    score_scenarios = [scoring.CountCombinationsEqualToN(n=15),
                        scoring.HasPairs_InHand(), scoring.HasStraight_InHand(), scoring.HasFlush(is_crib=is_crib)]
    for scenario in score_scenarios:
        s, desc = scenario.check(cards[:])
        score += s
        if desc:
            logger.debug("[EOR SCORING] " + desc)
    return score


class CribbageGame:
    """Main cribbage game class."""
    
    # Class-level constants
    MAX_SCORE = 121  # game ends at this score
    CRIB_SIZE = 4  # size of the crib
    N_GO = 31  # round sequence ends at this card point total

    def __init__(self, players, seed: int | None = None):
        # self.players = players  #: the two players
        self.players = [deepcopy(p) for p in players]
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
        starting_player = self._rng.choice([0, 1])
        logger.debug("Coin flip. %s is dealer." % str(self.players[starting_player]))
        player_gen = self._alternate_players(starting_player)
        game_score = [0 for _ in self.players]
        while max(game_score) < self.MAX_SCORE:
            dealer = next(player_gen)
            r = CribbageRound(self, dealer=dealer, seed=self.seed)
            r.play()
            game_score = [self.board.get_score(p) for p in self.players]
            logger.debug(f"{game_score=}")
            logger.debug(self.board)
        return game_score # list of player 1's final peg vs player 2's final peg


class CribbageRound:
    """Individual round of cribbage."""

    # def __init__(self, game, dealer, seed: int | None = None):
    def __init__(self, game, dealer, seed: int | None = None):
        # Replenish deck for each round
        self._rng_round = random.Random(seed)
        self.deck = Deck(seed=seed)
        self.game_winner = None
        self.game = game
        self.hands = {self.game.players[0].name: [], self.game.players[1].name: []}
        self.player_hand_after_discard = {self.game.players[0].name: [], self.game.players[1].name: []}
        self.crib = []
        self.table = []
        self.starter = None
        self.dealer = dealer
        self.nondealer = [p for p in self.game.players if p.name != dealer.name][0]
        self.most_recent_player = None        
        self.round_state = RoundState(self.game, dealer=dealer, seed=seed)

    def _deal(self):
        """Deal cards.

        :return: None
        """
        shuffles = 3  # ACC Rule 2.1
        cards_per_player = 6
        for i in range(shuffles):
            self.deck.shuffle()
        for _ in range(cards_per_player):
            for key in self.hands.keys():
                if len(self.hands[key]) < cards_per_player:
                    self.hands[key].append(self.deck.draw())
        logger.debug("Cards dealt.")

    def _populate_crib(self):
        """Solicit crib card decisions from players and place these cards in the crib.

        :return: None
        """        
        # for p in self.game.players:
        for pi, player in self.game.players_dict.items():
            cards_to_crib = player.select_crib_cards(self.hands[pi], dealer_is_self=(player == self.dealer))
            logger.debug(f"Cards cribbed: {cards_to_crib}")
            if not set(cards_to_crib).issubset(set(self.hands[pi])):
                raise IllegalCardChoiceError("Crib cards selected are not part of player's hand.")
            elif len(cards_to_crib) != 2:
                raise IllegalCardChoiceError("Wrong number of cards sent to crib.")
            else:
                self.crib += cards_to_crib
                for card in cards_to_crib:
                    self.hands[pi].remove(card)
                self.player_hand_after_discard[pi] = self.hands[pi][:]
                logger.debug(f"Player {player.name} has hand {self.hands[pi]} after cribbing.")
        assert len(self.crib) == self.game.CRIB_SIZE, "Crib size is not %s" % self.game.CRIB_SIZE

    def table_to_str(self, sequence_start_idx):
        """Render current table state as a string.

        This function converts the current table state into a string consisting of all previous up-to-31 sequences
        in parentheses followed by the current (active) sequence.
        :param sequence_start_idx: Start index of the current sequence.
        :return: String representing the current table state.
        """
        prev, curr = "", ""
        for play in self.table[:sequence_start_idx]:
            prev += str(play) + ", "
        if prev:
            prev = "(" + prev[:-2] + ") "
        for play in self.table[sequence_start_idx:]:
            curr += str(play) + ", "
        return prev + curr[:-2]

    def _cut(self):
        """Cut the deck."""
        cut_point = self._rng_round.randrange(len(self.deck))
        self.deck.cut(cut_point=cut_point)
        logger.debug("Cards cut.")

    def get_table_value(self, sequence_start_idx):
        """Get the total value of cards in the current active sequence.

        :param sequence_start_idx: Table index where current sequence begins.
        :return: Total value of cards in active sequence.
        """
        return_val = sum(i.get_value() for i in self.table[sequence_start_idx:]) if self.table else 0
        return return_val

    def set_up_round_and_deal_cards(self):
        """Set up cribbage round and deal cards to players."""
        self._cut()
        self._deal()
        # round1 cards = {Random1: [qc, kc, 6h, 4h, 7s, 5d], Random2: [5s, 6c, 4d, 2h, 2d, 3d]}
        logger.debug(self.hands)
        self._populate_crib()
        self.starter = self.deck.draw()

    def play(self):
        """Start cribbage round."""
        loser = None
        self.set_up_round_and_deal_cards()
        logger.debug("Starter card is %s." % str(self.starter))
        if self.starter.rank == 'j':
            self.game.board.peg(self.dealer, 1)
            logger.debug("2 points to %s for his heels." % str(self.dealer))
        active_players = [self.nondealer, self.dealer]
        while sum([len(v) for v in self.hands.values()]) and self.game_winner is None:
            sequence_start_idx = len(self.table)
            while active_players and self.game_winner is None:
                logger.debug(f"In while loop {len(active_players)}")
                for player in active_players:
                    logger.debug(f"Player {player.name}'s turn to play.")
                    logger.debug(f"active table cards {self.table[sequence_start_idx:]}")
                    # logger.debug("Table: " + self.table_to_str(sequence_start_idx))
                    # logger.debug("Player %s's hand: %s" % (player, self.hands[player]))
                    # logger.debug(f"{self.table=}")
                    # logger.debug(f"table is {self.table}")
                    count = self.get_table_value(sequence_start_idx) 
                    card = player.select_card_to_play(hand=self.hands[player.name], table=self.table[sequence_start_idx:],
                                                 crib=self.crib, count=count)
                    logger.debug(f"Player {player.name} selected card {card} with count {count}")
                    if card is None or card.get_value() + count > 31:
                        logger.debug("Player %s chooses go." % str(player))
                        loser = loser if loser else player
                        active_players.remove(player)
                        # If no one can play any more cards, give point to player of last card played
                    else:
                        # self.table.append({'player': p, 'card': card})
                        # logger.debug("Player %s plays %s." % (str(p), str(card)))
                        self.table.append(card)
                        self.most_recent_player = player
                        self.hands[player.name].remove(card)
                        if not self.hands[player.name]:                            
                            active_players.remove(player)
                        logger.debug("Player %s plays %s for %d" %
                                (str(player), str(card), self.get_table_value(sequence_start_idx)))
                        # Consider cards played by both players when scoring during play
                        assert self.get_table_value(sequence_start_idx) <= 31, \
                            "Value of cards on table must be <= 31 to be eligible for scoring."
                        # only scores the latest play, need to test
                        sequence = self.table[sequence_start_idx:]
                        score = self._score_play(sequence)
                        # score = self._score_play(card_seq=[move['card'] for move in self.table[sequence_start_idx:]])
                        if score:
                            winner = self.game.board.peg(player, score)   
                            if winner is not None:
                                self.game_winner = winner
                                break

            if self.game_winner is None:
                self.go_or_31_reached(active_players)

        # Score each player's hand
        if self.game_winner is None:
            for p in self.game.players:
                p_cards_played = self.player_hand_after_discard[p.name] + [self.starter]
                # logger.debug("Scoring " + str(p) + "'s hand: " + str(p_cards_played))
                score = self._score_hand(cards=self.player_hand_after_discard[p.name], is_crib=False)  # Include starter card as part of hand
                if score:
                    self.game.board.peg(p, score)

            # Score the crib
            logger.debug("Scoring the crib: " + str(self.crib + [self.starter]))
            score = self._score_hand(cards=(self.crib + [self.starter]), is_crib=True)  # Include starter card as part of crib
            if score:
                self.game.board.peg(self.dealer, score)

    def go_or_31_reached(self, active_players):
        # If both players have reached 31 or "go" and not run out of cards, continue play
        logger.debug(f"In go or 31 {len(active_players)}")
        if not active_players:
            player_of_last_card = self.most_recent_player
            self.game.board.peg(player_of_last_card, 1)
            logger.debug("Point to %s for last card played." % player_of_last_card)
            # Fix: mutate the list in place instead of reassigning
            new_players = [p for p in self.game.players if p != player_of_last_card and self.hands[p.name]]
            if self.hands[player_of_last_card.name]:
                new_players.append(player_of_last_card)
            active_players.clear()
            active_players.extend(new_players)


    def _score_play(self, card_seq):
        return score_play(card_seq)

    def _score_hand(self, cards, is_crib: bool = False):
        return score_hand(cards, is_crib)


    def _score_hand_with_breakdown(self, cards, is_crib: bool = False):
        """Score a hand and return both score and breakdown.

        :param cards: Cards in a single player's hand.
        :param is_crib: Whether this is scoring a crib.
        :return: Tuple of (total_score, list of score descriptions).
        """
        score = 0
        breakdown = []
        score_scenarios = [scoring.CountCombinationsEqualToN(n=15),
                           scoring.HasPairs_InHand(), scoring.HasStraight_InHand(), scoring.HasFlush(is_crib=is_crib)]
        for scenario in score_scenarios:
            s, desc = scenario.check(cards[:])
            if s > 0 and desc:
                score += s
                breakdown.append({"points": s, "description": desc})
        return score, breakdown



class IllegalCardChoiceError(Exception):
    """Raised when player client returns an invalid card selection."""
    pass


def main():
    players = [RandomPlayer("Player1"), RandomPlayer("Player2")]
    game = CribbageGame(players=players)
    game.start()


if __name__ == '__main__':
    main()
