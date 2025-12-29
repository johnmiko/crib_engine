import logging

logger = logging.getLogger(__name__)

class CribbageBoard:
    """Board used to peg (track) points during a cribbage game."""

    def __init__(self, players, max_score):
        self.max_score = max_score
        self.pegs = {p.name: {'front': 0, 'rear': 0} for p in players}

    def __str__(self):
        s = "[PEGS] "
        for player in self.pegs.keys():
            s += str(player) + " "
            for peg in self.pegs[player]:
                s += str(peg) + ": " + str(self.pegs[player][peg]) + ", "
            s = s[:-2]
            s += "; "
        s = s[:-2]
        return s

    def __repr__(self):
        return str(self)

    def peg(self, player, points):
        """Add points for a player.

        :param player: Player who should receive points.
        :param points: Number of points to add to the player.
        :return: None
        """
        assert points > 0, "You must peg 1 or more points."
        self.pegs[player.name]['rear'] = self.pegs[player.name]['front']
        self.pegs[player.name]['front'] += points
        if self.pegs[player.name]['front'] >= self.max_score:
            self.pegs[player.name]['front'] = self.max_score
            return player

    def get_score(self, player):
        """Return a given player's current score.

        :param player: Player to check.
        :return: Score for player.
        """
        front_peg = self.pegs[player]['front']
        logger.debug(f"{front_peg=}")
        return front_peg