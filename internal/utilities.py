import datetime
import re

from internal import constants


def is_time_format(s):
    """Check if string is in HH:MM:SS.SS format or a legal variation."""
    return bool(re.compile(r"(?<!.)(\d{1,2})?:?(\d{2})?:?(?<!\d)(\d{1,2})\.?\d{1,2}?(?!.)").match(s))


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
    if str(datetime.timedelta(seconds=record)).count(".") == 1:
        return str(datetime.timedelta(seconds=record))[: -4 or None]
    return str(datetime.timedelta(seconds=record)) + ".00"


def convert_short_types(map_type):
    """Convert user inputted map_type to proper map_type if using abbreviation."""
    if map_type in ["MULTI", "MULTILVL", "MULTILEVEL"]:
        return "MULTILEVEL"
    elif map_type in ["PIO", "PIONEER"]:
        return "PIONEER"
    elif map_type in ["HC", "HARDCORE"]:
        return "HARDCORE"
    elif map_type in ["MC", "MILDCORE"]:
        return "MILDCORE"
    elif map_type in ["TA", "TIMEATTACK", "TIME-ATTACK"]:
        return "TIME-ATTACK"
    return map_type


def map_name_converter(map_name):
    """Convert variations of map_name to proper map_name for database."""
    for i in range(len(constants.ALL_MAP_NAMES)):
        if map_name in constants.ALL_MAP_NAMES[i]:
            return constants.ALL_MAP_NAMES[i][0]
    return
