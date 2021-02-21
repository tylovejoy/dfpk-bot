from aiohttp import web
import asyncio
import discord
from discord.ext import commands
import aiohttp


class WebServer(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.site = None

    async def webserver(self):
        routes = web.RouteTableDef()

        @routes.post('/test')
        async def test(request):
            print('\n--- request ---\n')

            # ----------------------------------------------------------------------

            print('ARGS string:', request.query_string)  # arguments in URL as string
            print('ARGS       :', request.query)         # arguments in URL as dictionary

            # ----------------------------------------------------------------------

            # >> it can't use at the same time: `content.read()`, `text()`, `post()`, `json()`, `multiparts()`
            # >> because they all read from the same stream (not get from variable)
            # >> and after first read this stream is empty

            # ----------------------------------------------------------------------

            #print('BODY bytes :', await request.content.read())  # body as bytes  (post data as bytes, json as bytes)
            #print('BODY string:', await request.text())          # body as string (post data as string, json as string)

            # ----------------------------------------------------------------------

            #print('POST       :', await request.post())         # POST data

            # ----------------------------------------------------------------------

            #try:
            #    print('JSON:', await request.json())  # json data as dictionary/list
            #except Exception as ex:
            #    print('JSON: ERROR:', ex)

            # ----------------------------------------------------------------------

            try:
                #print('MULTIPART:', await request.multipart())  # files and forms
                reader = await request.multipart()
                print('MULTIPART:', reader)
                while True:
                    part = await reader.next()
                    if part is None:
                        break
                    print('filename:', part.filename)
                    print('>>> start <<<')
                    print(await part.text())
                    print('>>> end <<<')
            except Exception as ex:
                print('MULTIPART: ERROR:', ex)

            # ----------------------------------------------------------------------

            return web.Response(text='Testing...')

        async def handler(request):
            return web.Response(text="DFPK Bot")
        app = web.Application()
        app.router.add_get('/', handler)
        runner = web.AppRunner(app)
        await runner.setup()
        self.site = web.TCPSite(runner, '127.0.0.1', 8080)
        await self.bot.wait_until_ready()
        await self.site.start()

    def __unload(self):
        asyncio.ensure_future(self.site.stop())


def setup(bot):
    ws = WebServer(bot)
    bot.add_cog(ws)
    bot.loop.create_task(ws.webserver())
