import re
import sys

import discord
from aiostream import stream
from discord.ext import commands
from pymongo.collation import Collation

import internal.constants as constants
import internal.pb_utils
from database.WorldRecords import WorldRecords
from internal import confirmation

if len(sys.argv) > 1:
    if sys.argv[1] == "test":
        from internal import constants_bot_test as constants_bot
else:
    from internal import constants_bot_prod as constants_bot


class SubmitPersonalBest(commands.Cog, name="Personal best submission/deletion"):
    """Commands to submit and delete personal bests."""

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        """Check if channel is RECORD_CHANNEL."""
        if ctx.channel.id == constants_bot.RECORD_CHANNEL_ID:
            return True

    # Submit personal best records
    @commands.command(
        help=(
            "Submit personal bests. Upload a screenshot with this message for proof!\n"
            "There will be a link to the original post when using the `/pb` command.\n"
            "Also updates a personal best if it is faster.\n\n"
            "<record> must be in HH:MM:SS.SS format! You can omit the hours or minutes.\n\n"
            "Use quotation marks around level names that have spaces.\n\n"
            "A list of previously submitted level names will appear on confirmation message."
        ),
        brief="Submit personal best",
    )
    async def submitpb(self, ctx, map_code, level, record):
        """Submit personal best to database."""

        if not re.match(r"^[a-zA-Z0-9]+$", map_code):
            await ctx.send(
                "Only letters A-Z and numbers 0-9 allowed in <map_code>. Map submission rejected."
            )
            return

        map_code = map_code.upper()
        level = level.upper()
        record_in_seconds = internal.pb_utils.time_convert(record)

        # Validates time
        if not record_in_seconds:
            await ctx.send("Invalid time. Map submission rejected.")
            return

        # Find currently associated levels
        level_checker = {}
        async for entry in (
            WorldRecords.find({"code": map_code})
            .sort([("level", 1), ("record", 1)])
            .collation(Collation(locale="en_US", numericOrdering=True))
            .limit(30)
        ):
            if entry.level.upper() not in level_checker.keys():
                level_checker[entry.level.upper()] = None

        # init embed
        embed = discord.Embed(title="Is this correct?")
        embed.add_field(
            name="Currently submitted level names:",
            value=f"{', '.join(level_checker) if level_checker else 'N/A'}",
        )

        # Finds document
        submission = await WorldRecords.find_one(
            {
                "code": map_code,
                "level": re.compile(level, re.IGNORECASE),
                "posted_by": ctx.author.id,
            }
        )

        # If document is found, verifies if submitted time is faster.
        if submission and record_in_seconds >= submission.record:
            await ctx.channel.send("Personal best needs to be faster to update.")
            return

        # Create new PB document, if none exists.
        if not submission:
            submission = WorldRecords(
                **dict(
                    code=map_code,
                    name=ctx.author.name,
                    record=record_in_seconds,
                    level=level,
                    posted_by=ctx.author.id,
                    message_id=ctx.message.id,
                    url=ctx.message.jump_url,
                    verified=False,
                )
            )

        # Verification embed for user.
        embed.add_field(
            name=f"Name: {submission.name}",
            value=(
                f"> Code: {submission.code}\n"
                f"> Level: {submission.level.upper()}\n"
                f"> Record: {internal.pb_utils.display_record(record_in_seconds)}\n"
            ),
            inline=False,
        )

        # Confirmation
        msg = await ctx.send(embed=embed)
        confirmed = await confirmation.confirm(ctx, msg)

        if confirmed is True:

            channel = self.bot.get_channel(constants_bot.HIDDEN_VERIFICATION_CHANNEL)

            # Try to fetch hidden_msg.
            try:
                hidden_msg = await channel.fetch_message(submission.hidden_id)
                if hidden_msg:
                    await hidden_msg.delete()
            # If not found, HTTPException is thrown, safely ignore
            except discord.errors.HTTPException:
                pass
            finally:
                await msg.edit(content="Submission accepted")

                # New hidden message
                hidden_msg = await channel.send(
                    f"{ctx.author.name} needs verification!\n{submission.code} - Level {submission.level} - {internal.pb_utils.display_record(record_in_seconds)}\n{ctx.message.jump_url}"
                )

                # Update submission
                submission.record = record_in_seconds
                submission.message_id = ctx.message.id
                submission.url = ctx.message.jump_url
                submission.name = ctx.author.name
                submission.verified = False
                submission.hidden_id = hidden_msg.id

                # Save document
                await submission.commit()

                # verification reacts
                await ctx.message.add_reaction(constants.VERIFIED_EMOJI)
                await ctx.message.add_reaction(constants.NOT_VERIFIED_EMOJI)

                # Find top 10 records and display submission's place in top 10.
                top_10 = (
                    WorldRecords.find(
                        {"code": map_code, "level": re.compile(level, re.IGNORECASE)}
                    )
                    .sort("record", 1)
                    .limit(10)
                )
                en = stream.enumerate(top_10)
                async with en.stream() as streamer:
                    async for rank, entry in streamer:
                        if submission:
                            if entry.pk == submission.pk:
                                await ctx.channel.send(
                                    f"Your rank is {rank + 1} on the unverified scoreboard."
                                )

        elif confirmed is False:
            await msg.edit(
                content="Submission has not been accepted.",
            )
        elif confirmed is None:
            await msg.edit(
                content="Submission timed out! Submission has not been accepted.",
            )

    # Delete pb
    @commands.command(
        help="Delete personal best record for a particular map code.\n<name> will default to your own.\nThis is only required for when a mod deletes another person's personal best.\nOnly original posters and mods can delete a personal best.",
        brief="Delete personal best record",
    )
    async def deletepb(self, ctx, map_code, level, name=""):
        """Delete personal best from database."""

        map_code = map_code.upper()
        level = level.upper()

        # Searches for author PB if none provided
        if name == "":
            name = ctx.author.name

        search = await WorldRecords.find_one(
            {
                "code": map_code,
                "level": re.compile(level, re.IGNORECASE),
                "name": name,
            }
        )

        if not search:
            await ctx.channel.send(
                "Provided arguments might not exist. Personal best deletion was unsuccesful."
            )
            return

        if search.posted_by != ctx.author.id or not bool(
            any(role.id in constants_bot.ROLE_WHITELIST for role in ctx.author.roles)
        ):
            await ctx.channel.send(
                "You do not have sufficient permissions. Personal best was not deleted."
            )
            return

        embed = discord.Embed(title="Do you want to delete this?")
        embed.add_field(
            name=f"Name: {search.name}",
            value=(
                f"> Code: {search.code}\n"
                f"> Level: {search.level.upper()}\n"
                f"> Record: {internal.pb_utils.display_record(search.record)}\n"
            ),
            inline=False,
        )

        msg = await ctx.send(embed=embed)
        confirmed = await confirmation.confirm(ctx, msg)

        if confirmed is True:
            await msg.edit(content="Personal best deleted succesfully.")
            await search.delete()
        elif confirmed is False:
            await msg.edit(content="Personal best was not deleted.")
        elif confirmed is None:
            await msg.edit(
                content="Deletion timed out! Personal best has not been deleted."
            )


def setup(bot):
    """Add Cog to Discord bot."""
    bot.add_cog(SubmitPersonalBest(bot))
