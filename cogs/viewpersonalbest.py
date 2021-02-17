import discord
from discord.ext import commands
import asyncio
from internal import constants, utilities, confirmation
from database.WorldRecords import WorldRecords
from mongosanitizer.sanitizer import sanitize
import prettytable
import datetime
import logging


class ViewPersonalBest(commands.Cog, name="Personal bests and leaderboards"):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        if ctx.channel.id == constants.RECORD_CHANNEL_ID:
            return True

    @commands.command(
        help="View personal best record for a particular map code.\n[name] is optional. Defaults to the user who used the command.\nUse [name] to find personal best of other users.",
        brief="View personal best record",
    )
    async def pb(self, ctx, map_code, level, name=""):
        if name == "":
            name = ctx.author.name
        map_code = map_code.upper()
        if await WorldRecords.count_documents({"code": map_code, "name": name, "level": level}) == 1:
            search = await WorldRecords.find_one({"code": map_code, "name": name, "level": level})
            pt = prettytable.PrettyTable(field_names=["Level", "Record", "Name", "Verified"])
            pt.add_row([search.level, utilities.display_record(search.record), search.name, constants.VERIFIED_EMOJI if search.verified is True else constants.NOT_VERIFIED_EMOJI])
            await ctx.channel.send(
                f"```\n{pt}```\n{search.url}"  # noqa: E501
            )
        else:
            await ctx.channel.send("Personal best doesn't exist.")

    # view scoreboard
    @commands.command(
        help=("View top 10 verified/unverified records for a particular level on a map. "
              "Links to original posts are included"),
        brief="View top 10 verified/unverified records",
        aliases=["sb"],
    )
    async def scoreboard(self, ctx, map_code, level):
        map_code = map_code.upper()
        title = f"CODE: {map_code} LEVEL {level} - TOP 10 VERIFIED/UNVERIFIED RECORDS:\n"
        count = 1
        post = 0
        pt = prettytable.PrettyTable()
        pt.field_names = ["Position", "Record", "Name", "Verified"]

        async for entry in (WorldRecords.find({"code": map_code, "level": level})).sort("record", 1).limit(10):
            post = 1
            pt.add_row([count, utilities.display_record(entry.record), entry.name, constants.VERIFIED_EMOJI if entry.verified is True else constants.NOT_VERIFIED_EMOJI])
            count += 1
        if post:
            await ctx.send(f"{title}```\n{pt}```")
        else:
            await ctx.send(f"No scoreboard for {map_code} level {level}!")

    # view leaderboard
    @commands.command(
        help=("View top 10 verified records for a particular level on a map. "
              "Links to original posts are included"),
        brief="View top 10 records",
        aliases=["lb"],
    )
    async def leaderboard(self, ctx, map_code, level):
        map_code = map_code.upper()
        title = f"CODE: {map_code} LEVEL {level} - TOP 10 VERIFIED RECORDS:\n"
        post = 0
        count = 1
        pt = prettytable.PrettyTable()
        pt.field_names = ["Position", "Record", "Name", "Verified"]
        async for entry in (
            WorldRecords.find({"code": map_code, "level": level, "verified": True})
            .sort("record", 1)
            .limit(10)
        ):
            post = 1
            pt.add_row([count, utilities.display_record(entry.record), entry.name, constants.VERIFIED_EMOJI if entry.verified is True else constants.NOT_VERIFIED_EMOJI])
            count += 1
        if post:
            await ctx.send(f"{title}```\n{pt}```")
        else:
            await ctx.send(f"No leaderboard for {map_code} level {level}!")

    # view world record
    @commands.command(
        help="View world record(s) for a particular map code.\n[level] is an optional argument that will display a single level's world record.\nIf [level] is included, command will show only that level's world record.",
        brief="View world record",
        aliases=["wr"]
    )
    async def worldrecord(self, ctx, map_code, level=""):
        map_code = map_code.upper()
        pt = prettytable.PrettyTable()
        post = 0
        url = ''
        if level == "":
            title = f"CODE: {map_code} - VERIFIED WORLD RECORDS:\n"
            level_checker = set()
            pt.field_names = ["Level", "Record", "Name", "Verified"]
            async for entry in (
                WorldRecords.find({"code": map_code, "verified": True})
                .sort("record", 1)
                .limit(20)
            ):
                if entry.level not in level_checker:
                    post = 1
                    level_checker.add(entry.level)
                    pt.add_row([entry.level, utilities.display_record(entry.record), entry.name, constants.VERIFIED_EMOJI if entry.verified is True else constants.NOT_VERIFIED_EMOJI])
        else:
            title = f"CODE: {map_code} LEVEL {level} - VERIFIED WORLD RECORD:\n"
            async for entry in (
                WorldRecords.find({"code": map_code, "level": level, "verified": True})
                .sort("record", 1)
                .limit(1)
            ):
                post = 1
                pt.field_names = ["Record", "Name", "Verified"]
                pt.add_row([utilities.display_record(entry.record), entry.name, constants.VERIFIED_EMOJI if entry.verified is True else constants.NOT_VERIFIED_EMOJI])
                url = entry.url
        if post:
            await ctx.send(f"{title}```\n{pt}```\n{url}")
        else:
            await ctx.send(f"No world record for {map_code}{' level ' + level if level else ''}!")





def setup(bot):
    bot.add_cog(ViewPersonalBest(bot))
