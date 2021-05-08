import sys

import discord
from discord.ext import commands

from database.BonusData import BonusData
from database.HardcoreData import HardcoreData
from database.MildcoreData import MildcoreData
from database.TimeAttackData import TimeAttackData
from internal.pb_utils import time_convert, display_record
from internal.tournament_utils import (
    category_sort,
    tournament_boards,
    confirm_collection_drop,
    exporter,
)

if len(sys.argv) > 1:
    if sys.argv[1] == "test":
        from internal import constants_bot_test as constants_bot, confirmation
else:
    from internal import constants_bot_prod as constants_bot


def viewable_channels():
    def predicate(ctx):
        return ctx.channel.id in [
            constants_bot.TOURNAMENT_CHAT_CHANNEL_ID,
            constants_bot.ORG_CHANNEL_ID,
        ]

    return commands.check(predicate)


class Tournament(commands.Cog, name="Tournament"):
    """Tournament"""

    def __init__(self, bot):
        self.bot = bot

    def cog_check(self, ctx):
        if ctx.channel.id in [
            constants_bot.TOURNAMENT_CHAT_CHANNEL_ID,
            constants_bot.HC_CHANNEL_ID,
            constants_bot.TA_CHANNEL_ID,
            constants_bot.MC_CHANNEL_ID,
            constants_bot.BONUS_CHANNEL_ID,
            constants_bot.ORG_CHANNEL_ID,
        ]:
            return True

    @commands.command(
        name="submit",
        help="Record must be in HH:MM:SS.ss format. Attach a screenshot to the submission message.",
        brief="Submit times to tournament.",
    )
    async def submit(self, ctx, record):

        category = category_sort(ctx.message)
        if category is None:
            return

        if not ctx.message.attachments:
            await ctx.send(
                "No attachment found. Please submit time with attachment in the same message."
            )
            return

        record_in_seconds = time_convert(record)

        # Validates time
        if not record_in_seconds:
            await ctx.send("Invalid time. Map submission rejected.")
            return

        # Finds document
        if category == "TIMEATTACK":
            _find_one = TimeAttackData.find_one({"posted_by": ctx.author.id})
        elif category == "MILDCORE":
            _find_one = MildcoreData.find_one({"posted_by": ctx.author.id})
        elif category == "HARDCORE":
            _find_one = HardcoreData.find_one({"posted_by": ctx.author.id})
        else:  # "BONUS"
            _find_one = BonusData.find_one({"posted_by": ctx.author.id})

        search = await _find_one

        # If document is found, verifies if submitted time is faster (if verified).
        if (search and (record_in_seconds >= search.record)) is True:
            await ctx.channel.send(
                "Times submitted for the tournament needs to be faster than prior submissions."
            )
            return

        # Create new TournamentData document, if none exists.
        if not search:
            if category == "TIMEATTACK":
                _new_submission = TimeAttackData
            elif category == "MILDCORE":
                _new_submission = MildcoreData
            elif category == "HARDCORE":
                _new_submission = HardcoreData
            else:  # "BONUS"
                _new_submission = BonusData

            search = _new_submission(
                **{
                    "posted_by": ctx.author.id,
                    "record": record_in_seconds,
                    "attachment_url": ctx.message.attachments[0].url,
                }
            )

        embed = discord.Embed(title="Is this correct?")
        # Verification embed for user.
        embed.add_field(
            name=f"Name: {discord.utils.find(lambda m: m.id == search.posted_by, ctx.guild.members).name}",
            value=(
                f"> Category: {category}\n"
                f"> Record: {display_record(record_in_seconds)}\n"
            ),
            inline=False,
        )

        msg = await ctx.send(embed=embed)
        confirmed = await confirmation.confirm(ctx, msg)

        if confirmed is True:
            await msg.edit(content="Submission accepted")
            # Update record
            search.record = record_in_seconds
            # Save document
            await search.commit()

        elif confirmed is False:
            await msg.edit(
                content="Submission has not been accepted.",
            )

        elif confirmed is None:
            await msg.edit(
                content="Submission timed out! Submission has not been accepted.",
            )

    @commands.group(pass_context=True, case_insensitive=True)
    @viewable_channels()
    async def view(self, ctx):
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title="View Tournament Times",
                description="Choose a specific category to view currently submitted times for that category.",
            )
            for cmd in self.bot.get_command("view").walk_commands():
                embed.add_field(name=f"{cmd}", value=f"{cmd.help}", inline=False)
            await ctx.send(embed=embed)

    @view.command(
        name="ta", aliases=["timeattack", "time-attack"], help="View time attack times"
    )
    @viewable_channels()
    async def _timeattack(self, ctx):
        await tournament_boards(ctx, "TIMEATTACK")

    @view.command(name="mc", aliases=["mildcore"], help="View mildcore times")
    @viewable_channels()
    async def _mildcore(self, ctx):
        await tournament_boards(ctx, "MILDCORE")

    @view.command(name="hc", aliases=["hardcore"], help="View hardcore times")
    @viewable_channels()
    async def _hardcore(self, ctx):
        await tournament_boards(ctx, "HARDCORE")

    @view.command(name="bonus", help="View bonus times")
    @viewable_channels()
    async def _bonus(self, ctx):
        await tournament_boards(ctx, "BONUS")

    @commands.group(pass_context=True, case_insensitive=True)
    @commands.has_role(constants_bot.ORG_ROLE_ID)
    async def clear(self, ctx):
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title="Clear Tournament Times",
                description="Clear all times from a specific tournament category.",
            )
            for cmd in self.bot.get_command("clear").walk_commands():
                embed.add_field(name=f"{cmd}", value=f"{cmd.help}", inline=False)
            await ctx.send(embed=embed)

    @clear.command(
        name="ta", aliases=["timeattack", "time-attack"], help="Clear time attack times"
    )
    @commands.has_role(constants_bot.ORG_ROLE_ID)
    async def _timeattack_clear(self, ctx):
        await confirm_collection_drop(ctx, "time attack")

    @clear.command(name="mc", aliases=["mildcore"], help="Clear mildcore times")
    @commands.has_role(constants_bot.ORG_ROLE_ID)
    async def _mildcore_clear(self, ctx):
        await confirm_collection_drop(ctx, "mildcore")

    @clear.command(name="hc", aliases=["hardcore"], help="Clear hardcore times")
    @commands.has_role(constants_bot.ORG_ROLE_ID)
    async def _hardcore_clear(self, ctx):
        await confirm_collection_drop(ctx, "hardcore")

    @clear.command(name="bonus", help="Clear bonus times")
    @commands.has_role(constants_bot.ORG_ROLE_ID)
    async def _bonus_clear(self, ctx):
        await confirm_collection_drop(ctx, "bonus")

    @clear.command(name="all", help="Clear all times")
    @commands.has_role(constants_bot.ORG_ROLE_ID)
    async def _all_clear(self, ctx):
        await confirm_collection_drop(ctx, "all")

    @commands.group(pass_context=True, case_insensitive=True)
    @commands.has_role(constants_bot.ORG_ROLE_ID)
    async def export(self, ctx):
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title="Export Tournament Screenshots",
                description="Grab all screenshots from a specific tournament category.",
            )
            for cmd in self.bot.get_command("export").walk_commands():
                embed.add_field(name=f"{cmd}", value=f"{cmd.help}", inline=False)
            await ctx.send(embed=embed)

    @export.command(
        name="ta",
        aliases=["timeattack", "time-attack"],
        help="Export time attack screenshots",
    )
    async def _export_timeattack(self, ctx):
        await exporter(
            ctx, "TIMEATTACK", self.bot.get_channel(constants_bot.EXPORT_SS_CHANNEL_ID)
        )

    @export.command(name="mc", aliases=["mildcore"], help="Export mildcore screenshots")
    async def _export_mildcore(self, ctx):
        await exporter(
            ctx, "MILDCORE", self.bot.get_channel(constants_bot.EXPORT_SS_CHANNEL_ID)
        )

    @export.command(name="hc", aliases=["hardcore"], help="Export hardcore screenshots")
    async def _export_hardcore(self, ctx):
        await exporter(
            ctx, "HARDCORE", self.bot.get_channel(constants_bot.EXPORT_SS_CHANNEL_ID)
        )

    @export.command(name="bonus", help="Export bonus screenshots")
    async def _export_bonus(self, ctx):
        await exporter(
            ctx, "BONUS", self.bot.get_channel(constants_bot.EXPORT_SS_CHANNEL_ID)
        )


def setup(bot):
    """Add Cog to Discord bot."""
    bot.add_cog(Tournament(bot))
