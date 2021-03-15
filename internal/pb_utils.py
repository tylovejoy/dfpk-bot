import datetime
import re

import discord

import internal.constants as constants
from database.WorldRecords import WorldRecords


async def boards(ctx, map_code, level, title, query):
    """Display boards for scoreboard and leaderboard commands."""
    count = 1
    exists = False
    embed = discord.Embed(title=f"{title}")
    async for entry in WorldRecords.find(query).sort("record", 1).limit(10):
        exists = True
        embed.add_field(
            name=f"#{count} - {entry.name}",
            value=(
                f"> Record: {display_record(entry.record)}\n"
                f"> Verified: {constants.VERIFIED_EMOJI if entry.verified is True else constants.NOT_VERIFIED_EMOJI}"
            ),
            inline=False,
        )
        count += 1
    if exists:
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"No scoreboard for {map_code} level {level.upper()}!")


def is_time_format(s):
    """Check if string is in HH:MM:SS.SS format or a legal variation."""
    return bool(
        re.compile(
            r"(?<!.)(\d{1,2})?:?(\d{2})?:?(?<!\d)(\d{1,2})\.?\d{1,2}?(?!.)"
        ).match(s)
    )


def time_convert(time_input):
    """Convert time (str) into seconds (float)."""
    time_list = time_input.split(":")
    if len(time_list) == 1:
        return float(time_list[0])
    elif len(time_list) == 2:
        return float((int(time_list[0]) * 60) + float(time_list[1]))
    elif len(time_list) == 3:
        return float(
            (int(time_list[0]) * 3600) + (int(time_list[1]) * 60) + float(time_list[2])
        )
    return


def display_record(record):
    """Display record in HH:MM:SS.SS format."""
    if check_negative(record):
        return format_timedelta(record)
    elif str(datetime.timedelta(seconds=record)).count(".") == 1:
        return str(datetime.timedelta(seconds=record))[: -4 or None]
    return str(datetime.timedelta(seconds=record)) + ".00"


def check_negative(s):
    try:
        f = float(s)
        if f < 0:
            return True
        # Otherwise return false
        return False
    except ValueError:
        return False


def format_timedelta(td):
    if datetime.timedelta(seconds=td) < datetime.timedelta(0):
        return '-' + format_timedelta(-td)
    else:
        return str(td)
