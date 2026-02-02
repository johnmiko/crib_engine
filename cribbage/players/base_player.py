"""Agents that interact with the CribbageGame."""
import random
from abc import ABCMeta, abstractmethod
from typing import Optional, List
from cribbage.playingcards import Card


class BasePlayer(metaclass=ABCMeta):
    """Abstract Base Class"""

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

    def __repr__(self):
        return str(self)
    
    def get_name(self) -> str:
        return self.name

    @abstractmethod
    def select_crib_cards(self, player_state, round_state):
        """Select cards to place in crib.

        :param player_state: PlayerState object with hand, score, is_dealer, known_cards
        :param round_state: RoundState object with starter_card, count, table_cards, etc.
        :return: list of 2 cards to place in crib
        """
        raise NotImplementedError

    @abstractmethod
    def select_card_to_play(self, player_state, round_state) -> Optional[Card]:
        """Select next card to play.

        :param player_state: PlayerState object with hand, score, is_dealer, known_cards
        :param round_state: RoundState object with starter_card, count, table_cards, etc.
        :return: card to play or None if must say go
        """
        raise NotImplementedError


class HumanPlayer(BasePlayer):
    """Interface for a human user to play."""

    def present_cards_for_selection(self, cards, n_cards=1):
        """Presents a text-based representation of the game via stdout and prompts a human user for decisions.

        :param cards: list of cards in player's hand
        :param n_cards: number of cards that player must select
        :return: list of n_cards cards selected from player's hand
        """
        cards_selected = []
        while len(cards_selected) < n_cards:
            s = ""
            for idx, card in enumerate(cards):
                s += "(" + str(idx + 1) + ") " + str(card)
                if card != cards[-1]:
                    s += ","
                s += " "
            msg = "Select a card: " if n_cards == 1 else "Select %d cards: " % n_cards
            print(s)
            selection = input(msg)
            card_indices = [int(s) for s in selection.split() if s.isdigit()]
            for idx in card_indices:
                if idx < 1 or idx > len(cards):
                    print("%d is an invalid selection." % idx)
                else:
                    cards_selected.append(cards[idx-1])
        return cards_selected

    def select_crib_cards(self, player_state, round_state):
        return self.present_cards_for_selection(cards=player_state.hand, n_cards=2)

    def select_card_to_play(self, player_state, round_state):
        return self.present_cards_for_selection(cards=player_state.hand, n_cards=1)[0]

class HumanPlayerAPI(HumanPlayer):
    """Interface for a human user to play."""

    def get_selection(self, msg):
        """Get selection from external source (e.g., API call)."""
        # This method should be implemented to get input from an external source
        raise NotImplementedError

    def present_cards_for_selection(self, cards, n_cards=1):
        """Presents a text-based representation of the game via stdout and prompts a human user for decisions.

        :param cards: list of cards in player's hand
        :param n_cards: number of cards that player must select
        :return: list of n_cards cards selected from player's hand
        """
        cards_selected = []
        while len(cards_selected) < n_cards:
            s = ""
            for idx, card in enumerate(cards):
                s += "(" + str(idx + 1) + ") " + str(card)
                if card != cards[-1]:
                    s += ","
                s += " "
            msg = "Select a card: " if n_cards == 1 else "Select %d cards: " % n_cards
            print(s)
            selection = self.get_selection(msg)
            card_indices = [int(s) for s in selection.split() if s.isdigit()]
            for idx in card_indices:
                if idx < 1 or idx > len(cards):
                    print("%d is an invalid selection." % idx)
                else:
                    cards_selected.append(cards[idx-1])
        return cards_selected
