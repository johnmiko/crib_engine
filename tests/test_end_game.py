"""Tests for end-of-game scenarios to ensure correct winner determination."""
import pytest
from cribbage.cribbagegame import CribbageGame
from cribbage.cribbageround import CribbageRound
from cribbage.players.play_first_card_player import PlayFirstCardPlayer
from cribbage.playingcards import Card, build_hand
from logging import getLogger

from cribbage.utils import play_game, play_multiple_games, wilson_ci

logger = getLogger(__name__)

class MockCribbageRound(CribbageRound):
    def __init__(self, game, dealer, seed=None, mock_starter_card=Card('kh'), should_populate_crib=True):
        super().__init__(game, dealer, seed)
        self.mock_starter_card = mock_starter_card
        self.should_populate_crib = should_populate_crib
        # Pre-set starter so setup_crib_phase won't override it
        self.starter = self.mock_starter_card

    def setup_crib_phase(self):
        """Override to respect mock_starter_card."""
        if self.should_populate_crib:
            self._populate_crib()
            self.history.crib = [str(card) for card in self.crib]
        self.history.score_at_start_of_round = [self.game.board.get_score(p) for p in self.game.players]
        # starter already set in __init__

def test_p1_wins_by_pegging_to_121():
    """Test that p1 wins by pegging 15 for 2 points from 119 to 121."""
    p1 = PlayFirstCardPlayer(name="Player1")
    p2 = PlayFirstCardPlayer(name="Player2")
    game = CribbageGame(players=[p1, p2], seed=123)
    
    # Set both players to 119 points
    game.board.pegs[p1.name]['front'] = 119
    game.board.pegs[p1.name]['rear'] = 119
    game.board.pegs[p2.name]['front'] = 119
    game.board.pegs[p2.name]['rear'] = 119
    
    # if dealer is p1 then p2 starts
    round1 = CribbageRound(game=game, dealer=p1, seed=123)
    round1.starter = Card("9h")
    round1.hands = {
        p1.name: build_hand(['5h', '5d', '5c', '5s']),
        p2.name: build_hand(['10h', '10d', '10c', '10s'])
    }
    
    round1.play()
    
    # p2 plays 10h, p1 plays 5h for 15 and scores 2 points -> 121
    assert game.board.get_score(p1) == 121, f"Expected p1 to have 121, got {game.board.get_score(p1)}"
    # The game should recognize p1 as winner
    assert round1.game_winner.name == "Player1", "Expected p1 to be the winner"
    assert game.board.get_score(p2) == 119, f"{p2.name} score did not change because game has ended already"


def test_p2_wins_by_pegging_to_121():
    """Test that p1 wins by pegging 15 for 2 points from 119 to 121."""
    p1 = PlayFirstCardPlayer(name="Player1")
    p2 = PlayFirstCardPlayer(name="Player2")
    game = CribbageGame(players=[p1, p2], seed=123)
    
    # Set both players to 119 points
    game.board.pegs[p1.name]['front'] = 118
    game.board.pegs[p1.name]['rear'] = 118
    game.board.pegs[p2.name]['front'] = 116
    game.board.pegs[p2.name]['rear'] = 116
    
    # if dealer is p1 then p2 starts
    round1 = CribbageRound(game=game, dealer=p1, seed=123)
    round1.starter = Card("9h")
    round1.hands = {
        p1.name: build_hand(['5h', '5d', '5c', '5s']),
        p2.name: build_hand(['5h', '5d', '5c', '5s'])
    }
    
    round1.play()
    
    # p2 plays 10h, p1 plays 5h for 15 and scores 2 points -> 121
    assert game.board.get_score(p2) == 121, f"Expected p2 to have 121, got {game.board.get_score(p2)}"
    # The game should recognize p2 as winner
    assert round1.game_winner.name == "Player2", "Expected p2 to be the winner"
    assert game.board.get_score(p1) == 120, f"{p1.name} score did not change because game has ended already"


