from cribbage.players.beginner_player import BeginnerPlayer
from cribbage.players.medium_player import MediumPlayer
from cribbage.utils import play_multiple_games
import logging
import numpy as np

logging.basicConfig(level=logging.WARNING)

beginner_player = BeginnerPlayer(name='BeginnerPlayer')
medium_player = MediumPlayer(name='MediumPlayer')

print("Running 20 trials of 100 games each to check variance...")
winrates = []
avg_diffs = []
for trial in range(20):
    results = play_multiple_games(100, p0=medium_player, p1=beginner_player)
    winrate = results["winrate"]
    wins = results["wins"]
    avg_diff = sum(results["diffs"])/len(results["diffs"])
    winrates.append(winrate)
    avg_diffs.append(avg_diff)
    print(f"Trial {trial+1:2d}: Winrate={winrate:.2%} ({wins:2d}/100), Avg diff={avg_diff:6.2f}")

print(f"\nSummary:")
print(f"Mean winrate: {np.mean(winrates):.2%}")
print(f"Std dev winrate: {np.std(winrates):.2%}")
print(f"Min winrate: {min(winrates):.2%}")
print(f"Max winrate: {max(winrates):.2%}")
print(f"\nMean avg diff: {np.mean(avg_diffs):.2f}")
print(f"Std dev avg diff: {np.std(avg_diffs):.2f}")
