import discord
from discord import app_commands
from discord.ext import commands
import random
from wakeonlan import send_magic_packet
from dotenv import load_dotenv
import os
import wom

load_dotenv()
justin_mac_address = os.getenv('justin_mac_address')
bingo_mac_address = os.getenv('bingo_mac_address')

client = wom.Client()

class Random(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    #ui for the "wake" command
    class WoLMenu(discord.ui.View):
        @discord.ui.button(label="Justin", style=discord.ButtonStyle.blurple)
        async def button_one(self, interaction, button):
            send_magic_packet(justin_mac_address)
            await interaction.response.send_message("waking this bitch up", ephemeral=True, delete_after=10)

        @discord.ui.button(label="Bingo", style=discord.ButtonStyle.red)
        async def button_two(self, interaction, button):
            send_magic_packet(bingo_mac_address)
            await interaction.response.send_message("waking Bingo up", ephemeral=True, delete_after=10)

    #simple test to see if bot is running properly within discord
    @app_commands.command(name="test")
    async def test(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"test command initiated by {interaction.user.mention}, {self.bot.user.name} is online and ready to respond. Local Portainer can be reached at https://192.168.1.154:9443/#!/home if needed.", ephemeral=True)

    #command to wake up devices using WoL, buttons are generated from the WoLMenu class
    @app_commands.command(name="wake")
    @commands.has_permissions(administrator=True)
    async def wake(self, interaction: discord.Interaction):
        await interaction.response.send_message("Choose a device to wake up:", view=Random.WoLMenu(), ephemeral=True, delete_after=15)

    #basic dice roll - asks for side amount
    @app_commands.command(name="roll")
    async def roll(self, interaction: discord.Interaction, d: int):
        result = random.randint(1, d)
        await interaction.response.send_message(f"{interaction.user.mention} rolled a {result} from a d{d}", ephemeral=True)

    #0.1% chance to respond to someone typing
    @commands.Cog.listener()
    async def on_typing(self, channel, user, when):
        if random.randint(1, 1000) == 1 and user != self.bot.user:
            responses = [
                f"oh brother {user.display_name} is typing again",
                f"what is it this time {user.display_name}?",
                f"brother why is {user.display_name} speaking?"
            ]
            response = random.choice(responses)
            await channel.send(response)

    #pulls osrs stats from WOM
    @app_commands.command(name="osrs")
    async def osrs(self, interaction: discord.Interaction, username: str):
        try:
            await client.start()
            result = await client.players.update_player(username)
            if result.is_ok:
                combat_level = result.unwrap().combat_level
                data = result.unwrap().latest_snapshot.data
                skills = ['attack','defence','strength','hitpoints','ranged','prayer','magic','cooking','woodcutting','fletching','fishing','firemaking','crafting','smithing','mining','herblore','agility','thieving','slayer','farming','runecrafting','hunter','construction', 'sailing']
                overall_lvl = data.skills['overall'].level
                overall_exp = data.skills['overall'].experience
                overall = f"Lvl {overall_lvl} ({overall_exp:,} XP)"

                skill_lines = []
                for i in range(0, len(skills), 3):
                    skill_group = skills[i:i+3]
                    line_parts = []
                    for skill in skill_group:
                        exp = data.skills[skill].experience
                        lvl = data.skills[skill].level
                        line_parts.append(f"{skill.capitalize()}: Lvl {lvl} ({exp:,} XP)")
                    skill_lines.append("  ".join(line_parts))
                
                skills_text = "\n".join(skill_lines)
                message = f"```\n{username}'s Combat Level: {combat_level} | Total Level: {overall}\n\n{skills_text}\n```"
                await interaction.response.send_message(message, delete_after=15)
            else:
                await interaction.response.send_message(f"Could not find player: {username}", delete_after=15)
        except Exception as e:
            await interaction.response.send_message(f"Error fetching stats: {str(e)}", delete_after=15)
        finally:
            await client.close()

async def setup(bot):
    await bot.add_cog(Random(bot))