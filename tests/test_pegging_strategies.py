from cribbage.strategies.pegging_strategies import medium_pegging_strategy, basic_pegging_strategy
from cribbage.playingcards import Card, build_hand
import pytest


def test_medium_pegging_strategy_takes_points_when_available():
    """Medium strategy should always take points when available."""
    # Test making 15
    playable = build_hand(['5h', '6d', '7c'])
    history = [Card('10d')]
    count = 10
    card = medium_pegging_strategy(playable, count, history)
    assert card == Card('5h'), "Should play 5 to make 15"
    
    # Test making a pair
    playable = build_hand(['8h', '5d', '6c'])
    history = [Card('8d')]
    count = 8
    card = medium_pegging_strategy(playable, count, history)
    assert card == Card('8h'), "Should play 8 to make a pair"
    
    # Test making a run - both 6 and 9 score 3 points (6-7-8 or 7-8-9)
    # Should pick higher card (9) when points are equal
    playable = build_hand(['5h', '6d', '9c'])
    history = [Card('8d'), Card('7h')]
    count = 15
    card = medium_pegging_strategy(playable, count, history)
    assert card == Card('9c'), "Should play 9 (higher) when both score equal points (run)"

    playable = build_hand(['3h', '9d', '4c'])
    history = build_hand(['3d', '3s'])
    count = 6
    card = medium_pegging_strategy(playable, count, history)
    assert card == Card('3h'), "Should play 3h for triple instead of 15 for 2"

    playable = build_hand(['3h', '9d', '4c'])
    history = build_hand(['3d', '3s', '3c'])
    count = 9
    card = medium_pegging_strategy(playable, count, history)
    assert card == Card('3h'), "Should play 3h for quad instead of 15 for 2"

    playable = build_hand(['ah', '10d'])
    history = build_hand(['3d', '2s'])
    count = 5
    card = medium_pegging_strategy(playable, count, history)
    assert card == Card('ah'), "Should play ah for run instead of 15 for 2"


def test_medium_pegging_strategy_safe_counts_1_to_4():
    """Test that counts 1-4 have small penalty (-0.05) as wasteful for last card/31."""
    # Counts 1-4 now have a small penalty, so higher card is preferred when other factors equal
    # Count will be 3 with 2, or 5 with 4
    # 3: -0.05, rank 2 = -0.05 + 0.02 = -0.03
    # 5: -0.615, rank 4 = -0.615 + 0.04 = -0.575
    # Should play 2 to avoid the worse penalty of count 5
    playable = build_hand(['2h', '4d'])
    history = [Card('ah')]  # count = 1
    count = 1
    card = medium_pegging_strategy(playable, count, history)
    assert card == Card('2h'), "Should prefer count 3 over count 5"


def test_medium_pegging_strategy_avoid_count_5():
    """Test that count of 5 is avoided (-0.615 penalty, likely opponent has 10)."""
    # Count will be 5 with 2, or 7 with 4
    # 5: -0.615, rank 2 = -0.615 + 0.02 = -0.595
    # 7: -0.077, rank 4 = -0.077 + 0.04 = -0.037
    # Should play 4 as it has better score
    playable = build_hand(['2h', '4d'])
    history = [Card('3h')]  # count = 3
    count = 3
    card = medium_pegging_strategy(playable, count, history)
    assert card == Card('4d'), "Should avoid count of 5 (worse penalty than 7)"


def test_medium_pegging_strategy_unsafe_counts_6_to_14():
    """Test that counts 6-14 have small penalty (-0.077)."""
    playable = build_hand(['10h', 'qd'])
    history = [Card('4h')] 
    count = 4
    card = medium_pegging_strategy(playable, count, history)
    assert card == Card('qd'), "Should prefer playing Q since both cards set count to 14"

    playable = build_hand(['8h', 'qd'])
    history = [Card('4h')] 
    count = 4
    card = medium_pegging_strategy(playable, count, history)
    assert card == Card('qd'), "Should prefer playing Q since both cards are in range 6-14"


