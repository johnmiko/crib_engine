"""Tests for end-of-game scenarios to ensure correct winner determination."""
from cribbage.cribbagegame import CribbageGame
from cribbage.cribbageround import CribbageRound
from cribbage.players.play_first_card_player import PlayFirstCardPlayer
from cribbage.playingcards import Card, build_hand
from logging import getLogger

logger = getLogger(__name__)


def test_p1_wins_by_pegging_to_121():
    """Test that p1 wins by pegging 15 for 2 points from 119 to 121."""
    p0 = PlayFirstCardPlayer(name="Player1")
    p1 = PlayFirstCardPlayer(name="Player2")
    game = CribbageGame(players=[p0, p1], seed=123)
    
    # Set both players to 119 points
    game.board.pegs[p0.name]['front'] = 119
    game.board.pegs[p0.name]['rear'] = 119
    game.board.pegs[p1.name]['front'] = 119
    game.board.pegs[p1.name]['rear'] = 119
    
    # Create a round where p0 (non-dealer) can peg 15 for 2 points
    round1 = CribbageRound(game=game, dealer=p1, seed=123)
    round1.hands = {
        p0.name: build_hand(['5h', '6d', '7c', '8s']),
        p1.name: build_hand(['ah', '2d', '3c', '4s'])
    }
    round1.starter = Card("9h")
    
    # p0 plays first (non-dealer), plays 5h
    # p1 plays 10-value card... wait, p1 doesn't have one
    # Let me set it up so p1 plays 10, then p0 plays 5 to make 15
    round1.hands = {
        p0.name: build_hand(['5h', '6d', '7c', '8s']),
        p1.name: build_hand(['10h', '10d', '10c', '10s'])
    }
    
    round1.play()
    
    # p1 plays 10h, p0 plays 5h for 15 and scores 2 points -> 121
    assert game.board.get_score(p0) == 121, f"Expected p0 to have 121, got {game.board.get_score(p0)}"
    # The game should recognize p0 as winner
    assert round1.game_winner == p0, "Expected p0 to be the winner"


def test_p2_wins_by_pegging_to_121():
    """Test that p2 wins by pegging 15 for 2 points from 119 to 121."""
    p0 = PlayFirstCardPlayer(name="Player1")
    p1 = PlayFirstCardPlayer(name="Player2")
    game = CribbageGame(players=[p0, p1], seed=123)
    
    # Set both players to 119 points
    game.board.pegs[p0.name]['front'] = 119
    game.board.pegs[p0.name]['rear'] = 119
    game.board.pegs[p1.name]['front'] = 119
    game.board.pegs[p1.name]['rear'] = 119
    
    # Create a round where p1 (dealer) can peg first to reach 121
    # p0 is non-dealer, plays first, plays a 10
    # p1 plays 5 to make 15 and win
    round1 = CribbageRound(game=game, dealer=p1, seed=123)
    round1.hands = {
        p0.name: build_hand(['10h', '10d', '10c', '10s']),
        p1.name: build_hand(['5h', '6d', '7c', '8s'])
    }
    round1.starter = Card("9h")
    
    round1.play()
    
    # p0 plays 10h, p1 plays 5h for 15 and scores 2 points -> 121
    assert game.board.get_score(p1) == 121, f"Expected p1 to have 121, got {game.board.get_score(p1)}"
    # The game should recognize p1 as winner
    assert round1.game_winner == p1, "Expected p1 to be the winner"


def test_p1_counts_first_and_wins():
    """Test that p1 (non-dealer) wins by counting hand first when p2 has crib."""
    p0 = PlayFirstCardPlayer(name="Player1")
    p1 = PlayFirstCardPlayer(name="Player2")
    game = CribbageGame(players=[p0, p1], seed=123)
    
    # Set both players to 119 points
    game.board.pegs[p0.name]['front'] = 119
    game.board.pegs[p0.name]['rear'] = 119
    game.board.pegs[p1.name]['front'] = 119
    game.board.pegs[p1.name]['rear'] = 119
    
    # p1 is dealer, so p0 counts first
    # p0 has a hand worth 2+ points, p1 has worthless hand
    round1 = CribbageRound(game=game, dealer=p1, seed=123)
    
    # Give p0 a pair for 2 points
    round1.player_hand_after_discard = {
        p0.name: build_hand(['5h', '5d', '6c', '7s']),
        p1.name: build_hand(['ah', '2d', '3c', '4s'])
    }
    round1.starter = Card("9h")
    round1.crib = build_hand(['10h', '10d'])
    
    # Skip pegging - just score hands
    round1.hands = {p0.name: [], p1.name: []}  # No cards left to peg
    round1.play()
    
    # p0 should reach at least 121
    assert game.board.get_score(p0) >= 121, f"Expected p0 to have >=121, got {game.board.get_score(p0)}"
    # The game should recognize p0 as winner
    assert round1.game_winner == p0, "Expected p0 to be the winner"


