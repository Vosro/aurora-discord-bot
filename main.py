import discord
from discord import app_commands
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os


load_dotenv()
token = os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True
intents.guilds = True

class MyBot(commands.Bot):
    async def setup_hook(self):
        # Load all cogs in well.. ./cogs
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                await self.load_extension(f'cogs.{filename[:-3]}')
                print(f'Loaded extension: {filename}')
bot = MyBot(command_prefix='!', intents=intents, status=discord.Status.idle, activity=discord.CustomActivity(name="jorkin it"))

## verifies bot is running and commands are synced
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Error syncing commands: {e}")
    try:
        #keep already posted ticket buttons working after bot restarts
        from cogs.Ticket import Ticket
        bot.add_view(Ticket.TicketButton())
    except Exception as e:
        print(f"Error adding TicketButton view: {e}")

@bot.tree.command(name="reload", description="Reloads all cogs")
@commands.is_owner()
async def reload_cogs(interaction: discord.Interaction):
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.reload_extension(f'cogs.{filename[:-3]}')
            print(f'Reloaded extension: {filename}')
    await interaction.response.send_message("Cogs reloaded!", ephemeral=True, delete_after=10)

#bot.run(token, log_handler=handler, log_level=logging.DEBUG)
bot.run(token)