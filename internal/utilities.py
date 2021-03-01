import datetime
import re


def is_english(s):
    return s.isascii()


time_regex = re.compile(r"(?<!.)(\d{1,2})?:?(\d{2})?:?(?<!\d)(\d{1,2})\.?\d{1,2}?(?!.)")


def is_time_format(s):
    return bool(time_regex.match(s))


def date_func(s):
    if s.count(":") == 0 and s.count(".") == 0:
        return datetime.datetime.strptime(s, "%S").time()
    elif s.count(":") == 0 and s.count(".") == 1:
        return datetime.datetime.strptime(s, "%S.%f").time()
    elif s.count(":") == 1 and s.count(".") == 1:
        return datetime.datetime.strptime(s, "%M:%S.%f").time()
    elif s.count(":") == 1 and s.count(".") == 0:
        return datetime.datetime.strptime(s, "%M:%S").time()
    elif s.count(":") == 2 and s.count(".") == 1:
        return datetime.datetime.strptime(s, "%H:%M:%S.%f").time()
    elif s.count(":") == 2 and s.count(".") == 0:
        return datetime.datetime.strptime(s, "%H:%M:%S").time()
    return


def time_convert(time_input):
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
    if str(datetime.timedelta(seconds=record)).count(".") == 1:
        return str(datetime.timedelta(seconds=record))[: -4 or None]
    else:
        return str(datetime.timedelta(seconds=record)) + ".00"


def convert_short_types(map_type):
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
    else:
        return map_type
