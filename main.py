import discord
from discord import app_commands
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
from wakeonlan import send_magic_packet
import random

load_dotenv()
token = os.getenv('DISCORD_TOKEN')
justin_mac_address = os.getenv('justin_mac_address')
bingo_mac_address = os.getenv('bingo_mac_address')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)

class WoLMenu(discord.ui.View):
    @discord.ui.button(label="Justin", style=discord.ButtonStyle.blurple)
    async def button_one(self, interaction, button):
        send_magic_packet(justin_mac_address)
        await interaction.response.send_message("Sent Wake-on-LAN packet to Justin's PC.")

    @discord.ui.button(label="Bingo", style=discord.ButtonStyle.red)
    async def button_two(self, interaction, button):
        send_magic_packet(bingo_mac_address)
        await interaction.response.send_message("Sent Wake-on-LAN packet to Bingo.")

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")

@bot.command()
async def ping(ctx):
    await ctx.send('Pong!')

@bot.command()
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
        await ctx.message.delete()
        await ctx.send(f"Joined {channel.name}", delete_after=5)
    else:
        await ctx.send("You are not connected to a voice channel.")

@bot.event
async def on_voice_state_update(member, before, after):
    voice_client = member.guild.voice_client
    if voice_client and len(voice_client.channel.members) == 1:
        await voice_client.disconnect()
        print(f"Left the voice channel because {member} was the last one there.")

@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Left the voice channel.")
    else:
        await ctx.send("I am not connected to a voice channel.")


@bot.command()
@commands.has_permissions(administrator=True)
async def wake(ctx):
    await ctx.send("Choose a device to wake up:", view=WoLMenu(), delete_after=30)

@bot.event
async def on_typing(channel, user, when):
    if random.randint(1, 100) == 1 and user != bot.user:
        responses = [
            f"I see you are typing... {user.mention}",
            "What are you going to say?",
            "Don't keep me waiting!",
            "I'm all ears!",
            "Can't wait to read your message!"
        ]
        response = random.choice(responses)
        await channel.send(response)



bot.run(token, log_handler=handler, log_level=logging.DEBUG)