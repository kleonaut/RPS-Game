import json
import discord
from discord.ext import commands
from cogs.game import Game

print("-\n-\n-\n-\n-\n------ ENVIRONMENT STARTED, BOOTING UP")

# Scope: Bot, Application.Commands
# Perms: Send Messages, Embed Links, Use Slash Commands
# Perm integer: 2147502080
# Invite URL: https://discord.com/oauth2/authorize?client_id=909967801928785980&permissions=2147502080&integration_type=0&scope=bot+applications.commands

# Default intents - the bot can't read message content
intents = discord.Intents.default()

# Instantiate the bot
bot = commands.Bot(command_prefix="!", intents=intents)

#bot.load_extension('cogs.game')
bot.add_cog(Game(bot))

# Listener
@bot.event
async def on_ready():
    print("------ BOT IS RUNNING")

# Load token from local file
with open("config.json", "r") as file:
    config = json.load(file)
bot.run(config["TOKEN"])

