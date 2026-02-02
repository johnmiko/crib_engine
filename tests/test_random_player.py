from cribbage.players.random_player import RandomPlayer
from cribbage.playingcards import Card, build_hand
from conftest import make_player_state, make_round_state


def test_random_player_can_be_seeded():
    player1 = RandomPlayer(name="Random1", seed=42)
    player2 = RandomPlayer(name="Random2", seed=42)
    hand = build_hand(['5h', '7d', '9s', 'kc', '2h', '3d'])
    
    player_state1 = make_player_state(hand.copy(), is_dealer=True)
    player_state2 = make_player_state(hand.copy(), is_dealer=True)
    round_state = make_round_state()
    
    crib_cards1 = player1.select_crib_cards(player_state1, round_state)
    crib_cards2 = player2.select_crib_cards(player_state2, round_state)
    assert crib_cards1 == crib_cards2, "Crib card selections should be the same for same seed"
    
    table = build_hand(['4h', '6d'])
    player_state1 = make_player_state(hand.copy())
    player_state2 = make_player_state(hand.copy())
    round_state = make_round_state(count=10, table_cards=table.copy())
    
    card_to_play1 = player1.select_card_to_play(player_state1, round_state)
    card_to_play2 = player2.select_card_to_play(player_state2, round_state)
    assert card_to_play1 == card_to_play2, "Card to play selections should be the same for same seed"