import discord
from discord import app_commands
from discord.ext import commands

class Tests(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    #voice join test
    @commands.command()
    async def join(self, ctx):
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            await channel.connect()
            await ctx.message.delete()
            await ctx.send(f"Joined {channel.name}", delete_after=5)
        else:
            await ctx.send("You are not connected to a voice channel.", delete_after=5)

        #voice leave test
    @commands.command()
    async def leave(self, ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("Left the voice channel.")
        else:
            await ctx.send("I am not connected to a voice channel.", delete_after=5)

    #voice leave test if alone
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        voice_client = member.guild.voice_client
        if voice_client and len(voice_client.channel.members) == 1:
            await voice_client.disconnect()
            print(f"Left the voice channel because {member} was the last one there.")

async def setup(bot):
    await bot.add_cog(Tests(bot))