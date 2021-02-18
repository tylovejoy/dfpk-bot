import discord
from discord.ext import commands
import asyncio
from internal import constants, utilities, confirmation
from database.WorldRecords import WorldRecords
from mongosanitizer.sanitizer import sanitize
import prettytable
import datetime
import logging


class Verification(commands.Cog, name="Verification"):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        if ctx.channel.id == constants.RECORD_CHANNEL_ID:
            return True

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload=None):
        if payload.user_id == constants.BOT_ID:
            return
        if not (True if any(role.id in constants.ROLE_WHITELIST for role in payload.member.roles) else False):
            return
        if payload is not None:
            search = await WorldRecords.find_one({"message_id": payload.message_id})
            if search is not None and payload.message_id == search.message_id:
                guild = self.bot.get_guild(payload.guild_id)
                channel = guild.get_channel(payload.channel_id)
                msg = await channel.fetch_message(payload.message_id)
                hidden_channel = guild.get_channel(constants.HIDDEN_VERIFICATION_CHANNEL)
                hidden_msg = await hidden_channel.fetch_message(search.hidden_id)
                await hidden_msg.delete()
                if str(payload.emoji) == constants.VERIFIED_EMOJI:
                    search.verified = True
                    await search.commit()
                    await msg.author.send(f'Your submission has been verified by {payload.member.name}!\n```Map Code: {search.code}{constants.NEW_LINE}Level: {search.level}{constants.NEW_LINE}Record: {utilities.display_record(search.record)}```{msg.jump_url}')

                elif str(payload.emoji) == constants.NOT_VERIFIED_EMOJI:
                    search.verified = False
                    await search.commit()
                    await msg.author.send(f'{payload.member.name} has rejected your submission and is not verified!\n```Map Code: {search.code}{constants.NEW_LINE}Level: {search.level}{constants.NEW_LINE}Record: {utilities.display_record(search.record)}```{msg.jump_url}')

                await msg.clear_reactions()

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload=None):
        if payload is not None:
            search = await WorldRecords.find_one({"message_id": payload.message_id})
            if search is not None:
                channel = self.bot.get_channel(constants.HIDDEN_VERIFICATION_CHANNEL)
                try:
                    hidden_msg = await channel.fetch_message(search.hidden_id)
                    if hidden_msg:
                        await hidden_msg.delete()
                except:
                    pass
                finally:

                    await search.delete()


def setup(bot):
    bot.add_cog(Verification(bot))
