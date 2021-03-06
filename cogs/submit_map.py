import re
import sys

from discord.ext import commands

from database.MapData import MapData
from internal import confirmation, utilities
from internal.map_utils import map_submit_embed, map_edit_confirmation, map_edit_checks

if len(sys.argv) > 1:
    if sys.argv[1] == "test":
        from internal import test_constants as constants
else:
    from internal import constants


class SubmitMap(commands.Cog, name="Map submission/deletion/editing"):
    """Commands to submit, delete, and edit maps."""

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        """Check if command is used in MAP_SUBMIT_CHANNEL."""
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
        """Submit a map to database."""

        if not re.match(r"^[a-zA-Z0-9]+$", map_code):
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

        # map_code must be unique.
        if count != 0:
            await ctx.send(f"{map_code} already exists! Map submission rejected.")
            return

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

        embed = await map_submit_embed(submission, "Is this submission correct?")

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
            await msg.edit(content="Submission timed out! Map submission rejected.")

    @commands.command(
        help="Delete map code\nOnly original posters and mods can delete a map code.",
        brief="Delete map code",
    )
    async def deletemap(self, ctx, map_code):
        """Delete a specific map_code."""

        map_code = map_code.upper()

        search = await MapData.find_one({"code": map_code})

        if await map_edit_checks(ctx, map_code, search) == 0:
            return

        embed = await map_submit_embed(search, "Do you want to delete this?")

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

    @commands.command(
        help="Edit description for a certain map code. <desc> will overwrite current description.\nOnly original posters and mods can edit a map code.",
        brief="Edit description for a certain map code",
    )
    async def editdesc(self, ctx, map_code, *, desc):
        """Edit a specific map_code's description."""

        map_code = map_code.upper()

        search = await MapData.find_one({"code": map_code})

        if await map_edit_checks(ctx, map_code, search) == 0:
            return

        search.desc = desc

        embed = await map_submit_embed(search, "Is this submission correct?")

        msg = await ctx.send(embed=embed)
        confirmed = await confirmation.confirm(ctx, msg)

        await map_edit_confirmation(confirmed, msg, search)

    @commands.command(
        help="Edit map types for a certain map code.\n<map_type> will overwrite current map types.\nOnly original posters and mods can edit a map code.",
        brief="Edit map types for a certain map code",
    )
    async def edittypes(self, ctx, map_code, *, map_type):
        """Edit a specific map_code's map_types."""

        map_code = map_code.upper()

        search = await MapData.find_one({"code": map_code})

        if await map_edit_checks(ctx, map_code, search) == 0:
            return

        map_type = [utilities.convert_short_types(x.upper()) for x in map_type.split()]

        for x in map_type:
            if x not in constants.TYPES_OF_MAP:
                await ctx.send(
                    "<map_type> doesn't exist! Map submission rejected. Use `/maptypes` for a list of acceptable map types."
                )
                return

        search.type = map_type

        embed = await map_submit_embed(search, "Is this submission correct?")

        msg = await ctx.send(embed=embed)
        confirmed = await confirmation.confirm(ctx, msg)

        await map_edit_confirmation(confirmed, msg, search)

    @commands.command(
        help="Edit the map code for a certain map code.\nOnly original posters and mods can edit a map code.",
        brief="Edit the map code for a certain map code",
    )
    async def editcode(self, ctx, map_code, new_map_code):
        """Edit a specific map_code's map_code."""

        map_code = map_code.upper()
        new_map_code = new_map_code.upper()

        if not re.match(r"^[a-zA-Z0-9]+$", new_map_code):
            await ctx.send(
                "Only letters A-Z and numbers 0-9 allowed in <map_code>. Map submission rejected."
            )
            return

        search = await MapData.find_one({"code": map_code})

        search.code = new_map_code

        embed = await map_submit_embed(search, "Is this submission correct?")

        msg = await ctx.send(embed=embed)
        confirmed = await confirmation.confirm(ctx, msg)

        await map_edit_confirmation(confirmed, msg, search)


def setup(bot):
    """Add Cog to Discord bot."""
    bot.add_cog(SubmitMap(bot))
