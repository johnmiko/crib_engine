from cribbage.players.beginner_player import BeginnerPlayer
from cribbage.playingcards import Card, build_hand
import pytest


def test_beginner_player_discard_5_5_6_7_9_q():
    """Test that beginner player chooses correct discards for hand: 5,5,6,7,9,Q"""
    player = BeginnerPlayer(name="Beginner")
    hand = build_hand(['5h', '5d', '6c', '7s', '9h', 'qd'])
    
    # As dealer (keeping cards that benefit own crib)
    crib_cards_dealer = player.select_crib_cards(hand.copy(), dealer_is_self=True)
    # Convert to set for easier comparison (order doesn't matter)
    discarded_ranks_dealer = sorted([c.rank for c in crib_cards_dealer])
    
    # As non-dealer (keeping cards that minimize opponent's crib)
    crib_cards_non_dealer = player.select_crib_cards(hand.copy(), dealer_is_self=False)
    discarded_ranks_non_dealer = sorted([c.rank for c in crib_cards_non_dealer])
    
    # Calculate expected discards:
    # Keeping 5,5,6,7 (4 cards) = 8 points (pair of 5s + 15s)
    # Discarding 9,Q to crib = 0 points in crib
    # Dealer: 8 + 0 = 8
    # Non-dealer: 8 - 0 = 8
    
    # Keeping 5,6,7,9 (4 cards) = 5 points (run of 3: 5-6-7, plus 15: 6+9)
    # Discarding 5,Q to crib = 0 points
    # Dealer: 5 + 0 = 5
    # Non-dealer: 5 - 0 = 5
    
    # Keeping 5,6,7,Q (4 cards) = 5 points (run of 3: 5-6-7, plus 15: 5+Q)
    # Discarding 5,9 to crib = 0 points
    # Dealer: 5 + 0 = 5
    # Non-dealer: 5 - 0 = 5
    
    # Best choice for both dealer and non-dealer should be keeping 5,5,6,7
    # and discarding 9,Q
    expected_discards = ['9', 'q']    
    assert discarded_ranks_dealer == expected_discards, \
        f"Expected to discard {expected_discards} as dealer, but got {discarded_ranks_dealer}"
    assert discarded_ranks_non_dealer == expected_discards, \
        f"Expected to discard {expected_discards} as non-dealer, but got {discarded_ranks_non_dealer}"


def test_beginner_player_basic_pegging_strategy():    
    player = BeginnerPlayer(name="Beginner")    
    # Test 1: Empty table, count=0
    # NOTE: basic_pegging_strategy has a bug - when no points available, it plays
    # the first card instead of the highest. So it will play 5h (first card in hand)
    # rather than 7s (highest card). This test documents actual behavior.
    table = []
    # First king is played    
    assert player.select_card_to_play(build_hand(['ah', '10d', 'kc', 'ks']), table, count=0) == Card("kc")
    # First king is played    
    assert player.select_card_to_play(build_hand(['ks', 'ah', '10d', 'kc']), table, count=0) == Card("ks")
    # 5d, 10d,ks,kc score 2 points, so first king is played (highest rank)
    assert player.select_card_to_play(build_hand(['5d', '10d', 'js','jc']), build_hand(["5c"]), count=5) == Card("js")
    # 5d and 2d score 3 points so it is played. 5 is higher so it's played
    assert player.select_card_to_play(build_hand(['5d', '2d', 'ks','kc']), build_hand(["3d","4c"]), count=7) == Card("5d")
    # below are added asserts of errors I saw while playing    
    # when actually playing a game, beginner did not play correct cards here    
    # Test 2: Opponent plays 8, count=8 - player can make 15 with 7
    # Basic pegging strategy should prioritize scoring 15
    table = [Card('8h')]
    remaining_hand = build_hand(['5h', '5d', '6c', '7s'])
    card_played = player.select_card_to_play(remaining_hand.copy(), table, count=8)
    assert card_played.rank == '7', f"Expected to play 7 to make 15, but played {card_played.rank}"
    
    # Test 3: Table is [8, 7], count=15 - player has 5,5,6 left
    # Playing 6 makes a run of 3 (6-7-8) for 3 points!
    table = [Card('8h'), Card('7d')]
    remaining_hand = build_hand(['5h', '5d', '6c'])
    card_played = player.select_card_to_play(remaining_hand.copy(), table, count=15)
    # Should play 6 to score 3 points for the run
    assert card_played.rank == '6', f"Expected to play 6 to make run (6-7-8), but played {card_played.rank}"
    
    # Test 4: Count is 26, can only play 5 (not 6 as it would bust)
    table = [Card('8h'), Card('7d'), Card('6s'), Card('5c')]
    remaining_hand = build_hand(['5h', '5d'])
    card_played = player.select_card_to_play(remaining_hand.copy(), table, count=26)
    assert card_played.rank == '5', f"Expected to play 5 (only playable card), but played {card_played.rank}"
    
    # Test 5: Count is 21, player has [5,5,6] left, opponent played [8,7,5]
    # Playing 5 makes a pair for 2 points, but playing 6 makes a run of 4 (5-6-7-8) for 4 points!
    table = [Card('8h'), Card('7d'), Card('5c')]
    remaining_hand = build_hand(['5h', '5d', '6c'])
    card_played = player.select_card_to_play(remaining_hand.copy(), table, count=21)
    # Should play 6 to make run of 4 for 4 points (better than pair for 2 points)
    assert card_played.rank == '6', f"Expected to play 6 to make run of 4, but played {card_played.rank}"
    
    # Test 6: Opponent plays 10, count=10 - player can make 15 with a 5
    table = [Card('10h')]
    remaining_hand = build_hand(['5h', '5d', '6c', '7s'])
    card_played = player.select_card_to_play(remaining_hand.copy(), table, count=10)
    # Should play 5 to make 15 (scores 2 points)
    assert card_played.rank == '5', f"Expected to play 5 to make 15, but played {card_played.rank}"
    
    # Test 7: Count is 24, opponent played [8,7,9]
    # Playing 7 makes a pair for 2 points + doesn't reach 31
    # Playing 6 makes a run of 4 (6-7-8-9) for 4 points!
    table = [Card('8h'), Card('7d'), Card('9c')]
    remaining_hand = build_hand(['5h', '5d', '6c', '7s'])
    card_played = player.select_card_to_play(remaining_hand.copy(), table, count=24)
    # Should play 6 to make run of 4 for 4 points (better than pair or 31)
    assert card_played.rank == '6', f"Expected to play 6 to make run of 4, but played {card_played.rank}"
