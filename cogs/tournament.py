import sys
from internal.tournament_utils import tournament_category

from discord.ext import commands

if len(sys.argv) > 1:
    if sys.argv[1] == "test":
        from internal import constants_bot_test as constants_bot
else:
    from internal import constants_bot_prod as constants_bot


class Tournament(commands.Cog, name="Tournament"):
    """Tournament"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        help="", brief="Submit times to hardcore tournament.", aliases=["hardcore"]
    )
    async def hc(self, ctx):
        pass

    @commands.Cog.listener("on_message")
    async def submit_with_image(self, message):

        if message.channel.id == constants_bot.TA_CHANNEL_ID:
            which_category = tournament_category.TA
        elif message.channel.id == constants_bot.MC_CHANNEL_ID:
            which_category = tournament_category.MC
        elif message.channel.id == constants_bot.HC_CHANNEL_ID:
            which_category = tournament_category.HC
        elif message.channel.id == constants_bot.BONUS_CHANNEL_ID:
            which_category = tournament_category.BONUS
        else:
            return




def setup(bot):
    """Add Cog to Discord bot."""
    bot.add_cog(Tournament(bot))
