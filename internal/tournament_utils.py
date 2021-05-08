import sys


if len(sys.argv) > 1:
    if sys.argv[1] == "test":
        from internal import constants_bot_test as constants_bot
else:
    from internal import constants_bot_prod as constants_bot


def category_sort(message):
    if message.channel.id == constants_bot.TA_CHANNEL_ID:
        which_category = "TIMEATTACK"
    elif message.channel.id == constants_bot.MC_CHANNEL_ID:
        which_category = "MILDCORE"
    elif message.channel.id == constants_bot.HC_CHANNEL_ID:
        which_category = "HARDCORE"
    elif message.channel.id == constants_bot.BONUS_CHANNEL_ID:
        which_category = "BONUS"
    else:
        return None
    return which_category
