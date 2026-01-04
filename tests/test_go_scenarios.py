from cribbage.cribbagegame import CribbageGame
from cribbage.cribbageround import CribbageRound
from cribbage.players.play_first_card_player import PlayFirstCardPlayer
from cribbage.players.random_player import RandomPlayer
from cribbage.playingcards import Card, build_hand
from logging import getLogger
from unittest.mock import patch

logger = getLogger(__name__)


def test_go_scenario_with_continuation():
    """
    Test "go" logic, who scores and who's turn it is 
    """
    p0 = PlayFirstCardPlayer(name="Player1")
    p1 = PlayFirstCardPlayer(name="Player2")
    game1 = CribbageGame(players=[p0, p1], seed=123)
    round1 = CribbageRound(game=game1, dealer=p0, seed=123)
    round1.hands = {
        p0.name: build_hand(['js', 'jc', '10h','10d','10c', '10s']),
        p1.name: build_hand(['jh', 'jd', 'qh','qd','qc', 'qs'])
    }
    round1.starter = Card("kc")
    round1.play()    
    # p1 goes first, qd scores 30, p0 says go, p1 says go, p1 scores 1 for last card
    # p0 then plays 10d, scores 1 with 10c and then 1 for 10s for last card
    assert round1.table == build_hand(["qh", "10h", "qd", "10d", "qc", "10c", "qs", "10s"])
    assert round1.history.score_after_pegging == [2,1]
    # Give player 0 an ace instead, letting them play and score 31
    # Player 0 scores 31, and gets 1 for last card
    # During 2nd sequence, player 1 scores 1 for qc
    game1 = CribbageGame(players=[p0, p1], seed=123)
    round1 = CribbageRound(game=game1, dealer=p0, seed=123)
    round1.history.score_after_pegging = []
    round1.hands = {
        p0.name: build_hand(['js', 'jc', '10h','ad','10c', '10s']),
        p1.name: build_hand(['jh', 'jd', 'qh','qd','qc', 'qs'])
    }
    round1.starter = Card("kc")
    round1.play()    
    assert round1.history.score_after_pegging == [3,1]
    assert round1.table == build_hand(["qh", "10h", "qd", "ad", "qc", "10c", "qs", "10s"])
    game1 = CribbageGame(players=[p0, p1], seed=123)
    round1 = CribbageRound(game=game1, dealer=p0, seed=123)
    round1.history.score_after_pegging = []
    round1.hands = {
        p0.name: build_hand(['js', 'jc', '10h','ad','ac', '10s']),
        p1.name: build_hand(['jh', 'jd', 'qh','9d','qc', 'qs'])
    }
    round1.starter = Card("kc")
    round1.play()    
    assert round1.history.score_after_pegging == [4,1]
    assert round1.table == build_hand(["qh", "10h", "9d", "ad", "ac", "qc", "10s", "qs"])
    game1 = CribbageGame(players=[p0, p1], seed=123)
    round1 = CribbageRound(game=game1, dealer=p0, seed=123)
    round1.history.score_after_pegging = []
    round1.hands = {
        p0.name: build_hand(['js', 'jc', '10h','ad','ac', 'as']),
        p1.name: build_hand(['jh', 'jd', 'qh','8d','qc', 'qs'])
    }
    round1.starter = Card("kc")
    round1.play()    
    assert round1.history.score_after_pegging == [10,3]
    assert round1.table == build_hand(["qh", "10h", "8d", "ad", "ac", "as", "qc", "qs"])
    game1 = CribbageGame(players=[p0, p1], seed=123)
    round1 = CribbageRound(game=game1, dealer=p1, seed=123)
    round1.hands = {
        p0.name: build_hand(['js', 'jc', '10h','10d','10c', '10s']),
        p1.name: build_hand(['jh', 'jd', 'qh','qd','qc', 'qs'])
    }
    round1.starter = Card("kc")
    round1.play()    
    # p1 goes first, qd scores 30, p0 says go, p1 says go, p1 scores 1 for last card
    # p0 then plays 10d, scores 1 with 10c and then 1 for 10s for last card
    assert round1.table == build_hand(["10h","qh", "10d","qd","10c",  "qc", "10s", "qs"])
    assert round1.history.score_after_pegging == [1,2]


    # # Override play_pegging to always play first available card (deterministic)
    # def mock_play_first(playable, count, history_since_reset):
    #     return playable[0] if playable else None
    
    # with patch.object(p0, 'play_pegging', side_effect=mock_play_first):
    #     with patch.object(p1, 'play_pegging', side_effect=mock_play_first):
    #         round1.play()
    
    # # Get the final scores
    # game1_score = [game1.board.get_score(p) for p in [p0, p1]]
    
    # # Log the round details for debugging
    # logger.info(f"Table (cards played in order): {round1.table}")
    # logger.info(f"Crib: {round1.crib}")
    # logger.info(f"Player1 hand after discard: {round1.player_hand_after_discard[p0.name]}")
    # logger.info(f"Player2 hand after discard: {round1.player_hand_after_discard[p1.name]}")
    # logger.info(f"Scores: Player1={game1_score[0]}, Player2={game1_score[1]}")
    
    # # Verify that all 8 cards (4 from each player) are in the table
    # assert len(round1.table) == 8, f"Expected 8 cards in table, got {len(round1.table)}"
    
    # # Verify that the cards are from the post-discard hands
    # p0_hand_cards = round1.player_hand_after_discard[p0.name]
    # p1_hand_cards = round1.player_hand_after_discard[p1.name]
    # all_played_cards = set(round1.table)
    # expected_cards = set(p0_hand_cards + p1_hand_cards)
    # assert all_played_cards == expected_cards, \
    #     f"Cards in table {all_played_cards} don't match cards from hands {expected_cards}"
    
    # # Verify crib has 4 cards (2 from each player)
    # assert len(round1.crib) == 4, f"Expected 4 cards in crib, got {len(round1.crib)}"
    
    # # With these specific seeds and "play first card" strategy, we get:
    # # Player1 (dealer) hand after discard: [7d, 4s, qc, ks]
    # # Player2 (non-dealer) hand after discard: [jd, 7s, kh, 4h]
    # # Expected play sequence (Player2 plays first):
    # # Sequence 1: 4h (4), 7d (11), 7s (18), 4s (22) - both players pass/go
    # # Sequence 2: ks (10), kh (20), qc (30), jd (40 > 31, would go over)
    # # Actually, let's verify by manually checking the sequence
    
    # # The table is: [4h, 7d, 7s, 4s, ks, kh, qc, jd]
    # # Let me verify this makes sense:
    # # Seq1: 4h(4) 7d(11) 7s(18) 4s(22) - stop (both cant play without going over 31)
    # # Seq2: ks(10) kh(20) qc(30) jd(40) - but jd would be 40, can't play!
    # # So there should be a "go" or sequence break somewhere
    
    # # Let's just verify the play made sense by checking scores include "go" points
    # # Scores are Player1=5, Player2=5 - includes pairs and goes
    # expected_table = build_hand(['4h', '7d', '7s', '4s', 'ks', 'kh', 'qc', 'jd'])
    
    # # Manually verify the sequence could happen with "go"s:
    # # Check if there are sequences where count reset happened
    # # We can infer "go"s occurred based on: count never exceeds 31, and all cards played
    # # Verify by simulating the count:
    # values = [c.get_value() for c in round1.table]
    # # Expected: [4, 7, 7, 4, 10, 10, 10, 10] = 62 total
    # # This MUST have had sequence breaks (goes or 31s)
    
    # # Trace through with "play first card" logic:
    # # P2: 4h(4), P1: 7d(11), P2: 7s(18), P1: 4s(22)
    # # P2's remaining cards: jd(10), kh(10) - both would make 32, so P2 says "go"
    # # P1's remaining cards: qc(10), ks(10) - both would make 32, so P1 also can't play
    # # Both said "go" → last player to play (P1 with 4s) gets 1 point, sequence resets
    # # New sequence: P2: (who plays first after reset?) - should be P2 (non-dealer)
    # # Actually after a "go", the player who got the point plays first in new sequence
    # # So P1 plays first: ks(10), P2: kh(20), P1: qc(30), P2: jd(40 > 31)
    # # So P2 can't play jd, says "go", P1 gets 1 point
    # # New sequence: P2: jd(10), all out, P2 gets last card point
    
    # # The actual order suggests: [4h, 7d, 7s, 4s] [ks, kh, qc] [jd]
    # # Which indicates 2 "go"s occurred - perfect for our test!
    
    # # Assert the exact table sequence
    # assert round1.table == expected_table, \
    #     f"Expected table {expected_table}, got {round1.table}. " \
    #     f"This may indicate play order changed with RNG updates."
    
    # logger.info("✓ GO scenario test passed - table sequence is correct!")
