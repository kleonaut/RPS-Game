import discord
from utils.enums import Move

# Stores info about an ongoing duel
class DuelEvent:

    def __init__(self, player1: discord.Member, player2: discord.Member):
        # Beats Map is a clever way to determine which move beats which
        self._beats_map = {
            Move.ROCK:     Move.SCISSORS,
            Move.PAPER:    Move.ROCK,
            Move.SCISSORS: Move.PAPER
        }
        self.moves: dict[int, Move] = {} # Member.id -> Move

        self.winner = None
        self.loser = None
        self.is_a_tie = None
        self.players = [player1, player2]

    def make_a_move(self, player: discord.Member, move: Move):
        if player.id in self.moves:
            self.moves[0] = move
        # Make move
        else:
            self.moves[player.id] = move

    def is_complete(self) -> bool:
        if len(self.moves) != 2:
            return False

        # Determine winner and loser while we are at it

        # Extract moves from _moves dict
        p0_move = self.moves.get(self.players[0].id)
        p1_move = self.moves.get(self.players[1].id)

        # If player plays with themselves, use 0 for second player id instead
        if self.players[0] == self.players[1]:
            p1_move = self.moves.get(0)

        # Tie
        if p0_move == p1_move:
            self.is_a_tie = True
            return True

        self.is_a_tie = False
        if self._beats_map[p0_move] == p1_move:
            self.winner = self.players[0]
            self.loser = self.players[1]
        else:
            self.winner = self.players[1]
            self.loser = self.players[0]
        return True