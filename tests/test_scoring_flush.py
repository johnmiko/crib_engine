import pytest

from cribbage.cribbagegame import CribbageGame
from cribbage.cribbageround import CribbageRound
from cribbage.players.random_player import RandomPlayer
from cribbage.playingcards import Card, Deck, build_hand
from cribbage.scoring import score_hand

def make_card(rank: str, suit: str) -> Card:
    # Accepts rank and suit as names, e.g., ("five", "spades")
    rank_map = {'ace': 'a', 'two': '2', 'three': '3', 'four': '4', 'five': '5', 'six': '6', 'seven': '7', 'eight': '8', 'nine': '9', 'ten': '10', 'jack': 'j', 'queen': 'q', 'king': 'k'}
    suit_map = {'hearts': 'h', 'diamonds': 'd', 'clubs': 'c', 'spades': 's'}
    return Card(f"{rank_map[rank]}{suit_map[suit]}")

def make_round() -> CribbageRound:
    game = CribbageGame(players=[RandomPlayer("player1"), RandomPlayer("player2")])
    return CribbageRound(game, dealer=game.players[0])

def make_flush_cards(starter_suit: str):
    """Four heart hand cards plus a starter in the requested suit."""
    return [
        make_card("eight", "hearts"),
        make_card("nine", "hearts"),
        make_card("queen", "hearts"),
        make_card("king", "hearts"),
        make_card("three", starter_suit),
    ]

def test_hand_flush_scores_four_without_starter_match():
    hand = build_hand(["3h", "8h", "9h", "qh", "kc"])
    score = score_hand(hand, is_crib=False)
    assert score == 4

def test_hand_flush_scores_five_with_starter_match():
    hand = build_hand(["3h", "8h", "9h", "qh", "kh"])
    score = score_hand(hand, is_crib=False)
    assert score == 5

def test_crib_flush_no_starter_is_0():
    score = score_hand(build_hand(["3h", "8h", "9h", "qh", "kc"]), is_crib=True)
    assert score == 0

def test_crib_flush_with_starter_is_5():
    score = score_hand(build_hand(["3h", "8h", "9h", "qh", "kh"]), is_crib=True)
    assert score == 5

def test_explicit_starter_card_is_handled_correctly():
    score = score_hand(build_hand(["3h", "8h", "9h", "qh"]), is_crib=True, starter_card=Card("kh"))
    assert score == 5
    score = score_hand(build_hand(["3h", "8h", "9h", "qh"]), is_crib=True, starter_card=Card("kc"))
    assert score == 0
    score = score_hand(build_hand(["3h", "8h", "9h", "qh"]), is_crib=False, starter_card=Card("kc"))
    assert score == 4
    score = score_hand(build_hand(["3h", "8h", "9h", "qh"]), is_crib=False, starter_card=Card("kh"))
    assert score == 5