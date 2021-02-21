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



def setup(bot):
    bot.add_cog(MapSearch(bot))
