"""Cribbage game."""

import random
import logging
from . import scoring
from .player import HumanPlayer, RandomPlayer
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
        self.players = players  #: the two players
        self.board = CribbageBoard(self.players, self.MAX_SCORE)  #: the cribbage board for scoring
        assert len(self.players) == 2, "Currently, only 2-player games are supported."

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
        starting_player = random.choice([0, 1])
        logger.info("Coin flip. %s is dealer." % str(self.players[starting_player]))
        player_gen = self._alternate_players(starting_player)
        game_score = [0 for _ in self.players]
        while max(game_score) < self.MAX_SCORE:
            dealer = next(player_gen)
            r = CribbageRound(self, dealer=dealer)
            r.play()
            game_score = [self.board.get_score(p) for p in self.players]
            logger.info(f"{game_score=}")
            debug(self.board)
        return game_score # list of player 1's final peg vs player 2's final peg


class CribbageRound:
    """Individual round of cribbage."""

    def __init__(self, game, dealer):
        # Replenish deck for each round
        self.deck = Deck()
        self.game_winner = None
        self.game = game
        self.hands = {player: [] for player in self.game.players}
        self.player_hand_after_discard = {player: [] for player in self.game.players}
        self.crib = []
        self.table = []
        self.starter = None
        self.dealer = dealer
        self.nondealer = [p for p in self.game.players if p != dealer][0]
        self.most_recent_player = None

    def _deal(self):
        """Deal cards.

        :return: None
        """
        shuffles = 3  # ACC Rule 2.1
        cards_per_player = 6
        for i in range(shuffles):
            self.deck.shuffle()
        for _ in range(cards_per_player):
            for p in self.game.players:
                self.hands[p].append(self.deck.draw())
        logger.debug("Cards dealt.")

    def _populate_crib(self):
        """Solicit crib card decisions from players and place these cards in the crib.

        :return: None
        """        
        for p in self.game.players:
            cards_to_crib = p.select_crib_cards(self.hands[p], dealer_is_self=(p == self.dealer))
            debug(f"Cards cribbed: {cards_to_crib}")
            if not set(cards_to_crib).issubset(set(self.hands[p])):
                raise IllegalCardChoiceError("Crib cards selected are not part of player's hand.")
            elif len(cards_to_crib) != 2:
                raise IllegalCardChoiceError("Wrong number of cards sent to crib.")
            else:
                self.crib += cards_to_crib
                for card in cards_to_crib:
                    self.hands[p].remove(card)
                self.player_hand_after_discard[p] = self.hands[p][:]
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
        cut_point = random.randrange(len(self.deck))
        self.deck.cut(cut_point=cut_point)
        logger.debug("Cards cut.")

    def get_table_value(self, sequence_start_idx):
        """Get the total value of cards in the current active sequence.

        :param sequence_start_idx: Table index where current sequence begins.
        :return: Total value of cards in active sequence.
        """
        return_val = sum(i.get_value() for i in self.table[sequence_start_idx:]) if self.table else 0
        return return_val

    def play(self):
        """Start cribbage round."""
        loser = None
        self._cut()
        self._deal()
        logger.debug(self.hands)
        self._populate_crib()
        self._cut()
        self.starter = self.deck.draw()
        if self.starter.get_rank() == 'jack':
            self.game.board.peg(self.dealer, 1)
            logger.info("2 points to %s for his heels." % str(self.dealer))
        active_players = [self.nondealer, self.dealer]
        while sum([len(v) for v in self.hands.values()]) and self.game_winner is None:
            sequence_start_idx = len(self.table)
            while active_players and self.game_winner is None:
                for p in active_players:
                    logger.debug("Table: " + self.table_to_str(sequence_start_idx))
                    logger.debug("Player %s's hand: %s" % (p, self.hands[p]))
                    logger.info(f"{self.table}")
                    logger.debug(f"table is {self.table}")
                    count = self.get_table_value(sequence_start_idx) 
                    card = p.select_card_to_play(hand=self.hands[p], table=self.table[sequence_start_idx:],
                                                 crib=self.crib, count=count)
                    if card is None or card.get_value() + count > 31:
                        logger.info("Player %s chooses go." % str(p))
                        loser = loser if loser else p
                        active_players.remove(p)
                        # If no one can play any more cards, give point to player of last card played
                    else:
                        # self.table.append({'player': p, 'card': card})
                        self.table.append(card)
                        self.most_recent_player = p
                        self.hands[p].remove(card)
                        if not self.hands[p]:
                            active_players.remove(p)
                        logger.info("Player %s plays %s for %d" %
                                (str(p), str(card), self.get_table_value(sequence_start_idx)))
                        # Consider cards played by both players when scoring during play
                        assert self.get_table_value(sequence_start_idx) <= 31, \
                            "Value of cards on table must be <= 31 to be eligible for scoring."
                        # only scores the latest play, need to test
                        sequence = self.table + [card]
                        score = self._score_play(sequence)
                        # score = self._score_play(card_seq=[move['card'] for move in self.table[sequence_start_idx:]])
                        if score:
                            winner = self.game.board.peg(p, score)   
                            if winner is not None:
                                self.game_winner = winner
                                break

            if self.game_winner is None:
                self.go_or_31_reached(active_players)

        # Score each player's hand
        if self.game_winner is None:
            for p in self.game.players:
                p_cards_played = self.player_hand_after_discard[p] + [self.starter]
                # logger.debug("Scoring " + str(p) + "'s hand: " + str(p_cards_played))
                score = self._score_hand(cards=self.player_hand_after_discard[p], is_crib=False)  # Include starter card as part of hand
                if score:
                    self.game.board.peg(p, score)

            # Score the crib
            logger.info("Scoring the crib: " + str(self.crib + [self.starter]))
            score = self._score_hand(cards=(self.crib + [self.starter]), is_crib=True)  # Include starter card as part of crib
            if score:
                self.game.board.peg(self.dealer, score)

    def go_or_31_reached(self, active_players):
        # If both players have reached 31 or "go" and not run out of cards, continue play
        if len(active_players) == 0:
            player_of_last_card = self.most_recent_player
            self.game.board.peg(player_of_last_card, 1)
            logger.info("Point to %s for last card played." % player_of_last_card)
            # Fix: mutate the list in place instead of reassigning
            new_players = [p for p in self.game.players if p != player_of_last_card and self.hands[p]]
            if self.hands[player_of_last_card]:
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


