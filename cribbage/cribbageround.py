import logging
import random

from cribbage import scoring
from cribbage.playingcards import Card, Deck
from cribbage.state import RoundState

logger = logging.getLogger(__name__)

class IllegalCardChoiceError(Exception):
    """Raised when player client returns an invalid card selection."""
    pass

class PlayRecord: 
    def __init__(self, description, full_table, active_table, table_count, player_name, card, hand):
        self.description = description
        self.full_table = full_table
        self.active_table = active_table
        self.table_count = table_count
        self.player_name = player_name
        self.card = card
        self.hand = hand

    def __str__(self):
        hand_str = f"hand: {[str(c) for c in self.hand]}" if self.hand is not None else ""
        card_str = f", card: {str(self.card)}" if self.card is not None else ""
        return f"{self.description} {hand_str}, table count: {self.table_count}"

class RoundHistory:
    def __init__(self):
        self.dealer = None
        self.cards_dealt = {}
        self.hand_scores = {}
        self.crib_score = 0
        self.starter = None
        self.score_at_start_of_round = []
        self.score_after_pegging = []
        self.score_after_hands = []
        self.play_record = []  # List of PlayRecord objects
        self.crib = []

    # def __str__(self) -> str:
    #     return f"""score at start={self.score_at_start_of_round} dealer={self.dealer}, cards_dealt={self.cards_dealt}, crib={self.crib}\nplays {[str(pr) for pr in self.play_record]}\nhand_scores={self.hand_scores}, crib_score={self.crib_score},score after pegging={self.score_after_pegging}, score after hands={self.score_after_hands}"""

    def __str__(self) -> str:
        plays = "\n    ".join(str(pr) for pr in self.play_record)

        dealt = "\n    ".join(
            f"{p}: {cards}" for p, cards in self.cards_dealt.items()
        )

        return (
            f"Round:\n"
            f"  score at start: {self.score_at_start_of_round}\n"
            f"  dealer: {self.dealer}\n"
            f"  starter: {self.starter}\n"
            f"  dealt:\n    {dealt}\n"
            f"  crib: {self.crib}\n"
            f"  plays:\n    {plays}\n"
            f"  hand_scores: {self.hand_scores}\n"
            f"  crib_score: {self.crib_score}\n"
            f"  score_after_pegging: {self.score_after_pegging}\n"
            f"  score_after_hands: {self.score_after_hands}"
        )


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
        self.table = [] # all cards that have been played over each "up to 31" thing
        self.starter = None
        self.dealer = dealer
        self.nondealer = [p for p in self.game.players if p.name != dealer.name][0]
        self.most_recent_player = None        
        self.round_state = RoundState(self.game, dealer=dealer, seed=seed)
        self.play_record = []
        self.history = RoundHistory()

    def __str__(self) -> str:
        return str(self.history)

    def _deal(self):
        """Deal cards.

        :return: None
        """
        # shuffles = 3  # ACC Rule 2.1
        # for i in range(shuffles):
        # shuffling is done when deck is created
        #     self.deck.shuffle()
        cards_per_player = 6
        for _ in range(cards_per_player):
            for key in self.hands.keys():
                if len(self.hands[key]) < cards_per_player:
                    self.hands[key].append(self.deck.draw())
        logger.debug("Cards dealt.")

    def _populate_crib(self):
        """Solicit crib card decisions from players and place these cards in the crib.

        :return: None
        """        
        player_scores_dict = {}
        for pi, player in self.game.players_dict.items():
            player_scores_dict[player.name] = self.game.board.get_score(player)
        for pi, player in self.game.players_dict.items():                        
            player_score = player_scores_dict[player.name]
            other_player_name = [next(name for name in player_scores_dict.keys() if name != player.name)]
            opponent_score = player_scores_dict[other_player_name[0]]
            cards_to_crib = player.select_crib_cards(self.hands[pi], dealer_is_self=(player == self.dealer), your_score=player_score, opponent_score=opponent_score)
            logger.debug(f"{player.name} cribs: {cards_to_crib} when dealt hand {self.hands[pi]}")
            if not set(cards_to_crib).issubset(set(self.hands[pi])):
                raise IllegalCardChoiceError("Crib cards selected are not part of player's hand.")
            elif len(cards_to_crib) != 2:
                raise IllegalCardChoiceError("Wrong number of cards sent to crib.")
            else:
                self.crib += cards_to_crib
                for card in cards_to_crib:
                    self.hands[pi].remove(card)
                self.player_hand_after_discard[pi] = self.hands[pi][:]
                logger.debug(f"{player.name} has hand {self.hands[pi]} after cribbing.")
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
        self.history.dealer = self.dealer.name
        self.history.cards_dealt = {p.name: [str(card) for card in self.hands[p.name]] for p in self.game.players}
        self._populate_crib()
        self.history.crib = [str(card) for card in self.crib]
        self.history.score_at_start_of_round = [self.game.board.get_score(p) for p in self.game.players]
        self.starter = self.deck.draw()

    def play(self):
        """Start cribbage round."""
        loser = None
        self.set_up_round_and_deal_cards()
        logger.debug("Starter card is %s." % str(self.starter))
        if self.starter.rank == 'j': # type: ignore
            self.play_record.append(PlayRecord(f"Dealer {self.dealer.name} scores 2 point for heels.", self.table, self.table, 0, self.dealer.name, self.starter, hand=None))
            self.game_winner = self.game.board.peg(self.dealer, 2)     
            if self.game_winner is not None:
                 return       
            logger.debug("2 points to %s for his heels." % str(self.dealer))
        self.history.starter = str(self.starter)
        active_players = [self.nondealer, self.dealer]
        players_said_go = []
        any_player_has_at_least_1_card = any(len(hand) > 0 for hand in self.hands.values())
        while any_player_has_at_least_1_card and self.game_winner is None:
            sequence_start_idx = len(self.table)
            while any_player_has_at_least_1_card and self.game_winner is None:
                # Create a copy to iterate over, since we modify active_players during iteration
                players_to_check = list(active_players)
                for player in players_to_check:
                    if player in players_said_go:
                        logger.debug(f"Player {player.name} has already said go, skipping.")
                        continue  
                    logger.debug(f"score is {[self.game.board.get_score(p) for p in self.game.players]}")
                    logger.debug(f"Player {player.name}'s turn to play.")
                    logger.debug(f"active table cards {self.table[sequence_start_idx:]}")
                    count = self.get_table_value(sequence_start_idx)                                           
                    card = player.select_card_to_play(hand=self.hands[player.name], table=self.table[sequence_start_idx:],
                                                 crib=self.crib, count=count)                    
                    if card is None or card.get_value() + count > 31:
                        logger.debug("Player %s chooses go." % str(player))                        
                        loser = loser if loser else player                        
                        players_said_go.append(player)
                    else:
                        self.play_record.append(PlayRecord(f"{player.name} {str(card)}", self.table, self.table[sequence_start_idx:], self.get_table_value(sequence_start_idx), player.name, card, hand=self.hands[player.name][:]))                        
                        self.table.append(card)
                        logger.debug(f"Player {player.name} selected card {card} at count {count} to {self.get_table_value(sequence_start_idx)}")
                        if self.get_table_value(sequence_start_idx) == 31:
                            self.game.board.peg(player, 1)
                            self.play_record.append(PlayRecord(f"{player.name} scores 1 point for 31.", self.table, self.table, self.get_table_value(0), player.name, None, hand=None))                                                    
                        self.most_recent_player = player
                        self.hands[player.name].remove(card)
                        # Consider cards played by both players when scoring during play
                        assert self.get_table_value(sequence_start_idx) <= 31, \
                            "Value of cards on table must be <= 31 to be eligible for scoring."
                        # only scores the latest play, need to test
                        sequence = self.table[sequence_start_idx:]
                        # score play handles the 31 case
                        score = self._score_play(sequence)
                        # score = self._score_play(card_seq=[move['card'] for move in self.table[sequence_start_idx:]])
                        if score:
                            self.play_record.append(PlayRecord(f"{player.name} scores {score} point(s).", self.table, self.table[sequence_start_idx:], self.get_table_value(sequence_start_idx), player.name, card, hand=self.hands[player.name][:]))
                            winner = self.game.board.peg(player, score)   
                            if winner is not None:
                                self.game_winner = winner
                                return

                    if self.game_winner is None:
                        if len(players_said_go) == 2:
                            # Everyone has said go                        
                            logger.debug("All players have said go or reached 31.")  
                            players_to_check = self.go_or_31_reached(players_said_go, self.table[sequence_start_idx:])
                            players_said_go = []
                            sequence_start_idx = len(self.table)
                        any_player_has_at_least_1_card = any(len(hand) > 0 for hand in self.hands.values())
                        if not any_player_has_at_least_1_card:                            
                            self.game_winner = self.game.board.peg(player, 1)
                            self.play_record.append(PlayRecord(f"{player.name} scores 1 point for last card played", self.table, self.table, self.get_table_value(0),player.name, None, hand=None))
                            self.history.score_after_pegging = [self.game.board.get_score(p) for p in self.game.players]
                            break

        # Score each player's hand
        # Non-dealer counts first, then dealer, then crib
        # Game ends immediately when someone reaches 121
        if self.game_winner is None:
            # Non-dealer counts first
            logger.debug(f"Scoring non-dealer {self.nondealer.name} hand: {self.player_hand_after_discard.get(self.nondealer.name, 'NOT FOUND')}")
            p_cards_played = self.player_hand_after_discard[self.nondealer.name] + [self.starter]
            score = self._score_hand(cards=self.player_hand_after_discard[self.nondealer.name] + [self.starter], is_crib=False)
            self.history.hand_scores[self.nondealer.name] = score
            logger.debug(f"Non-dealer {self.nondealer.name} scored {score} points")
            if score:
                winner = self.game.board.peg(self.nondealer, score)
                if winner is not None:
                    self.game_winner = winner
                    logger.debug(f"Non-dealer {self.nondealer.name} wins!")
                    return

        # Dealer counts second (if game not yet won)
        if self.game_winner is None:
            logger.debug(f"Scoring dealer {self.dealer.name} hand: {self.player_hand_after_discard.get(self.dealer.name, 'NOT FOUND')}")
            p_cards_played = self.player_hand_after_discard[self.dealer.name] + [self.starter]
            score = self._score_hand(cards=self.player_hand_after_discard[self.dealer.name] + [self.starter], is_crib=False)
            self.history.hand_scores[self.dealer.name] = score
            logger.debug(f"Dealer {self.dealer.name} scored {score} points")
            if score:
                winner = self.game.board.peg(self.dealer, score)
                if winner is not None:
                    self.game_winner = winner
                    logger.debug(f"Dealer {self.dealer.name} wins!")
                    return

        # Score the crib (if game not yet won)
        if self.game_winner is None:
            logger.debug("Scoring the crib: " + str(self.crib + [self.starter]))
            score = self._score_hand(cards=(self.crib + [self.starter]), is_crib=True)
            self.history.crib_score = score  # Include starter card as part of crib
            if score:
                winner = self.game.board.peg(self.dealer, score)
                if winner is not None:
                    self.game_winner = winner
                    return

        self.history.score_after_hands = [self.game.board.get_score(p) for p in self.game.players]
        self.history.play_record = self.play_record

    def go_or_31_reached(self, players_said_go, count):
        # If both players have reached 31 or "go" and not run out of cards, continue play
        # players_said_go is a list of players ordered by who said go first
        # function is called when all players had said go
        # last player to say go gets 1 point
        logger.debug(f"In go or 31 {len(players_said_go)}")
        self.play_record.append(PlayRecord(f"{players_said_go[-1].name} scores 1 point for last card played", self.table, self.table, self.get_table_value(0),players_said_go[-1].name, None, hand=None))
        self.game_winner = self.game.board.peg(players_said_go[-1], 1)
        logger.debug(f"score is {[self.game.board.get_score(p) for p in self.game.players]}")
        return players_said_go

    def go_or_31_reached_old(self, active_players):
        # If both players have reached 31 or "go" and not run out of cards, continue play
        logger.debug(f"In go or 31 {len(active_players)}")
        if not active_players:
            player_of_last_card = self.most_recent_player
            self.play_record.append(PlayRecord(f"{player_of_last_card.name} scores 1 point for last card played", self.table, self.table, self.get_table_value(0), player_of_last_card.name, None, hand=None))
            self.game.board.peg(player_of_last_card, 1)
            logger.debug("Point to %s for last card played." % player_of_last_card)
            # Fix: mutate the list in place instead of reassigning
            new_players = [p for p in self.game.players if p != player_of_last_card and self.hands[p.name]]
            if self.hands[player_of_last_card.name]: # type: ignore
                new_players.append(player_of_last_card)
            active_players.clear()
            active_players.extend(new_players)
        else:
            self.play_record.append(PlayRecord(f"{self.most_recent_player.name} scores 1 point for 31 or go.", self.table, self.table, self.get_table_value(0), self.most_recent_player.name, None, hand=self.hands[self.most_recent_player.name][:]))
            # self.play_record.append(PlayRecord(f"{player.name} go", self.table, self.table[sequence_start_idx:], self.get_table_value(sequence_start_idx), player.name, None, hand=self.hands[player.name][:]))                        
            # self.play_record.append(PlayRecord(f"{self.most_recent_player.name} scores 1 point for go.", self.table, self.table[sequence_start_idx:], self.get_table_value(sequence_start_idx), self.most_recent_player.name, None, hand=self.hands[self.most_recent_player.name][:]))


    def _score_play(self, card_seq):
        return scoring.score_play(card_seq)

    def _score_hand(self, cards, is_crib: bool = False):
        return scoring.score_hand(cards, is_crib)


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

