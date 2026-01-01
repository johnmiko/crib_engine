import pytest

from cribbage.cribbagegame import CribbageGame
from cribbage.board import CribbageBoard
from cribbage.cribbageround import CribbageRound
from cribbage.players.random_player import RandomPlayer
from cribbage.playingcards import Card, Deck
import unittest
from cribbage import scoring
from cribbage import playingcards as pc

def make_card(rank: str, suit: str) -> Card:
    # Accepts rank and suit as names, e.g., ("five", "spades")
    rank_map = {'ace': 'a', 'two': '2', 'three': '3', 'four': '4', 'five': '5', 'six': '6', 'seven': '7', 'eight': '8', 'nine': '9', 'ten': '10', 'jack': 'j', 'queen': 'q', 'king': 'k'}
    suit_map = {'hearts': 'h', 'diamonds': 'd', 'clubs': 'c', 'spades': 's'}
    return Card(f"{rank_map[rank]}{suit_map[suit]}")

def make_round() -> CribbageRound:
    game = CribbageGame(players=[RandomPlayer("player1"), RandomPlayer("player2")])
    return CribbageRound(game, dealer=game.players[0])

def test_hand_double_run_and_fifteens():
    """
    Hand: 5, 5, 6, 10, starter 4
    Expected:
    - Pair of 5s: 2
    - Fifteens (5+10 twice, and 4+5+6 twice): 8
    - Runs of 3 (4-5-6 twice): 6
    Total: 16 points
    """
    round_inst = make_round()
    cards = [
        make_card("five", "spades"),
        make_card("five", "clubs"),
        make_card("six", "diamonds"),
        make_card("ten", "hearts"),
        make_card("four", "spades"),  # starter
    ]
    score = round_inst._score_hand(cards, is_crib=False)
    assert score == 16, f"Expected 16 points, got {score}"

def make_card(rank: str, suit: str) -> Card:
    # Accepts rank and suit as names, e.g., ("five", "spades")
    rank_map = {'ace': 'a', 'two': '2', 'three': '3', 'four': '4', 'five': '5', 'six': '6', 'seven': '7', 'eight': '8', 'nine': '9', 'ten': '10', 'jack': 'j', 'queen': 'q', 'king': 'k'}
    suit_map = {'hearts': 'h', 'diamonds': 'd', 'clubs': 'c', 'spades': 's'}
    return Card(f"{rank_map[rank]}{suit_map[suit]}")

def make_round() -> CribbageRound:
    game = CribbageGame(players=[RandomPlayer("player1"), RandomPlayer("player2")])
    return CribbageRound(game, dealer=game.players[0])

def test_hand_double_run_and_fifteens():
    """
    Hand: 5, 5, 6, 10, starter 4
    Expected:
    - Pair of 5s: 2
    - Fifteens (5+10 twice, and 4+5+6 twice): 8
    - Runs of 3 (4-5-6 twice): 6
    Total: 16 points
    """
    round_inst = make_round()
    cards = [
        make_card("five", "spades"),
        make_card("five", "clubs"),
        make_card("six", "diamonds"),
        make_card("ten", "hearts"),
        make_card("four", "spades"),  # starter
    ]
    score = round_inst._score_hand(cards, is_crib=False)
    assert score == 16, f"Expected 16 points, got {score}"

def test_hand_with_double_runs_pair_and_fifteens():
    """
    Hand: 5, 6, 7, 8, starter 7
    - Run of 4 (5,6,7,8): 4 points
    - Run of 4 using starter 7 (5,6,7,8): 4 points
    - Pair of 7s (7 and 7): 2 points
    - 7 + 8 = 15: 2 points
    - 7 + 8 = 15: 2 points
    Total: 14 points
    """
    round_inst = make_round()
    cards = [
        make_card("five", "spades"),
        make_card("six", "diamonds"),
        make_card("seven", "spades"),
        make_card("eight", "diamonds"),
        make_card("seven", "diamonds"),  # starter
    ]
    score = round_inst._score_hand(cards, is_crib=False)
    assert score == 14, f"Expected 14 points, got {score}"

