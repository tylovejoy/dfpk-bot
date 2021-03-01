import re
import sys

import discord
from discord.ext import commands
from pymongo.collation import Collation

from database.WorldRecords import WorldRecords
from internal import utilities, confirmation

if len(sys.argv) > 1:
    if sys.argv[1] == "test":
        from internal import test_constants as constants
else:
    from internal import constants


class SubmitPersonalBest(commands.Cog, name="Personal best submission/deletion"):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        if ctx.channel.id == constants.RECORD_CHANNEL_ID:
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
        # input validation
        if "$" in map_code or "$" in level or "$" in record:
            map_code.replace("$", "")
            level.replace("$", "")
            record.replace("$", "")
        for x in map_code:
            if (
                x
                not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
            ):
                await ctx.send(
                    "Only letters A-Z and numbers 0-9 allowed in <map_code>. Map submission rejected."
                )
                return
        level = level.upper()
        record_in_seconds = utilities.time_convert(record)
        level_checker = {}
        embed = discord.Embed(title="Is this correct?")
        async for entry in (
            WorldRecords.find({"code": map_code.upper()})
            .sort([("level", 1), ("record", 1)])
            .collation(Collation(locale="en_US", numericOrdering=True))
            .limit(30)
        ):
            if entry.level.upper() not in level_checker.keys():
                level_checker[entry.level.upper()] = None
        embed.add_field(
            name="Currently submitted level names:",
            value=f"{', '.join(level_checker) if level_checker else 'N/A'}",
        )
        if record_in_seconds:
            map_code = map_code.upper()
            which_place = False
            submission = None
            # New DB entry for PB
            if (
                await WorldRecords.count_documents(
                    {"code": map_code, "level": re.compile(level, re.IGNORECASE), "posted_by": ctx.author.id}
                )
                == 0
            ):
                submission = WorldRecords(
                    **dict(
                        code=map_code,
                        name=ctx.author.name,
                        record=record_in_seconds,
                        level=level.upper(),
                        posted_by=ctx.author.id,
                        message_id=ctx.message.id,
                        url=ctx.message.jump_url,
                        verified=False,
                    )
                )
                embed.add_field(
                    name=f"Name: {submission.name}",
                    value=(
                        f"> Code: {submission.code}\n"
                        f"> Level: {submission.level.upper()}\n"
                        f"> Record: {utilities.display_record(record_in_seconds)}\n"
                    ),
                    inline=False,
                )

                msg = await ctx.send(embed=embed)
                confirmed = await confirmation.confirm(ctx, msg)

                if confirmed is True:
                    await msg.edit(
                        content=f"Submission accepted",
                    )

                    channel = self.bot.get_channel(
                        constants.HIDDEN_VERIFICATION_CHANNEL
                    )

                    hidden_msg = await channel.send(
                        f"{submission.code} - Level {submission.level} - {utilities.display_record(record_in_seconds)}\n{submission.url}"
                    )
                    submission.hidden_id = hidden_msg.id
                    await submission.commit()
                    await ctx.message.add_reaction(constants.VERIFIED_EMOJI)
                    await ctx.message.add_reaction(constants.NOT_VERIFIED_EMOJI)
                    which_place = True
                elif confirmed is False:
                    await msg.edit(
                        content=f"Submission has not been accepted.",
                    )
                elif confirmed is None:
                    await msg.edit(
                        content=f"Submission timed out! Submission has not been accepted.",
                    )

            # If there is already a personal best in DB
            elif (
                await WorldRecords.count_documents(
                    {"code": map_code, "level": re.compile(level, re.IGNORECASE), "posted_by": ctx.author.id}
                )
                == 1
            ):
                submission = await WorldRecords.find_one(
                    {"code": map_code, "level": re.compile(level, re.IGNORECASE), "posted_by": ctx.author.id}
                )
                # If new record is faster than old record
                if record_in_seconds < submission.record:
                    embed.add_field(
                        name=f"Name: {submission.name}",
                        value=(
                            f"> Code: {submission.code}\n"
                            f"> Level: {submission.level.upper()}\n"
                            f"> Record: {utilities.display_record(record_in_seconds)}\n"
                        ),
                        inline=False,
                    )
                    msg = await ctx.send(
                        embed=embed,
                    )
                    confirmed = await confirmation.confirm(ctx, msg)

                    if confirmed is True:
                        # Delete standing hidden channel post, if applicable
                        channel = self.bot.get_channel(
                            constants.HIDDEN_VERIFICATION_CHANNEL
                        )
                        try:
                            hidden_msg = await channel.fetch_message(
                                submission.hidden_id
                            )
                            if hidden_msg:
                                await hidden_msg.delete()
                        except:
                            pass
                        finally:
                            await msg.edit(content="Submission accepted")

                            # Update submission
                            submission.record = record_in_seconds
                            submission.message_id = ctx.message.id
                            submission.url = ctx.message.jump_url
                            submission.name = ctx.author.name
                            submission.verified = False

                            # New hidden message
                            hidden_msg = await channel.send(
                                f"{submission.name} - {submission.code} - Level {submission.level} - {utilities.display_record(record_in_seconds)}\n{submission.url}"
                            )
                            submission.hidden_id = hidden_msg.id
                            await submission.commit()

                            await ctx.message.add_reaction(constants.VERIFIED_EMOJI)
                            await ctx.message.add_reaction(constants.NOT_VERIFIED_EMOJI)
                            which_place = True
                    elif confirmed is False:
                        await msg.edit(content=f"Submission has not been accepted.")
                    elif confirmed is None:
                        await msg.edit(
                            content=f"Submission timed out! Submission has not been accepted."
                        )

                else:
                    await ctx.channel.send(
                        "Personal best needs to be faster to update."
                    )
            if which_place:
                update = (
                    WorldRecords.find({"code": map_code, "level": re.compile(level, re.IGNORECASE)})
                    .sort("record", 1)
                    .limit(10)
                )
                rank = 0
                async for entry in update:
                    rank += 1
                    if submission:
                        if entry.pk == submission.pk:
                            await ctx.channel.send(
                                f"Your rank is {rank} on the unverified scoreboard."
                            )

    # Delete pb
    @commands.command(
        help="Delete personal best record for a particular map code.\n<name> will default to your own.\nThis is only required for when a mod deletes another person's personal best.\nOnly original posters and mods can delete a personal best.",
        brief="Delete personal best record",
    )
    async def deletepb(self, ctx, map_code, level, name=""):
        if "$" in map_code or "$" in level or "$" in name:
            map_code.replace("$", "")
            level.replace("$", "")
            name.replace("$", "")
        map_code = map_code.upper()
        if name == "":
            name = ctx.author.name
        level = level.upper()
        if (
            await WorldRecords.count_documents(
                {"code": map_code, "level": re.compile(level, re.IGNORECASE), "name": name}
            )
            == 1
        ):
            search = await WorldRecords.find_one(
                {"code": map_code, "level": re.compile(level, re.IGNORECASE), "name": name}
            )

            if search.posted_by == ctx.author.id or bool(any(role.id in constants.ROLE_WHITELIST for role in ctx.author.roles)):
                embed = discord.Embed(title="Do you want to delete this?")
                embed.add_field(
                    name=f"Name: {search.name}",
                    value=(
                        f"> Code: {search.code}\n"
                        f"> Level: {search.level.upper()}\n"
                        f"> Record: {utilities.display_record(search.record)}\n"
                    ),
                    inline=False,
                )
                msg = await ctx.send(embed=embed)
                confirmed = await confirmation.confirm(ctx, msg)
                if confirmed is True:
                    await msg.edit(content=f"Personal best deleted succesfully.")
                    await search.delete()
                elif confirmed is False:
                    await msg.edit(content=f"Personal best was not deleted.")
                elif confirmed is None:
                    await msg.edit(
                        content=f"Deletion timed out! Personal best has not been deleted."
                    )

            else:
                await ctx.channel.send("You cannot delete that!")
        else:
            await ctx.channel.send(
                "Provided arguments might not exist. Personal best deletion was unsuccesful."
            )


def setup(bot):
    bot.add_cog(SubmitPersonalBest(bot))
