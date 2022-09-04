import discord
from discord.ext import commands
from discord.ext.commands import Cog


class Help(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cmd = bot.get_command
        self.color = bot.user_color

    @commands.group(invoke_without_command=True)
    async def help(self, ctx, *, command_name=None):
        """ Shows the possible help categories. """
        bot_prefix = '@Zana '

        # Shortcut to command search
        if command_name is not None:
            return await ctx.invoke(self.cmd('help command'), cmd_name=command_name)

        desc = "**Bot not respoding to your messages or commands?**: Please read `@Zana notice`, thanks!\n\n" \
               "**Linking items:** The bot links items for you in chat if you decorate item names with " \
               "[[]] for example [[Xoph\'s Blood]]\n\n" \
               "**Path of Building preview:** If a pastebin link is posted in a chat the bot can see " \
               "and is a valid pob pastebin, the bot will reply with a detailed preview.\n\n" \
               "**Item Paste Conversion:** If you copy an item from PoB or PoETradeMacro, and" \
               " if you paste it in chat, the bot will convert it into the bot's image form. Nee" \
               "ds `Manage Messages` to delete user's post\n\n" \
               "**Permissions:** The permissions required to function :-\n" \
               "`Send Messages`, `Manage Messages`, `Embed Links`, `Read Message History`," \
               "`Attach Files`, `Add Reactions`, `Use External Emojis`\n" \
               "--\nTo get help or more information on a specific command, use:\n" \
               f"`{bot_prefix}help <command name>`\n" \
               "--\nYou can also join the semi-support server [here](https://discord.gg/hUWQ5fJ)\n" \
               "--\nRead my messy code [here](http://github.com/xKynn/zana) and PoE.py" \
               " [here](http://github.com/xKynn/PoE.py)\n" \
               "--\nIf you like my work and would like to help me, " \
               "Ko-Fi/Paypal: [Link](https://ko-fi.com/D1D6EXXV)\n" \
               "Patreon for server costs: [Link](https://www.patreon.com/demo36)\n" \
               "--\nDislike the font for stats in charinfo/PoB info?\n" \
               "I had to use it instead of discord's markdown formatting because of a bug in " \
               "discord/electron regarding text formatting in embedded data."

        embed = discord.Embed(title='Help', description=desc, color=self.color)
        embed.set_footer(text="Contact me at Demo#7645 with any questions or suggestions")

        # This can't go in the init because help isn't loaded last & thus misses some commands
        cm_list = [
            f"***{c.name}*** - {c.short_doc}" for c in self.bot.commands if c.name not in ['pob', 'link', 'convert']
        ]
        embed.add_field(name="Commands", value=' • ' + '\n • '.join(cm_list[(len(cm_list) // 2) - 1:]))
        embed.add_field(name="Commands (cont.)", value=' • ' + '\n • '.join(cm_list[:(len(cm_list) // 2) - 1]))
        await ctx.send(embed=embed)

    @help.command(name='command', aliases=['cmd', 'commands'])
    async def help_command(self, ctx, *, cmd_name: str = None):
        """ Sends help for a specific command. """
        bot_prefix = '@Zana '

        # Get command object
        cmd_obj = self.cmd(cmd_name)

        # Handle no command found
        if cmd_obj is None:
            return await ctx.error(f'Command {cmd_name} not found')

        embed = discord.Embed(title=cmd_obj.name, description=cmd_obj.short_doc, color=self.color)

        # Input aliases and parameters to embed
        if cmd_obj.aliases:
            embed.add_field(name='Aliases', value='\n'.join([f'\u2022 {x}' for x in cmd_obj.aliases]))
        if cmd_obj.clean_params:
            embed.add_field(name='Parameters', value='\n'.join([f'\u2022 {x}' for x in cmd_obj.clean_params]))

        # Handle group commands
        if isinstance(cmd_obj, commands.core.Group):
            value = '\n'.join([f'\u2022 {x}' for x in cmd_obj.commands])
            embed.add_field(name='Group commands', value=value, inline=False)

        # Add usage last
        value = f'```{bot_prefix}\u200b{cmd_name} {" ".join([f"<{x}>" for x in cmd_obj.clean_params])}```'
        embed.add_field(name='Usage', value=value, inline=False)

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Help(bot))
