"""Cribbage score conditions used during and after rounds."""
from calendar import c
from itertools import combinations
from abc import ABCMeta, abstractmethod
from logging import getLogger
logger = getLogger(__name__)

class ScoreCondition(metaclass=ABCMeta):
    """Abstract Base Class"""

    def __init__(self):
        pass

    @abstractmethod
    def check(self, hand):
        raise NotImplementedError

class JackMatchStarterSuitScorer(ScoreCondition):
    """
    Awards 1 point if there is a jack in the hand and its suit matches the starter card's suit.
    """    
    def check(self, hand_and_starter):
        starter = hand_and_starter[-1]  # assuming last card is the starter
        hand = hand_and_starter[:-1]
        
        starter_suit = starter.suit
        for card in hand:
            if card.rank.lower() == 'j' and card.suit == starter_suit:                
                return 1, "Jack match starter suit"
        return 0, "" 

class HasPairTripleQuad(ScoreCondition):
    def check(self, cards):
        description = None
        pair_rank = ""
        same, score = 0, 0
        if len(cards) > 1:
            last = cards[-4:][::-1]
            while same == 0 and last:
                if all(card.rank == last[0].rank for card in last):
                    same = len(last)
                    pair_rank = last[0].rank
                last.pop()
            if same == 2:
                score = 2
                description = "Pair (%s)" % pair_rank
            elif same == 3:
                score = 6
                description = "Pair Royal (%s)" % pair_rank
            elif same == 4:
                score = 12
                description = "Double Pair Royal (%s)" % pair_rank
        return score, description


class HasPairs_InHand(ScoreCondition):
    """Find all pairs/triples/quads in a hand (not just consecutive)."""
    def check(self, cards):
        if len(cards) < 2:
            return 0, ""
        
        # Count cards of each rank
        rank_counts = {}
        for card in cards:
            rank_name = card.rank
            rank_counts[rank_name] = rank_counts.get(rank_name, 0) + 1
        
        # Calculate score based on pairs
        score = 0
        descriptions = []
        for rank_name, count in rank_counts.items():
            if count == 2:
                score += 2
                descriptions.append(f"Pair ({rank_name})")
            elif count == 3:
                score += 6  # 3 pairs from 3 cards
                descriptions.append(f"Pair Royal ({rank_name})")
            elif count == 4:
                score += 12  # 6 pairs from 4 cards
                descriptions.append(f"Double Pair Royal ({rank_name})")
        
        description = ", ".join(descriptions) if descriptions else ""
        return score, description


class ExactlyEqualsN(ScoreCondition):

    def __init__(self, n):
        self.n = n
        super().__init__()

    def check(self, cards):
        value = sum(i.get_value() for i in cards)
        if value == self.n:
            # ACC rules give 2 for 15; treat 31 as 1 to avoid double-counting with last-card point
            score = 1 if self.n == 31 else 2
        else:
            score = 0
        description = "%d count" % self.n if score else ""
        return score, description


class HasStraight_InHand(ScoreCondition):

    @staticmethod
    def _enumerate_straights(cards):
        potential_straights = []
        straights = []
        straights_deduped = []
        if cards:
            for i in range(3, len(cards) + 1):
                potential_straights += list(combinations(cards, i))
            for p in potential_straights:
                rank_set = set([int(card.rank) if card.rank.isdigit() else {'a':1,'j':11,'q':12,'k':13}[card.rank.lower()] for card in p])
                if ((max(rank_set) - min(rank_set) + 1) == len(p) == len(rank_set)):
                    straights.append(set(p))
            for s in straights:
                subset = False
                for o in straights:
                    if s.issubset(o) and s is not o:
                        subset = True
                if not subset:
                    straights_deduped.append(s)
        return straights_deduped

    @classmethod
    def check(cls, cards):
        description = ""
        points = 0
        straights = cls._enumerate_straights(cards)
        for s in straights:
            assert len(s) >= 3, "Straights must be 3 or more cards."
            description += "%d-card straight " % len(s)
            points += len(s)
        return points, description