def test_p1_counts_first_and_wins():
    """Test that p2 (non-dealer) wins by counting hand first when p2 has crib."""
    p1 = PlayFirstCardPlayer(name="Player1")
    p2 = PlayFirstCardPlayer(name="Player2")
    game = CribbageGame(players=[p1, p2], seed=123)
    
    # Set both players to 119 points
    game.board.pegs[p1.name]['front'] = 119
    game.board.pegs[p1.name]['rear'] = 119
    game.board.pegs[p2.name]['front'] = 119
    game.board.pegs[p2.name]['rear'] = 119
    
    # p2 is dealer, so p1 goes first and scores first
    # p2 will peg 1 point for the last card
    round1 = MockCribbageRound(game=game, dealer=p2, seed=123, mock_starter_card=Card("9h"), should_populate_crib=True)
    
    # Give each player 6 cards initially (will discard 2 to crib)
    # Give p1 cards that include a scoring 4-card hand
    round1.hands = {
        p1.name: build_hand(['3h', '3d', 'ac', 'as', 'ah', 'ad']), 
        p2.name: build_hand(['3c', '3s', '2c', '2s', '2h', '2d'])  
    }
    
    round1.play()
    
    # p1 should reach at least 121
    assert game.board.get_scores() == [121, 120]
    assert round1.game_winner.name == p1.name, "Expected p1 to be the winner"


def test_p2_counts_first_and_wins():
    """Test that p2 (non-dealer) wins by counting hand first when p2 has crib."""
    p1 = PlayFirstCardPlayer(name="Player1")
    p2 = PlayFirstCardPlayer(name="Player2")
    game = CribbageGame(players=[p1, p2], seed=123)
    
    # Set both players to 119 points
    game.board.pegs[p1.name]['front'] = 119
    game.board.pegs[p1.name]['rear'] = 119
    game.board.pegs[p2.name]['front'] = 119
    game.board.pegs[p2.name]['rear'] = 119
    
    # p2 is dealer, so p1 goes first and scores first
    # p2 will peg 1 point for the last card
    round1 = MockCribbageRound(game=game, dealer=p1, seed=123, mock_starter_card=Card("9h"), should_populate_crib=True)
    
    # Give each player 6 cards initially (will discard 2 to crib)
    # Give p1 cards that include a scoring 4-card hand
    round1.hands = {
        p1.name: build_hand(['3h', '3d', 'ac', 'as', 'ah', 'ad']), 
        p2.name: build_hand(['3c', '3s', '2c', '2s', '2h', '2d'])  
    }
    
    round1.play()
    # p1 should reach at least 121
    assert game.board.get_scores() == [120, 121]
    assert round1.game_winner.name == p2.name, "Expected p2 to be the winner"


def test_p1_counts_second_and_wins():
    p1 = PlayFirstCardPlayer(name="Player1")
    p2 = PlayFirstCardPlayer(name="Player2")
    game = CribbageGame(players=[p1, p2], seed=123)
    
    # Set both players to 119 points
    game.board.pegs[p1.name]['front'] = 119
    game.board.pegs[p1.name]['rear'] = 119
    game.board.pegs[p2.name]['front'] = 100
    game.board.pegs[p2.name]['rear'] = 100    
    # p1 is dealer, so p2 goes first and scores first    
    round1 = MockCribbageRound(game=game, dealer=p1, seed=123, mock_starter_card=Card("10h"), should_populate_crib=True)    
    round1.hands = {
        p1.name: build_hand(['3h', '3d', 'ac', 'as', 'ah', 'ad']), 
        p2.name: build_hand(['3c', '3s', '2c', '2s', '2h', '2d'])  
    }    
    round1.play()
    assert game.board.get_scores() == [121, 112]
    assert round1.game_winner.name == p1.name, "Expected p1 to be the winner"