class TestPairScoring(unittest.TestCase):
    def setUp(self):
        pass

    def test_pair_pair(self):
        s = scoring.HasPairTripleQuad()
        hand = [pc.Card('2h'), pc.Card('3h'), pc.Card('4h'), pc.Card('5h'), pc.Card('6h'), pc.Card('7h'), pc.Card('8h'), pc.Card('9h'), pc.Card('10h'), pc.Card('jh'), pc.Card('qh'), pc.Card('kh'), pc.Card('ah')]
        hand.append(pc.Card('9h'))
        hand.append(pc.Card('9h'))
        score, _ = s.check(hand)
        self.assertEqual(score, 2)

    def test_pair_triple(self):
        s = scoring.HasPairTripleQuad()
        hand = [pc.Card('2h'), pc.Card('3h'), pc.Card('4h'), pc.Card('5h'), pc.Card('6h'), pc.Card('7h'), pc.Card('8h'), pc.Card('9h'), pc.Card('10h'), pc.Card('jh'), pc.Card('qh'), pc.Card('kh'), pc.Card('ah')]
        hand.append(pc.Card('9h'))
        hand.append(pc.Card('9h'))
        hand.append(pc.Card('9h'))
        score, _ = s.check(hand)
        self.assertEqual(score, 6)

    def test_pair_quadruple(self):
        s = scoring.HasPairTripleQuad()
        hand = [pc.Card('2h') for _ in range(6)]
        score, _ = s.check(hand)
        self.assertEqual(score, 12)

    def test_pair_nothing(self):
        s = scoring.HasPairTripleQuad()
        hand = [pc.Card('2h'), pc.Card('3h'), pc.Card('4h'), pc.Card('5h'), pc.Card('6h'), pc.Card('7h'), pc.Card('8h'), pc.Card('9h'), pc.Card('10h'), pc.Card('jh'), pc.Card('qh'), pc.Card('kh'), pc.Card('ah')]
        score, _ = s.check(hand)
        self.assertEqual(score, 0)
        hand = [pc.Card('2h'), pc.Card('3h'), pc.Card('4h'), pc.Card('5h'), pc.Card('6h'), pc.Card('7h'), pc.Card('8h'), pc.Card('9h'), pc.Card('10h'), pc.Card('jh'), pc.Card('qh'), pc.Card('kh'), pc.Card('ah')]
        score, _ = s.check(hand)
        self.assertEqual(score, 0)
        hand = [pc.Card('9h'), pc.Card('9h'), pc.Card('9h'), pc.Card('8h')]
        score, _ = s.check(hand)
        self.assertEqual(score, 0)
        hand = [pc.Card('9h')]
        score, _ = s.check(hand)
        self.assertEqual(score, 0)

    def test_pair_minimumcards(self):
        s = scoring.HasPairTripleQuad()
        hand = [pc.Card('9h'), pc.Card('9h')]
        score, _ = s.check(hand)
        self.assertEqual(score, 2)
        hand = [pc.Card('9h'), pc.Card('9h'), pc.Card('9h')]
        score, _ = s.check(hand)
        self.assertEqual(score, 6)
        hand = [pc.Card('9h'), pc.Card('9h'), pc.Card('9h'), pc.Card('9h')]
        score, _ = s.check(hand)
        self.assertEqual(score, 12)


