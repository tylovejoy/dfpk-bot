import asyncio
from pathlib import Path
import discord
from discord.ext import commands
from pretty_help import PrettyHelp
import logging

# Logging setup
logging.basicConfig(level=logging.INFO)


class Bot(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(
            command_prefix=commands.when_mentioned_or(*kwargs.pop("prefix")),
            description=kwargs.pop("description"),
            intents=discord.Intents.all(),
            case_insensitive=kwargs.pop("case_insensitive"),
            help_command=PrettyHelp(show_index=False, color=discord.Color.purple()),
        )
        self.start_time = None
        self.app_info = None

        self.loop.create_task(self.load_all_extensions())

    async def load_all_extensions(self):
        await self.wait_until_ready()
        await asyncio.sleep(
            1
        )  # Ensure that on_ready has completed and finished printing
        cogs = [x.stem for x in Path("cogs").glob("*.py")]
        logging.info("Loading extensions...\n")
        for extension in cogs:
            try:
                self.load_extension(f"cogs.{extension}")
                logging.info(f"loaded {extension}")
            except Exception as e:
                error = f"{extension}\n {type(e).__name__} : {e}"
                logging.info(f"failed to load extension {error}")

    async def on_ready(self):
        """

        """
        self.app_info = await self.application_info()
        logging.info(
            f"\n\nLogged in as: {self.user.name}\n"
            f"Using discord.py version: {discord.__version__}\n"
            f"Owner: {self.app_info.owner}\n\n"
        )

    async def on_message(self, message):
        if message.author.bot:
            return  # ignore all bots
        await self.process_commands(message)
