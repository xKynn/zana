import aiohttp
import json
import os

from discord import Game
from discord.ext import commands
from pathlib import Path
from utils.custom_context import ZanaContext
from utils.server_config import ServerConfig
from poe.exceptions import OutdatedPoBException
from poe.exceptions import AbsentItemBaseException


class Zana(commands.AutoShardedBot):
    def __init__(self, *args, **kwargs):
        self.description = 'To be continued'

        # Configs & toke
        # if a bot token is define in docker then use that else fallback to config.json
        if "BOT_TOKEN" in os.environ:
            bot_token = os.getenv("BOT_TOKEN")
        else:
            with open('config.json') as file:
                self.config = json.load(file)

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
            try:
                async with message.channel.typing():
                    await self.find_command.invoke(ctx)
            except:
            #except Exception:
                await ctx.error("There was an error with your request.")
                await self.report(ctx.message.content)
        elif 'pastebin.com/' in ctx.message.content or "pob.party/share/" in ctx.message.content:
            if str(ctx.guild.id) in self.server_config.conf and \
                    self.server_config.conf[str(ctx.guild.id)].get('disable_pastebin'):
                return
            try:
                await message.channel.trigger_typing()
                await self.pob_command.invoke(ctx)

            except Exception as e:
                if "OutdatedPoBException" in str(e):
                    await ctx.error(
                        "There was an error with parsing your pastebin. It was missing key build information. "
                        "It is very likely it was exported from an outdated path of building version, please try "
                        "exporting it from a newer version.")
                elif "AbsentItemBaseException" in str(e):
                    await ctx.error(
                        "There was an error with parsing your pastebin. One or more corresponding item bases could not be"
                        " found on the wiki. Zana can not correctly render items if the base types"
                        " are not consistent with in-game names, same goes for item names for uniques."
                        " Rare item names are changeable.")
                else:
                    await ctx.error("There was an error with parsing your pastebin.")
                await self.report(ctx.message.content)

        elif ctx.message.content.startswith("Item Class:"):
            try:
                if "personal Map Device" in ctx.message.content:
                    return
                if str(ctx.guild.id) in self.server_config.conf and \
                        self.server_config.conf[str(ctx.guild.id)].get('convert'):
                    return
                self.loop.create_task(self.convert_command.invoke(ctx))
            except Exception:
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
        dump_chanel = os.getenv('dump_channel', default='475526519255728128')
        self.dump_channel = self.get_channel(475526519255728128)
        self.ses = aiohttp.ClientSession()
        c = await self.application_info()
        self.owner = c.owner
        print(f'Client logged in.\n'
              f'{self.user.name}\n'
              f'{self.user.id}\n'
              '--------------------------')
        game = Game(f"Now in {len(self.guilds)} servers. Thanks for your support!")
        await self.change_presence(activity=game)
