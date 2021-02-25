import discord
from discord.ext import commands
import asyncio
import sys
from database.MapData import MapData
import re
import prettytable
from math import ceil
from textwrap import fill
from internal import utilities

if len(sys.argv) > 1:
    if sys.argv[1] == "test":
        from internal import test_constants as constants
else:
    from internal import constants


def normal_map_query(map_name, map_type=""):
    apostrophe = "'"
    if map_type:
        return {
            "map_name": f"{''.join(map_name.split()).lower().replace(apostrophe, '').replace(':', '')}",
            "type": map_type.upper(),
        }
    else:
        return {
            "map_name": f"{''.join(map_name.split()).lower().replace(apostrophe, '').replace(':', '')}"
        }


class MapSearch(commands.Cog, name="Map Search"):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        if ctx.channel.id == constants.MAP_CHANNEL_ID:
            return True

    async def searchmap(
        self, ctx, query: dict, map_type="", map_name="", creator="", map_code=""
    ):
        # Checks for map_type, if exists
        if map_type:
            if map_type not in constants.TYPES_OF_MAP:
                await ctx.send(
                    f"{map_type} not in map types. Use `/maptypes` for a list of acceptable map types."
                )
                return

        row, page, embeds = 0, 1, []

        embed = discord.Embed(
            title=map_name
            if map_name
            else creator
            if creator
            else map_code + f" Page {page}"
        )
        count = await MapData.count_documents(query)

        async for entry in MapData.find(query):

            if row != 0 and (row % 10 == 0 or count - 1 == row):
                embed.add_field(
                    name=f"{entry.code} - {constants.PRETTY_NAMES[entry.map_name]}",
                    value=f"> Creator: {entry.creator}\n> Map Types: {', '.join(entry.type)}\n> Description: {entry.desc}",
                    inline=False,
                )
                page += 1
                embeds.append(embed)
                embed = discord.Embed(
                    title=map_name
                    if map_name
                    else creator
                    if creator
                    else map_code + f" Page {page}"
                )

            elif row % 10 != 0 or row == 0:
                embed.add_field(
                    name=f"{entry.code} - {constants.PRETTY_NAMES[entry.map_name]}",
                    value=f"> Creator: {entry.creator}\n> Map Types: {', '.join(entry.type)}\n> Description: {entry.desc}",
                    inline=False,
                )

            if count == 1:
                embeds.append(embed)
            row += 1

        if row:
            await self.pages(
                ctx,
                contents=embeds,
                total_pages=len(embeds),
                map_name=map_name if map_name else creator if creator else map_code,
            )
        else:
            await ctx.send(
                f"Nothing exists for {map_name if map_name else creator if creator else map_code}!"
            )

    async def pages(self, ctx, contents, total_pages, map_name):
        cur_page = 1
        message = await ctx.send(embed=contents[cur_page - 1])
        # getting the message object for editing and reacting

        await message.add_reaction(constants.LEFT_REACTION_EMOJI)
        await message.add_reaction(constants.RIGHT_REACTION_EMOJI)

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in [
                constants.LEFT_REACTION_EMOJI,
                constants.RIGHT_REACTION_EMOJI,
            ]
            # This makes sure nobody except the command sender can interact with the "menu"

        while True:
            try:
                reaction, user = await self.bot.wait_for(
                    "reaction_add", timeout=60, check=check
                )
                # waiting for a reaction to be added - times out after x seconds, 60 in this
                # example

                if (
                    str(reaction.emoji) == constants.RIGHT_REACTION_EMOJI
                    and cur_page != total_pages
                ):
                    cur_page += 1
                    await message.edit(embed=contents[cur_page - 1])
                    await message.remove_reaction(reaction, user)

                elif (
                    str(reaction.emoji) == constants.LEFT_REACTION_EMOJI
                    and cur_page > 1
                ):
                    cur_page -= 1
                    await message.edit(embed=contents[cur_page - 1])
                    await message.remove_reaction(reaction, user)

                else:
                    if cur_page == total_pages:
                        cur_page = 1
                        await message.edit(embed=contents[cur_page - 1])
                        await message.remove_reaction(reaction, user)
                    elif cur_page == 1:
                        cur_page = total_pages
                        await message.edit(embed=contents[cur_page - 1])
                        await message.remove_reaction(reaction, user)

            except asyncio.TimeoutError:
                await message.clear_reactions()
                break
                # ending the loop if user doesn't react after x seconds

    """
    Newest maps
    """

    @commands.command(
        help="Lists most recent submitted maps which are not labeled as NOSTALGIA.",
        brief="Lists most recent submitted maps",
        aliases=["new", "latest"],
    )
    async def newest(self, ctx):
        embed = discord.Embed(title="Newest Maps")

        count = await MapData.count_documents()
        row = 0
        async for entry in MapData.find({"map_type": {"$nin": ["NOSTALGIA"]}}).skip(
            count - constants.NEWEST_MAPS_LIMIT
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
            await ctx.send(f"No latest maps!")

    """
    Creator search
    """

    @commands.command(
        help="Search for maps by a specific creator.\n<creator> is not case-sensitive and can contain a portion of a name.",
        brief="Search for maps by a specific creator",
    )
    async def creator(self, ctx, creator):
        query = {"creator": re.compile(creator, re.IGNORECASE)}
        await self.searchmap(ctx, query, creator=creator.capitalize())

    """
    Reverse map search
    """

    @commands.command(
        help="Search for the creator/details of a map. Enter <map_code> to find the details of that code.",
        brief="Search for the creator/details of a map",
        aliases=["code"],
    )
    async def mapcode(self, ctx, map_code):
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

    """
    Megamap / Multimaps
    """

    @commands.command(
        help="Display all megamaps",
        brief="Display all megamaps",
    )
    async def megamap(self, ctx):
        map_name = "Megamap"
        query = {"type": "MEGAMAP"}
        await self.searchmap(ctx, query, map_name=map_name)

    @commands.command(
        help="Display all multimaps",
        brief="Display all multimaps",
    )
    async def multimap(self, ctx):
        map_name = "Multimap"
        query = {"type": "MULTIMAP"}
        await self.searchmap(ctx, query, map_name=map_name)

    """
    Normal Maps
    """

    @commands.command(
        aliases=constants.AYUTTHAYA[1:],
        help="Display all Ayutthaya maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Ayutthaya maps.",
        hidden=True,
    )
    async def ayutthaya(self, ctx, map_type=""):
        map_name = "Ayutthaya"
        map_type = utilities.convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await self.searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.BLACKFOREST[1:],
        help="Display all Black Forest maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Black Forest maps.",
        hidden=True,
    )
    async def blackforest(self, ctx, map_type=""):
        map_name = "Black Forest"
        map_type = utilities.convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await self.searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.BLIZZARDWORLD[1:],
        help="Display all Blizzard World maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Blizzard World maps.",
        hidden=True,
    )
    async def blizzardworld(self, ctx, map_type=""):
        map_name = "Blizzard World"
        map_type = utilities.convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await self.searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.BUSAN[1:],
        help="Display all Busan maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Busan maps.",
        hidden=True,
    )
    async def busan(self, ctx, map_type=""):
        map_name = "Busan"
        map_type = utilities.convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await self.searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.CASTILLO[1:],
        help="Display all Castillo maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Castillo maps.",
        hidden=True,
    )
    async def castillo(self, ctx, map_type=""):
        map_name = "Castillo"
        map_type = utilities.convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await self.searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.CHATEAUGUILLARD[1:],
        help="Display all Chateau Guillard maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Chateau Guillard maps.",
        hidden=True,
    )
    async def chateauguillard(self, ctx, map_type=""):
        map_name = "Chateau Guillard"
        map_type = utilities.convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await self.searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.DORADO[1:],
        help="Display all Dorado maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Dorado maps.",
        hidden=True,
    )
    async def dorado(self, ctx, map_type=""):
        map_name = "Dorado"
        map_type = utilities.convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await self.searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.EICHENWALDE[1:],
        help="Display all Eichenwalde maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Eichenwalde maps.",
        hidden=True,
    )
    async def eichenwalde(self, ctx, map_type=""):
        map_name = "Eichenwalde"
        map_type = utilities.convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await self.searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.HANAMURA[1:],
        help="Display all Hanamura maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Hanamura maps.",
        hidden=True,
    )
    async def hanamura(self, ctx, map_type=""):
        map_name = "Hanamura"
        map_type = utilities.convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await self.searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.HAVANA[1:],
        help="Display all Havana maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Havana maps.",
        hidden=True,
    )
    async def havana(self, ctx, map_type=""):
        map_name = "Havana"
        map_type = utilities.convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await self.searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.HOLLYWOOD[1:],
        help="Display all Hollywood maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Hollywood maps.",
        hidden=True,
    )
    async def hollywood(self, ctx, map_type=""):
        map_name = "Hollywood"
        map_type = utilities.convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await self.searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.HORIZONLUNARCOLONY[1:],
        help="Display all Horizon Lunar Colony maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Horizon Lunar Colony maps.",
        hidden=True,
    )
    async def horizonlunarcolony(self, ctx, map_type=""):
        map_name = "Horizon Lunar Colony"
        map_type = utilities.convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await self.searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.ILIOS[1:],
        help="Display all Ilios maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Ilios maps.",
        hidden=True,
    )
    async def ilios(self, ctx, map_type=""):
        map_name = "Ilios"
        map_type = utilities.convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await self.searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.JUNKERTOWN[1:],
        help="Display all Junkertown maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Junkertown maps.",
        hidden=True,
    )
    async def junkertown(self, ctx, map_type=""):
        map_name = "Junkertown"
        map_type = utilities.convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await self.searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.LIJIANGTOWER[1:],
        help="Display all Lijiang Tower maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Lijiang Tower maps.",
        hidden=True,
    )
    async def lijiangtower(self, ctx, map_type=""):
        map_name = "Lijiang Tower"
        map_type = utilities.convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await self.searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.NECROPOLIS[1:],
        help="Display all Necropolis maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Necropolis maps.",
        hidden=True,
    )
    async def necropolis(self, ctx, map_type=""):
        map_name = "Necropolis"
        map_type = utilities.convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await self.searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.NEPAL[1:],
        help="Display all Nepal maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Nepal maps.",
        hidden=True,
    )
    async def nepal(self, ctx, map_type=""):
        map_name = "Nepal"
        map_type = utilities.convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await self.searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.NUMBANI[1:],
        help="Display all Numbani maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Numbani maps.",
        hidden=True,
    )
    async def numbani(self, ctx, map_type=""):
        map_name = "Numbani"
        map_type = utilities.convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await self.searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.OASIS[1:],
        help="Display all Oasis maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Oasis maps.",
        hidden=True,
    )
    async def oasis(self, ctx, map_type=""):
        map_name = "Oasis"
        map_type = utilities.convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await self.searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.PARIS[1:],
        help="Display all Paris maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Paris maps.",
        hidden=True,
    )
    async def paris(self, ctx, map_type=""):
        map_name = "Paris"
        map_type = utilities.convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await self.searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.RIALTO[1:],
        help="Display all Rialto maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Rialto maps.",
        hidden=True,
    )
    async def rialto(self, ctx, map_type=""):
        map_name = "Rialto"
        map_type = utilities.convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await self.searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.ROUTE66[1:],
        help="Display all Route 66 maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Route 66 maps.",
        hidden=True,
    )
    async def route66(self, ctx, map_type=""):
        map_name = "Route 66"
        map_type = utilities.convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await self.searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.TEMPLEOFANUBIS[1:],
        help="Display all Temple of Anubis maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Temple of Anubis maps.",
        hidden=True,
    )
    async def templeofanubis(self, ctx, map_type=""):
        map_name = "Temple of Anubis"
        map_type = utilities.convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await self.searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.VOLSKAYAINDUSTRIES[1:],
        help="Display all Volskaya Industries maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Volskaya Industries maps.",
        hidden=True,
    )
    async def volskayaindustries(self, ctx, map_type=""):
        map_name = "Volskaya Industries"
        map_type = utilities.convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await self.searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.WATCHPOINTGIBRALTAR[1:],
        help="Display all Watchpoint Gibraltar maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Watchpoint Gibraltar maps.",
        hidden=True,
    )
    async def watchpointgibraltar(self, ctx, map_type=""):
        map_name = "Watchpoint Gibraltar"
        map_type = utilities.convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await self.searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.KINGSROW[1:],
        help="Display all King's Row maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all King's Row maps.",
        hidden=True,
    )
    async def kingsrow(self, ctx, map_type=""):
        map_name = "King's Row"
        map_type = utilities.convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await self.searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.PETRA[1:],
        help="Display all Petra maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Petra maps.",
        hidden=True,
    )
    async def petra(self, ctx, map_type=""):
        map_name = "Petra"
        map_type = utilities.convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await self.searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.ECOPOINTANTARCTICA[1:],
        help="Display all Ecopoint Antarctica maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Ecopoint Antarctica maps.",
        hidden=True,
    )
    async def ecopointantarctica(self, ctx, map_type=""):
        map_name = "Ecopoint Antarctica"
        map_type = utilities.convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await self.searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.KANEZAKA[1:],
        help="Display all Kanezaka maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Kanezaka maps.",
        hidden=True,
    )
    async def kanezaka(self, ctx, map_type=""):
        map_name = "Kanezaka"
        map_type = utilities.convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await self.searchmap(ctx, query, map_type=map_type, map_name=map_name)

    """
    Workshop maps / Practice Range 
    """

    @commands.command(
        aliases=constants.WORKSHOPCHAMBER[1:],
        help="Display all Workshop Chamber maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Workshop Chamber maps.",
        hidden=True,
    )
    async def workshopchamber(self, ctx, map_type=""):
        map_name = "Workshop Chamber"
        map_type = utilities.convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await self.searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.WORKSHOPEXPANSE[1:],
        help="Display all Workshop Expanse maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Workshop Expanse maps.",
        hidden=True,
    )
    async def workshopexpanse(self, ctx, map_type=""):
        map_name = "Workshop Expanse"
        map_type = utilities.convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await self.searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.WORKSHOPGREENSCREEN[1:],
        help="Display all Workshop Greenscreen maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Workshop Greenscreen maps.",
        hidden=True,
    )
    async def workshopgreenscreen(self, ctx, map_type=""):
        map_name = "Workshop Greenscreen"
        map_type = utilities.convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await self.searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.WORKSHOPISLAND[1:],
        help="Display all Workshop Island maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Workshop Island maps.",
        hidden=True,
    )
    async def workshopisland(self, ctx, map_type=""):
        map_name = "Workshop Island"
        map_type = utilities.convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await self.searchmap(ctx, query, map_type=map_type, map_name=map_name)

    @commands.command(
        aliases=constants.PRACTICERANGE[1:],
        help="Display all Practice Range maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Practice Range maps.",
        hidden=True,
    )
    async def practicerange(self, ctx, map_type=""):
        map_name = "Practice Range"
        map_type = utilities.convert_short_types(map_type.upper())
        query = normal_map_query(map_name, map_type)
        await self.searchmap(ctx, query, map_type=map_type, map_name=map_name)


def setup(bot):
    bot.add_cog(MapSearch(bot))
