import unittest
from cribbage import scoring
from cribbage import playingcards as pc


class TestPairScoring(unittest.TestCase):
    def setUp(self):
        pass

    def test_pair_pair(self):
        s = scoring.HasPairTripleQuad()
        hand = [pc.Card('2h'), pc.Card('3h'), pc.Card('4h'), pc.Card('5h'), pc.Card('6h'), pc.Card('7h'), pc.Card('8h'), pc.Card('9h'), pc.Card('10h'), pc.Card('jh'), pc.Card('qh'), pc.Card('kh'), pc.Card('ah')]
        hand.append(pc.Card('9h'))
        hand.append(pc.Card('9h'))
        score, _ = s.check(hand)
        self.assertEqual(score, 2)

    def test_pair_triple(self):
        s = scoring.HasPairTripleQuad()
        hand = [pc.Card('2h'), pc.Card('3h'), pc.Card('4h'), pc.Card('5h'), pc.Card('6h'), pc.Card('7h'), pc.Card('8h'), pc.Card('9h'), pc.Card('10h'), pc.Card('jh'), pc.Card('qh'), pc.Card('kh'), pc.Card('ah')]
        hand.append(pc.Card('9h'))
        hand.append(pc.Card('9h'))
        hand.append(pc.Card('9h'))
        score, _ = s.check(hand)
        self.assertEqual(score, 6)

    def test_pair_quadruple(self):
        s = scoring.HasPairTripleQuad()
        hand = [pc.Card('2h') for _ in range(6)]
        score, _ = s.check(hand)
        self.assertEqual(score, 12)

    def test_pair_nothing(self):
        s = scoring.HasPairTripleQuad()
        hand = [pc.Card('2h'), pc.Card('3h'), pc.Card('4h'), pc.Card('5h'), pc.Card('6h'), pc.Card('7h'), pc.Card('8h'), pc.Card('9h'), pc.Card('10h'), pc.Card('jh'), pc.Card('qh'), pc.Card('kh'), pc.Card('ah')]
        score, _ = s.check(hand)
        self.assertEqual(score, 0)
        hand = [pc.Card('2h'), pc.Card('3h'), pc.Card('4h'), pc.Card('5h'), pc.Card('6h'), pc.Card('7h'), pc.Card('8h'), pc.Card('9h'), pc.Card('10h'), pc.Card('jh'), pc.Card('qh'), pc.Card('kh'), pc.Card('ah')]
        score, _ = s.check(hand)
        self.assertEqual(score, 0)
        hand = [pc.Card('9h'), pc.Card('9h'), pc.Card('9h'), pc.Card('8h')]
        score, _ = s.check(hand)
        self.assertEqual(score, 0)
        hand = [pc.Card('9h')]
        score, _ = s.check(hand)
        self.assertEqual(score, 0)

    def test_pair_minimumcards(self):
        s = scoring.HasPairTripleQuad()
        hand = [pc.Card('9h'), pc.Card('9h')]
        score, _ = s.check(hand)
        self.assertEqual(score, 2)
        hand = [pc.Card('9h'), pc.Card('9h'), pc.Card('9h')]
        score, _ = s.check(hand)
        self.assertEqual(score, 6)
        hand = [pc.Card('9h'), pc.Card('9h'), pc.Card('9h'), pc.Card('9h')]
        score, _ = s.check(hand)
        self.assertEqual(score, 12)


class TestExactlyEqualsN(unittest.TestCase):
    def setUp(self):
        pass

    def test_ExactlyEqualsN15_count_is_equal(self):
        s = scoring.ExactlyEqualsN(n=15)
        hand = [pc.Card('9h'), pc.Card('as'), pc.Card('5d')]
        score, _ = s.check(hand)
        self.assertEqual(score, 2)

    def test_ExactlyEqualsN15_count_is_less_than(self):
        s = scoring.ExactlyEqualsN(n=15)
        hand = [pc.Card('9h'), pc.Card('5d')]
        score, _ = s.check(hand)
        self.assertEqual(score, 0)

    def test_ExactlyEqualsN15_count_is_greater_than(self):
        s = scoring.ExactlyEqualsN(n=15)
        hand = [pc.Card('9h'), pc.Card('9c'), pc.Card('as'), pc.Card('5d')]
        score, _ = s.check(hand)
        self.assertEqual(score, 0)

    def test_ExactlyEqualsN15_one_card(self):
        s = scoring.ExactlyEqualsN(n=15)
        hand = [pc.Card('as')]
        score, _ = s.check(hand)
        self.assertEqual(score, 0)

    def test_ExactlyEqualsN31_count_is_equal(self):
        s = scoring.ExactlyEqualsN(n=31)
        hand = [pc.Card('9h'), pc.Card('ah'), pc.Card('jh'), pc.Card('qh'), pc.Card('as')]
        score, _ = s.check(hand)
        self.assertEqual(score, 1)

    def test_ExactlyEqualsN31_count_is_less_than(self):
        s = scoring.ExactlyEqualsN(n=31)
        hand = [pc.Card('9h'), pc.Card('ah'), pc.Card('jh'), pc.Card('qh')]
        score, _ = s.check(hand)
        self.assertEqual(score, 0)

    def test_ExactlyEqualsN31_count_is_greater_than(self):
        s = scoring.ExactlyEqualsN(n=31)
        hand = [pc.Card('9h'), pc.Card('ah'), pc.Card('jh'), pc.Card('qh'), pc.Card('2s')]
        score, _ = s.check(hand)
        self.assertEqual(score, 0)


