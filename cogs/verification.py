import logging
import sys

from discord.ext import commands

import internal.constants as constants
import internal.pb_utils
from database.WorldRecords import WorldRecords

if len(sys.argv) > 1:
    if sys.argv[1] == "test":
        from internal import constants_bot_test as constants_bot
else:
    from internal import constants_bot_prod as constants_bot


class Verification(commands.Cog, name="Verification"):
    """Listeners to delete or verify personal bests."""

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        """Check if channel is RECORD_CHANNEL."""
        if ctx.channel.id == constants_bot.RECORD_CHANNEL_ID:
            return True

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload=None):
        """Listen for verification reaction from moderators."""
        if payload.user_id == constants_bot.BOT_ID:
            return
        if not bool(
            any(
                role.id in constants_bot.ROLE_WHITELIST for role in payload.member.roles
            )
        ):
            return
        if payload is not None:
            search = await WorldRecords.find_one({"message_id": payload.message_id})
            if search is not None and payload.message_id == search.message_id:
                guild = self.bot.get_guild(payload.guild_id)
                channel = guild.get_channel(payload.channel_id)
                msg = await channel.fetch_message(payload.message_id)
                hidden_channel = guild.get_channel(
                    constants_bot.HIDDEN_VERIFICATION_CHANNEL
                )
                try:
                    hidden_msg = await hidden_channel.fetch_message(search.hidden_id)
                    await hidden_msg.delete()
                except:
                    pass
                finally:
                    try:
                        if str(payload.emoji) == constants.VERIFIED_EMOJI:
                            search.verified = True
                            await search.commit()
                            await msg.author.send(
                                f"Your submission has been verified by {payload.member.name}!\n```Map Code: {search.code}{constants.NEW_LINE}Level: {search.level}{constants.NEW_LINE}Record: {internal.pb_utils.display_record(search.record)}```{msg.jump_url}"
                            )

                        elif str(payload.emoji) == constants.NOT_VERIFIED_EMOJI:
                            search.verified = False
                            await search.commit()
                            await msg.author.send(
                                f"{payload.member.name} has rejected your submission and is not verified!\n```Map Code: {search.code}{constants.NEW_LINE}Level: {search.level}{constants.NEW_LINE}Record: {internal.pb_utils.display_record(search.record)}```{msg.jump_url}"
                            )
                    except:
                        pass
                    finally:
                        await msg.clear_reactions()

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload=None):
        """Listen for deleted messages.

        If a deleted message was a personal best,
        the record is deleted from the database.
        """
        if payload is not None:
            search = await WorldRecords.find_one({"message_id": payload.message_id})
            if search is not None:
                channel = self.bot.get_channel(
                    constants_bot.HIDDEN_VERIFICATION_CHANNEL
                )
                try:
                    hidden_msg = await channel.fetch_message(search.hidden_id)
                    if hidden_msg:
                        await hidden_msg.delete()
                except:
                    pass
                finally:

                    await search.delete()


def setup(bot):
    """Add Cog to Discord bot."""
    bot.add_cog(Verification(bot))
