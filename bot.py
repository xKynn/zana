import aiohttp
import json

from discord import Game
from discord import Embed
from discord.ext import commands
from pathlib import Path
from utils.custom_context import ZanaContext
from utils.server_config import ServerConfig
from poe.exceptions import OutdatedPoBException
from poe.exceptions import AbsentItemBaseException


class Zana(commands.AutoShardedBot):
    def __init__(self, *args, **kwargs):
        self.description = 'To be continued'

        # Configs & token
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

    async def report(self, ctx):
        embed = Embed(description="⚠ Zana encountered an error while processing your request. If you would like to send"
                                  " an error report, please react below.")
        embed.set_footer(
            text="This message auto-deletes in 30 seconds.")
        try:
            embed_msg = await ctx.send(embed=embed, delete_after=30)
            embed_id = embed_msg.id
            try:
                await ctx.message.delete()
            except Exception:
                #Funny thing is, error is an embed, if someone removes that perm,
                #the error doesn't go through as well
                await ctx.error("`Manage Messages` required to delete", delete_after=2)
            env_emoji = '📩'
            try:
                await embed_msg.add_reaction(env_emoji)
            except Exception:
                return

            def check(_payload):
                try:
                    check_one = str(_payload.emoji) == str(env_emoji)
                    check_two = _payload.message_id == embed_id
                    check_thr = _payload.user_id != self.user.id
                    check_fr = _payload.user_id == ctx.author.id
                    return all([check_one, check_two, check_thr, check_fr])
                except Exception:
                    return False

            payload = await self.wait_for('raw_reaction_add', check=check)
            try:
                await embed_msg.remove_reaction(payload.emoji, payload.member)
            except Exception:
                pass

            try:
                await self.owner.send(f"Error, context: `{ctx.message.content}`")
            except Exception:
                pass

            try:
                await embed_msg.add_reaction('✅')
            except Exception:
                return
        except Exception:
            pass

    # 'on_message' bot what a n00b omg
    # Only way to link items or provide pob without people requesting it as i wanted this to be a conversation based bot
    async def on_message(self, message):
        if message.author.id == self.user.id:
            return
        await self.wait_until_ready()
        ctx = await self.get_context(message, cls=ZanaContext)
        if '[[' in ctx.message.content and ']]' in ctx.message.content:
            if 1:
                await self.find_command.invoke(ctx)
            else:
                await ctx.error("There was an error with your request.")
                await self.report(ctx)
        elif 'pastebin.com/' in ctx.message.content or "pob.party/share/" in ctx.message.content:
            if str(ctx.guild.id) in self.server_config.conf and \
                    self.server_config.conf[str(ctx.guild.id)].get('disable_pastebin'):
                return
            try:
                await self.pob_command.invoke(ctx)

            except:
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
                await self.report(ctx)

        elif ctx.message.content.startswith("Item Class:"):
            try:
                if "personal Map Device" in ctx.message.content:
                    return
                if str(ctx.guild.id) in self.server_config.conf and \
                        self.server_config.conf[str(ctx.guild.id)].get('convert'):
                    return
                self.loop.create_task(self.convert_command.invoke(ctx))
            except Exception:
                await self.report(ctx)
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
        game = Game(f"Now in {len(self.guilds)} servers. Thanks for your support!")
        await self.change_presence(activity=game)
