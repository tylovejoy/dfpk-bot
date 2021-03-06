import asyncio
import re
import sys

import discord
import pymongo
from discord.ext import commands

from database.MapData import MapData
from internal import utilities, test_constants, constants
from disputils import BotEmbedPaginator, BotConfirmation, BotMultipleChoice

if len(sys.argv) > 1:
    if sys.argv[1] == "test":
        from internal import test_constants as constants
else:
    from internal import constants


async def searchmap(
    ctx, query: dict, map_type="", map_name="", creator="", map_code=""
):
    """Search database for query and displays it.

    Args:
        ctx (:obj: `commands.Context`)
        query (dict): Query for database
        map_type (str, optional): Type of map to search
        map_name (str, optional): Name of map to seach
        creator (str, optional): Creator of map to search
        map_code (str, optional): Map code to search

    Returns:
        None

    """
    # Checks for map_type, if exists
    if map_type:
        if map_type not in constants.TYPES_OF_MAP:
            await ctx.send(
                f"{map_type} not in map types. Use `/maptypes` for a list of acceptable map types."
            )
            return

    # init vars
    row, embeds = 0, []

    embed = discord.Embed(title=map_name or creator or map_code or map_type)
    count = await MapData.count_documents(query)

    async for entry in MapData.find(query).sort([("map_name", pymongo.ASCENDING)]):

        # Every 10th embed field, create a embed obj and add to a list
        if row != 0 and (row % 10 == 0 or count - 1 == row):

            embed.add_field(
                name=f"{entry.code} - {constants.PRETTY_NAMES[entry.map_name]}",
                value=f"> Creator: {entry.creator}\n> Map Types: {', '.join(entry.type)}\n> Description: {entry.desc}",
                inline=False,
            )
            embeds.append(embed)
            embed = discord.Embed(title=map_name or creator or map_code or map_type)

        # Create embed fields for fields 1 thru 9
        elif row % 10 != 0 or row == 0:
            embed.add_field(
                name=f"{entry.code} - {constants.PRETTY_NAMES[entry.map_name]}",
                value=f"> Creator: {entry.creator}\n> Map Types: {', '.join(entry.type)}\n> Description: {entry.desc}",
                inline=False,
            )

        # If only one page
        if count == 1:
            embeds.append(embed)
        row += 1

    # Displays paginated embeds
    if row:
        paginator = BotEmbedPaginator(ctx, embeds)
        await paginator.run()

    else:
        await ctx.send(
            f"Nothing exists for {map_name or creator or map_code or map_type}!"
        )


def normal_map_query(map_name, map_type=""):
    """Create a query string for map search commands.

    Args:
        map_name: The map name a user is searching for.
        map_type: The map type a user is searching for.

    Returns:
        dict: query for map search command, depending on if map_type is given.

    """
    apostrophe = "'"
    if map_type:
        return {
            "map_name": f"{''.join(map_name.split()).lower().replace(apostrophe, '').replace(':', '')}",
            "type": map_type.upper(),
        }
    return {
        "map_name": f"{''.join(map_name.split()).lower().replace(apostrophe, '').replace(':', '')}"
    }


async def map_submit_embed(document, title):
    embed = discord.Embed(title=title)
    embed.add_field(
        name=f"{document.code}",
        value=(
            f"> Map: {constants.PRETTY_NAMES[document.map_name]}\n"
            f"> Creator: {document.creator}\n"
            f"> Map Types: {' '.join(document.type)}\n"
            f"> Description: {document.desc}"
        ),
        inline=False,
    )
    return embed


async def map_edit_confirmation(confirmed, msg, document):
    if confirmed is True:
        await msg.edit(content=f"{document.code} has been edited.")
        await document.commit()
    elif confirmed is False:
        await msg.edit(content=f"{document.code} has not been edited.")
    elif confirmed is None:
        await msg.edit(
            content=f"Submission timed out! {document.code} has not been edited."
        )
    await msg.clear_reactions()


async def map_edit_checks(ctx, map_code, search) -> int:
    """User input validation. Display error to user.

    Returns:
        (int): if arguments do not pass checks return 0, else 1
    """
    if not search:
        await ctx.channel.send(f"{map_code} does not exist.")
        return 0
    # Only allow original poster OR whitelisted roles to delete.
    if search.posted_by != ctx.author.id or not bool(
        any(role.id in constants.ROLE_WHITELIST for role in ctx.author.roles)
    ):
        await ctx.channel.send(
            "You do not have sufficient permissions. Map was not deleted."
        )
        return 0
    return 1
