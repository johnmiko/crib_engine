from cribbage.playingcards import Card, build_hand
from cribbage.scoring import HasFlush, score_hand

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
            logger.info("[EOR SCORING] " + desc)
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


