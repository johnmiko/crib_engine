from cribbage.playingcards import Card, build_hand
from cribbage.scoring import score_hand
import itertools
from cribbage.players.rule_based_player import get_full_deck

dealt_hand = build_hand(['5h','6c','7d','9h','2h','10d'])
# When we keep 2H|5H|6C|7D, we discard 9H|10D
discarded_cards = build_hand(['9h','10d'])
full_deck = get_full_deck()
starter_pool = [c for c in full_deck if c not in dealt_hand]

# The actual crib calculation should be:
# - Our 2 discards (9H, 10D)
# - Opponent's 2 discards (from the remaining 46 cards)
# - 1 starter card (from the remaining 44 cards after opponent discards)

total = 0
count = 0

# Choose 2 cards for opponent's discard
for opp_discard in itertools.combinations(starter_pool, 2):
    remaining_for_starter = [c for c in starter_pool if c not in opp_discard]
    
    # Choose 1 starter from the remaining cards
    for starter in remaining_for_starter:
        crib_hand = list(discarded_cards) + list(opp_discard)
        score = score_hand(crib_hand, is_crib=True, starter_card=starter)
        total += score
        count += 1

print(f'Average: {total/count:.2f}, Count: {count}')
print(f'Expected: 3.80')
