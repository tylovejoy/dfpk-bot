import discord
from discord.ext import commands
import asyncio
from internal import constants, utilities
from database.MapData import MapData
import re
import prettytable
from math import ceil
from textwrap import fill, wrap


class MapSearch(commands.Cog, name="Map Search"):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        if ctx.channel.id == constants.MAP_CHANNEL_ID:
            return True

    #@commands.command(hidden=True)
    async def pages(self, ctx, contents, total_pages, map_name):
        cur_page = 1
        message = await ctx.send(
            f"{map_name}\n```Page {cur_page}/{total_pages}:\n{contents[cur_page - 1]}```"
        )
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
                    await message.edit(
                        content=f"{map_name}\n```Page {cur_page}/{total_pages}:\n{contents[cur_page - 1]}```"
                    )
                    await message.remove_reaction(reaction, user)

                elif (
                    str(reaction.emoji) == constants.LEFT_REACTION_EMOJI
                    and cur_page > 1
                ):
                    cur_page -= 1
                    await message.edit(
                        content=f"{map_name}\n```Page {cur_page}/{total_pages}:\n{contents[cur_page - 1]}```"
                    )
                    await message.remove_reaction(reaction, user)

                else:
                    if cur_page == total_pages:
                        cur_page = 1
                        await message.edit(
                            content=f"{map_name}\n```Page {cur_page}/{total_pages}:\n{contents[cur_page - 1]}```"
                        )
                        await message.remove_reaction(reaction, user)
                    elif cur_page == 1:
                        cur_page = total_pages
                        await message.edit(
                            content=f"{map_name}\n```Page {cur_page}/{total_pages}:\n{contents[cur_page - 1]}```"
                        )
                        await message.remove_reaction(reaction, user)

            except asyncio.TimeoutError:
                await message.clear_reactions()
                break
                # ending the loop if user doesn't react after x seconds

    """
    Newest maps
    """
    @commands.command(
        help="Lists most recent submitted maps",
        brief="",
        aliases=["new", "latest"]
    )
    async def newest(self, ctx):
        row = 0
        pt = prettytable.PrettyTable(
            field_names=["Map Code", "Map Type", "Map Name", "Description", "Creator"]
        )
        count = await MapData.count_documents()
        async for entry in MapData.find(
                {"map_type": {"$nin": ["NOSTALGIA"]}}
        ).skip(count - constants.NEWEST_MAPS_LIMIT):
            pt.add_row(
                [
                    entry.code,
                    fill(" ".join(entry.type), constants.TYPE_MAX_LENGTH),
                    constants.PRETTY_NAMES[entry.map_name],
                    fill(entry.desc, constants.DESC_MAX_LENGTH),
                    fill(entry.creator, constants.CREATOR_MAX_LENGTH),
                ]
            )
            row += 1
        if row:
            if ceil(row / constants.PT_PAGE_SIZE) != 1:
                s, e, split_pt = 0, constants.PT_PAGE_SIZE - 1, []
                while s < row:
                    split_pt.append(pt.get_string(start=s, end=e))
                    s += constants.PT_PAGE_SIZE
                    e += constants.PT_PAGE_SIZE
                await self.pages(
                    ctx,
                    split_pt,
                    ceil(row / constants.PT_PAGE_SIZE),
                    "Latest Maps",
                )
            else:
                await ctx.send(f"Latest Maps```Page 1/1:\n{pt}```")
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
        row = 0
        pt = prettytable.PrettyTable(
            field_names=["Map Code", "Map Type", "Map Name", "Description", "Creator"]
        )
        async for entry in MapData.find(
            {"creator": re.compile(creator, re.IGNORECASE)}
        ):
            pt.add_row(
                [
                    entry.code,
                    fill(" ".join(entry.type), constants.TYPE_MAX_LENGTH),
                    constants.PRETTY_NAMES[entry.map_name],
                    fill(entry.desc, constants.DESC_MAX_LENGTH),
                    fill(entry.creator, constants.CREATOR_MAX_LENGTH),
                ]
            )
            row += 1
        if row:
            if ceil(row / constants.PT_PAGE_SIZE) != 1:
                s, e, split_pt = 0, constants.PT_PAGE_SIZE - 1, []
                while s < row:
                    split_pt.append(pt.get_string(start=s, end=e))
                    s += constants.PT_PAGE_SIZE
                    e += constants.PT_PAGE_SIZE
                await self.pages(
                    ctx,
                    split_pt,
                    ceil(row / constants.PT_PAGE_SIZE),
                    creator.capitalize(),
                )
            else:
                await ctx.send(f"{creator.capitalize()}```Page 1/1:\n{pt}```")
        else:
            await ctx.send(f"No maps from {creator.capitalize()}!")

    """
    Reverse map search
    """

    @commands.command(
        help="Search for the creator/details of a map. Enter <map_code> to find the details of that code.",
        brief="Search for the creator/details of a map",
    )
    async def mapcode(self, ctx, map_code):
        row = 0
        pt = prettytable.PrettyTable(
            field_names=["Map Code", "Map Type", "Map Name", "Description", "Creator"]
        )
        async for entry in MapData.find({"_id": map_code.upper()}):
            pt.add_row(
                [
                    entry.code,
                    fill(" ".join(entry.type), constants.TYPE_MAX_LENGTH),
                    constants.PRETTY_NAMES[entry.map_name],
                    fill(entry.desc, constants.DESC_MAX_LENGTH),
                    fill(entry.creator, constants.CREATOR_MAX_LENGTH),
                ]
            )
            row = 1
        if row:
            await ctx.send(f"```\n{pt}```")
        else:
            await ctx.send(f"No maps {map_code.upper()}!")

    """
    Megamap / Multimaps
    """

    @commands.command(
        help="Display all megamaps",
        brief="Display all megamaps",
    )
    async def megamap(self, ctx):
        map_name = "Megamap"
        row = 0
        pt = prettytable.PrettyTable(
            field_names=["Map Code", "Map Name", "Description", "Creator"]
        )
        async for entry in MapData.find({"type": "MEGAMAP"}):
            pt.add_row(
                [
                    entry.code,
                    constants.PRETTY_NAMES[entry.map_name],
                    fill(entry.desc, constants.DESC_MAX_LENGTH),
                    fill(entry.creator, constants.CREATOR_MAX_LENGTH),
                ]
            )
            row += 1
        if row:
            if ceil(row / constants.PT_PAGE_SIZE) != 1:
                s, e, split_pt = 0, constants.PT_PAGE_SIZE - 1, []
                while s < row:
                    split_pt.append(pt.get_string(start=s, end=e))
                    s += constants.PT_PAGE_SIZE
                    e += constants.PT_PAGE_SIZE
                await self.pages(
                    ctx, split_pt, ceil(row / constants.PT_PAGE_SIZE), map_name
                )
            else:
                await ctx.send(f"{map_name}```Page 1/1:\n{pt}```")
        else:
            await ctx.send(f"No {map_name}s!")

    @commands.command(
        help="Display all multimaps",
        brief="Display all multimaps",
    )
    async def multimap(self, ctx):
        map_name = "Multimap"
        row = 0
        pt = prettytable.PrettyTable(
            field_names=["Map Code", "Map Name", "Description", "Creator"]
        )
        async for entry in MapData.find({"type": "MULTIMAP"}):
            pt.add_row(
                [
                    entry.code,
                    constants.PRETTY_NAMES[entry.map_name],
                    fill(entry.desc, constants.DESC_MAX_LENGTH),
                    fill(entry.creator, constants.CREATOR_MAX_LENGTH),
                ]
            )
            row += 1
        if row:
            if ceil(row / constants.PT_PAGE_SIZE) != 1:
                s, e, split_pt = 0, constants.PT_PAGE_SIZE - 1, []
                while s < row:
                    split_pt.append(pt.get_string(start=s, end=e))
                    s += constants.PT_PAGE_SIZE
                    e += constants.PT_PAGE_SIZE
                await self.pages(
                    ctx, split_pt, ceil(row / constants.PT_PAGE_SIZE), map_name
                )
            else:
                await ctx.send(f"{map_name}```Page 1/1:\n{pt}```")
        else:
            await ctx.send(f"No {map_name}s!")

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
        if map_type:
            map_type = map_type.upper()
            if map_type not in constants.TYPES_OF_MAP:
                await ctx.send(
                    f"{map_type} not in map types. Use `/maptypes` for a list of acceptable map types."
                )
                return
        row = 0
        pt = prettytable.PrettyTable(
            field_names=["Map Code", "Map Type", "Description", "Creator"]
        )
        async for entry in MapData.find(
            {"map_name": f"{''.join(map_name.split()).lower()}", "type": map_type}
            if map_type
            else {"map_name": f"{''.join(map_name.split()).lower()}"}
        ):
            pt.add_row(
                [
                    entry.code,
                    fill(" ".join(entry.type), constants.TYPE_MAX_LENGTH),
                    fill(entry.desc, constants.DESC_MAX_LENGTH),
                    fill(entry.creator, constants.CREATOR_MAX_LENGTH),
                ]
            )
            row += 1
        if row:
            if ceil(row / constants.PT_PAGE_SIZE) != 1:
                s, e, split_pt = 0, constants.PT_PAGE_SIZE - 1, []
                while s < row:
                    split_pt.append(pt.get_string(start=s, end=e))
                    s += constants.PT_PAGE_SIZE
                    e += constants.PT_PAGE_SIZE
                await self.pages(
                    ctx, split_pt, ceil(row / constants.PT_PAGE_SIZE), map_name
                )
            else:
                await ctx.send(f"{map_name}\n```Page 1/1:\n{pt}```")
        else:
            await ctx.send(f"No codes for {map_name}!")

    @commands.command(
        aliases=constants.BLACKFOREST[1:],
        help="Display all Black Forest maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Black Forest maps.",
        hidden=True,
    )
    async def blackforest(self, ctx, map_type=""):
        map_name = "Black Forest"
        if map_type:
            map_type = map_type.upper()
            if map_type not in constants.TYPES_OF_MAP:
                await ctx.send(
                    f"{map_type} not in map types. Use `/maptypes` for a list of acceptable map types."
                )
                return
        row = 0
        pt = prettytable.PrettyTable(
            field_names=["Map Code", "Map Type", "Description", "Creator"]
        )
        async for entry in MapData.find(
            {"map_name": f"{''.join(map_name.split()).lower()}", "type": map_type}
            if map_type
            else {"map_name": f"{''.join(map_name.split()).lower()}"}
        ):
            pt.add_row(
                [
                    entry.code,
                    fill(" ".join(entry.type), constants.TYPE_MAX_LENGTH),
                    fill(entry.desc, constants.DESC_MAX_LENGTH),
                    fill(entry.creator, constants.CREATOR_MAX_LENGTH),
                ]
            )
            row += 1
        if row:
            if ceil(row / constants.PT_PAGE_SIZE) != 1:
                s, e, split_pt = 0, constants.PT_PAGE_SIZE - 1, []
                while s < row:
                    split_pt.append(pt.get_string(start=s, end=e))
                    s += constants.PT_PAGE_SIZE
                    e += constants.PT_PAGE_SIZE
                await self.pages(
                    ctx, split_pt, ceil(row / constants.PT_PAGE_SIZE), map_name
                )
            else:
                await ctx.send(f"{map_name}\n```Page 1/1:\n{pt}```")
        else:
            await ctx.send(f"No codes for {map_name}!")

    @commands.command(
        aliases=constants.BLIZZARDWORLD[1:],
        help="Display all Blizzard World maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Blizzard World maps.",
        hidden=True,
    )
    async def blizzardworld(self, ctx, map_type=""):
        map_name = "Blizzard World"
        if map_type:
            map_type = map_type.upper()
            if map_type not in constants.TYPES_OF_MAP:
                await ctx.send(
                    f"{map_type} not in map types. Use `/maptypes` for a list of acceptable map types."
                )
                return
        row = 0
        pt = prettytable.PrettyTable(
            field_names=["Map Code", "Map Type", "Description", "Creator"]
        )
        async for entry in MapData.find(
            {"map_name": f"{''.join(map_name.split()).lower()}", "type": map_type}
            if map_type
            else {"map_name": f"{''.join(map_name.split()).lower()}"}
        ):
            pt.add_row(
                [
                    entry.code,
                    fill(" ".join(entry.type), constants.TYPE_MAX_LENGTH),
                    fill(entry.desc, constants.DESC_MAX_LENGTH),
                    fill(entry.creator, constants.CREATOR_MAX_LENGTH),
                ]
            )
            row += 1
        if row:
            if ceil(row / constants.PT_PAGE_SIZE) != 1:
                s, e, split_pt = 0, constants.PT_PAGE_SIZE - 1, []
                while s < row:
                    split_pt.append(pt.get_string(start=s, end=e))
                    s += constants.PT_PAGE_SIZE
                    e += constants.PT_PAGE_SIZE
                await self.pages(
                    ctx, split_pt, ceil(row / constants.PT_PAGE_SIZE), map_name
                )
            else:
                await ctx.send(f"{map_name}\n```Page 1/1:\n{pt}```")
        else:
            await ctx.send(f"No codes for {map_name}!")

    @commands.command(
        aliases=constants.BUSAN[1:],
        help="Display all Busan maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Busan maps.",
        hidden=True,
    )
    async def busan(self, ctx, map_type=""):
        map_name = "Busan"
        if map_type:
            map_type = map_type.upper()
            if map_type not in constants.TYPES_OF_MAP:
                await ctx.send(
                    f"{map_type} not in map types. Use `/maptypes` for a list of acceptable map types."
                )
                return
        row = 0
        pt = prettytable.PrettyTable(
            field_names=["Map Code", "Map Type", "Description", "Creator"]
        )
        async for entry in MapData.find(
            {"map_name": f"{''.join(map_name.split()).lower()}", "type": map_type}
            if map_type
            else {"map_name": f"{''.join(map_name.split()).lower()}"}
        ):
            pt.add_row(
                [
                    entry.code,
                    fill(" ".join(entry.type), constants.TYPE_MAX_LENGTH),
                    fill(entry.desc, constants.DESC_MAX_LENGTH),
                    fill(entry.creator, constants.CREATOR_MAX_LENGTH),
                ]
            )
            row += 1
        if row:
            if ceil(row / constants.PT_PAGE_SIZE) != 1:
                s, e, split_pt = 0, constants.PT_PAGE_SIZE - 1, []
                while s < row:
                    split_pt.append(pt.get_string(start=s, end=e))
                    s += constants.PT_PAGE_SIZE
                    e += constants.PT_PAGE_SIZE
                await self.pages(
                    ctx, split_pt, ceil(row / constants.PT_PAGE_SIZE), map_name
                )
            else:
                await ctx.send(f"{map_name}\n```Page 1/1:\n{pt}```")
        else:
            await ctx.send(f"No codes for {map_name}!")

    @commands.command(
        aliases=constants.CASTILLO[1:],
        help="Display all Castillo maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Castillo maps.",
        hidden=True,
    )
    async def castillo(self, ctx, map_type=""):
        map_name = "Castillo"
        if map_type:
            map_type = map_type.upper()
            if map_type not in constants.TYPES_OF_MAP:
                await ctx.send(
                    f"{map_type} not in map types. Use `/maptypes` for a list of acceptable map types."
                )
                return
        row = 0
        pt = prettytable.PrettyTable(
            field_names=["Map Code", "Map Type", "Description", "Creator"]
        )
        async for entry in MapData.find(
            {"map_name": f"{''.join(map_name.split()).lower()}", "type": map_type}
            if map_type
            else {"map_name": f"{''.join(map_name.split()).lower()}"}
        ):
            pt.add_row(
                [
                    entry.code,
                    fill(" ".join(entry.type), constants.TYPE_MAX_LENGTH),
                    fill(entry.desc, constants.DESC_MAX_LENGTH),
                    fill(entry.creator, constants.CREATOR_MAX_LENGTH),
                ]
            )
            row += 1
        if row:
            if ceil(row / constants.PT_PAGE_SIZE) != 1:
                s, e, split_pt = 0, constants.PT_PAGE_SIZE - 1, []
                while s < row:
                    split_pt.append(pt.get_string(start=s, end=e))
                    s += constants.PT_PAGE_SIZE
                    e += constants.PT_PAGE_SIZE
                await self.pages(
                    ctx, split_pt, ceil(row / constants.PT_PAGE_SIZE), map_name
                )
            else:
                await ctx.send(f"{map_name}\n```Page 1/1:\n{pt}```")
        else:
            await ctx.send(f"No codes for {map_name}!")

    @commands.command(
        aliases=constants.CHATEAUGUILLARD[1:],
        help="Display all Chateau Guillard maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Chateau Guillard maps.",
        hidden=True,
    )
    async def chateauguillard(self, ctx, map_type=""):
        map_name = "Chateau Guillard"
        if map_type:
            map_type = map_type.upper()
            if map_type not in constants.TYPES_OF_MAP:
                await ctx.send(
                    f"{map_type} not in map types. Use `/maptypes` for a list of acceptable map types."
                )
                return
        row = 0
        pt = prettytable.PrettyTable(
            field_names=["Map Code", "Map Type", "Description", "Creator"]
        )
        async for entry in MapData.find(
            {"map_name": f"{''.join(map_name.split()).lower()}", "type": map_type}
            if map_type
            else {"map_name": f"{''.join(map_name.split()).lower()}"}
        ):
            pt.add_row(
                [
                    entry.code,
                    fill(" ".join(entry.type), constants.TYPE_MAX_LENGTH),
                    fill(entry.desc, constants.DESC_MAX_LENGTH),
                    fill(entry.creator, constants.CREATOR_MAX_LENGTH),
                ]
            )
            row += 1
        if row:
            if ceil(row / constants.PT_PAGE_SIZE) != 1:
                s, e, split_pt = 0, constants.PT_PAGE_SIZE - 1, []
                while s < row:
                    split_pt.append(pt.get_string(start=s, end=e))
                    s += constants.PT_PAGE_SIZE
                    e += constants.PT_PAGE_SIZE
                await self.pages(
                    ctx, split_pt, ceil(row / constants.PT_PAGE_SIZE), map_name
                )
            else:
                await ctx.send(f"{map_name}\n```Page 1/1:\n{pt}```")
        else:
            await ctx.send(f"No codes for {map_name}!")

    @commands.command(
        aliases=constants.DORADO[1:],
        help="Display all Dorado maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Dorado maps.",
        hidden=True,
    )
    async def dorado(self, ctx, map_type=""):
        map_name = "Dorado"
        if map_type:
            map_type = map_type.upper()
            if map_type not in constants.TYPES_OF_MAP:
                await ctx.send(
                    f"{map_type} not in map types. Use `/maptypes` for a list of acceptable map types."
                )
                return
        row = 0
        pt = prettytable.PrettyTable(
            field_names=["Map Code", "Map Type", "Description", "Creator"]
        )
        async for entry in MapData.find(
            {"map_name": f"{''.join(map_name.split()).lower()}", "type": map_type}
            if map_type
            else {"map_name": f"{''.join(map_name.split()).lower()}"}
        ):
            pt.add_row(
                [
                    entry.code,
                    fill(" ".join(entry.type), constants.TYPE_MAX_LENGTH),
                    fill(entry.desc, constants.DESC_MAX_LENGTH),
                    fill(entry.creator, constants.CREATOR_MAX_LENGTH),
                ]
            )
            row += 1
        if row:
            if ceil(row / constants.PT_PAGE_SIZE) != 1:
                s, e, split_pt = 0, constants.PT_PAGE_SIZE - 1, []
                while s < row:
                    split_pt.append(pt.get_string(start=s, end=e))
                    s += constants.PT_PAGE_SIZE
                    e += constants.PT_PAGE_SIZE
                await self.pages(
                    ctx, split_pt, ceil(row / constants.PT_PAGE_SIZE), map_name
                )
            else:
                await ctx.send(f"{map_name}\n```Page 1/1:\n{pt}```")
        else:
            await ctx.send(f"No codes for {map_name}!")

    @commands.command(
        aliases=constants.EICHENWALDE[1:],
        help="Display all Eichenwalde maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Eichenwalde maps.",
        hidden=True,
    )
    async def eichenwalde(self, ctx, map_type=""):
        map_name = "Eichenwalde"
        if map_type:
            map_type = map_type.upper()
            if map_type not in constants.TYPES_OF_MAP:
                await ctx.send(
                    f"{map_type} not in map types. Use `/maptypes` for a list of acceptable map types."
                )
                return
        row = 0
        pt = prettytable.PrettyTable(
            field_names=["Map Code", "Map Type", "Description", "Creator"]
        )
        async for entry in MapData.find(
            {"map_name": f"{''.join(map_name.split()).lower()}", "type": map_type}
            if map_type
            else {"map_name": f"{''.join(map_name.split()).lower()}"}
        ):
            pt.add_row(
                [
                    entry.code,
                    fill(" ".join(entry.type), constants.TYPE_MAX_LENGTH),
                    fill(entry.desc, constants.DESC_MAX_LENGTH),
                    fill(entry.creator, constants.CREATOR_MAX_LENGTH),
                ]
            )
            row += 1
        if row:
            if ceil(row / constants.PT_PAGE_SIZE) != 1:
                s, e, split_pt = 0, constants.PT_PAGE_SIZE - 1, []
                while s < row:
                    split_pt.append(pt.get_string(start=s, end=e))
                    s += constants.PT_PAGE_SIZE
                    e += constants.PT_PAGE_SIZE
                await self.pages(
                    ctx, split_pt, ceil(row / constants.PT_PAGE_SIZE), map_name
                )
            else:
                await ctx.send(f"{map_name}\n```Page 1/1:\n{pt}```")
        else:
            await ctx.send(f"No codes for {map_name}!")

    @commands.command(
        aliases=constants.HANAMURA[1:],
        help="Display all Hanamura maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Hanamura maps.",
        hidden=True,
    )
    async def hanamura(self, ctx, map_type=""):
        map_name = "Hanamura"
        if map_type:
            map_type = map_type.upper()
            if map_type not in constants.TYPES_OF_MAP:
                await ctx.send(
                    f"{map_type} not in map types. Use `/maptypes` for a list of acceptable map types."
                )
                return
        row = 0
        pt = prettytable.PrettyTable(
            field_names=["Map Code", "Map Type", "Description", "Creator"]
        )
        async for entry in MapData.find(
            {"map_name": f"{''.join(map_name.split()).lower()}", "type": map_type}
            if map_type
            else {"map_name": f"{''.join(map_name.split()).lower()}"}
        ):
            pt.add_row(
                [
                    entry.code,
                    fill(" ".join(entry.type), constants.TYPE_MAX_LENGTH),
                    fill(entry.desc, constants.DESC_MAX_LENGTH),
                    fill(entry.creator, constants.CREATOR_MAX_LENGTH),
                ]
            )
            row += 1
        if row:
            if ceil(row / constants.PT_PAGE_SIZE) != 1:
                s, e, split_pt = 0, constants.PT_PAGE_SIZE - 1, []
                while s < row:
                    split_pt.append(pt.get_string(start=s, end=e))
                    s += constants.PT_PAGE_SIZE
                    e += constants.PT_PAGE_SIZE
                await self.pages(
                    ctx, split_pt, ceil(row / constants.PT_PAGE_SIZE), map_name
                )
            else:
                await ctx.send(f"{map_name}\n```Page 1/1:\n{pt}```")
        else:
            await ctx.send(f"No codes for {map_name}!")

    @commands.command(
        aliases=constants.HAVANA[1:],
        help="Display all Havana maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Havana maps.",
        hidden=True,
    )
    async def havana(self, ctx, map_type=""):
        map_name = "Havana"
        if map_type:
            map_type = map_type.upper()
            if map_type not in constants.TYPES_OF_MAP:
                await ctx.send(
                    f"{map_type} not in map types. Use `/maptypes` for a list of acceptable map types."
                )
                return
        row = 0
        pt = prettytable.PrettyTable(
            field_names=["Map Code", "Map Type", "Description", "Creator"]
        )
        async for entry in MapData.find(
            {"map_name": f"{''.join(map_name.split()).lower()}", "type": map_type}
            if map_type
            else {"map_name": f"{''.join(map_name.split()).lower()}"}
        ):
            pt.add_row(
                [
                    entry.code,
                    fill(" ".join(entry.type), constants.TYPE_MAX_LENGTH),
                    fill(entry.desc, constants.DESC_MAX_LENGTH),
                    fill(entry.creator, constants.CREATOR_MAX_LENGTH),
                ]
            )
            row += 1
        if row:
            if ceil(row / constants.PT_PAGE_SIZE) != 1:
                s, e, split_pt = 0, constants.PT_PAGE_SIZE - 1, []
                while s < row:
                    split_pt.append(pt.get_string(start=s, end=e))
                    s += constants.PT_PAGE_SIZE
                    e += constants.PT_PAGE_SIZE
                await self.pages(
                    ctx, split_pt, ceil(row / constants.PT_PAGE_SIZE), map_name
                )
            else:
                await ctx.send(f"{map_name}\n```Page 1/1:\n{pt}```")
        else:
            await ctx.send(f"No codes for {map_name}!")

    @commands.command(
        aliases=constants.HOLLYWOOD[1:],
        help="Display all Hollywood maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Hollywood maps.",
        hidden=True,
    )
    async def hollywood(self, ctx, map_type=""):
        map_name = "Hollywood"
        if map_type:
            map_type = map_type.upper()
            if map_type not in constants.TYPES_OF_MAP:
                await ctx.send(
                    f"{map_type} not in map types. Use `/maptypes` for a list of acceptable map types."
                )
                return
        row = 0
        pt = prettytable.PrettyTable(
            field_names=["Map Code", "Map Type", "Description", "Creator"]
        )
        async for entry in MapData.find(
            {"map_name": f"{''.join(map_name.split()).lower()}", "type": map_type}
            if map_type
            else {"map_name": f"{''.join(map_name.split()).lower()}"}
        ):
            pt.add_row(
                [
                    entry.code,
                    fill(" ".join(entry.type), constants.TYPE_MAX_LENGTH),
                    fill(entry.desc, constants.DESC_MAX_LENGTH),
                    fill(entry.creator, constants.CREATOR_MAX_LENGTH),
                ]
            )
            row += 1
        if row:
            if ceil(row / constants.PT_PAGE_SIZE) != 1:
                s, e, split_pt = 0, constants.PT_PAGE_SIZE - 1, []
                while s < row:
                    split_pt.append(pt.get_string(start=s, end=e))
                    s += constants.PT_PAGE_SIZE
                    e += constants.PT_PAGE_SIZE
                await self.pages(
                    ctx, split_pt, ceil(row / constants.PT_PAGE_SIZE), map_name
                )
            else:
                await ctx.send(f"{map_name}\n```Page 1/1:\n{pt}```")
        else:
            await ctx.send(f"No codes for {map_name}!")

    @commands.command(
        aliases=constants.HORIZONLUNARCOLONY[1:],
        help="Display all Horizon Lunar Colony maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Horizon Lunar Colony maps.",
        hidden=True,
    )
    async def horizonlunarcolony(self, ctx, map_type=""):
        map_name = "Horizon Lunar Colony"
        if map_type:
            map_type = map_type.upper()
            if map_type not in constants.TYPES_OF_MAP:
                await ctx.send(
                    f"{map_type} not in map types. Use `/maptypes` for a list of acceptable map types."
                )
                return
        row = 0
        pt = prettytable.PrettyTable(
            field_names=["Map Code", "Map Type", "Description", "Creator"]
        )
        async for entry in MapData.find(
            {"map_name": f"{''.join(map_name.split()).lower()}", "type": map_type}
            if map_type
            else {"map_name": f"{''.join(map_name.split()).lower()}"}
        ):
            pt.add_row(
                [
                    entry.code,
                    fill(" ".join(entry.type), constants.TYPE_MAX_LENGTH),
                    fill(entry.desc, constants.DESC_MAX_LENGTH),
                    fill(entry.creator, constants.CREATOR_MAX_LENGTH),
                ]
            )
            row += 1
        if row:
            if ceil(row / constants.PT_PAGE_SIZE) != 1:
                s, e, split_pt = 0, constants.PT_PAGE_SIZE - 1, []
                while s < row:
                    split_pt.append(pt.get_string(start=s, end=e))
                    s += constants.PT_PAGE_SIZE
                    e += constants.PT_PAGE_SIZE
                await self.pages(
                    ctx, split_pt, ceil(row / constants.PT_PAGE_SIZE), map_name
                )
            else:
                await ctx.send(f"{map_name}\n```Page 1/1:\n{pt}```")
        else:
            await ctx.send(f"No codes for {map_name}!")

    @commands.command(
        aliases=constants.ILIOS[1:],
        help="Display all Ilios maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Ilios maps.",
        hidden=True,
    )
    async def ilios(self, ctx, map_type=""):
        map_name = "Ilios"
        if map_type:
            map_type = map_type.upper()
            if map_type not in constants.TYPES_OF_MAP:
                await ctx.send(
                    f"{map_type} not in map types. Use `/maptypes` for a list of acceptable map types."
                )
                return
        row = 0
        pt = prettytable.PrettyTable(
            field_names=["Map Code", "Map Type", "Description", "Creator"]
        )
        async for entry in MapData.find(
            {"map_name": f"{''.join(map_name.split()).lower()}", "type": map_type}
            if map_type
            else {"map_name": f"{''.join(map_name.split()).lower()}"}
        ):
            pt.add_row(
                [
                    entry.code,
                    fill(" ".join(entry.type), constants.TYPE_MAX_LENGTH),
                    fill(entry.desc, constants.DESC_MAX_LENGTH),
                    fill(entry.creator, constants.CREATOR_MAX_LENGTH),
                ]
            )
            row += 1
        if row:
            if ceil(row / constants.PT_PAGE_SIZE) != 1:
                s, e, split_pt = 0, constants.PT_PAGE_SIZE - 1, []
                while s < row:
                    split_pt.append(pt.get_string(start=s, end=e))
                    s += constants.PT_PAGE_SIZE
                    e += constants.PT_PAGE_SIZE
                await self.pages(
                    ctx, split_pt, ceil(row / constants.PT_PAGE_SIZE), map_name
                )
            else:
                await ctx.send(f"{map_name}\n```Page 1/1:\n{pt}```")
        else:
            await ctx.send(f"No codes for {map_name}!")

    @commands.command(
        aliases=constants.JUNKERTOWN[1:],
        help="Display all Junkertown maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Junkertown maps.",
        hidden=True,
    )
    async def junkertown(self, ctx, map_type=""):
        map_name = "Junkertown"
        if map_type:
            map_type = map_type.upper()
            if map_type not in constants.TYPES_OF_MAP:
                await ctx.send(
                    f"{map_type} not in map types. Use `/maptypes` for a list of acceptable map types."
                )
                return
        row = 0
        pt = prettytable.PrettyTable(
            field_names=["Map Code", "Map Type", "Description", "Creator"]
        )
        async for entry in MapData.find(
            {"map_name": f"{''.join(map_name.split()).lower()}", "type": map_type}
            if map_type
            else {"map_name": f"{''.join(map_name.split()).lower()}"}
        ):
            pt.add_row(
                [
                    entry.code,
                    fill(" ".join(entry.type), constants.TYPE_MAX_LENGTH),
                    fill(entry.desc, constants.DESC_MAX_LENGTH),
                    fill(entry.creator, constants.CREATOR_MAX_LENGTH),
                ]
            )
            row += 1
        if row:
            if ceil(row / constants.PT_PAGE_SIZE) != 1:
                s, e, split_pt = 0, constants.PT_PAGE_SIZE - 1, []
                while s < row:
                    split_pt.append(pt.get_string(start=s, end=e))
                    s += constants.PT_PAGE_SIZE
                    e += constants.PT_PAGE_SIZE
                await self.pages(
                    ctx, split_pt, ceil(row / constants.PT_PAGE_SIZE), map_name
                )
            else:
                await ctx.send(f"{map_name}\n```Page 1/1:\n{pt}```")
        else:
            await ctx.send(f"No codes for {map_name}!")

    @commands.command(
        aliases=constants.LIJIANGTOWER[1:],
        help="Display all Lijiang Tower maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Lijiang Tower maps.",
        hidden=True,
    )
    async def lijiangtower(self, ctx, map_type=""):
        map_name = "Lijiang Tower"
        if map_type:
            map_type = map_type.upper()
            if map_type not in constants.TYPES_OF_MAP:
                await ctx.send(
                    f"{map_type} not in map types. Use `/maptypes` for a list of acceptable map types."
                )
                return
        row = 0
        pt = prettytable.PrettyTable(
            field_names=["Map Code", "Map Type", "Description", "Creator"]
        )
        async for entry in MapData.find(
            {"map_name": f"{''.join(map_name.split()).lower()}", "type": map_type}
            if map_type
            else {"map_name": f"{''.join(map_name.split()).lower()}"}
        ):
            pt.add_row(
                [
                    entry.code,
                    fill(" ".join(entry.type), constants.TYPE_MAX_LENGTH),
                    fill(entry.desc, constants.DESC_MAX_LENGTH),
                    fill(entry.creator, constants.CREATOR_MAX_LENGTH),
                ]
            )
            row += 1
        if row:
            if ceil(row / constants.PT_PAGE_SIZE) != 1:
                s, e, split_pt = 0, constants.PT_PAGE_SIZE - 1, []
                while s < row:
                    split_pt.append(pt.get_string(start=s, end=e))
                    s += constants.PT_PAGE_SIZE
                    e += constants.PT_PAGE_SIZE
                await self.pages(
                    ctx, split_pt, ceil(row / constants.PT_PAGE_SIZE), map_name
                )
            else:
                await ctx.send(f"{map_name}\n```Page 1/1:\n{pt}```")
        else:
            await ctx.send(f"No codes for {map_name}!")

    @commands.command(
        aliases=constants.NECROPOLIS[1:],
        help="Display all Necropolis maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Necropolis maps.",
        hidden=True,
    )
    async def necropolis(self, ctx, map_type=""):
        map_name = "Necropolis"
        if map_type:
            map_type = map_type.upper()
            if map_type not in constants.TYPES_OF_MAP:
                await ctx.send(
                    f"{map_type} not in map types. Use `/maptypes` for a list of acceptable map types."
                )
                return
        row = 0
        pt = prettytable.PrettyTable(
            field_names=["Map Code", "Map Type", "Description", "Creator"]
        )
        async for entry in MapData.find(
            {"map_name": f"{''.join(map_name.split()).lower()}", "type": map_type}
            if map_type
            else {"map_name": f"{''.join(map_name.split()).lower()}"}
        ):
            pt.add_row(
                [
                    entry.code,
                    fill(" ".join(entry.type), constants.TYPE_MAX_LENGTH),
                    fill(entry.desc, constants.DESC_MAX_LENGTH),
                    fill(entry.creator, constants.CREATOR_MAX_LENGTH),
                ]
            )
            row += 1
        if row:
            if ceil(row / constants.PT_PAGE_SIZE) != 1:
                s, e, split_pt = 0, constants.PT_PAGE_SIZE - 1, []
                while s < row:
                    split_pt.append(pt.get_string(start=s, end=e))
                    s += constants.PT_PAGE_SIZE
                    e += constants.PT_PAGE_SIZE
                await self.pages(
                    ctx, split_pt, ceil(row / constants.PT_PAGE_SIZE), map_name
                )
            else:
                await ctx.send(f"{map_name}\n```Page 1/1:\n{pt}```")
        else:
            await ctx.send(f"No codes for {map_name}!")

    @commands.command(
        aliases=constants.NEPAL[1:],
        help="Display all Nepal maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Nepal maps.",
        hidden=True,
    )
    async def nepal(self, ctx, map_type=""):
        map_name = "Nepal"
        if map_type:
            map_type = map_type.upper()
            if map_type not in constants.TYPES_OF_MAP:
                await ctx.send(
                    f"{map_type} not in map types. Use `/maptypes` for a list of acceptable map types."
                )
                return
        row = 0
        pt = prettytable.PrettyTable(
            field_names=["Map Code", "Map Type", "Description", "Creator"]
        )
        async for entry in MapData.find(
            {"map_name": f"{''.join(map_name.split()).lower()}", "type": map_type}
            if map_type
            else {"map_name": f"{''.join(map_name.split()).lower()}"}
        ):
            pt.add_row(
                [
                    entry.code,
                    fill(" ".join(entry.type), constants.TYPE_MAX_LENGTH),
                    fill(entry.desc, constants.DESC_MAX_LENGTH),
                    fill(entry.creator, constants.CREATOR_MAX_LENGTH),
                ]
            )
            row += 1
        if row:
            if ceil(row / constants.PT_PAGE_SIZE) != 1:
                s, e, split_pt = 0, constants.PT_PAGE_SIZE - 1, []
                while s < row:
                    split_pt.append(pt.get_string(start=s, end=e))
                    s += constants.PT_PAGE_SIZE
                    e += constants.PT_PAGE_SIZE
                await self.pages(
                    ctx, split_pt, ceil(row / constants.PT_PAGE_SIZE), map_name
                )
            else:
                await ctx.send(f"{map_name}\n```Page 1/1:\n{pt}```")
        else:
            await ctx.send(f"No codes for {map_name}!")

    @commands.command(
        aliases=constants.NUMBANI[1:],
        help="Display all Numbani maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Numbani maps.",
        hidden=True,
    )
    async def numbani(self, ctx, map_type=""):
        map_name = "Numbani"
        if map_type:
            map_type = map_type.upper()
            if map_type not in constants.TYPES_OF_MAP:
                await ctx.send(
                    f"{map_type} not in map types. Use `/maptypes` for a list of acceptable map types."
                )
                return
        row = 0
        pt = prettytable.PrettyTable(
            field_names=["Map Code", "Map Type", "Description", "Creator"]
        )
        async for entry in MapData.find(
            {"map_name": f"{''.join(map_name.split()).lower()}", "type": map_type}
            if map_type
            else {"map_name": f"{''.join(map_name.split()).lower()}"}
        ):
            pt.add_row(
                [
                    entry.code,
                    fill(" ".join(entry.type), constants.TYPE_MAX_LENGTH),
                    fill(entry.desc, constants.DESC_MAX_LENGTH),
                    fill(entry.creator, constants.CREATOR_MAX_LENGTH),
                ]
            )
            row += 1
        if row:
            if ceil(row / constants.PT_PAGE_SIZE) != 1:
                s, e, split_pt = 0, constants.PT_PAGE_SIZE - 1, []
                while s < row:
                    split_pt.append(pt.get_string(start=s, end=e))
                    s += constants.PT_PAGE_SIZE
                    e += constants.PT_PAGE_SIZE
                await self.pages(
                    ctx, split_pt, ceil(row / constants.PT_PAGE_SIZE), map_name
                )
            else:
                await ctx.send(f"{map_name}\n```Page 1/1:\n{pt}```")
        else:
            await ctx.send(f"No codes for {map_name}!")

    @commands.command(
        aliases=constants.OASIS[1:],
        help="Display all Oasis maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Oasis maps.",
        hidden=True,
    )
    async def oasis(self, ctx, map_type=""):
        map_name = "Oasis"
        if map_type:
            map_type = map_type.upper()
            if map_type not in constants.TYPES_OF_MAP:
                await ctx.send(
                    f"{map_type} not in map types. Use `/maptypes` for a list of acceptable map types."
                )
                return
        row = 0
        pt = prettytable.PrettyTable(
            field_names=["Map Code", "Map Type", "Description", "Creator"]
        )
        async for entry in MapData.find(
            {"map_name": f"{''.join(map_name.split()).lower()}", "type": map_type}
            if map_type
            else {"map_name": f"{''.join(map_name.split()).lower()}"}
        ):
            pt.add_row(
                [
                    entry.code,
                    fill(" ".join(entry.type), constants.TYPE_MAX_LENGTH),
                    fill(entry.desc, constants.DESC_MAX_LENGTH),
                    fill(entry.creator, constants.CREATOR_MAX_LENGTH),
                ]
            )
            row += 1
        if row:
            if ceil(row / constants.PT_PAGE_SIZE) != 1:
                s, e, split_pt = 0, constants.PT_PAGE_SIZE - 1, []
                while s < row:
                    split_pt.append(pt.get_string(start=s, end=e))
                    s += constants.PT_PAGE_SIZE
                    e += constants.PT_PAGE_SIZE
                await self.pages(
                    ctx, split_pt, ceil(row / constants.PT_PAGE_SIZE), map_name
                )
            else:
                await ctx.send(f"{map_name}\n```Page 1/1:\n{pt}```")
        else:
            await ctx.send(f"No codes for {map_name}!")

    @commands.command(
        aliases=constants.PARIS[1:],
        help="Display all Paris maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Paris maps.",
        hidden=True,
    )
    async def paris(self, ctx, map_type=""):
        map_name = "Paris"
        if map_type:
            map_type = map_type.upper()
            if map_type not in constants.TYPES_OF_MAP:
                await ctx.send(
                    f"{map_type} not in map types. Use `/maptypes` for a list of acceptable map types."
                )
                return
        row = 0
        pt = prettytable.PrettyTable(
            field_names=["Map Code", "Map Type", "Description", "Creator"]
        )
        async for entry in MapData.find(
            {"map_name": f"{''.join(map_name.split()).lower()}", "type": map_type}
            if map_type
            else {"map_name": f"{''.join(map_name.split()).lower()}"}
        ):
            pt.add_row(
                [
                    entry.code,
                    fill(" ".join(entry.type), constants.TYPE_MAX_LENGTH),
                    fill(entry.desc, constants.DESC_MAX_LENGTH),
                    fill(entry.creator, constants.CREATOR_MAX_LENGTH),
                ]
            )
            row += 1
        if row:
            if ceil(row / constants.PT_PAGE_SIZE) != 1:
                s, e, split_pt = 0, constants.PT_PAGE_SIZE - 1, []
                while s < row:
                    split_pt.append(pt.get_string(start=s, end=e))
                    s += constants.PT_PAGE_SIZE
                    e += constants.PT_PAGE_SIZE
                await self.pages(
                    ctx, split_pt, ceil(row / constants.PT_PAGE_SIZE), map_name
                )
            else:
                await ctx.send(f"{map_name}\n```Page 1/1:\n{pt}```")
        else:
            await ctx.send(f"No codes for {map_name}!")

    @commands.command(
        aliases=constants.RIALTO[1:],
        help="Display all Rialto maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Rialto maps.",
        hidden=True,
    )
    async def rialto(self, ctx, map_type=""):
        map_name = "Rialto"
        if map_type:
            map_type = map_type.upper()
            if map_type not in constants.TYPES_OF_MAP:
                await ctx.send(
                    f"{map_type} not in map types. Use `/maptypes` for a list of acceptable map types."
                )
                return
        row = 0
        pt = prettytable.PrettyTable(
            field_names=["Map Code", "Map Type", "Description", "Creator"]
        )
        async for entry in MapData.find(
            {"map_name": f"{''.join(map_name.split()).lower()}", "type": map_type}
            if map_type
            else {"map_name": f"{''.join(map_name.split()).lower()}"}
        ):
            pt.add_row(
                [
                    entry.code,
                    fill(" ".join(entry.type), constants.TYPE_MAX_LENGTH),
                    fill(entry.desc, constants.DESC_MAX_LENGTH),
                    fill(entry.creator, constants.CREATOR_MAX_LENGTH),
                ]
            )
            row += 1
        if row:
            if ceil(row / constants.PT_PAGE_SIZE) != 1:
                s, e, split_pt = 0, constants.PT_PAGE_SIZE - 1, []
                while s < row:
                    split_pt.append(pt.get_string(start=s, end=e))
                    s += constants.PT_PAGE_SIZE
                    e += constants.PT_PAGE_SIZE
                await self.pages(
                    ctx, split_pt, ceil(row / constants.PT_PAGE_SIZE), map_name
                )
            else:
                await ctx.send(f"{map_name}\n```Page 1/1:\n{pt}```")
        else:
            await ctx.send(f"No codes for {map_name}!")

    @commands.command(
        aliases=constants.ROUTE66[1:],
        help="Display all Route 66 maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Route 66 maps.",
        hidden=True,
    )
    async def route66(self, ctx, map_type=""):
        map_name = "Route 66"
        if map_type:
            map_type = map_type.upper()
            if map_type not in constants.TYPES_OF_MAP:
                await ctx.send(
                    f"{map_type} not in map types. Use `/maptypes` for a list of acceptable map types."
                )
                return
        row = 0
        pt = prettytable.PrettyTable(
            field_names=["Map Code", "Map Type", "Description", "Creator"]
        )
        async for entry in MapData.find(
            {"map_name": f"{''.join(map_name.split()).lower()}", "type": map_type}
            if map_type
            else {"map_name": f"{''.join(map_name.split()).lower()}"}
        ):
            pt.add_row(
                [
                    entry.code,
                    fill(" ".join(entry.type), constants.TYPE_MAX_LENGTH),
                    fill(entry.desc, constants.DESC_MAX_LENGTH),
                    fill(entry.creator, constants.CREATOR_MAX_LENGTH),
                ]
            )
            row += 1
        if row:
            if ceil(row / constants.PT_PAGE_SIZE) != 1:
                s, e, split_pt = 0, constants.PT_PAGE_SIZE - 1, []
                while s < row:
                    split_pt.append(pt.get_string(start=s, end=e))
                    s += constants.PT_PAGE_SIZE
                    e += constants.PT_PAGE_SIZE
                await self.pages(
                    ctx, split_pt, ceil(row / constants.PT_PAGE_SIZE), map_name
                )
            else:
                await ctx.send(f"{map_name}\n```Page 1/1:\n{pt}```")
        else:
            await ctx.send(f"No codes for {map_name}!")

    @commands.command(
        aliases=constants.TEMPLEOFANUBIS[1:],
        help="Display all Temple of Anubis maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Temple of Anubis maps.",
        hidden=True,
    )
    async def templeofanubis(self, ctx, map_type=""):
        map_name = "Temple of Anubis"
        if map_type:
            map_type = map_type.upper()
            if map_type not in constants.TYPES_OF_MAP:
                await ctx.send(
                    f"{map_type} not in map types. Use `/maptypes` for a list of acceptable map types."
                )
                return
        row = 0
        pt = prettytable.PrettyTable(
            field_names=["Map Code", "Map Type", "Description", "Creator"]
        )
        async for entry in MapData.find(
            {"map_name": f"{''.join(map_name.split()).lower()}", "type": map_type}
            if map_type
            else {"map_name": f"{''.join(map_name.split()).lower()}"}
        ):
            pt.add_row(
                [
                    entry.code,
                    fill(" ".join(entry.type), constants.TYPE_MAX_LENGTH),
                    fill(entry.desc, constants.DESC_MAX_LENGTH),
                    fill(entry.creator, constants.CREATOR_MAX_LENGTH),
                ]
            )
            row += 1
        if row:
            if ceil(row / constants.PT_PAGE_SIZE) != 1:
                s, e, split_pt = 0, constants.PT_PAGE_SIZE - 1, []
                while s < row:
                    split_pt.append(pt.get_string(start=s, end=e))
                    s += constants.PT_PAGE_SIZE
                    e += constants.PT_PAGE_SIZE
                await self.pages(
                    ctx, split_pt, ceil(row / constants.PT_PAGE_SIZE), map_name
                )
            else:
                await ctx.send(f"{map_name}\n```Page 1/1:\n{pt}```")
        else:
            await ctx.send(f"No codes for {map_name}!")

    @commands.command(
        aliases=constants.VOLSKAYAINDUSTRIES[1:],
        help="Display all Volskaya Industries maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Volskaya Industries maps.",
        hidden=True,
    )
    async def volskayaindustries(self, ctx, map_type=""):
        map_name = "Volskaya Industries"
        if map_type:
            map_type = map_type.upper()
            if map_type not in constants.TYPES_OF_MAP:
                await ctx.send(
                    f"{map_type} not in map types. Use `/maptypes` for a list of acceptable map types."
                )
                return
        row = 0
        pt = prettytable.PrettyTable(
            field_names=["Map Code", "Map Type", "Description", "Creator"]
        )
        async for entry in MapData.find(
            {"map_name": f"{''.join(map_name.split()).lower()}", "type": map_type}
            if map_type
            else {"map_name": f"{''.join(map_name.split()).lower()}"}
        ):
            pt.add_row(
                [
                    entry.code,
                    fill(" ".join(entry.type), constants.TYPE_MAX_LENGTH),
                    fill(entry.desc, constants.DESC_MAX_LENGTH),
                    fill(entry.creator, constants.CREATOR_MAX_LENGTH),
                ]
            )
            row += 1
        if row:
            if ceil(row / constants.PT_PAGE_SIZE) != 1:
                s, e, split_pt = 0, constants.PT_PAGE_SIZE - 1, []
                while s < row:
                    split_pt.append(pt.get_string(start=s, end=e))
                    s += constants.PT_PAGE_SIZE
                    e += constants.PT_PAGE_SIZE
                await self.pages(
                    ctx, split_pt, ceil(row / constants.PT_PAGE_SIZE), map_name
                )
            else:
                await ctx.send(f"{map_name}\n```Page 1/1:\n{pt}```")
        else:
            await ctx.send(f"No codes for {map_name}!")

    @commands.command(
        aliases=constants.WATCHPOINTGIBRALTAR[1:],
        help="Display all Watchpoint Gibraltar maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Watchpoint Gibraltar maps.",
        hidden=True,
    )
    async def watchpointgibraltar(self, ctx, map_type=""):
        map_name = "Watchpoint Gibraltar"
        if map_type:
            map_type = map_type.upper()
            if map_type not in constants.TYPES_OF_MAP:
                await ctx.send(
                    f"{map_type} not in map types. Use `/maptypes` for a list of acceptable map types."
                )
                return
        row = 0
        pt = prettytable.PrettyTable(
            field_names=["Map Code", "Map Type", "Description", "Creator"]
        )
        async for entry in MapData.find(
            {"map_name": f"{''.join(map_name.split()).lower()}", "type": map_type}
            if map_type
            else {"map_name": f"{''.join(map_name.split()).lower()}"}
        ):
            pt.add_row(
                [
                    entry.code,
                    fill(" ".join(entry.type), constants.TYPE_MAX_LENGTH),
                    fill(entry.desc, constants.DESC_MAX_LENGTH),
                    fill(entry.creator, constants.CREATOR_MAX_LENGTH),
                ]
            )
            row += 1
        if row:
            if ceil(row / constants.PT_PAGE_SIZE) != 1:
                s, e, split_pt = 0, constants.PT_PAGE_SIZE - 1, []
                while s < row:
                    split_pt.append(pt.get_string(start=s, end=e))
                    s += constants.PT_PAGE_SIZE
                    e += constants.PT_PAGE_SIZE
                await self.pages(
                    ctx, split_pt, ceil(row / constants.PT_PAGE_SIZE), map_name
                )
            else:
                await ctx.send(f"{map_name}\n```Page 1/1:\n{pt}```")
        else:
            await ctx.send(f"No codes for {map_name}!")

    @commands.command(
        aliases=constants.KINGSROW[1:],
        help="Display all King's Row maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all King's Row maps.",
        hidden=True,
    )
    async def kingsrow(self, ctx, map_type=""):
        map_name = "King's Row"
        if map_type:
            map_type = map_type.upper()
            if map_type not in constants.TYPES_OF_MAP:
                await ctx.send(
                    f"{map_type} not in map types. Use `/maptypes` for a list of acceptable map types."
                )
                return
        row = 0
        pt = prettytable.PrettyTable(
            field_names=["Map Code", "Map Type", "Description", "Creator"]
        )
        async for entry in MapData.find(
            {"map_name": f"{''.join(map_name.split()).lower()}", "type": map_type}
            if map_type
            else {"map_name": f"{''.join(map_name.split()).lower()}"}
        ):
            pt.add_row(
                [
                    entry.code,
                    fill(" ".join(entry.type), constants.TYPE_MAX_LENGTH),
                    fill(entry.desc, constants.DESC_MAX_LENGTH),
                    fill(entry.creator, constants.CREATOR_MAX_LENGTH),
                ]
            )
            row += 1
        if row:
            if ceil(row / constants.PT_PAGE_SIZE) != 1:
                s, e, split_pt = 0, constants.PT_PAGE_SIZE - 1, []
                while s < row:
                    split_pt.append(pt.get_string(start=s, end=e))
                    s += constants.PT_PAGE_SIZE
                    e += constants.PT_PAGE_SIZE
                await self.pages(
                    ctx, split_pt, ceil(row / constants.PT_PAGE_SIZE), map_name
                )
            else:
                await ctx.send(f"{map_name}\n```Page 1/1:\n{pt}```")
        else:
            await ctx.send(f"No codes for {map_name}!")

    @commands.command(
        aliases=constants.PETRA[1:],
        help="Display all Petra maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Petra maps.",
        hidden=True,
    )
    async def petra(self, ctx, map_type=""):
        map_name = "Petra"
        if map_type:
            map_type = map_type.upper()
            if map_type not in constants.TYPES_OF_MAP:
                await ctx.send(
                    f"{map_type} not in map types. Use `/maptypes` for a list of acceptable map types."
                )
                return
        row = 0
        pt = prettytable.PrettyTable(
            field_names=["Map Code", "Map Type", "Description", "Creator"]
        )
        async for entry in MapData.find(
            {"map_name": f"{''.join(map_name.split()).lower()}", "type": map_type}
            if map_type
            else {"map_name": f"{''.join(map_name.split()).lower()}"}
        ):
            pt.add_row(
                [
                    entry.code,
                    fill(" ".join(entry.type), constants.TYPE_MAX_LENGTH),
                    fill(entry.desc, constants.DESC_MAX_LENGTH),
                    fill(entry.creator, constants.CREATOR_MAX_LENGTH),
                ]
            )
            row += 1
        if row:
            if ceil(row / constants.PT_PAGE_SIZE) != 1:
                s, e, split_pt = 0, constants.PT_PAGE_SIZE - 1, []
                while s < row:
                    split_pt.append(pt.get_string(start=s, end=e))
                    s += constants.PT_PAGE_SIZE
                    e += constants.PT_PAGE_SIZE
                await self.pages(
                    ctx, split_pt, ceil(row / constants.PT_PAGE_SIZE), map_name
                )
            else:
                await ctx.send(f"{map_name}\n```Page 1/1:\n{pt}```")
        else:
            await ctx.send(f"No codes for {map_name}!")

    @commands.command(
        aliases=constants.ECOPOINTANTARCTICA[1:],
        help="Display all Ecopoint Antarctica maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Ecopoint Antarctica maps.",
        hidden=True,
    )
    async def ecopointantarctica(self, ctx, map_type=""):
        map_name = "Ecopoint Antarctica"
        if map_type:
            map_type = map_type.upper()
            if map_type not in constants.TYPES_OF_MAP:
                await ctx.send(
                    f"{map_type} not in map types. Use `/maptypes` for a list of acceptable map types."
                )
                return
        row = 0
        pt = prettytable.PrettyTable(
            field_names=["Map Code", "Map Type", "Description", "Creator"]
        )
        async for entry in MapData.find(
            {"map_name": f"{''.join(map_name.split()).lower()}", "type": map_type}
            if map_type
            else {"map_name": f"{''.join(map_name.split()).lower()}"}
        ):
            pt.add_row(
                [
                    entry.code,
                    fill(" ".join(entry.type), constants.TYPE_MAX_LENGTH),
                    fill(entry.desc, constants.DESC_MAX_LENGTH),
                    fill(entry.creator, constants.CREATOR_MAX_LENGTH),
                ]
            )
            row += 1
        if row:
            if ceil(row / constants.PT_PAGE_SIZE) != 1:
                s, e, split_pt = 0, constants.PT_PAGE_SIZE - 1, []
                while s < row:
                    split_pt.append(pt.get_string(start=s, end=e))
                    s += constants.PT_PAGE_SIZE
                    e += constants.PT_PAGE_SIZE
                await self.pages(
                    ctx, split_pt, ceil(row / constants.PT_PAGE_SIZE), map_name
                )
            else:
                await ctx.send(f"{map_name}\n```Page 1/1:\n{pt}```")
        else:
            await ctx.send(f"No codes for {map_name}!")

    @commands.command(
        aliases=constants.KANEZAKA[1:],
        help="Display all Kanezaka maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Kanezaka maps.",
        hidden=True,
    )
    async def kanezaka(self, ctx, map_type=""):
        map_name = "Kanezaka"
        if map_type:
            map_type = map_type.upper()
            if map_type not in constants.TYPES_OF_MAP:
                await ctx.send(
                    f"{map_type} not in map types. Use `/maptypes` for a list of acceptable map types."
                )
                return
        row = 0
        pt = prettytable.PrettyTable(
            field_names=["Map Code", "Map Type", "Description", "Creator"]
        )
        async for entry in MapData.find(
            {"map_name": f"{''.join(map_name.split()).lower()}", "type": map_type}
            if map_type
            else {"map_name": f"{''.join(map_name.split()).lower()}"}
        ):
            pt.add_row(
                [
                    entry.code,
                    fill(" ".join(entry.type), constants.TYPE_MAX_LENGTH),
                    fill(entry.desc, constants.DESC_MAX_LENGTH),
                    fill(entry.creator, constants.CREATOR_MAX_LENGTH),
                ]
            )
            row += 1
        if row:
            if ceil(row / constants.PT_PAGE_SIZE) != 1:
                s, e, split_pt = 0, constants.PT_PAGE_SIZE - 1, []
                while s < row:
                    split_pt.append(pt.get_string(start=s, end=e))
                    s += constants.PT_PAGE_SIZE
                    e += constants.PT_PAGE_SIZE
                await self.pages(
                    ctx, split_pt, ceil(row / constants.PT_PAGE_SIZE), map_name
                )
            else:
                await ctx.send(f"{map_name}\n```Page 1/1:\n{pt}```")
        else:
            await ctx.send(f"No codes for {map_name}!")

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
        if map_type:
            map_type = map_type.upper()
            if map_type not in constants.TYPES_OF_MAP:
                await ctx.send(
                    f"{map_type} not in map types. Use `/maptypes` for a list of acceptable map types."
                )
                return
        row = 0
        pt = prettytable.PrettyTable(
            field_names=["Map Code", "Map Type", "Description", "Creator"]
        )
        async for entry in MapData.find(
            {"map_name": f"{''.join(map_name.split()).lower()}", "type": map_type}
            if map_type
            else {"map_name": f"{''.join(map_name.split()).lower()}"}
        ):
            pt.add_row(
                [
                    entry.code,
                    fill(" ".join(entry.type), constants.TYPE_MAX_LENGTH),
                    fill(entry.desc, constants.DESC_MAX_LENGTH),
                    fill(entry.creator, constants.CREATOR_MAX_LENGTH),
                ]
            )
            row += 1
        if row:
            if ceil(row / constants.PT_PAGE_SIZE) != 1:
                s, e, split_pt = 0, constants.PT_PAGE_SIZE - 1, []
                while s < row:
                    split_pt.append(pt.get_string(start=s, end=e))
                    s += constants.PT_PAGE_SIZE
                    e += constants.PT_PAGE_SIZE
                await self.pages(
                    ctx, split_pt, ceil(row / constants.PT_PAGE_SIZE), map_name
                )
            else:
                await ctx.send(f"{map_name}\n```Page 1/1:\n{pt}```")
        else:
            await ctx.send(f"No codes for {map_name}!")

    @commands.command(
        aliases=constants.WORKSHOPEXPANSE[1:],
        help="Display all Workshop Expanse maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Workshop Expanse maps.",
        hidden=True,
    )
    async def workshopexpanse(self, ctx, map_type=""):
        map_name = "Workshop Expanse"
        if map_type:
            map_type = map_type.upper()
            if map_type not in constants.TYPES_OF_MAP:
                await ctx.send(
                    f"{map_type} not in map types. Use `/maptypes` for a list of acceptable map types."
                )
                return
        row = 0
        pt = prettytable.PrettyTable(
            field_names=["Map Code", "Map Type", "Description", "Creator"]
        )
        async for entry in MapData.find(
            {"map_name": f"{''.join(map_name.split()).lower()}", "type": map_type}
            if map_type
            else {"map_name": f"{''.join(map_name.split()).lower()}"}
        ):
            pt.add_row(
                [
                    entry.code,
                    fill(" ".join(entry.type), constants.TYPE_MAX_LENGTH),
                    fill(entry.desc, constants.DESC_MAX_LENGTH),
                    fill(entry.creator, constants.CREATOR_MAX_LENGTH),
                ]
            )
            row += 1
        if row:
            if ceil(row / constants.PT_PAGE_SIZE) != 1:
                s, e, split_pt = 0, constants.PT_PAGE_SIZE - 1, []
                while s < row:
                    split_pt.append(pt.get_string(start=s, end=e))
                    s += constants.PT_PAGE_SIZE
                    e += constants.PT_PAGE_SIZE
                await self.pages(
                    ctx, split_pt, ceil(row / constants.PT_PAGE_SIZE), map_name
                )
            else:
                await ctx.send(f"{map_name}\n```Page 1/1:\n{pt}```")
        else:
            await ctx.send(f"No codes for {map_name}!")

    @commands.command(
        aliases=constants.WORKSHOPGREENSCREEN[1:],
        help="Display all Workshop Greenscreen maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Workshop Greenscreen maps.",
        hidden=True,
    )
    async def workshopgreenscreen(self, ctx, map_type=""):
        map_name = "Workshop Greenscreen"
        if map_type:
            map_type = map_type.upper()
            if map_type not in constants.TYPES_OF_MAP:
                await ctx.send(
                    f"{map_type} not in map types. Use `/maptypes` for a list of acceptable map types."
                )
                return
        row = 0
        pt = prettytable.PrettyTable(
            field_names=["Map Code", "Map Type", "Description", "Creator"]
        )
        async for entry in MapData.find(
            {"map_name": f"{''.join(map_name.split()).lower()}", "type": map_type}
            if map_type
            else {"map_name": f"{''.join(map_name.split()).lower()}"}
        ):
            pt.add_row(
                [
                    entry.code,
                    fill(" ".join(entry.type), constants.TYPE_MAX_LENGTH),
                    fill(entry.desc, constants.DESC_MAX_LENGTH),
                    fill(entry.creator, constants.CREATOR_MAX_LENGTH),
                ]
            )
            row += 1
        if row:
            if ceil(row / constants.PT_PAGE_SIZE) != 1:
                s, e, split_pt = 0, constants.PT_PAGE_SIZE - 1, []
                while s < row:
                    split_pt.append(pt.get_string(start=s, end=e))
                    s += constants.PT_PAGE_SIZE
                    e += constants.PT_PAGE_SIZE
                await self.pages(
                    ctx, split_pt, ceil(row / constants.PT_PAGE_SIZE), map_name
                )
            else:
                await ctx.send(f"{map_name}\n```Page 1/1:\n{pt}```")
        else:
            await ctx.send(f"No codes for {map_name}!")

    @commands.command(
        aliases=constants.WORKSHOPISLAND[1:],
        help="Display all Workshop Island maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Workshop Island maps.",
        hidden=True,
    )
    async def workshopisland(self, ctx, map_type=""):
        map_name = "Workshop Island"
        if map_type:
            map_type = map_type.upper()
            if map_type not in constants.TYPES_OF_MAP:
                await ctx.send(
                    f"{map_type} not in map types. Use `/maptypes` for a list of acceptable map types."
                )
                return
        row = 0
        pt = prettytable.PrettyTable(
            field_names=["Map Code", "Map Type", "Description", "Creator"]
        )
        async for entry in MapData.find(
            {"map_name": f"{''.join(map_name.split()).lower()}", "type": map_type}
            if map_type
            else {"map_name": f"{''.join(map_name.split()).lower()}"}
        ):
            pt.add_row(
                [
                    entry.code,
                    fill(" ".join(entry.type), constants.TYPE_MAX_LENGTH),
                    fill(entry.desc, constants.DESC_MAX_LENGTH),
                    fill(entry.creator, constants.CREATOR_MAX_LENGTH),
                ]
            )
            row += 1
        if row:
            if ceil(row / constants.PT_PAGE_SIZE) != 1:
                s, e, split_pt = 0, constants.PT_PAGE_SIZE - 1, []
                while s < row:
                    split_pt.append(pt.get_string(start=s, end=e))
                    s += constants.PT_PAGE_SIZE
                    e += constants.PT_PAGE_SIZE
                await self.pages(
                    ctx, split_pt, ceil(row / constants.PT_PAGE_SIZE), map_name
                )
            else:
                await ctx.send(f"{map_name}\n```Page 1/1:\n{pt}```")
        else:
            await ctx.send(f"No codes for {map_name}!")

    @commands.command(
        aliases=constants.PRACTICERANGE[1:],
        help="Display all Practice Range maps. Optional argument for a single <map_type> to filter search. Use '/help maptypes' for a list of map types",
        brief="Display all Practice Range maps.",
        hidden=True,
    )
    async def practicerange(self, ctx, map_type=""):
        map_name = "Practice Range"
        if map_type:
            map_type = map_type.upper()
            if map_type not in constants.TYPES_OF_MAP:
                await ctx.send(
                    f"{map_type} not in map types. Use `/maptypes` for a list of acceptable map types."
                )
                return
        row = 0
        pt = prettytable.PrettyTable(
            field_names=["Map Code", "Map Type", "Description", "Creator"]
        )
        async for entry in MapData.find(
            {"map_name": f"{''.join(map_name.split()).lower()}", "type": map_type}
            if map_type
            else {"map_name": f"{''.join(map_name.split()).lower()}"}
        ):
            pt.add_row(
                [
                    entry.code,
                    fill(" ".join(entry.type), constants.TYPE_MAX_LENGTH),
                    fill(entry.desc, constants.DESC_MAX_LENGTH),
                    fill(entry.creator, constants.CREATOR_MAX_LENGTH),
                ]
            )
            row += 1
        if row:
            if ceil(row / constants.PT_PAGE_SIZE) != 1:
                s, e, split_pt = 0, constants.PT_PAGE_SIZE - 1, []
                while s < row:
                    split_pt.append(pt.get_string(start=s, end=e))
                    s += constants.PT_PAGE_SIZE
                    e += constants.PT_PAGE_SIZE
                await self.pages(
                    ctx, split_pt, ceil(row / constants.PT_PAGE_SIZE), map_name
                )
            else:
                await ctx.send(f"{map_name}\n```Page 1/1:\n{pt}```")
        else:
            await ctx.send(f"No codes for {map_name}!")


def setup(bot):
    bot.add_cog(MapSearch(bot))
