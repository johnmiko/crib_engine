"""Calculate exact crib scores for all hand combinations to verify test expectations."""
import sys

sys.path.append(".")
from cribbage.playingcards import build_hand
from cribbage.scoring import score_hand
import itertools
from cribbage.players.rule_based_player import get_full_deck
import pandas as pd
from time import perf_counter


dealt_hand = build_hand(["5h","6c","7d","9h","2h","10d"])
"3d,10c,6s,kd,6d,4c"
dealt_hand = build_hand(['3d', '10c', '6s', 'kd', '6d', '4c'])
full_deck = get_full_deck()

# Calculate exact crib scores for each possible discard
results = []

start = perf_counter()
for discard_idx in itertools.combinations(range(6), 2):
    kept_hand = [dealt_hand[i] for i in range(6) if i not in discard_idx]
    discarded_cards = [dealt_hand[i] for i in discard_idx]
    
    from cribbage.database import normalize_hand_to_str
    hand_key = normalize_hand_to_str(kept_hand)
    crib_key = normalize_hand_to_str(discarded_cards)
    
    starter_pool = [c for c in full_deck if c not in dealt_hand]
    
    # Calculate exact average crib score
    total = 0
    count = 0
    
    for opp_discard in itertools.combinations(starter_pool, 2):
        remaining_for_starter = [c for c in starter_pool if c not in opp_discard]
        
        for starter in remaining_for_starter:
            crib_hand = list(discarded_cards) + list(opp_discard)
            score = score_hand(crib_hand, is_crib=True, starter_card=starter)
            total += score
            count += 1
    
    avg_crib = total / count
    results.append({
        'hand_key': hand_key,
        'crib_key': crib_key,
        'avg_crib_score_exact': round(avg_crib, 2)
    })

end_time = perf_counter()
print(f"Calculated exact crib scores in {end_time - start:.2f} seconds.")
df = pd.DataFrame(results)
df = df.sort_values('hand_key')
print(df[['hand_key', 'avg_crib_score_exact']].to_string(index=False))
print("\n\nFormatted for test:")
print(f"hand_keys: {df['hand_key'].tolist()}")
print(f"avg_crib_scores: {df['avg_crib_score_exact'].tolist()}")