def test_p2_counts_first_and_wins():
    """Test that p2 (non-dealer) wins by counting hand first when p1 has crib."""
    p0 = PlayFirstCardPlayer(name="Player1")
    p1 = PlayFirstCardPlayer(name="Player2")
    game = CribbageGame(players=[p0, p1], seed=123)
    
    # Set both players to 119 points
    game.board.pegs[p0.name]['front'] = 119
    game.board.pegs[p0.name]['rear'] = 119
    game.board.pegs[p1.name]['front'] = 119
    game.board.pegs[p1.name]['rear'] = 119
    
    # p0 is dealer, so p1 counts first
    # p1 has a hand worth 2+ points, p0 has worthless hand
    round1 = CribbageRound(game=game, dealer=p0, seed=123)
    
    # Give p1 a pair for 2 points
    round1.player_hand_after_discard = {
        p0.name: build_hand(['ah', '2d', '3c', '4s']),
        p1.name: build_hand(['5h', '5d', '6c', '7s'])
    }
    round1.starter = Card("9h")
    round1.crib = build_hand(['10h', '10d'])
    
    # Skip pegging - just score hands
    round1.hands = {p0.name: [], p1.name: []}  # No cards left to peg
    round1.play()
    
    # p1 should reach at least 121
    assert game.board.get_score(p1) >= 121, f"Expected p1 to have >=121, got {game.board.get_score(p1)}"
    # The game should recognize p1 as winner
    assert round1.game_winner == p1, "Expected p1 to be the winner"


def test_p1_counts_second_and_wins():
    """Test that p1 (dealer) wins by counting hand second when p2 has 0 points."""
    p0 = PlayFirstCardPlayer(name="Player1")
    p1 = PlayFirstCardPlayer(name="Player2")
    game = CribbageGame(players=[p0, p1], seed=123)
    
    # Set both players to 119 points
    game.board.pegs[p0.name]['front'] = 119
    game.board.pegs[p0.name]['rear'] = 119
    game.board.pegs[p1.name]['front'] = 119
    game.board.pegs[p1.name]['rear'] = 119
    
    # p0 is dealer, so p1 counts first but has 0 points
    # p0 counts second and has 2+ points to win
    round1 = CribbageRound(game=game, dealer=p0, seed=123)
    
    # Give p0 a pair for 2 points, p1 has no points
    round1.player_hand_after_discard = {
        p0.name: build_hand(['5h', '5d', '6c', '7s']),
        p1.name: build_hand(['ah', '2d', '3c', '8s'])  # No scoring combinations
    }
    round1.starter = Card("9h")
    round1.crib = build_hand(['10h', 'jd'])
    
    # Skip pegging - just score hands
    round1.hands = {p0.name: [], p1.name: []}  # No cards left to peg
    round1.play()
    
    # p0 should reach at least 121
    assert game.board.get_score(p0) >= 121, f"Expected p0 to have >=121, got {game.board.get_score(p0)}"
    # The game should recognize p0 as winner
    assert round1.game_winner == p0, "Expected p0 to be the winner"


def test_p1_counts_second_and_wins_in_crib():
    """Test that p1 (dealer) wins via crib when both hands score 0."""
    p0 = PlayFirstCardPlayer(name="Player1")
    p1 = PlayFirstCardPlayer(name="Player2")
    game = CribbageGame(players=[p0, p1], seed=123)
    
    # Set both players to 119 points
    game.board.pegs[p0.name]['front'] = 119
    game.board.pegs[p0.name]['rear'] = 119
    game.board.pegs[p1.name]['front'] = 119
    game.board.pegs[p1.name]['rear'] = 119
    
    # p0 is dealer, both hands score 0, but crib scores 2+
    round1 = CribbageRound(game=game, dealer=p0, seed=123)
    
    # Both hands score 0
    round1.player_hand_after_discard = {
        p0.name: build_hand(['ah', '2d', '3c', '8s']),  # No scoring
        p1.name: build_hand(['2h', '3d', '4c', '9s'])   # No scoring
    }
    round1.starter = Card("6h")
    # Crib has a pair for 2 points
    round1.crib = build_hand(['5h', '5d', '10c', 'jd'])
    
    # Skip pegging - just score hands
    round1.hands = {p0.name: [], p1.name: []}  # No cards left to peg
    round1.play()
    
    # p0 should reach at least 121 via crib
    assert game.board.get_score(p0) >= 121, f"Expected p0 to have >=121, got {game.board.get_score(p0)}"
    # The game should recognize p0 as winner
    assert round1.game_winner == p0, "Expected p0 to be the winner via crib"


def test_end_of_game_stops_after_winner_determined():
    """Test that once a winner is determined, no further scoring occurs."""
    p0 = PlayFirstCardPlayer(name="Player1")
    p1 = PlayFirstCardPlayer(name="Player2")
    game = CribbageGame(players=[p0, p1], seed=123)
    
    # Set both players to 119 points
    game.board.pegs[p0.name]['front'] = 119
    game.board.pegs[p0.name]['rear'] = 119
    game.board.pegs[p1.name]['front'] = 119
    game.board.pegs[p1.name]['rear'] = 119
    
    # p1 is dealer, p0 counts first and wins with high-scoring hand
    # Even though p1's hand and crib would score, they shouldn't be counted
    round1 = CribbageRound(game=game, dealer=p1, seed=123)
    
    # p0 has high-scoring hand, p1 also has high-scoring hand
    round1.player_hand_after_discard = {
        p0.name: build_hand(['5h', '5d', '5c', '5s']),  # Four 5s = 12 points
        p1.name: build_hand(['jh', 'jd', 'jc', 'js'])   # Four jacks = 12 points
    }
    round1.starter = Card("10h")
    round1.crib = build_hand(['kh', 'kd', 'kc', 'ks'])  # Four kings = 12 points
    
    # Skip pegging
    round1.hands = {p0.name: [], p1.name: []}
    round1.play()
    
    # p0 should be at 131 (119 + 12)
    assert game.board.get_score(p0) == 131, f"Expected p0 to have 131, got {game.board.get_score(p0)}"
    # p1 should still be at 119 (no scoring after winner determined)
    assert game.board.get_score(p1) == 119, f"Expected p1 to stay at 119, got {game.board.get_score(p1)}"
    # Winner should be p0
    assert round1.game_winner == p0, "Expected p0 to be the winner"
