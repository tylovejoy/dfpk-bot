import discord
from discord.ext import commands
import asyncio
from internal import constants, utilities, confirmation
from database.WorldRecords import WorldRecords
from mongosanitizer.sanitizer import sanitize
import prettytable
import datetime
import logging


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
            "<record> must be in HH:MM:SS.SS format! You can omit the hours or minutes.\n"
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
        record_in_seconds = utilities.time_convert(record)
        level_checker = set()
        async for entry in (
            WorldRecords.find({"code": map_code.upper()})
            .sort("record", 1)
            .limit(30)
        ):
            if entry.level not in level_checker:
                level_checker.add(entry.level)
        if record_in_seconds:
            map_code = map_code.upper()
            which_place = False
            submission = None
            # New DB entry for PB
            if (
                await WorldRecords.count_documents(
                    {"code": map_code, "level": level, "posted_by": ctx.author.id}
                )
                == 0
            ):
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

                pt = prettytable.PrettyTable(
                    field_names=["Map Code", "Level", "Record", "Name"]
                )
                pt.add_row(
                    [
                        submission.code,
                        submission.level,
                        utilities.display_record(record_in_seconds),
                        submission.name,
                    ]
                )

                msg = await ctx.send("```\n" + ", ".join(level_checker) + "```\n" + f"```\nIs this correct?\n{pt}```")
                confirmed = await confirmation.confirm(ctx, msg)

                if confirmed is True:
                    await msg.edit(content=f"```\n{pt}```\nSubmission accepted")

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
                    await msg.edit(content=f"Submission has not been accepted.")
                elif confirmed is None:
                    await msg.edit(
                        content=f"Submission timed out! Submission has not been accepted."
                    )

            # If there is already a personal best in DB
            elif (
                await WorldRecords.count_documents(
                    {"code": map_code, "level": level, "posted_by": ctx.author.id}
                )
                == 1
            ):
                submission = await WorldRecords.find_one(
                    {"code": map_code, "level": level, "posted_by": ctx.author.id}
                )
                # If new record is faster than old record
                if record_in_seconds < submission.record:
                    pt = prettytable.PrettyTable(
                        field_names=["Map Code", "Level", "Record", "Name"]
                    )
                    pt.add_row(
                        [
                            submission.code,
                            submission.level,
                            utilities.display_record(record_in_seconds),
                            submission.name,
                        ]
                    )
                    msg = await ctx.send("```\n" + ", ".join(level_checker) + "```\n" + f"```\nIs this correct?\n{pt}```")
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
                            await msg.edit(content=f"```\n{pt}```\nSubmission accepted")

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
                    WorldRecords.find({"code": map_code, "level": level})
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
        if (
            await WorldRecords.count_documents(
                {"code": map_code, "level": level, "name": name}
            )
            == 1
        ):
            search = await WorldRecords.find_one(
                {"code": map_code, "level": level, "name": name}
            )

            if search.posted_by == ctx.author.id or (
                True
                if any(role.id in constants.ROLE_WHITELIST for role in ctx.author.roles)
                else False
            ):
                pt = prettytable.PrettyTable()
                pt.field_names = ["Map Code", "Level", "Record", "Name", "Verified"]
                pt.add_row(
                    [
                        search.code,
                        search.level,
                        utilities.display_record(search.record),
                        search.name,
                        search.verified,
                    ]
                )
                msg = await ctx.send(f"```\nDo you want to delete this?\n{pt}```")
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
