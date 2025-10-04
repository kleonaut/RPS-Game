import discord
from utils.enums import Move

# Stores info about an ongoing duel
class DuelEvent:

    class Player:
        def __init__(self, user: discord.Member):
            self.name = user.name
            self.id = user.id
            self.mention = user.mention
            self.display_name = user.display_name # For naming confirmation buttons

            self.beatCount = 0 # Number of times they have beaten the opponent this game. Two beats wins the game
            self.move = None # Their confirmed move for this round

        def begin_next_round(self):
            self.move = None

    def __init__(self, player1: discord.Member, player2: discord.Member):
        # Beats Map is a clever way to determine which move beats which
        self._beats_map = {
            Move.ROCK:     Move.SCISSORS,
            Move.PAPER:    Move.ROCK,
            Move.SCISSORS: Move.PAPER
        }

        self.players = [DuelEvent.Player(player1), DuelEvent.Player(player2)]
        self.winner = self.loser = None
        self.is_a_tie = False

    def make_a_move(self, player: discord.Member, move: Move):
        # If player plays themselves and this is their second confirmation
        if self.players[0].id == self.players[1].id and self.players[0].move:
            self.players[1].move = move
        else:
            for p in self.players:
                if p.id == player.id:
                    p.move = move
                    return

    def did_both_players_confirm_moves(self) -> bool:
        if self.players[0].move and self.players[1].move:

            # Determine tie
            if self.players[0].move == self.players[1].move:
                self.is_a_tie = True
                return True

            # Determine winner and loser, add beat count to the winner
            if self._beats_map[self.players[0].move] == self.players[1].move:
                self.winner = self.players[0]
                self.players[0].beatCount += 1
                self.loser = self.players[1]
            else:
                self.winner = self.players[1]
                self.players[1].beatCount += 1
                self.loser = self.players[0]
            return True
        else: return False

    def begin_next_round(self):
        self.is_a_tie = False
        self.winner = self.loser = None
        for p in self.players:
            p.begin_next_round()

    def is_fully_completed(self):
        for p in self.players:
            if p.beatCount > 1:
                return True
        return False
