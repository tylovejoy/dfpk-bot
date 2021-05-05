import re
import sys
from pymongo import ASCENDING, DESCENDING
import discord
from discord.ext import commands

import internal.constants as constants
from database.MapData import MapData
from internal.map_utils import searchmap, convert_short_types

if len(sys.argv) > 1:
    if sys.argv[1] == "test":
        from internal import constants_bot_test as constants_bot
else:
    from internal import constants_bot_prod as constants_bot


class MapSearchTypes(commands.Cog, name="Map Search"):
    """A collection of map search commands.

    Additional map searching commands.
    Examples:
        - Searches all maps with this map_type:
            - multimap
            - ablock
            - newest
            - megamap
            - etc.
    """

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        """Check if command is used in MAP_CHANNEL."""
        if ctx.channel.id == constants_bot.MAP_CHANNEL_ID or (ctx.guild is None):
            return True

    @commands.command(
        help="Displays all multilevel maps.",
        brief="Displays all multilevel maps.",
        aliases=["multi", "multilvl"],
    )
    async def multilevel(self, ctx):
        """Search for and display all multilevel maps."""
        map_name = "Multilevel"
        query = {"type": "MULTILEVEL"}
        await searchmap(ctx, query, map_name=map_name)

    @commands.command(
        help="Displays all single level maps.",
        brief="Displays all single level maps.",
    )
    async def single(self, ctx):
        """Search for and display all single maps."""
        map_name = "SINGLE"
        query = {"type": "SINGLE"}
        await searchmap(ctx, query, map_name=map_name)

    @commands.command(
        help="Displays all pioneer maps.",
        brief="Displays all pioneer maps.",
        aliases=["pio"],
    )
    async def pioneer(self, ctx):
        """Search for and display all pioneer maps."""
        map_name = "Pioneer"
        query = {"type": "PIONEER"}
        await searchmap(ctx, query, map_name=map_name)

    @commands.command(
        help="Displays all time attack maps.",
        brief="Displays all time attack maps.",
        aliases=["time-attack", "ta"],
    )
    async def timeattack(self, ctx):
        """Search for and display all time attack maps."""
        map_name = "Time Attack"
        query = {"type": "TIME-ATTACK"}
        await searchmap(ctx, query, map_name=map_name)

    @commands.command(
        help="Displays all tutorial maps.",
        brief="Displays all tutorial maps.",
        aliases=["tut"],
    )
    async def tutorial(self, ctx):
        """Search for and display all tutorial maps."""
        map_name = "Tutorial"
        query = {"type": "TUTORIAL"}
        await searchmap(ctx, query, map_name=map_name)

    @commands.command(
        help="Displays all hardcore maps.",
        brief="Displays all hardcore maps.",
        aliases=["hc"],
    )
    async def hardcore(self, ctx):
        """Search for and display all hardcore maps."""
        map_name = "Hardcore"
        query = {"type": "HARDCORE"}
        await searchmap(ctx, query, map_name=map_name)

    @commands.command(
        help="Displays all mildcore maps.",
        brief="Displays all mildcore maps.",
        aliases=["mc"],
    )
    async def mildcore(self, ctx):
        """Search for and display all mildcore maps."""
        map_name = "Mildcore"
        query = {"type": "MILDCORE"}
        await searchmap(ctx, query, map_name=map_name)

    @commands.command(
        help="Displays all out of map maps.",
        brief="Displays all out of map maps.",
        aliases=["oom", "out-of-map"],
    )
    async def outofmap(self, ctx):
        """Search for and display all out of map maps."""
        map_name = "Out of Map"
        query = {"type": "OUT-OF-MAP"}
        await searchmap(ctx, query, map_name=map_name)

    @commands.command(
        help="Displays all ability lock maps.",
        brief="Displays all ability lock maps.",
        aliases=["ablock", "ab"],
    )
    async def abilityblock(self, ctx):
        """Search for and display all ability block maps."""
        map_name = "Ability Block"
        query = {"type": "ABLOCK"}
        await searchmap(ctx, query, map_name=map_name)

    @commands.command(
        help="Displays all nostalgia maps.",
        brief="Displays all nostalgia maps.",
        aliases=["old"],
    )
    async def nostalgia(self, ctx):
        """Search for and display all nostalgia maps."""
        map_name = "Nostalgia"
        query = {"type": "NOSTALGIA"}
        await searchmap(ctx, query, map_name=map_name)

    @commands.command(
        help="Lists most recent submitted maps which are not labeled as NOSTALGIA.",
        brief="Lists most recent submitted maps",
        aliases=["new", "latest"],
    )
    async def newest(self, ctx, map_type=""):
        """Show newest maps.

        Display constants_bot.NEWEST_MAPS_LIMIT amount of maps that were submitted
        """
        embed = discord.Embed(title="Newest Maps")

        row = 0
        query = {}
        map_type = convert_short_types(map_type.upper())
        if map_type:
            if map_type not in constants.TYPES_OF_MAP:
                await ctx.send(
                    f"{map_type} not in map types. Use `/maptypes` for a list of acceptable map types."
                )
                return
            query = {"type": map_type}
        count = await MapData.count_documents(query)
        # async for entry in MapData.find(query).sort(
        #             [("_id", ASCENDING)]
        #         ).limit(
        #     constants.NEWEST_MAPS_LIMIT
        # ):
        async for entry in MapData.find(query).skip(
            (count - constants.NEWEST_MAPS_LIMIT)
            if count > constants.NEWEST_MAPS_LIMIT
            else 0
        ):
            embed.add_field(
                name=f"{entry.code} - {constants.PRETTY_NAMES[entry.map_name]}",
                value=f"> Creator: {entry.creator}\n> Map Types: {', '.join(entry.type)}\n> Description: {entry.desc}",
                inline=False,
            )
            row = 1
        if row:
            await ctx.send(embed=embed)
        else:
            await ctx.send("No latest maps!")

    @commands.command(
        help="Search for maps by a specific creator.\n<creator> is not case-sensitive and can contain a portion of a name.",
        brief="Search for maps by a specific creator",
    )
    async def creator(self, ctx, creator):
        """Search for and display maps by a certain creator."""
        query = {"creator": re.compile(re.escape(creator), re.IGNORECASE)}
        await searchmap(ctx, query, creator=creator.capitalize())

    @commands.command(
        help="Search for the creator/details of a map. Enter <map_code> to find the details of that code.",
        brief="Search for the creator/details of a map",
        aliases=["code"],
    )
    async def mapcode(self, ctx, map_code):
        """Search for and display a certain map code."""
        code = map_code.upper()
        query = {"code": code}
        embed = None
        async for entry in MapData.find(query):
            embed = discord.Embed()
            embed.add_field(
                name=f"{entry.code} - {constants.PRETTY_NAMES[entry.map_name]}",
                value=f"> Creator: {entry.creator}\n> Map Types: {', '.join(entry.type)}\n> Description: {entry.desc}",
                inline=False,
            )
        if embed:
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"{code} does not exist!")

    @commands.command(
        help="Display all frameworks",
        brief="Display all frameworks",
        aliases=["FW"],
    )
    async def framework(self, ctx):
        """Search for and display all frameworks."""
        map_name = "Frameworks"
        query = {"$or": [{"type": "FRAMEWORK"}, {"map_name": "FRAMEWORK"}]}
        await searchmap(ctx, query, map_name=map_name)

    @commands.command(
        help="Display all megamaps",
        brief="Display all megamaps",
    )
    async def megamap(self, ctx):
        """Search for and display all megamaps."""
        map_name = "Megamap"
        query = {"type": "MEGAMAP"}
        await searchmap(ctx, query, map_name=map_name)

    @commands.command(
        help="Display all multimaps",
        brief="Display all multimaps",
    )
    async def multimap(self, ctx):
        """Search for and display all multimaps."""
        map_name = "Multimap"
        query = {"type": "MULTIMAP"}
        await searchmap(ctx, query, map_name=map_name)


def setup(bot):
    """Add Cog to Discord bot."""
    bot.add_cog(MapSearchTypes(bot))
