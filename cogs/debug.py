from discord.ext import commands
from jishaku.cog import JishakuBase, jsk
from jishaku.metacog import GroupCogMeta


class Debugging(JishakuBase, metaclass=GroupCogMeta, command_parent=jsk):
    pass


def setup(bot: commands.Bot):
    bot.add_cog(Debugging(bot))
