import sys

import discord
from discord.ext import commands

from database.MapData import MapData
from internal import confirmation, utilities

if len(sys.argv) > 1:
    if sys.argv[1] == "test":
        from internal import test_constants as constants
else:
    from internal import constants


class SubmitMap(commands.Cog, name="Map submission/deletion"):
    """Commands to submit and delete maps."""

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        """Checks if command is used in MAP_SUBMIT_CHANNEL"""
        if ctx.channel.id == constants.MAP_SUBMIT_CHANNEL_ID:
            return True

    @commands.command(
        help=(
            "Submit map code with optional description.\n\n"
            "If multiple entries for <creator> OR <map_type>, wrap both in a single set of quotation marks!\n\n"  # noqa: E501
            'Example: "name1 & name2" OR "pioneer hardcore"\n\n'
            f"<type> can be {' | '.join(constants.TYPES_OF_MAP)}\n\n"
            "[desc] is optional, no need to wrap in quotation marks. Use this to add # of levels, checkpoints, etc."
        ),
        brief="Submit map code",
    )
    async def submitmap(self, ctx, map_code, map_name, map_type, creator, *, desc=""):
        """Submits a map to database.

        Args:
            ctx: bot Context
            map_code (str):
            map_name (str):
            map_type (str):
            creator (str):
            desc (str):

        Returns:

        """
        # A hack to avoid mongoDB injection...
        # TODO: Proper sanitization
        if (
            "$" in map_code
            or "$" in map_name
            or "$" in map_type
            or "$" in creator
            or "$" in desc
        ):
            map_code.replace("$", "")
            map_name.replace("$", "")
            map_type.replace("$", "")
            creator.replace("$", "")
            desc.replace("$", "")
        # Checks for a-zA-Z0-9 in map_code
        # TODO: Change to regex?
        for x in map_code:
            if (
                x
                not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
            ):
                await ctx.send(
                    "Only letters A-Z and numbers 0-9 allowed in <map_code>. Map submission rejected."
                )
                return
        map_name = map_name.lower()
        if not utilities.map_name_converter(map_name):
            await ctx.send(
                "<map_name> doesn't exist! Map submission rejected. Use `/maps` for a list of acceptable maps."
            )
            return

        # Splits submitted map_types into a list, converts shortened versions
        # Example:
        #          multi -> multilevel
        #          pio   -> pioneer
        map_type = [utilities.convert_short_types(x.upper()) for x in map_type.split()]

        # Checks map_type(s) exists
        for x in map_type:
            if x not in constants.TYPES_OF_MAP:
                await ctx.send(
                    "<map_type> doesn't exist! Map submission rejected. Use `/maptypes` for a list of acceptable map types."
                )
                return

        map_code = map_code.upper()
        count = await MapData.count_documents({"code": map_code})

        # Create submission, if none exists.
        if count == 0:
            new_map_name = utilities.map_name_converter(map_name)
            submission = MapData(
                **dict(
                    code=map_code,
                    creator=creator,
                    map_name=new_map_name,
                    desc=desc,
                    posted_by=ctx.author.id,
                    type=map_type,
                )
            )
            embed = discord.Embed(title="Is this submission correct?")

            embed.add_field(
                name=f"{submission.code}",
                value=(
                    f"> Map: {constants.PRETTY_NAMES[submission.map_name]}\n"
                    f"> Creator: {submission.creator}\n"
                    f"> Map Types: {' '.join(submission.type)}\n"
                    f"> Description: {submission.desc}"
                ),
                inline=False,
            )
            msg = await ctx.send(embed=embed)
            confirmed = await confirmation.confirm(ctx, msg)

            # User confirmation with reactions
            if confirmed is True:
                await msg.edit(
                    content=f"{constants.CONFIRM_REACTION_EMOJI} Confirmed! Map submission accepted."
                )
                await submission.commit()
            elif confirmed is False:
                await msg.edit(
                    content=f"{constants.CANCEL_REACTION_EMOJI} Map submission rejected."
                )
            elif confirmed is None:
                await msg.edit(
                    content=f"Submission timed out! Map submission rejected."
                )

        else:
            await ctx.send(f"{map_code} already exists! Map submission rejected.")

    # Delete map code
    @commands.command(
        help="Delete map code\nOnly original posters and mods can delete a map code.",
        brief="Delete map code",
    )
    async def deletemap(self, ctx, map_code):
        """Deletes a specific map_code."""
        map_code = map_code.upper()

        # If exists
        if await MapData.count_documents({"code": map_code}) == 1:
            search = await MapData.find_one({"code": map_code})
            # Only allow original poster OR whitelisted roles to delete.
            if search.posted_by == ctx.author.id or bool(
                any(role.id in constants.ROLE_WHITELIST for role in ctx.author.roles)
            ):
                embed = discord.Embed(title="Do you want to delete this?")
                embed.add_field(
                    name=f"{search.code}",
                    value=(
                        f"> Map: {constants.PRETTY_NAMES[search.map_name]}\n"
                        f"> Creator: {search.creator}\n"
                        f"> Map Types: {' '.join(search.type)}\n"
                        f"> Description: {search.desc}"
                    ),
                    inline=False,
                )

                msg = await ctx.send(embed=embed)
                confirmed = await confirmation.confirm(ctx, msg)

                # User confirmation using reactions
                if confirmed is True:
                    await msg.edit(content=f"{search.code} has been deleted.")
                    await search.delete()
                elif confirmed is False:
                    await msg.edit(content=f"{search.code} has not been deleted.")
                elif confirmed is None:
                    await msg.edit(
                        content=f"Submission timed out! {search.code} has not been deleted."
                    )
            else:
                await ctx.channel.send(
                    "You do not have sufficient permissions. Map was not deleted."
                )
        else:
            await ctx.channel.send(f"{map_code} does not exist.")

    @commands.command(
        help="Edit description for a certain map code. <desc> will overwrite current description.\nOnly original posters and mods can edit a map code.",
        brief="Edit description for a certain map code",
    )
    async def editdesc(self, ctx, map_code, *, desc):
        """Edits a specific map_code's description."""
        # TODO: Proper sanitization
        if "$" in map_code or "$" in desc:
            map_code.replace("$", "")
            desc.replace("$", "")

        map_code = map_code.upper()

        if await MapData.count_documents({"code": map_code}) == 1:
            search = await MapData.find_one({"code": map_code})

            # Only allow original poster OR whitelisted roles to delete.
            if search.posted_by == ctx.author.id or bool(
                any(role.id in constants.ROLE_WHITELIST for role in ctx.author.roles)
            ):
                search.desc = desc
                embed = discord.Embed(title="Is this submission correct?")

                embed.add_field(
                    name=f"{search.code}",
                    value=(
                        f"> Map: {constants.PRETTY_NAMES[search.map_name]}\n"
                        f"> Creator: {search.creator}\n"
                        f"> Map Types: {' '.join(search.type)}\n"
                        f"> Description: {search.desc}"
                    ),
                    inline=False,
                )

                msg = await ctx.send(embed=embed)
                confirmed = await confirmation.confirm(ctx, msg)

                if confirmed is True:
                    await msg.edit(content=f"{search.code} has been edited.")
                    await search.commit()
                elif confirmed is False:
                    await msg.edit(content=f"{search.code} has not been edited.")
                elif confirmed is None:
                    await msg.edit(
                        content=f"Submission timed out! {search.code} has not been edited."
                    )
                await msg.clear_reactions()

    @commands.command(
        help="Edit map types for a certain map code.\n<map_type> will overwrite current map types.\nOnly original posters and mods can edit a map code.",
        brief="Edit map types for a certain map code",
    )
    async def edittypes(self, ctx, map_code, *, map_type):
        """Edits a specific map_code's map_types."""
        # TODO: Proper sanitization
        if "$" in map_code or "$" in map_type:
            map_code.replace("$", "")
            map_type.replace("$", "")

        map_code = map_code.upper()
        map_type = [utilities.convert_short_types(x.upper()) for x in map_type.split()]

        for x in map_type:
            if x not in constants.TYPES_OF_MAP:
                await ctx.send(
                    "<map_type> doesn't exist! Map submission rejected. Use `/maptypes` for a list of acceptable map types."
                )
                return

        if await MapData.count_documents({"code": map_code}) == 1:
            search = await MapData.find_one({"code": map_code})

            # Only allow original poster OR whitelisted roles to delete.
            if search.posted_by == ctx.author.id or bool(
                any(role.id in constants.ROLE_WHITELIST for role in ctx.author.roles)
            ):
                search.type = map_type
                embed = discord.Embed(title="Is this submission correct?")

                embed.add_field(
                    name=f"{search.code}",
                    value=(
                        f"> Map: {constants.PRETTY_NAMES[search.map_name]}\n"
                        f"> Creator: {search.creator}\n"
                        f"> Map Types: {' '.join(search.type)}\n"
                        f"> Description: {search.desc}"
                    ),
                    inline=False,
                )

                msg = await ctx.send(embed=embed)
                confirmed = await confirmation.confirm(ctx, msg)

                if confirmed is True:
                    await msg.edit(content=f"{search.code} has been edited.")
                    await search.commit()
                elif confirmed is False:
                    await msg.edit(content=f"{search.code} has not been edited.")
                elif confirmed is None:
                    await msg.edit(
                        content=f"Submission timed out! {search.code} has not been edited."
                    )
                await msg.clear_reactions()

    @commands.command(
        help="Edit the map code for a certain map code.\nOnly original posters and mods can edit a map code.",
        brief="Edit the map code for a certain map code",
    )
    async def editcode(self, ctx, map_code, new_map_code):
        """Edits a specific map_code's map_code."""
        # TODO: Proper sanitization
        if "$" in map_code or "$" in new_map_code:
            map_code.replace("$", "")
            new_map_code.replace("$", "")

        map_code = map_code.upper()
        new_map_code = new_map_code.upper()

        if await MapData.count_documents({"code": map_code}) == 1:
            search = await MapData.find_one({"code": map_code})

            # Only allow original poster OR whitelisted roles to delete.
            if search.posted_by == ctx.author.id or bool(
                any(role.id in constants.ROLE_WHITELIST for role in ctx.author.roles)
            ):
                search.code = new_map_code
                embed = discord.Embed(title="Is this submission correct?")

                embed.add_field(
                    name=f"{search.code}",
                    value=(
                        f"> Map: {constants.PRETTY_NAMES[search.map_name]}\n"
                        f"> Creator: {search.creator}\n"
                        f"> Map Types: {' '.join(search.type)}\n"
                        f"> Description: {search.desc}"
                    ),
                    inline=False,
                )

                msg = await ctx.send(embed=embed)
                confirmed = await confirmation.confirm(ctx, msg)

                if confirmed is True:
                    await msg.edit(content=f"{search.code} has been edited.")
                    await search.commit()
                elif confirmed is False:
                    await msg.edit(content=f"{search.code} has not been edited.")
                elif confirmed is None:
                    await msg.edit(
                        content=f"Submission timed out! {search.code} has not been edited."
                    )
                await msg.clear_reactions()


def setup(bot):
    bot.add_cog(SubmitMap(bot))
