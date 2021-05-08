import sys

from enum import Enum

if len(sys.argv) > 1:
    if sys.argv[1] == "test":
        from internal import constants_bot_test as constants_bot
else:
    from internal import constants_bot_prod as constants_bot


class TournamentCategory(Enum):
    HC = "HC"
    TA = "TA"
    MC = "MC"
    BONUS = "BONUS"


def category_sort(message):
    if message.channel.id == constants_bot.TA_CHANNEL_ID:
        which_category = TournamentCategory.TA
    elif message.channel.id == constants_bot.MC_CHANNEL_ID:
        which_category = TournamentCategory.MC
    elif message.channel.id == constants_bot.HC_CHANNEL_ID:
        which_category = TournamentCategory.HC
    elif message.channel.id == constants_bot.BONUS_CHANNEL_ID:
        which_category = TournamentCategory.BONUS
    else:
        return None
    return which_category
