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

    async def report(self, msg):
        await self.owner.send(f"Error, context: `{msg}`")

    # 'on_message' bot what a n00b omg
    # Only way to link items or provide pob without people requesting it as i wanted this to be a conversation based bot
    async def on_message(self, message):
        if message.author.id == self.user.id:
            return
        await self.wait_until_ready()
        ctx = await self.get_context(message, cls=ZanaContext)
        if '[[' in ctx.message.content and ']]' in ctx.message.content:
            if 1:
                async with message.channel.typing():
                    await self.find_command.invoke(ctx)
            else:
                await ctx.error("There was an error with your request.")
                await self.report(ctx.message.content)
        elif 'pastebin.com/' in ctx.message.content:
            if str(ctx.guild.id) in self.server_config.conf and 'disable_pastebin' in self.server_config.conf[str(ctx.guild.id)] \
                    and self.server_config.conf[str(ctx.guild.id)]['disable_pastebin']:
                return
            if 1:
                await message.channel.trigger_typing()
                await self.pob_command.invoke(ctx)
            else:
                await ctx.error("There was an error with parsing your pastebin.")
                await self.report(ctx.message.content)
        elif ctx.message.content.startswith("Rarity:"):
            try:
                if str(ctx.guild.id) in self.server_config.conf and 'convert' in self.server_config.conf[str(ctx.guild.id)] and \
                        self.server_config.conf[str(ctx.guild.id)]['convert']:
                    return
                async with message.channel.typing():
                    res = await self.convert_command.invoke(ctx)
                try:
                    if res:
                        await ctx.message.delete()
                except:
                    #Funny thing is, error is an embed, if someone removes that perm,
                    #the error doesn't go through as well
                    await ctx.error("`Manage Messages` required to delete", delete_after=2)
            except:
                await self.report(ctx.message.content)
        else:
            await self.invoke(ctx)

    async def on_ready(self):

        for ext in self.startup_ext:
            try:
                self.load_extension(f'cogs.{ext}')
            except Exception as e:
                print(f'Failed to load extension: {ext}\n{e}')
            else:
                print(f'Loaded extension: {ext}')

        # Gather all commands on_message is going to need
        self.find_command = self.get_command('link')
        self.pob_command = self.get_command('pob')
        self.convert_command = self.get_command('convert')

        # Dump channel where i can upload 10 images at once, get url and serve in embeds freely as i'd like to
        self.dump_channel = self.get_channel(475526519255728128)
        self.ses = aiohttp.ClientSession()
        c = await self.application_info()
        self.owner = c.owner
        print(f'Client logged in.\n'
              f'{self.user.name}\n'
              f'{self.user.id}\n'
              '--------------------------')
