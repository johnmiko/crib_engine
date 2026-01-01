from cribbage.players.beginner_player import BeginnerPlayer
from cribbage.players.medium_player import MediumPlayer
from cribbage.utils import play_multiple_games
import logging

logging.basicConfig(level=logging.WARNING)

beginner_player = BeginnerPlayer(name='BeginnerPlayer')
medium_player = MediumPlayer(name='MediumPlayer')

print("Running 5 trials of 100 games each...")
for trial in range(5):
    results = play_multiple_games(100, p0=medium_player, p1=beginner_player)
    winrate = results["winrate"]
    wins = results["wins"]
    avg_diff = sum(results["diffs"])/len(results["diffs"])
    print(f"Trial {trial+1}: Winrate={winrate:.2%} ({wins}/100), Avg diff={avg_diff:.2f}")
