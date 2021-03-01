import sys

from discord.ext import commands

if len(sys.argv) > 1:
    if sys.argv[1] == "test":
        from internal import test_constants as constants
else:
    from internal import constants


class MapHelp(commands.Cog, name="Helpful Map Commands"):
    """Helpful map commands/utility.

    Shows user acceptable map names and map types to use with other commands.
    """

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        """Checks if commands are used in MAP_CHANNEL and MAP_SUBMIT_CHANNEL"""
        if ctx.channel.id in (
            constants.MAP_CHANNEL_ID,
            constants.MAP_SUBMIT_CHANNEL_ID,
        ):
            return True

    @commands.command(
        help="Shows all acceptable map names for commands",
        brief="Shows map names for commands",
    )
    async def maps(self, ctx):
        """Displays acceptable map names for use in other commands"""
        post = ""
        for maps in constants.ALL_MAP_NAMES:
            post += " | ".join(maps) + "\n"
        await ctx.send(f"```Acceptable map names:\n{post}```")

    @commands.command(
        aliases=["types"],
        help="Shows all acceptable map types for commands",
        brief="Shows map types for commands",
    )
    async def maptypes(self, ctx):
        """Displays acceptable map types for use in other commands"""
        await ctx.send("Map types:\n```\n" + "\n".join(constants.TYPES_OF_MAP) + "```")


def setup(bot):
    bot.add_cog(MapHelp(bot))