class HasStraight_DuringPlay(ScoreCondition):

    @staticmethod
    def _is_straight(cards):
        rank_set = set([int(card.rank) if card.rank.isdigit() else {'a':1,'j':11,'q':12,'k':13}[card.rank.lower()] for card in cards])
        return ((max(rank_set) - min(rank_set) + 1) == len(cards) == len(rank_set)) if len(cards) > 2 else False

    @classmethod
    def check(cls, cards):
        description = ""
        card_set = cards[:]
        while card_set:
            if cls._is_straight(card_set):
                description = "%d-card straight" % len(card_set)
                return len(card_set), description
            card_set.pop(0)
        return 0, description

class CountCombinationsEqualToN(ScoreCondition):
    def __init__(self, n):
        self.n = n
        super().__init__()

    def check(self, cards):
        n_counts, score = 0, 0
        cmb_list = []
        card_values = [card.get_value() for card in cards]
        for i in range(len(card_values)):
            cmb_list += list(combinations(card_values, i + 1))
        for i in cmb_list:
            n_counts += 1 if sum(i) == self.n else 0
        description = "%d unique %d-counts" % (n_counts, self.n) if n_counts else ""
        score = n_counts * 2
        return score, description


class HasFlush(ScoreCondition):
    def __init__(self, is_crib: bool = False, starter_card=None):
        super().__init__()
        self.is_crib = is_crib
        self.starter_card = starter_card

    def check(self, cards):
        logger.debug("Checking flush for cards: %s", cards)
        logger.debug("length of cards: %d", len(cards))
        if len(cards) < 4:
            return 0, ""

        score = 0
        if (len(cards) == 4) and (self.starter_card is None):
            suits = [card.suit for card in cards]
            if len(set(suits)) == 1:
                return 4, "only 4 cards checked, but has flush"
            return 0, ""
        # include to catch user error of function
        if self.starter_card in cards:
            # Exclude starter for flush check
            cards = [c for c in cards if c != self.starter_card]
        elif len(cards) == 5 and self.starter_card is None:
            # Assume last card is starter if not provided
            self.starter_card = cards[-1]
            cards = cards[:-1]
        elif self.is_crib and len(cards) == 4 and self.starter_card is None:
            raise ValueError("Starter card must be provided for crib flush check with 4 hand cards.")
        suits = [card.suit for card in cards]
        if self.is_crib:
            # Crib flush only scores when all five match (hand + starter)
            if len(cards) != 4 or self.starter_card is None:
                raise ValueError("Crib flush check requires exactly 4 hand cards and a starter card.")
            if len(set(suits + [self.starter_card.suit])) == 1:
                score = 5
        else:
            # Standard hand flush: 4 for four-card flush; +1 if starter also matches when present            
                hand_suits = suits
                if self.starter_card is None:
                    a = 1 
                    raise ValueError("starter card not passed in ", cards)
                starter_suit = self.starter_card.suit
                if len(set(hand_suits)) == 1:
                    score = 4 + (1 if starter_suit == hand_suits[0] else 0)        
        description = "" if score == 0 else ("%d-card flush" % score)
        return score, description

def score_play(card_seq):
    """Return score for latest move in an active play sequence.

    :param card_seq: List of all cards played (oldest to newest).
    :return: Points earned by player of latest card played in the sequence.
    """
    score = 0
    score_scenarios = [ExactlyEqualsN(n=15), ExactlyEqualsN(n=31),
                        HasPairTripleQuad(), HasStraight_DuringPlay()]
    for scenario in score_scenarios:
        s, desc = scenario.check(card_seq[:])
        score += s
        if desc:
            logger.debug("[SCORE] " + desc)
    return score


def score_hand(cards, is_crib: bool = False, starter_card=None):
    """Score a hand at the end of a round.

    :param cards: Cards in a single player's hand.
    :return: Points earned by player.
    """
    score = 0
    if starter_card is None and len(cards) == 5:
        starter_card = cards[-1]
    score_scenarios = [CountCombinationsEqualToN(n=15), JackMatchStarterSuitScorer(),
                        HasPairs_InHand(), HasStraight_InHand(), HasFlush(is_crib=is_crib, starter_card=starter_card)]
    for scenario in score_scenarios:
        s, desc = scenario.check(cards[:])
        score += s
        if desc:
            logger.debug("[EOR SCORING] " + desc)
    return score