import logging

import pytest
from cribbage.players.random_player import RandomPlayer
from cribbage.players.play_first_card_player import PlayFirstCardPlayer
from cribbage.players.beginner_player import BeginnerPlayer
from cribbage.players.medium_player import MediumPlayer

from cribbage.utils import play_multiple_games
from cribbage.cribbagegame import CribbageGame
import sqlite3
import pandas as pd

logger = logging.getLogger(__name__)

# run find_strategy_discard_differences.py to update discards_differ.log before running these tests
# @pytest.fixture(scope="module")
# def fixture_generate_discard_differences_log():
#     from scripts.find_strategy_discard_differences import generate_discard_differences_log
#     generate_discard_differences_log()

def test_beginner_vs_medium_crib_discards_all_hands():    
    filename = "discards_differ.log"
    df = pd.read_csv(filename, header=0)
    logger.info(f"Score difference when different discards were selected (medium - beginner)")
    df2 = df.drop_duplicates(subset=["dealt", "starter"])
    df2["score_dif"] = df2["medium_score"] - df2["beginner_score"]
    total_score_dif = df2["score_dif"].sum()
    avg_score_dif = df2["score_dif"].mean()
    logger.info(f"Average score difference over {len(df2)} hands: {avg_score_dif:.2f}")
    logger.info(f"Total score difference over {len(df2)} hands: {total_score_dif}")
    assert total_score_dif > 0, "MediumPlayer should have a positive score difference over BeginnerPlayer when discards differ"

def test_beginner_vs_medium_crib_discards_only_where_discards_are_different():    
    filename = "discards_differ.log"
    df = pd.read_csv(filename, header=0)
    logger.info(f"Score difference when different discards were selected (medium - beginner)")
    df[["medium_discard", "beginner_discard"]] = (
        df[["medium_discard", "beginner_discard"]]
        .apply(lambda col: col.str.split(",").apply(lambda x: ",".join(sorted(x))))
    )
    df["score_dif"] = df["medium_score"] - df["beginner_score"]
    df2 = df[df["medium_discard"] != df["beginner_discard"]]    
    total_score_dif = df2["score_dif"].sum()
    avg_score_dif = df2["score_dif"].mean()
    logger.info(f"Average score difference over {len(df2)} hands: {avg_score_dif:.2f}")
    logger.info(f"Total score difference over {len(df2)} hands: {total_score_dif}")
    assert total_score_dif > 0, "MediumPlayer should have a positive score difference over BeginnerPlayer when discards differ"