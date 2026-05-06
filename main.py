import discord
from discord import app_commands
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
from wakeonlan import send_magic_packet
import random
import wom
import traceback

load_dotenv()
token = os.getenv('DISCORD_TOKEN')
justin_mac_address = os.getenv('justin_mac_address')
bingo_mac_address = os.getenv('bingo_mac_address')

client = wom.Client()

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True
intents.guilds = True

class MyBot(commands.Bot):
    async def setup_hook(self):
        self.add_view(TicketButton()) #keep the ticket button working if you restart
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

#Modal for ticket system
class TicketPrompt(discord.ui.Modal, title="Open Ticket"):
    Issue =discord.ui.TextInput(
        label="Describe your issue",
        style=discord.TextStyle.long, 
        placeholder="Please describe the reason for opening this ticket...",
        required=True,
        max_length=1000
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            Ticket_Number=random.randint(1, 99999)
            guild=interaction.guild
            category = discord.utils.get(guild.categories, name="Tickets")
            overwrites={
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            
            channel=await guild.create_text_channel(
                name=f"🎟️ticket-{Ticket_Number}",
                overwrites=overwrites,
                category=category
            )

            await interaction.response.send_message(f"Ticket submitted! Your ticket number is {Ticket_Number}", ephemeral=True)
            await channel.send(f"{interaction.user.mention} has opened a ticket with the following issue:\n{self.Issue.value}")
        except Exception as e:
            print(f"Error in ticket submission: {e}")
            traceback.print_exc()
            try:
                await interaction.response.send_message("An error occurred while submitting your ticket. Please try again later.", ephemeral=True)
            except discord.InteractionResponded:
                await interaction.followup.send("An error occurred while submitting your ticket. Please try again later.", ephemeral=True)

    async def on_error(self, error: Exception, interaction: discord.Interaction):
        print(f"Modal error: {error}")
        traceback.print_exc()
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message("An error occurred while submitting your ticket. Please try again later.", ephemeral=True)
            else:
                await interaction.followup.send("An error occurred while submitting your ticket. Please try again later.", ephemeral=True)
        except Exception as e:
            print(f"Error sending error message: {e}")
            traceback.print_exc()

#UI for ticket system - generates a button that opens the TicketPrompt modal when clicked
class TicketButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Open Ticket", style=discord.ButtonStyle.green, custom_id="open_ticket_button")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TicketPrompt())

#simple test to see if bot is running properly within discord
@bot.tree.command(name="test")
async def test(interaction: discord.Interaction):
    await interaction.response.send_message(f"test command initiated by {interaction.user.mention}, {bot.user.name} is online and ready to respond. Local Portainer can be reached at https://192.168.1.154:9443/#!/home if needed.", ephemeral=True)

#send permament ticket button
@bot.command()
async def ticket(ctx):
    await ctx.send("Click the button below to open a ticket!", view=TicketButton())

#voice join test
@bot.command()
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
        await ctx.message.delete()
        await ctx.send(f"Joined {channel.name}", delete_after=5)
    else:
        await ctx.send("You are not connected to a voice channel.", delete_after=5)

#voice leave test
@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Left the voice channel.")
    else:
        await ctx.send("I am not connected to a voice channel.", delete_after=5)

#voice leave test if alone
@bot.event
async def on_voice_state_update(member, before, after):
    voice_client = member.guild.voice_client
    if voice_client and len(voice_client.channel.members) == 1:
        await voice_client.disconnect()
        print(f"Left the voice channel because {member} was the last one there.")

#closes ticket channel
@bot.tree.command(name="close")
async def close(interaction: discord.Interaction, category_name: str = "Archived Tickets"):
    if interaction.channel.name.startswith("🎟️ticket-"):
        #await interaction.channel.delete()
        category = discord.utils.get(interaction.guild.categories, name=category_name)
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        }
        if category:
            await interaction.channel.edit(category=category, overwrites=overwrites)
            await interaction.response.send_message(f"```Ticket closed and archived``` {interaction.user}")
        else:
            await interaction.response.send_message(f"Category '{category_name}' not found.", ephemeral=True, delete_after=5)
    else:
        await interaction.response.send_message("This command can only be used in a ticket channel.", ephemeral=True, delete_after=5)

#basic dice roll - asks for side amount
@bot.tree.command(name="roll")
async def roll(interaction: discord.Interaction, d: int):
    result = random.randint(1, d)
    await interaction.response.send_message(f"{interaction.user.mention} rolled a {result} from a d{d}", ephemeral=True)

#command to wake up devices using WoL, buttons are generated from the WoLMenu class
@bot.tree.command(name="wake")
@commands.has_permissions(administrator=True)
async def wake(interaction: discord.Interaction):
    await interaction.response.send_message("Choose a device to wake up:", view=WoLMenu(), ephemeral=True, delete_after=15)

#0.1% chance to respond to someone typing
@bot.event
async def on_typing(channel, user, when):
    if random.randint(1, 1000) == 1 and user != bot.user:
        responses = [
            f"oh brother {user.display_name} is typing again",
            f"what is it this time {user.display_name}?",
            f"brother why is {user.display_name} speaking?"
        ]
        response = random.choice(responses)
        await channel.send(response)

#pulls osrs stats from WOM
@bot.tree.command(name="osrs")
async def osrs(interaction: discord.Interaction, username: str):
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


bot.run(token, log_handler=handler, log_level=logging.DEBUG)