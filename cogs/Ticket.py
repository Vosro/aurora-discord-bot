import discord
from discord import app_commands
from discord.ext import commands
import random
import traceback

class Ticket(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

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
            await interaction.response.send_modal(Ticket.TicketPrompt())
    #send permament ticket button
    @commands.command()
    async def ticket(self, ctx):
        await ctx.send("Click the button below to open a ticket!", view=self.TicketButton())

    #archives ticket channel
    @app_commands.command(name="close")
    async def close(self, interaction: discord.Interaction, category_name: str = "Archived Tickets"):
        if interaction.channel.name.startswith("🎟️ticket-"):
            #await interaction.channel.delete()
            category = discord.utils.get(interaction.guild.categories, name=category_name)
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            }
            if category:
                await interaction.channel.edit(category=category, overwrites=overwrites)
                await interaction.response.send_message(f"```Ticket closed and archived``` by: {interaction.user}")
            else:
                await interaction.response.send_message(f"Category '{category_name}' not found.", ephemeral=True, delete_after=5)
        else:
            await interaction.response.send_message("This command can only be used in a ticket channel.", ephemeral=True, delete_after=5)

    
async def setup(bot):
    await bot.add_cog(Ticket(bot))