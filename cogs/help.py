import discord
from discord.ext import commands


class Help:
    def __init__(self, bot):
        self.bot = bot
        self.cmd = bot.get_command
        self.color = bot.user_color

    @commands.group(invoke_without_command=True)
    async def help(self, ctx, *, command_name: str=None):
        """ Shows the possible help categories """
        bot_prefix = '@Zana '
        # Shortcut to command search
        if command_name is not None:
            return await ctx.invoke(self.cmd('help command'), cmd_name=command_name)

        em = discord.Embed(title='Help',
                           description='**Linking items:** The bot links items for you in chat if you decorate item names with '
                                       "[[]] for example [[Xoph's Blood]]\n\n"
                                       "**Path of Building preview:** If a pastebin link is posted in a chat the bot can see "
                                       "and is a valid pob pastebin, the bot will reply with a detailed preview.\n\n"
                                       '**Item Paste Conversion:** If you copy an item from PoB or PoETradeMacro, pasting'
                                       " if you paste it in chat, the bot will convert it into the bot's image form. Nee"
                                       "ds `Manage Messages` to delete user's post"
                                       '**Permissions:** The permissions required to function :-\n'
                                       '`Send Messages`, `Manage Messages`, `Embed Links`, `Read Message History`,'
                                       '`Attach Files`, `Read Message History`, `Add Reactions`, `Use External Emojis`\n'
                                       '--\nTo get help or more information on a specific command, use:\n'
                                       f'`{bot_prefix}help cmd|command <command name>` for a specific command.\n'
                                       f'`{bot_prefix}help <command name>` is also a shortcut for the above.\n'
                                       'You can also join the semi-support server [here](https://discord.gg/hUWQ5fJ)',
                           color=self.color)

        # This can't go in the init because help isn't loaded last & thus misses some commands
        em.add_field(name="Commands", value='\n -'.join(c.name for c in self.bot.commands if c.name not in ['pob', 'link']))
        try:
            await ctx.send(embed=em)
        except:
            await ctx.send("`Embed Links` permission is required to see the help!")

    @help.command(name='category', aliases=['categories', 'ctg'])
    async def help_categories(self, ctx, *, category_name: str=None):
        """ Get brief help for each command in a specific category """
        bot_prefix = '@Zana '
        # Handle no input
        if category_name is None:
            return await ctx.error('Category must be provided.')

        # This bit checks whether the category exists -> case insensitive
        # We need the proper name, though, so we search for the proper capitalization
        # And set category_name = to it
        if category_name.casefold() in [x.casefold() for x in self.bot.cogs]:
            category_name = min(self.bot.cogs, key=lambda v: len(set(category_name) ^ set(v)))
        else:
            return await ctx.error(f'`{category_name}` is not a category.')

        em = discord.Embed(title=category_name, color=self.color)
        em.add_field(name='Commands', value=' -'+'\n'.join([f'\u2022 `{bot_prefix}{x.name}` - {x.short_doc}'
                                                       for x in self.bot.get_cog_commands(category_name)]))

        await ctx.send(embed=em)

    @help.command(name='command', aliases=['cmd', 'commands'])
    async def help_command(self, ctx, *, cmd_name: str=None):
        """ Sends help for a specific command """
        bot_prefix = '@Zana '
        # Get command object
        cmd_obj = self.cmd(cmd_name)

        # Handle no command found
        if cmd_obj is None:
            return await ctx.error(f'Command {cmd_name} not found')

        em = discord.Embed(title=cmd_obj.name, description=cmd_obj.short_doc, color=self.color)

        # Input aliases and parameters to embed
        if cmd_obj.aliases:
            em.add_field(name='Aliases', value='\n'.join([f'\u2022 {x}' for x in cmd_obj.aliases]))
        if cmd_obj.clean_params:
            em.add_field(name='Parameters', value='\n'.join([f'\u2022 {x}' for x in cmd_obj.clean_params]))

        # Handle group commands
        if isinstance(cmd_obj, commands.core.Group):
            em.add_field(name='Group commands',
                         value='\n'.join([f'\u2022 {x}' for x in cmd_obj.commands]),
                         inline=False)

        # Add usage last
        em.add_field(name='Usage',
                     value=f'```{bot_prefix}\u200b{cmd_name} '
                           f'{" ".join([f"<{x}>" for x in cmd_obj.clean_params])}```',
                     inline=False)

        await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(Help(bot))
    