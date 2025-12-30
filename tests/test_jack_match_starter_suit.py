import pytest
from cribbage.playingcards import Card, build_hand
from cribbage.scoring import JackMatchStarterSuitScorer

    
def test_jack_match_starter_suit_scores_one():
    hand = build_hand(["ah","ac","jh","ks", "2h"])
    assert JackMatchStarterSuitScorer().check(hand) == (1, "Jack match starter suit")

def test_jack_match_starter_suit_scores_zero():
    hand = build_hand(["ah","ac","jh","ks", "2d"])
    assert JackMatchStarterSuitScorer().check(hand) == (0, "")

def test_no_jack_in_hand_and_starter_is_jack():
    hand = build_hand(["ah","ac","2h","ks", "jh"])
    assert JackMatchStarterSuitScorer().check(hand) == (0, "")
