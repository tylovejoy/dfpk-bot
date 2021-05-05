import logging
import re
import sys

import bson
import discord
import pymongo
from discord.ext import commands
from disputils import BotEmbedPaginator
from pymongo.collation import Collation

import internal.constants as constants
import internal.pb_utils
from database.MapData import MapData
from database.WorldRecords import WorldRecords
from internal.pb_utils import boards

if len(sys.argv) > 1:
    if sys.argv[1] == "test":
        from internal import constants_bot_test as constants_bot
else:
    from internal import constants_bot_prod as constants_bot


class ViewPersonalBest(commands.Cog, name="Personal bests and leaderboards"):
    """Commands to display personal records in different formats.
    World Records, Leaderboards, Scoreboards, etc.
    """

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        """Check if channel is RECORD_CHANNEL."""
        if ctx.channel.id == constants_bot.RECORD_CHANNEL_ID or (
            ctx.guild is None
        ):
            return True

    @commands.command(
        help="View personal best record for a particular map code.\n[name] is optional. Defaults to the user who used the command.\nUse [name] to find personal best of other users.",
        brief="View personal best record",
    )
    async def pb(self, ctx, name=None):
        """Display personal best of a particular user, or author of command."""

        # Query for own PBs (w/ no name arg) or another's PBs
        if name is None:
            query = {
                "$or": [
                    {"posted_by": bson.int64.Int64(ctx.author.id)},
                    {"name": ctx.author.name},
                ]
            }
        else:
            query = {"name": re.compile(re.escape(name), re.IGNORECASE)}

        embed_dict = {}
        cur_map = None
        async for entry in WorldRecords.find(query, {"_id": False, "url": False, "hidden_id": False, "message_id": False, "posted_by": False}).sort([("code", pymongo.ASCENDING), ("level", pymongo.ASCENDING)]):
            # Find if map_code for PB is in MapData to display map name and creator name.
            if entry.code != cur_map:
                cur_map = entry.code
                map_data_connection = await MapData.find_one(
                    {"code": entry.code},
                    {"_id": False, "code": True, "map_name": True, "creator": True},
                )
                if map_data_connection:
                    map_name = constants.PRETTY_NAMES[map_data_connection.map_name]
                    creator = map_data_connection.creator
                else:
                    map_name = "Needs Map"
                    creator = "Needs Author"

            # Create a dict of all the indivudal map_codes and the PBs for each map_code
            if embed_dict.get(str(entry.code), None) is None:
                embed_dict[str(entry.code)] = {
                    "title": f"{entry.code} - {map_name} by {creator}\n",
                    "value": ""
                }
            embed_dict[str(entry.code)]["value"] += f"> **Level: {entry.level}**\n> Record: {internal.pb_utils.display_record(entry.record)}\n> Verified: {constants.VERIFIED_EMOJI if entry.verified is True else constants.NOT_VERIFIED_EMOJI}\n━━━━━━━━━━━━\n"

        embeds = []
        embed = discord.Embed(title=name)

        if len(embed_dict) > 0:
            for i, map_pbs in enumerate(embed_dict.values()):
                if len(map_pbs["value"]) > 1024:
                    # if over 1024 char limit
                    # split pbs dict value into list of individual pbs
                    # and divide in half.. Add two fields instead of just one.
                    delimiter_regex = r">.*\n>.*\n>.*\n━━━━━━━━━━━━\n"
                    pb_split = re.findall(delimiter_regex, map_pbs["value"])
                    pb_split_1 = pb_split[:len(pb_split) // 2]
                    pb_split_2 = pb_split[len(pb_split) // 2:]
                    embed.add_field(name=f"{map_pbs['title']} (1)",
                                    value="".join(pb_split_1),
                                    inline=False)
                    embed.add_field(name=f"{map_pbs['title']} (2)",
                                    value="".join(pb_split_2),
                                    inline=False)
                else:
                    embed.add_field(name=map_pbs["title"], value=map_pbs["value"],
                                    inline=False)
                if (i + 1) % 3 == 0 or (i + 1) == len(embed_dict):
                    embeds.append(embed)
                    embed = discord.Embed(title=name)

        if embeds:
            paginator = BotEmbedPaginator(ctx, embeds)
            await paginator.run()
        else:
            await ctx.send(f"Nothing exists for {name}!")

    # view scoreboard
    @commands.command(
        help="View top 10 verified/unverified records for a particular level on a map.",
        brief="View top 10 verified/unverified records",
        aliases=["sb"],
    )
    async def scoreboard(self, ctx, map_code, *, level):
        """Display top 10 verified/unverified records for a particular level."""
        map_code = map_code.upper()
        title = f"{map_code} - LEVEL {level.upper()} - TOP 10 VERIFIED/UNVERIFIED RECORDS:\n"
        query = {
            "code": map_code,
            "level": re.compile(
                r"^" + re.escape(level) + r"$", re.IGNORECASE
            ),
        }
        await boards(ctx, map_code, level, title, query)

    # view leaderboard
    @commands.command(
        help="View top 10 verified records for a particular level on a map.",
        brief="View top 10 records",
        aliases=["lb"],
    )
    async def leaderboard(self, ctx, map_code, *, level):
        """Display top 10 verified records for a particular level."""
        map_code = map_code.upper()
        title = f"{map_code} - LEVEL {level.upper()} - TOP 10 VERIFIED RECORDS:\n"
        query = {
            "code": map_code,
            "level": re.compile(
                r"^" + re.escape(level) + r"$", re.IGNORECASE
            ),
            "verified": True,
        }
        await boards(ctx, map_code, level.upper(), title, query)

    @commands.command(
        help="View world record(s) for a particular map code.\n[level] is an optional argument that will display a single level's world record.\nIf [level] is included, command will show only that level's world record.",
        brief="View world record",
        aliases=["wr"],
    )
    async def worldrecord(self, ctx, map_code, level=""):
        """Display world record for a level on a particular map_code, or all levels."""
        map_code = map_code.upper()
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
            ):
                if entry.level.upper() not in level_checker.keys():
                    level_checker[entry.level.upper()] = None
                    exists = True
                    embed.add_field(
                        name=f"Level {entry.level.upper()} - {entry.name}",
                        value=f"> Record: {internal.pb_utils.display_record(entry.record)}\n",
                        inline=False,
                    )

        else:
            async for entry in (
                WorldRecords.find(
                    {
                        "code": map_code,
                        "level": re.compile(
                            r"^" + re.escape(level) + r"$", re.IGNORECASE
                        ),
                        "verified": True,
                    }
                )
                .sort("record", 1)
                .limit(1)
            ):
                title = f"{map_code} - LEVEL {entry.level.upper()} - VERIFIED WORLD RECORD:\n"
                exists = True
                embed = discord.Embed(title=f"{title}")
                embed.add_field(
                    name=f"{entry.name}",
                    value=f"> Record: {internal.pb_utils.display_record(entry.record)}\n",
                    inline=False,
                )
                url = entry.url
        if exists:
            await ctx.send(f"{url}", embed=embed)
        else:
            await ctx.send(
                f"No world record for {map_code}{' level ' + level.upper() if level else ''}!"
            )

    @commands.command(
        help="Lists level names that are currently associated with <map_code>.",
        brief="Lists level names that are currently associated with <map_code>",
        aliases=["levelnames"],
    )
    async def levels(self, ctx, map_code):
        """Display all levels associated with a particular map_code."""

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
            embed = discord.Embed(title=f"{title}")
            embed.add_field(
                name="Currenly submitted levels:", value=f"{', '.join(level_checker)}"
            )

            await ctx.send(embed=embed)

        else:
            await ctx.send(f"No level names found for {map_code}!")


def setup(bot):
    """Add Cog to Discord bot."""
    bot.add_cog(ViewPersonalBest(bot))
