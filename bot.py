import json
import os
import discord
from discord.ext import commands
from discord.commands import Option

# Load data and config
if os.path.exists("players.json"):
    with open("players.json", "r") as f: # r = read mode, w = write mode
        data = json.load(f) # data is now a dict
    print("--- DATA LOADED FROM FILE ---")
else:
    data = {}  # start empty
    print("--- DATA FILE NOT FOUND ---")

with open("config.json", "r") as f:
    config = json.load(f)
GUILD = config["guild_id"]
TOKEN = config["token"]

# Temp object that stores info about the ongoing duel
class DuelEvent:

    def __init__(self, player0: discord.Member, player1: discord.Member):
        self.p0 = player0
        self.p1 = player1
        self.moves = [None, None]

    def place_move(self, playerID: int, move: str):
        self.moves[playerID] = move

    def is_complete(self):
        if self.moves[0] and self.moves[1]:
            return True

    def winner(self):

        # If the duel is not complete
        if not self.moves[0] or not self.moves[1]:
            return None

        # If it's a tie
        if self.moves[0] == self.moves[1]:
            return None

        beats = {"rock": "scissors", "paper": "rock", "scissors": "paper"}
        if beats[self.moves[0]] == self.moves[1]:
            return self.p0
        else:
            return self.p1


# ------ Rock - Paper - Scissors buttons ------


class MoveSelectionView(discord.ui.View):

    def __init__(self, playerID: int, duelEvent: DuelEvent):
        super().__init__()
        self.playerID = playerID
        self.duel = duelEvent

    # Every choice calls this function
    async def process_move(self, interaction: discord.Interaction, move: str):

        self.duel.place_move(self.playerID, move)
        self.disable_all_items()
        await interaction.response.edit_message(view=self)

        # Resolve the duel
        if self.duel.is_complete():
            winner = self.duel.winner()
            if winner:

                winner_id = str(winner.id)
                data.setdefault(winner_id, {"username": winner.name, "xp": 0, "wins": 0}) # if winner's id not in data, create it with default values
                data[winner_id]["xp"] += 10
                data[winner_id]["wins"] += 1
                with open("players.json", "w") as f:
                    json.dump(data, f, indent=4)

                await interaction.followup.send(f"{self.duel.p0.mention} plays {self.duel.moves[0]}\n{self.duel.p1.mention} plays {self.duel.moves[1]}\n{winner.mention} wins!! +10 XP", ephemeral=False)
            
            else:
                await interaction.followup.send(f"{self.duel.p0.mention} plays {self.duel.moves[0]}\n{self.duel.p1.mention} plays {self.duel.moves[1]}\nIts a tie!!", ephemeral=False)

    # Buttons themselves
    @discord.ui.button(label="Rock", style=discord.ButtonStyle.success)
    async def rock_button(self, button, interaction):
        for child in self.children:
            if child != button:
                child.style=discord.ButtonStyle.secondary
        await self.process_move(interaction, "rock")

    @discord.ui.button(label="Paper", style=discord.ButtonStyle.primary)
    async def paper_button(self, button, interaction):
        for child in self.children:
            if child != button:
                child.style=discord.ButtonStyle.secondary
        await self.process_move(interaction, "paper")

    @discord.ui.button(label="Scissors", style=discord.ButtonStyle.danger)
    async def scissors_button(self, button, interaction):
        for child in self.children:
            if child != button:
                child.style=discord.ButtonStyle.secondary
        await self.process_move(interaction, "scissors")


# ------ Two player buttons. This exists to confirm both players. Each presses their own name and receives move options ------


class AcceptDuelView(discord.ui.View):

    def __init__(self, duelEvent: DuelEvent):
        super().__init__()
        self.disable_on_timeout = True
        self.duel = duelEvent
        self.p0_button.label = f"{self.duel.p0.display_name}"
        self.p1_button.label = f"{self.duel.p1.display_name}"

    # Prevent others from confirming
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self.duel.p0.id and interaction.data["custom_id"] == "p0":
            return True
        if interaction.user.id == self.duel.p1.id and interaction.data["custom_id"] == "p1":
            return True
        await interaction.response.defer(ephemeral=True)
        return False

    @discord.ui.button(label="Placeholder", style=discord.ButtonStyle.secondary, custom_id="p0")
    async def p0_button(self, button, interaction):
        button.disabled = True
        button.style = discord.ButtonStyle.success
        await interaction.response.edit_message(view=self)
        await interaction.followup.send("\u200b", view=MoveSelectionView(0, self.duel), ephemeral=True)

    @discord.ui.button(label="Placeholder", style=discord.ButtonStyle.secondary, custom_id="p1")
    async def p1_button(self, button, interaction):
        button.disabled = True
        button.style = discord.ButtonStyle.success
        await interaction.response.edit_message(view=self)
        await interaction.followup.send("\u200b", view=MoveSelectionView(1, self.duel), ephemeral=True)


# ------ Slash commands ------


@bot.slash_command(guild_ids=[GUILD], name="rps", description="Challenge another user in a game of Rock-Paper-Scissors")
async def rps(ctx, opponent: Option(discord.Member, "Pick a user to challange", required = True)):
    # Keep this code, it prevents user for challanging themselves
    #if ctx.author.id == opponent.id:
    #    await ctx.respond(f"Don't play with yourself :P", ephemeral=True)
    #else:
        duelEvent = DuelEvent(ctx.author, opponent)
        await ctx.respond(f"{ctx.author.mention} challenges {opponent.mention} to an RPS duel. Both must accept this challenge to proceed.", view=AcceptDuelView(duelEvent))

@bot.slash_command(guild_ids=[GUILD], name="rps-stats", description="See RPS stastics of a chosen user")
async def wincount(ctx, user: Option(discord.Member, "Pick a user to analyse", required = True)):
    user_id = str(user.id)
    data.setdefault(user_id, {"username": user.name, "xp": 0, "wins": 0}) # if user is not in data, create it with default values
    win_or_wins = "wins"
    if data[user_id]["wins"] == 1:
        win_or_wins = "win"
    await ctx.respond(f"{user.display_name} has {data[user_id]["xp"]} XP and {data[user_id]["wins"]} {win_or_wins}")


# ----- Create the bot ------


# Default intents, the bot can't read message content
intents = discord.Intents.default()

# Create bot with default intents
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print("--- COMMANDS READY ---")

bot.run(TOKEN)
