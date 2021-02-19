from discord.ext import commands

from internal import constants


class MapHelp(commands.Cog, name="Helpful Map Commands"):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        if (
            ctx.channel.id == constants.MAP_CHANNEL_ID
            or ctx.channel.id == constants.MAP_SUBMIT_CHANNEL_ID
        ):
            return True

    """
    Display maps / map types
    """

    @commands.command(
        help="Shows all acceptable map names for commands",
        brief="Shows map names for commands",
    )
    async def maps(self, ctx):
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
        await ctx.send("Map types:\n```" + "\n".join(constants.TYPES_OF_MAP) + "```")


def setup(bot):
    bot.add_cog(MapHelp(bot))
