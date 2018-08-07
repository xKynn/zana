import aiohttp
import json

from datetime import datetime
from discord.ext import commands
from pathlib import Path
from utils.custom_context import ZanaContext
from utils.server_config import ServerConfig

class Zana(commands.Bot):
    def __init__(self, *args, **kwargs):
        self.description = 'To be continued'

        # Configs & token
        with open('config.json') as f:
            self.config = json.load(f)


        # TODO:
        # - Dynamic prefixes (per guild)
        # - Migrate help command from Watashi
        super().__init__(command_prefix=commands.when_mentioned, description=self.description,
                         pm_help=None, *args, **kwargs)

        # Startup extensions (none yet)
        self.startup_ext = [x.stem for x in Path('cogs').glob('*.py')]

        # aiohttp session
        self.session = aiohttp.ClientSession(loop=self.loop)

        # Make room for the help command
        self.remove_command('help')

        # Embed color
        # Keeping with user_color convention to make migration from Watashi easier
        self.user_color = 0x781D1D

        self.server_config = ServerConfig('server_config.json')
        print(self.server_config.conf)

    def run(self):
        super().run(self.config['token'])

    # Utilise custom context for error messaging etc.
    async def on_message(self, message):
        if message.author.id == self.user.id:
            return
        await self.wait_until_ready()
        ctx = await self.get_context(message, cls=ZanaContext)
        if '[[' in ctx.message.content and ']]' in ctx.message.content:
            await self.find_command.invoke(ctx)
        elif 'pastebin.com/' in ctx.message.content:
            await self.pob_command.invoke(ctx)
        else:
            await self.invoke(ctx)

    async def on_ready(self):
        if not hasattr(self, 'start_time'):
            self.start_time = datetime.now()

        for ext in self.startup_ext:
            try:
                self.load_extension(f'cogs.{ext}')
            except Exception as e:
                print(f'Failed to load extension: {ext}\n{e}')
            else:
                print(f'Loaded extension: {ext}')
        self.find_command = self.get_command('link')
        self.pob_command = self.get_command('pob')
        self.dump_channel = self.get_channel(475526519255728128)
        self.ses = aiohttp.ClientSession()
        print(f'Client logged in at {self.start_time}.\n'
              f'{self.user.name}\n'
              f'{self.user.id}\n'
              '--------------------------')