class TestExactlyEqualsN(unittest.TestCase):
    def setUp(self):
        pass

    def test_ExactlyEqualsN15_count_is_equal(self):
        s = scoring.ExactlyEqualsN(n=15)
        hand = [pc.Card('9h'), pc.Card('as'), pc.Card('5d')]
        score, _ = s.check(hand)
        self.assertEqual(score, 2)

    def test_ExactlyEqualsN15_count_is_less_than(self):
        s = scoring.ExactlyEqualsN(n=15)
        hand = [pc.Card('9h'), pc.Card('5d')]
        score, _ = s.check(hand)
        self.assertEqual(score, 0)

    def test_ExactlyEqualsN15_count_is_greater_than(self):
        s = scoring.ExactlyEqualsN(n=15)
        hand = [pc.Card('9h'), pc.Card('9c'), pc.Card('as'), pc.Card('5d')]
        score, _ = s.check(hand)
        self.assertEqual(score, 0)

    def test_ExactlyEqualsN15_one_card(self):
        s = scoring.ExactlyEqualsN(n=15)
        hand = [pc.Card('as')]
        score, _ = s.check(hand)
        self.assertEqual(score, 0)

    def test_ExactlyEqualsN31_count_is_equal(self):
        s = scoring.ExactlyEqualsN(n=31)
        hand = [pc.Card('9h'), pc.Card('ah'), pc.Card('jh'), pc.Card('qh'), pc.Card('as')]
        score, _ = s.check(hand)
        self.assertEqual(score, 1)

    def test_ExactlyEqualsN31_count_is_less_than(self):
        s = scoring.ExactlyEqualsN(n=31)
        hand = [pc.Card('9h'), pc.Card('ah'), pc.Card('jh'), pc.Card('qh')]
        score, _ = s.check(hand)
        self.assertEqual(score, 0)

    def test_ExactlyEqualsN31_count_is_greater_than(self):
        s = scoring.ExactlyEqualsN(n=31)
        hand = [pc.Card('9h'), pc.Card('ah'), pc.Card('jh'), pc.Card('qh'), pc.Card('2s')]
        score, _ = s.check(hand)
        self.assertEqual(score, 0)


class TestHasStraight_DuringPlay(unittest.TestCase):

    def setUp(self):
        self.s = scoring.HasStraight_DuringPlay()

    def test_HasStraight_DuringPlay_2card(self):
        hand = [pc.Card('4h'), pc.Card('5s')]
        score, _ = self.s.check(hand)
        self.assertEqual(score, 0)

    def test_HasStraight_DuringPlay_3card(self):
        hand = [pc.Card('4h'), pc.Card('5s'), pc.Card('6d')]
        score, _ = self.s.check(hand)
        self.assertEqual(score, 3)

    def test_HasStraight_DuringPlay_4card(self):
        hand = [pc.Card('2h'), pc.Card('4h'), pc.Card('5s'), pc.Card('6d'), pc.Card('7d')]
        score, _ = self.s.check(hand)
        self.assertEqual(score, 4)

    def test_HasStraight_DuringPlay_3card_after_broken(self):
        hand = [pc.Card('2h'), pc.Card('4h'), pc.Card('5s'), pc.Card('6d'), pc.Card('7d'), pc.Card('5c')]
        score, _ = self.s.check(hand)
        self.assertEqual(score, 3)

    def test_HasStraight_DuringPlay_6card_outoforder(self):
        hand = [pc.Card('2h'), pc.Card('4h'), pc.Card('5s'), pc.Card('6d'), pc.Card('7d'), pc.Card('3c')]
        score, _ = self.s.check(hand)
        self.assertEqual(score, 6)

    def test_HasStraight_DuringPlay_4card_broken(self):
        hand = [pc.Card('4h'), pc.Card('5s'), pc.Card('6d'), pc.Card('7d'), pc.Card('2c')]
        score, _ = self.s.check(hand)
        self.assertEqual(score, 0)

    def test_HasStraight_DuringPlay_12card(self):
        hand = [pc.Card(f"{r}h") for r in ['a','2','3','4','5','6','7','8','9','10','j','q','k']]
        score, _ = self.s.check(hand)
        self.assertEqual(score, 13)