class TestHasStraight_DuringPlay(unittest.TestCase):

    def setUp(self):
        self.s = scoring.HasStraight_DuringPlay()

    def test_HasStraight_DuringPlay_2card(self):
        hand = [pc.Card('4h'), pc.Card('5s')]
        score, _ = self.s.check(hand)
        self.assertEqual(score, 0)

    def test_HasStraight_DuringPlay_3card(self):
        hand = [pc.Card('4h'), pc.Card('5s'), pc.Card('6d')]
        score, _ = self.s.check(hand)
        self.assertEqual(score, 3)

    def test_HasStraight_DuringPlay_4card(self):
        hand = [pc.Card('2h'), pc.Card('4h'), pc.Card('5s'), pc.Card('6d'), pc.Card('7d')]
        score, _ = self.s.check(hand)
        self.assertEqual(score, 4)

    def test_HasStraight_DuringPlay_3card_after_broken(self):
        hand = [pc.Card('2h'), pc.Card('4h'), pc.Card('5s'), pc.Card('6d'), pc.Card('7d'), pc.Card('5c')]
        score, _ = self.s.check(hand)
        self.assertEqual(score, 3)

    def test_HasStraight_DuringPlay_6card_outoforder(self):
        hand = [pc.Card('2h'), pc.Card('4h'), pc.Card('5s'), pc.Card('6d'), pc.Card('7d'), pc.Card('3c')]
        score, _ = self.s.check(hand)
        self.assertEqual(score, 6)

    def test_HasStraight_DuringPlay_4card_broken(self):
        hand = [pc.Card('4h'), pc.Card('5s'), pc.Card('6d'), pc.Card('7d'), pc.Card('2c')]
        score, _ = self.s.check(hand)
        self.assertEqual(score, 0)

    def test_HasStraight_DuringPlay_12card(self):
        hand = [pc.Card(f"{r}h") for r in ['a','2','3','4','5','6','7','8','9','10','j','q','k']]
        score, _ = self.s.check(hand)
        self.assertEqual(score, 13)


class TestHasStraight_InHand(unittest.TestCase):

    def setUp(self):
        self.s = scoring.HasStraight_InHand()

    def test_HasStraight_InHand_2card(self):
        hand = [pc.Card('4h'), pc.Card('5s')]
        score, _ = self.s.check(hand)
        self.assertEqual(score, 0)

    def test_HasStraight_InHand_3card(self):
        hand = [pc.Card('4h'), pc.Card('5s'), pc.Card('6d')]
        score, _ = self.s.check(hand)
        self.assertEqual(score, 3)

    def test_HasStraight_InHand_4card(self):
        hand = [pc.Card('2h'), pc.Card('4h'), pc.Card('5s'), pc.Card('6d'), pc.Card('7d')]
        score, _ = self.s.check(hand)
        self.assertEqual(score, 4)

    def test_HasStraight_InHand_Double_4_Straight(self):
        hand = [pc.Card('2h'), pc.Card('4h'), pc.Card('5s'), pc.Card('6d'), pc.Card('7d'), pc.Card('5c')]
        score, _ = self.s.check(hand)
        self.assertEqual(score, 8)

    def test_HasStraight_InHand_6card_outoforder(self):
        hand = [pc.Card('2h'), pc.Card('4h'), pc.Card('5s'), pc.Card('6d'), pc.Card('7d'), pc.Card('3c')]
        score, _ = self.s.check(hand)
        self.assertEqual(score, 6)

    def test_HasStraight_InHand_4card_broken(self):
        hand = [pc.Card('4h'), pc.Card('5s'), pc.Card('6d'), pc.Card('7d'), pc.Card('2c')]
        score, _ = self.s.check(hand)
        self.assertEqual(score, 4)

    def test_HasStraight_InHand_ThreePairs(self):
        hand = [pc.Card('4h'), pc.Card('4s'), pc.Card('5d'), pc.Card('5s'), pc.Card('6d'), pc.Card('6h'), pc.Card('2c')]
        score, _ = self.s.check(hand)
        self.assertEqual(score, 24)

    def test_HasStraight_InHand_NoStraight(self):
        hand = [pc.Card('2h'), pc.Card('4s'), pc.Card('6d'), pc.Card('8s'), pc.Card('10d'), pc.Card('qh')]
        score, _ = self.s.check(hand)
        self.assertEqual(score, 0)

    def test_HasStraight_InHand_EmptyHand(self):
        hand = []
        score, _ = self.s.check(hand)
        self.assertEqual(score, 0)

    def test_HasStraight_InHand_12card(self):
        hand = [pc.Card(f"{r}h") for r in ['a','2','3','4','5','6','7','8','9','10','j','q','k']]
        score, _ = self.s.check(hand)
        self.assertEqual(score, 13)


class TestCountCombinationsEqualToN(unittest.TestCase):
    def setUp(self):
        pass

    def test_CountCombinationsEqualToN_one(self):
        s = scoring.CountCombinationsEqualToN(n=15)
        hand = [pc.Card('9h'), pc.Card('as'), pc.Card('5d')]
        score, _ = s.check(hand)
        self.assertEqual(score, 2)

    def test_CountCombinationsEqualToN_two_overlapping(self):
        s = scoring.CountCombinationsEqualToN(n=15)
        hand = [pc.Card('9h'), pc.Card('5c'), pc.Card('as'), pc.Card('5d')]
        score, _ = s.check(hand)
        self.assertEqual(score, 4)

    def test_CountCombinationsEqualToN_two_nonoverlapping(self):
        s = scoring.CountCombinationsEqualToN(n=15)
        hand = [pc.Card('9h'), pc.Card('5c'), pc.Card('as'), pc.Card('7d'), pc.Card('8d')]
        score, _ = s.check(hand)
        self.assertEqual(score, 4)


if __name__ == '__main__':
    unittest.main()
