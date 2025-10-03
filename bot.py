import json
import os
import discord
from discord.ext import commands
from discord.commands import Option
from typing import List

print("--- ENVIRONMENT STARTED ---")

# Default intents, the bot can't read message content
intents = discord.Intents.default()
# Scope: Bot. Application.Cmmands; Perms: Send Messages, Embed Links, Use Slash Commands; Perm integer: 2147502080
# Invite URL: https://discord.com/oauth2/authorize?client_id=909967801928785980&permissions=2147502080&integration_type=0&scope=bot+applications.commands

# Create bot with default intents
bot = commands.Bot(command_prefix="!", intents=intents)

# Load data and config
if os.path.exists("players.json"):
    with open("players.json", "r") as f: # r = read mode, w = write mode
        data = json.load(f) # data is now a dict
    print("--- PLAYERS DATA LOADED FROM FILE ---")
else:
    data = {}  # start empty
    print("--- PLAYERS DATA FILE NOT FOUND, NEW WILL BE GENERATED UPON INTERACTION ---")

with open("config.json", "r") as f:
    config = json.load(f)
GUILD_IDS = config["guild_ids"]
TOKEN = config["token"]

# Temp object that stores info about the ongoing duel
class DuelEvent:

    def __init__(self, player0: discord.Member, player1: discord.Member):
        self.p0 = player0
        self.p1 = player1
        self.moves: List[str|None] = [None, None]

    def place_move(self, player_id: int, move: str):
        self.moves[player_id] = move

    def is_complete(self) -> bool:
        if self.moves[0] and self.moves[1]:
            return True
        return False

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
    @discord.ui.button(label="Rock", style=discord.ButtonStyle.secondary) # type: ignore
    async def rock_button(self, button, interaction):
        for child in self.children:
            if child != button:
                child.style=discord.ButtonStyle.secondary
        await self.process_move(interaction, "rock")

    @discord.ui.button(label="Paper", style=discord.ButtonStyle.primary) # type: ignore
    async def paper_button(self, button, interaction):
        for child in self.children:
            if child != button:
                child.style=discord.ButtonStyle.secondary
        await self.process_move(interaction, "paper")

    @discord.ui.button(label="Scissors", style=discord.ButtonStyle.danger) # type: ignore
    async def scissors_button(self, button, interaction):
        for child in self.children:
            if child != button:
                child.style=discord.ButtonStyle.secondary
        await self.process_move(interaction, "scissors")


# ------ Two player buttons. This exists to confirm both players. Each presses their own name and receives move options ------


class AcceptDuelView(discord.ui.View):

    def __init__(self, duel_vent: DuelEvent):
        super().__init__()
        self.disable_on_timeout = True
        self.duel = duel_vent
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

    @discord.ui.button(label="Placeholder", style=discord.ButtonStyle.secondary, custom_id="p0") # type: ignore
    async def p0_button(self, button, interaction):
        button.disabled = True
        button.style = discord.ButtonStyle.success
        await interaction.response.edit_message(view=self)
        await interaction.followup.send("\u200b", view=MoveSelectionView(0, self.duel), ephemeral=True)

    @discord.ui.button(label="Placeholder", style=discord.ButtonStyle.secondary, custom_id="p1") # type: ignore
    async def p1_button(self, button, interaction):
        button.disabled = True
        button.style = discord.ButtonStyle.success
        await interaction.response.edit_message(view=self)
        await interaction.followup.send("\u200b", view=MoveSelectionView(1, self.duel), ephemeral=True)


# ------ Slash commands ------
# type: ignore[reportInvalidTypeForm]

@bot.slash_command(guild_ids=GUILD_IDS, name="rps", description="Challenge another user in a game of Rock-Paper-Scissors")
async def rps(ctx, opponent: Option(discord.Member, description="Pick a user to challange", required = True)): # type: ignore
    # Keep this code, it prevents user for challenging themselves
    #if ctx.author.id == opponent.id:
    #    await ctx.respond(f"Don't play with yourself :P", ephemeral=True)
    #else:
        duelEvent = DuelEvent(ctx.author, opponent)
        await ctx.respond(f"{ctx.author.mention} challenges {opponent.mention} to an RPS duel. Both must accept this challenge to proceed.", view=AcceptDuelView(duelEvent))

@bot.slash_command(guild_ids=GUILD_IDS, name="rps-stats", description="See RPS stastics of a chosen user")
async def win_count(ctx, user: Option(discord.Member, description="Pick a user to analyse", required = True)): # type: ignore
    user_id = str(user.id)
    data.setdefault(user_id, {"username": user.name, "xp": 0, "wins": 0}) # if user is not in data, create it with default values
    win_or_wins = "wins"
    if data[user_id]["wins"] == 1:
        win_or_wins = "win"
    await ctx.respond(f"{user.display_name} has {data[user_id]["xp"]} XP and {data[user_id]["wins"]} {win_or_wins}")


# ------ Run the bot ------


@bot.event
async def on_ready():
    print("--- BOT COMMANDS READY ---")

bot.run(TOKEN)