from cribbage.playingcards import Card, build_hand
from cribbage.scoring import score_hand
import itertools
from cribbage.players.rule_based_player import get_full_deck
from collections import Counter

dealt_hand = build_hand(['5h','6c','7d','9h','2h','10d'])
# When we keep 2H|5H|6C|7D, we discard 9H|10D
discarded_cards = build_hand(['9h','10d'])
full_deck = get_full_deck()
starter_pool = [c for c in full_deck if c not in dealt_hand]

# Maybe the crib calculator uses only rank information and assigns suits uniformly?
# Let me check my function's calculation by comparing the total

# According to my function: 4.38
# According to brute force: 4.84
# According to test: 3.80

# The difference suggests the crib calculator might be using different assumptions
# Let me check if the issue is with suit handling

print("Testing with specific example:")
print(f"Our discards: {discarded_cards}")

# Test one specific case manually
opp_discard = [Card('3c'), Card('4d')]  # Random opponent discard
starter = Card('5s')  # Random starter (not 5h, 5d since those are dealt)
crib = list(discarded_cards) + opp_discard
score1 = score_hand(crib, is_crib=True, starter_card=starter)
print(f"Crib {crib} with starter {starter}: {score1}")

# Now let me check: what if the expected values are for YOUR crib, not opponent's?
# When dealer_is_self=True
print("\n\nWhat if it's actually OUR crib when we're dealer?")