class TestHasStraight_InHand(unittest.TestCase):

    def setUp(self):
        self.s = scoring.HasStraight_InHand()

    def test_HasStraight_InHand_2card(self):
        hand = [pc.Card('4h'), pc.Card('5s')]
        score, _ = self.s.check(hand)
        self.assertEqual(score, 0)

    def test_HasStraight_InHand_3card(self):
        hand = [pc.Card('4h'), pc.Card('5s'), pc.Card('6d')]
        score, _ = self.s.check(hand)
        self.assertEqual(score, 3)

    def test_HasStraight_InHand_4card(self):
        hand = [pc.Card('2h'), pc.Card('4h'), pc.Card('5s'), pc.Card('6d'), pc.Card('7d')]
        score, _ = self.s.check(hand)
        self.assertEqual(score, 4)

    def test_HasStraight_InHand_Double_4_Straight(self):
        hand = [pc.Card('2h'), pc.Card('4h'), pc.Card('5s'), pc.Card('6d'), pc.Card('7d'), pc.Card('5c')]
        score, _ = self.s.check(hand)
        self.assertEqual(score, 8)

    def test_HasStraight_InHand_6card_outoforder(self):
        hand = [pc.Card('2h'), pc.Card('4h'), pc.Card('5s'), pc.Card('6d'), pc.Card('7d'), pc.Card('3c')]
        score, _ = self.s.check(hand)
        self.assertEqual(score, 6)

    def test_HasStraight_InHand_4card_broken(self):
        hand = [pc.Card('4h'), pc.Card('5s'), pc.Card('6d'), pc.Card('7d'), pc.Card('2c')]
        score, _ = self.s.check(hand)
        self.assertEqual(score, 4)

    def test_HasStraight_InHand_ThreePairs(self):
        hand = [pc.Card('4h'), pc.Card('4s'), pc.Card('5d'), pc.Card('5s'), pc.Card('6d'), pc.Card('6h'), pc.Card('2c')]
        score, _ = self.s.check(hand)
        self.assertEqual(score, 24)

    def test_HasStraight_InHand_NoStraight(self):
        hand = [pc.Card('2h'), pc.Card('4s'), pc.Card('6d'), pc.Card('8s'), pc.Card('10d'), pc.Card('qh')]
        score, _ = self.s.check(hand)
        self.assertEqual(score, 0)

    def test_HasStraight_InHand_EmptyHand(self):
        hand = []
        score, _ = self.s.check(hand)
        self.assertEqual(score, 0)

    def test_HasStraight_InHand_12card(self):
        hand = [pc.Card(f"{r}h") for r in ['a','2','3','4','5','6','7','8','9','10','j','q','k']]
        score, _ = self.s.check(hand)
        self.assertEqual(score, 13)


class TestCountCombinationsEqualToN(unittest.TestCase):
    def setUp(self):
        pass

    def test_CountCombinationsEqualToN_one(self):
        s = scoring.CountCombinationsEqualToN(n=15)
        hand = [pc.Card('9h'), pc.Card('as'), pc.Card('5d')]
        score, _ = s.check(hand)
        self.assertEqual(score, 2)

    def test_CountCombinationsEqualToN_two_overlapping(self):
        s = scoring.CountCombinationsEqualToN(n=15)
        hand = [pc.Card('9h'), pc.Card('5c'), pc.Card('as'), pc.Card('5d')]
        score, _ = s.check(hand)
        self.assertEqual(score, 4)

    def test_CountCombinationsEqualToN_two_nonoverlapping(self):
        s = scoring.CountCombinationsEqualToN(n=15)
        hand = [pc.Card('9h'), pc.Card('5c'), pc.Card('as'), pc.Card('7d'), pc.Card('8d')]
        score, _ = s.check(hand)
        self.assertEqual(score, 4)


class TestCribbageBoard(unittest.TestCase):
    def setUp(self):
        self.players = [RandomPlayer("Player1"), RandomPlayer("Player2")]
        self.board = CribbageBoard(players=self.players, max_score=121)

    def test_peg(self):
        self.board.peg(self.players[0], 100)
        self.assertEqual(self.board.pegs[self.players[0].name]['front'], 100)
        self.assertEqual(self.board.pegs[self.players[0].name]['rear'], 0)

    def test_peg_leapfrog(self):
        self.board.peg(self.players[0], 100)
        self.board.peg(self.players[0], 5)
        self.assertEqual(self.board.pegs[self.players[0].name]['front'], 105)
        self.assertEqual(self.board.pegs[self.players[0].name]['rear'], 100)