class CribbageBoard:
    """Board used to peg (track) points during a cribbage game."""

    def __init__(self, players, max_score):
        self.max_score = max_score
        self.pegs = {p: {'front': 0, 'rear': 0} for p in players}

    def __str__(self):
        s = "[PEGS] "
        for player in self.pegs.keys():
            s += str(player) + " "
            for peg in self.pegs[player]:
                s += str(peg) + ": " + str(self.pegs[player][peg]) + ", "
            s = s[:-2]
            s += "; "
        s = s[:-2]
        return s

    def __repr__(self):
        return str(self)

    def peg(self, player, points):
        """Add points for a player.

        :param player: Player who should receive points.
        :param points: Number of points to add to the player.
        :return: None
        """
        assert points > 0, "You must peg 1 or more points."
        self.pegs[player]['rear'] = self.pegs[player]['front']
        self.pegs[player]['front'] += points
        if self.pegs[player]['front'] >= self.max_score:
            self.pegs[player]['front'] = self.max_score
            return player

    def get_score(self, player):
        """Return a given player's current score.

        :param player: Player to check.
        :return: Score for player.
        """
        front_peg = self.pegs[player]['front']
        logger.debug(f"{front_peg=}")
        return front_peg


class IllegalCardChoiceError(Exception):
    """Raised when player client returns an invalid card selection."""

    pass


def main():
    players = [RandomPlayer("Player1"), RandomPlayer("Player2")]
    game = CribbageGame(players=players)
    game.start()


if __name__ == '__main__':
    main()