def test_p1_counts_second_and_wins_in_crib():
    p1 = PlayFirstCardPlayer(name="Player1")
    p2 = PlayFirstCardPlayer(name="Player2")
    game = CribbageGame(players=[p1, p2], seed=123)
    
    # Set both players to 119 points
    game.board.pegs[p1.name]['front'] = 100
    game.board.pegs[p1.name]['rear'] = 100
    game.board.pegs[p2.name]['front'] = 100
    game.board.pegs[p2.name]['rear'] = 100    
    # p1 is dealer, so p2 goes first and scores first    
    round1 = MockCribbageRound(game=game, dealer=p1, seed=123, mock_starter_card=Card("10h"), should_populate_crib=True)    
    round1.hands = {
        p1.name: build_hand(['3h', '3d', 'ac', 'as', 'ah', 'ad']), 
        p2.name: build_hand(['3c', '3s', '2c', '2s', '2h', '2d'])  
    }    
    round1.play()
    assert game.board.get_scores() == [121, 112]
    assert round1.game_winner.name == p1.name, "Expected p1 to be the winner"

def test_p2_wins_on_nibs():
    p1 = PlayFirstCardPlayer(name="Player1")
    p2 = PlayFirstCardPlayer(name="Player2")
    game = CribbageGame(players=[p1, p2], seed=123)
    
    # Set both players to 119 points
    game.board.pegs[p1.name]['front'] = 119
    game.board.pegs[p1.name]['rear'] = 119
    game.board.pegs[p2.name]['front'] = 119
    game.board.pegs[p2.name]['rear'] = 119    
    # p2 is dealer, so will get the nib points    
    round1 = MockCribbageRound(game=game, dealer=p2, seed=123, mock_starter_card=Card("jh"), should_populate_crib=True)    
    round1.hands = {
        p1.name: build_hand(['3h', '3d', 'ac', 'as', 'ah', 'ad']), 
        p2.name: build_hand(['3c', '3s', '2c', '2s', '2h', '2d'])  
    }    
    round1.play()
    assert game.board.get_scores() == [119, 121]
    assert round1.game_winner.name == p2.name, "Expected p2 to be the winner"

@pytest.mark.slow
def test_tie_is_impossible():
    def play_multiple_end_games(num_games, p0, p1, seed=None) -> dict:
        wins = 0
        ties = 0
        diffs = []
        for i in range(num_games):
            # if (i % 100) == 0:
            logger.info(f"Playing game {i}/{num_games}")
            if i % 2 == 0:
                game = CribbageGame(players=[p0, p1], seed=seed)
            else:
                game = CribbageGame(players=[p1, p0], seed=seed)
            game.board.pegs[p0.name]['front'] = 119
            game.board.pegs[p0.name]['rear'] = 119
            game.board.pegs[p1.name]['front'] = 119
            game.board.pegs[p1.name]['rear'] = 119    
            # Alternate seats because cribbage has dealer advantage
            if i % 2 == 0:
                final_pegging_scores = game.start()
                s0, s1 = (final_pegging_scores[0], final_pegging_scores[1])
                diff = s0 - s1
            else:
                final_pegging_scores = game.start()
                s0, s1 = (final_pegging_scores[0], final_pegging_scores[1])
                diff = s1 - s0
            if diff > 0:
                wins += 1
            elif diff == 0:             
                ties += 1
            diffs.append(diff)
        winrate = wins / (num_games - ties)
        lo, hi = wilson_ci(wins, (num_games - ties))    
        return {"wins":wins, "diffs": diffs, "winrate": winrate, "ci_lo": lo, "ci_hi": hi, "ties": ties}
    num_games = 500
    p1 = PlayFirstCardPlayer(name="Player1")
    p2 = PlayFirstCardPlayer(name="Player2")
    results = play_multiple_end_games(num_games, p0=p1, p1=p2)    
    wins, diffs, win_rate, lo, hi, ties = results["wins"], results["diffs"], results["winrate"], results["ci_lo"], results["ci_hi"], results["ties"]
    assert ties == 0, f"Ties should be impossible but got {ties} ties in {num_games} games"