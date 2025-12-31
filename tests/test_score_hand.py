from cribbage.playingcards import build_hand
from cribbage.scoring import HasFlush, score_hand

import logging

logger = logging.getLogger(__name__)

def test_has_flush():
    kept_key = "3H|4H|5H|6H"
    is_crib = False
    starter_card = None
    score_scenarios = [HasFlush(is_crib=is_crib, starter_card=starter_card)]
    cards = build_hand(kept_key)
    score = 0
    for scenario in score_scenarios:
        s, desc = scenario.check(cards[:])
        score += s
        if desc:
            logger.info("[EOR SCORING] " + desc)
    assert score == 4

def test_score_hand_flush_and_run():
    kept_key = "3H|4H|5H|6H"
    score = score_hand(build_hand(kept_key), is_crib=False)
    assert score == 10