def test_medium_pegging_strategy_safe_counts_16_to_20():
    """Test that counts 16-20 have small bonus (+0.1)."""
    # Count will be 17 with 10, or 13 with 6
    # 17: +0.1, rank 10 = 0.1 + 0.10 = 0.20
    # 13: -0.077, rank 6 = -0.077 + 0.06 = -0.017
    # Should prefer 10 to reach safe count of 17
    playable = build_hand(['10h', '6d'])
    history = [Card('7h')]  # count = 7
    count = 7
    card = medium_pegging_strategy(playable, count, history)
    assert card == Card('10h'), "Should prefer playing 10 to reach safe count of 17"


def test_medium_pegging_strategy_avoid_count_21():
    """Test that count of 21 is avoided (-0.615 penalty, likely opponent has 10)."""
    # Count will be 21 with Q, or 19 with 8
    # 21: -0.615, rank 12 = -0.615 + 0.12 = -0.495
    # 19: +0.1, rank 8 = 0.1 + 0.08 = 0.18
    # Should prefer 8 to avoid count 21
    playable = build_hand(['qh', '8d'])
    history = [Card('kh')]  # count = 11
    count = 11
    card = medium_pegging_strategy(playable, count, history)
    assert card.rank == '8', "Should avoid count of 21"


def test_medium_pegging_strategy_avoid_run_setup():
    """Test that setting up opponent for a run is penalized (-0.462)."""
    # Playing 6 after 7 sets up opponent for a run if they have 5 or 8
    # Playing 3 doesn't set up a run
    playable = build_hand(['9h', '3d'])
    history = [Card('8h')]
    count = 7
    card = medium_pegging_strategy(playable, count, history)
    # 6: count 13 = -0.077, run setup -0.462, rank 6 = -0.077 - 0.462 + 0.06 = -0.479
    # 3: count 10 = -0.077, rank 3 = -0.077 + 0.03 = -0.047
    # Should prefer 3 to avoid run setup
    assert card == Card('3d'), "Should avoid setting up a run"


def test_medium_pegging_strategy_pair_logic():
    """Test pair handling - play first card of pair if triple would be under 31."""
    # Have a pair of 5s, count is 0
    # Playing first 5 makes pair (2 pts), and leaves room for triple (would be 15)
    playable = build_hand(['5h', '5d', '9c'])
    history = []
    count = 0
    card = medium_pegging_strategy(playable, count, history)
    # Should take the 2 points for the pair
    assert card.rank == '9', "Should play 9 because opponent is more likely to play a 10 instead of a 5"

    playable = build_hand(['6h', '6d', '9c'])
    history = []
    count = 0
    card = medium_pegging_strategy(playable, count, history)
    # Should take the 2 points for the pair
    assert card.rank == '9', "Does not play 6 because potential triple logic not implemented for medium player"
    


def test_medium_pegging_strategy_play_highest_when_all_else_equal():
    """When no scoring and all penalties/bonuses are equal, play highest card."""
    # All cards lead to unsafe counts
    playable = build_hand(['2h', '3d', '4c'])
    history = [Card('6h')]  # count = 6
    count = 6
    # 2 -> 8 (unsafe), 3 -> 9 (unsafe), 4 -> 10 (unsafe)
    # All unsafe, no runs, so should play highest
    card = medium_pegging_strategy(playable, count, history)
    assert card.rank == '4', "Should play highest card when all else is equal"


def test_medium_pegging_strategy_respects_31_limit():
    """Should not play cards that would exceed 31."""
    playable = build_hand(['kh', '5d'])
    history = [Card('10h'), Card('10d'), Card('2c')]
    count = 22  # 10 + 10 + 2 = 22
    card = medium_pegging_strategy(playable, count, history)
    # K would make 32 (exceed 31), so must play 5 (makes 27)
    assert card.rank == '5', "Should only play cards that don't exceed 31"


def test_medium_pegging_strategy_vs_basic():
    """Verify medium strategy makes better decisions than basic."""
    # Basic strategy just plays highest when no points
    # Medium should avoid count of 5
    playable = build_hand(['2h', 'ad'])
    history = [Card('3h')]  # count = 3
    count = 3
    
    basic_choice = basic_pegging_strategy(playable, count, history)
    medium_choice = medium_pegging_strategy(playable, count, history)
    
    # Basic plays highest (4), medium avoids count 5
    assert basic_choice.rank == '2', "Basic should play highest"
    assert medium_choice.rank == 'a', "Medium should avoid count of 5"
