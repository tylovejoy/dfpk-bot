"""
A functional demo of all possible test cases. This is the format you will want to use with your testing bot.

    Run with:
        python example_tests.py TARGET_NAME TESTER_TOKEN
"""
import asyncio
import sys
from distest import TestCollector
from distest import run_dtest_bot
from discord import Embed, Member, Status
from distest import TestInterface

# The tests themselves

test_collector = TestCollector()
created_channel = None


@test_collector()
async def test_submitpb(interface):
    await interface.assert_reply_equals("/submitpb 1 1", "")



# Actually run the bot

if __name__ == "__main__":
    run_dtest_bot(sys.argv, test_collector)








