import re
import sys

import discord
import prettytable
from discord.ext import commands
from pymongo.collation import Collation

from database.WorldRecords import WorldRecords
from internal import utilities

if len(sys.argv) > 1:
    if sys.argv[1] == "test":
        from internal import test_constants as constants
else:
    from internal import constants


async def boards(ctx, map_code, level, title, query):
    """
    Displays boards for scoreboard and leaderboard commands
    """
    count = 1
    exists = False
    embed = discord.Embed(title=f"{title}")
    async for entry in WorldRecords.find(query).sort("record", 1).limit(10):
        exists = True
        embed.add_field(
            name=f"#{count} - {entry.name}",
            value=(
                f"> Record: {utilities.display_record(entry.record)}\n"
                f"> Verified: {constants.VERIFIED_EMOJI if entry.verified is True else constants.NOT_VERIFIED_EMOJI}"
            ),
            inline=False,
        )
        count += 1
    if exists:
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"No scoreboard for {map_code} level {level.upper()}!")


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
        level = level.upper()
        query = {
            "code": map_code,
            "name": name,
            "level": re.compile(level, re.IGNORECASE),
        }
        if await WorldRecords.count_documents(query) == 1:
            search = await WorldRecords.find_one(query)
            embed = discord.Embed(title=f"Personal best for {search.name}")
            embed.add_field(
                name=f"{search.code} - Level {search.level.upper()}",
                value=(
                    f"> Record: {utilities.display_record(search.record)}\n"
                    f"> Verified: {constants.VERIFIED_EMOJI if search.verified is True else constants.NOT_VERIFIED_EMOJI}"
                ),
                inline=False,
            )
            await ctx.channel.send(f"{search.url}", embed=embed)
        else:
            await ctx.channel.send("Personal best doesn't exist.")

    # view scoreboard
    @commands.command(
        help="View top 10 verified/unverified records for a particular level on a map.",
        brief="View top 10 verified/unverified records",
        aliases=["sb"],
    )
    async def scoreboard(self, ctx, map_code, level):
        map_code = map_code.upper()
        title = f"{map_code} - LEVEL {level.upper()} - TOP 10 VERIFIED/UNVERIFIED RECORDS:\n"
        query = {"code": map_code, "level": re.compile(level, re.IGNORECASE)}
        await boards(ctx, map_code, level, title, query)

    # view leaderboard
    @commands.command(
        help="View top 10 verified records for a particular level on a map.",
        brief="View top 10 records",
        aliases=["lb"],
    )
    async def leaderboard(self, ctx, map_code, level):
        map_code = map_code.upper()
        title = f"{map_code} - LEVEL {level.upper()} - TOP 10 VERIFIED RECORDS:\n"
        query = {
            "code": map_code,
            "level": re.compile(level, re.IGNORECASE),
            "verified": True,
        }
        await boards(ctx, map_code, level.upper(), title, query)

    # view world record
    @commands.command(
        help="View world record(s) for a particular map code.\n[level] is an optional argument that will display a single level's world record.\nIf [level] is included, command will show only that level's world record.",
        brief="View world record",
        aliases=["wr"],
    )
    async def worldrecord(self, ctx, map_code, level=""):
        map_code = map_code.upper()
        pt = prettytable.PrettyTable()
        exists = False
        url = ""
        embed = None
        if level == "":
            title = f"{map_code} - VERIFIED WORLD RECORDS:\n"
            level_checker = {}
            embed = discord.Embed(title=f"{title}")
            async for entry in (
                WorldRecords.find({"code": map_code, "verified": True})
                .sort([("level", 1), ("record", 1)])
                .collation(Collation(locale="en_US", numericOrdering=True))
                .limit(25)
            ):
                if entry.level.upper() not in level_checker.keys():
                    level_checker[entry.level.upper()] = None
                    exists = True
                    embed.add_field(
                        name=f"Level {entry.level.upper()} - {entry.name}",
                        value=f"> Record: {utilities.display_record(entry.record)}\n",
                        inline=False,
                    )

        else:
            title = f"{map_code} - LEVEL {level.upper()} - VERIFIED WORLD RECORD:\n"
            async for entry in (
                WorldRecords.find(
                    {
                        "code": map_code,
                        "level": re.compile(level, re.IGNORECASE),
                        "verified": True,
                    }
                )
                .sort("record", 1)
                .limit(1)
            ):
                exists = True
                embed = discord.Embed(title=f"{title}")
                embed.add_field(
                    name=f"{entry.name}",
                    value=f"> Record: {utilities.display_record(entry.record)}\n",
                    inline=False,
                )
                url = entry.url
        if exists:
            await ctx.send(f"{url}", embed=embed)
        else:
            await ctx.send(
                f"No world record for {map_code}{' level ' + level.upper() if level else ''}!"
            )

    # view levels associated with PBs in a map code
    @commands.command(
        help="Lists level names that are currently associated with <map_code>.",
        brief="Lists level names that are currently associated with <map_code>",
        aliases=["levelnames"],
    )
    async def levels(self, ctx, map_code):
        map_code = map_code.upper()
        title = f"{map_code} - LEVEL NAMES:\n"
        level_checker = {}
        async for entry in (
            WorldRecords.find({"code": map_code})
            .sort([("level", 1)])
            .collation(Collation(locale="en_US", numericOrdering=True))
            .limit(30)
        ):
            if entry.level.upper() not in level_checker.keys():
                level_checker[entry.level.upper()] = None
        if level_checker:
            embed = discord.Embed(title=f"{map_code}")
            embed.add_field(
                name="Currenly submitted levels:", value=f"{', '.join(level_checker)}"
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"No level names found for {map_code}!")


def setup(bot):
    bot.add_cog(ViewPersonalBest(bot))
