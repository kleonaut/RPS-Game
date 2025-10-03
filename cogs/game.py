import discord
from discord.ext import commands
from discord.commands import Option
from utils.dataHolder import DataHolder
from utils.duelEvent import DuelEvent
from utils.enums import Move
import json
from random import randint

# Load environment variables
with open("config.json", "r") as file:
    config = json.load(file)
GUILD_IDS = config["GUILD_IDS"] # Commands only run in these servers. Allows instant command autocompletion updates
DEV_ID = int(config["DEV_ID"]) # Used for cheats during development

class Game(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = DataHolder()




    # ----------------------------------- /rps command
    @discord.slash_command(guild_ids=GUILD_IDS, name="rps", description="Challenge another user in a game of Rock-Paper-Scissors")
    async def rps(self,ctx, opponent: Option(discord.Member, description="Pick a user to challenge", required=True)):  # type: ignore

        # Cant's play with yourself unless you are a developer
        if ctx.author.id == opponent.id and ctx.author.id != DEV_ID:
            await ctx.respond(f"You can't challenge yourself", ephemeral=True)

        # Duel object tracks players and their moves, and calculates the outcome
        duel = DuelEvent(ctx.author, opponent)
        await ctx.respond(f"{ctx.author.mention} challenges {opponent.mention} to an RPS duel. Both must accept this challenge to proceed.", view=Game.ConfirmDuelMessage(duel, self.data))




    # ----------------------------------- /rps-stats command
    @discord.slash_command(guild_ids=GUILD_IDS, name="rps-stats", description="See RPS statistics of a chosen user")
    async def win_count(self, ctx, user: Option(discord.Member, description="Pick a user to analyse", required=True)):  # type: ignore
        stats = self.data.stats(user)

        # Dynamic grammar for nouns
        if stats["wins"] == 1: win_or_wins = "win"
        else: win_or_wins = "wins"
        if stats["losses"] == 1: loss_or_losses = "loss"
        else: loss_or_losses = "losses"
        if stats["games"] == 1: game_or_games = "game"
        else: game_or_games = "games"

        # Message is visible to everyone on purpose
        await ctx.respond(f"{user.display_name} has {stats["xp"]} XP\n"
                          f"{stats["wins"]} {win_or_wins} and {stats["losses"]} {loss_or_losses}\n"
                          f"over {stats["games"]} {game_or_games}")




    # ----------------------------------- Challenge confirmation screen.
    # Contains a button for each player with their name on it.
    # Each player clicks their own name and is sent a move selection screen defined elsewhere
    class ConfirmDuelMessage(discord.ui.View):
        def __init__(self, duel: DuelEvent, data: DataHolder):
            super().__init__()
            self.disable_on_timeout = True
            self.duel = duel
            self.data = data

            # Each button has the name of a player on it
            self.player1_button.label = f"{self.duel.players[0].display_name}"
            self.player2_button.label = f"{self.duel.players[1].display_name}"

        # TODO: Add time out message. Timeout function already exists. Consider expanding timeout time for now

        # Prevent others from confirming, only player with the name of the button can confirm
        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            if interaction.user.id == self.duel.players[0].id and interaction.data["custom_id"] == "player1_button":
                return True
            if interaction.user.id == self.duel.players[1].id and interaction.data["custom_id"] == "player2_button":
                return True
            await interaction.response.defer(ephemeral=True)
            return False

        # First player button
        @discord.ui.button(label="placeholder", style=discord.ButtonStyle.secondary, custom_id="player1_button")  # type: ignore
        async def player1_button(self, button, interaction):
            button.disabled = True
            button.style = discord.ButtonStyle.success
            await interaction.response.edit_message(view=self)
            await interaction.followup.send("\u200b", view=Game.PickMoveMessage(interaction.user, self.duel, self.data), ephemeral=True)

        # Second player button
        @discord.ui.button(label="placeholder", style=discord.ButtonStyle.secondary, custom_id="player2_button")  # type: ignore
        async def player2_button(self, button, interaction):
            button.disabled = True
            button.style = discord.ButtonStyle.success
            await interaction.response.edit_message(view=self)
            await interaction.followup.send("\u200b", view=Game.PickMoveMessage(interaction.user, self.duel, self.data), ephemeral=True)




    # ----------------------------------- Move selection screen
    # Is created ephemeral, and with an empty string message, so that when edited, the buttons don't move
    # Contains a button for rock, paper, and scissors
    # When both players confirm their choices, a final message is sent, the duel is logged, and then saved
    class PickMoveMessage(discord.ui.View):
        def __init__(self, player: discord.Member, duel: DuelEvent, data: DataHolder):
            super().__init__()
            self.disable_on_timeout = True
            self.player = player
            self.duel = duel
            self.data = data

        # Every choice, whether it's rock, paper, or scissors, calls this function
        async def confirm_move(self, interaction: discord.Interaction, move: Move):
            self.disable_all_items()
            await interaction.response.edit_message(view=self)
            self.duel.make_a_move(self.player, move)

            # When both players made their choices, resolve the game, log, and save
            if self.duel.is_complete():
                if self.duel.is_a_tie:
                    await interaction.followup.send(f"Both {self.duel.players[0].mention} and {self.duel.players[1].mention} play {self.duel.moves[self.duel.players[0].id]}\n"
                                                    f"Its a tie! No XP earned", ephemeral=False)
                else:
                    # Slightly different messages for variety
                    if randint(0, 1) == 1:
                        await interaction.followup.send( f"{self.duel.winner.mention} plays {self.duel.moves[self.duel.winner.id]} and beats {self.duel.loser.mention}'s {self.duel.moves[self.duel.loser.id]}\n\n"
                                                     f"{self.duel.winner.mention} wins and earns 20 XP!", ephemeral=False)
                    else:
                        await interaction.followup.send( f"{self.duel.loser.mention} plays {self.duel.moves[self.duel.loser.id]} and loses to {self.duel.winner.mention}'s {self.duel.moves[self.duel.winner.id]}\n\n"
                                                     f"{self.duel.winner.mention} wins! 20 XP earned", ephemeral=False)

                # Update user's stats and save
                self.data.log_duel_results(self.duel)
                self.data.save_to_disk()

        # Green rock button
        @discord.ui.button(label="Rock", style=discord.ButtonStyle.success)  # type: ignore
        async def rock_button(self, button, interaction):
            # Gray out all other buttons for effect
            for b in self.children:
                if b != button:
                    b.style = discord.ButtonStyle.secondary
            await self.confirm_move(interaction, Move.ROCK)

        # Blue paper button
        @discord.ui.button(label="Paper", style=discord.ButtonStyle.primary)  # type: ignore
        async def paper_button(self, button, interaction):
            for child in self.children:
                if child != button:
                    child.style = discord.ButtonStyle.secondary
            await self.confirm_move(interaction, Move.PAPER)

        # Red scissors button
        @discord.ui.button(label="Scissors", style=discord.ButtonStyle.danger)  # type: ignore
        async def scissors_button(self, button, interaction):
            for child in self.children:
                if child != button:
                    child.style = discord.ButtonStyle.secondary
            await self.confirm_move(interaction, Move.SCISSORS)