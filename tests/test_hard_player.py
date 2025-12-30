from cribbage.players.hard_player import HardPlayer
from cribbage.playingcards import build_hand


def test_hard_player_chooses_correct_discard():
    player = HardPlayer()
    hand = build_hand(["ac","ad","ah","as","2h","2d"])
    crib_cards = player.select_crib_cards(hand, dealer_is_self=True)
    assert crib_cards == build_hand(["ac","ad"])