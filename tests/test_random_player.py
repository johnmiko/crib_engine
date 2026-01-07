from cribbage.players.random_player import RandomPlayer
from cribbage.playingcards import Card, build_hand


def test_random_player_can_be_seeded():
    player1 = RandomPlayer(name="Random1", seed=42)
    player2 = RandomPlayer(name="Random2", seed=42)
    hand = build_hand(['5h', '7d', '9s', 'kc', '2h', '3d'])    
    crib_cards1 = player1.select_crib_cards(hand.copy(), dealer_is_self=True)
    crib_cards2 = player2.select_crib_cards(hand.copy(), dealer_is_self=True)
    assert crib_cards1 == crib_cards2, "Crib card selections should be the same for same seed"
    table = build_hand(['4h', '6d'])
    card_to_play1 = player1.select_card_to_play(hand.copy(), table.copy(), count=10, crib=crib_cards1)
    card_to_play2 = player2.select_card_to_play(hand.copy(), table.copy(), count=10, crib=crib_cards2)
    assert card_to_play1 == card_to_play2, "Card to play selections should be the same for same seed"