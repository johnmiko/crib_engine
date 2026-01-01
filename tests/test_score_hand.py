from cribbage.playingcards import Card, build_hand
from cribbage.scoring import HasFlush, score_hand, JackMatchStarterSuitScorer

import logging

logger = logging.getLogger(__name__)

def test_has_flush():
    kept_key = "3H|4H|5H|6H"
    is_crib = False
    starter_card = None
    score_scenarios = [HasFlush(is_crib=is_crib)]
    cards = build_hand(kept_key)
    score = 0
    for scenario in score_scenarios:
        s, desc = scenario.check(cards[:], starter=starter_card)
        score += s
        if desc:
            logger.debug("[EOR SCORING] " + desc)
    assert score == 4

def test_score_hand_flush_and_run():
    kept_key = "3H|4H|5H|6H"
    score = score_hand(build_hand(kept_key), is_crib=False)
    assert score == 10

def test_score_hand_flush_and_run_and_15s():
    kept_key = "3H|4H|5H|6H"
    starter = Card("ks")
    score = score_hand(build_hand(kept_key), is_crib=False, starter_card=starter)
    assert score == 12

def test_crib_has_flush_is_correct():
    kept_key = "AH|2H|9H|10H"
    starter = Card("ks")
    score = score_hand(build_hand(kept_key), is_crib=True, starter_card=starter)
    assert score == 0
    kept_key = "AH|2H|9H|10H"
    starter = Card("kh")
    score = score_hand(build_hand(kept_key), is_crib=True, starter_card=starter)
    assert score == 5
    kept_key = "AH|2H|9H|10H|ks"    
    score = score_hand(build_hand(kept_key), is_crib=True, starter_card=None)
    assert score == 0
    kept_key = "AH|2H|9H|10H|kh"
    score = score_hand(build_hand(kept_key), is_crib=True, starter_card=None)
    assert score == 5

def test_jack_matches_starter_suit_in_crib():
    kept_key = "jH|jc|js|jd|kh"
    score = score_hand(build_hand(kept_key), is_crib=True, starter_card=None)
    assert score == 13
    kept_key = "jH|jc|js|jd"
    starter_card = Card("kh")
    score = score_hand(build_hand(kept_key), is_crib=True, starter_card=starter_card)
    assert score == 13
    kept_key = "jH|ac|8s|9d|kh"
    score = score_hand(build_hand(kept_key), is_crib=True, starter_card=None)
    assert score == 1
    kept_key = "jH|ac|8s|9d"
    starter_card = Card("kh")
    score = score_hand(build_hand(kept_key), is_crib=True, starter_card=starter_card)
    assert score == 1
    kept_key = "jc|ac|8s|9d|kh"
    score = score_hand(build_hand(kept_key), is_crib=True, starter_card=None)
    assert score == 0
    kept_key = "jc|ac|8s|9d"
    starter_card = Card("kh")
    score = score_hand(build_hand(kept_key), is_crib=True, starter_card=starter_card)
    assert score == 0


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

def test_jack_match_starter_suit_scores_one():
    hand = build_hand(["ah","ac","jh","ks", "2h"])
    assert JackMatchStarterSuitScorer().check(hand) == (1, "Jack match starter suit")

def test_jack_match_starter_suit_scores_zero():
    hand = build_hand(["ah","ac","jh","ks", "2d"])
    assert JackMatchStarterSuitScorer().check(hand) == (0, "")

def test_no_jack_in_hand_and_starter_is_jack():
    hand = build_hand(["ah","ac","2h","ks", "jh"])
    assert JackMatchStarterSuitScorer().check(hand) == (0, "")