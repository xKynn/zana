from discord.ext import commands

class Config:
    def __init__(self, bot):
        self.bot = bot

    def admin_check(ctx):
        return ctx.channel.permissions_for(ctx.author).administrator

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def disable_pastebin(self, ctx):
        """ Disable preview of posted pastebin links, requires Administrator perms"""
        conf = self.bot.server_config.conf
        if str(ctx.guild.id) not in conf:
            conf[str(ctx.guild.id)] = {}
        conf[str(ctx.guild.id)]['disable_pastebin'] = True
        self.bot.server_config.update(conf)
        await ctx.send("Disabled!")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def enable_pastebin(self, ctx):
        """ Enable preview of posted pastebin links, requires Administrator perms"""
        conf = self.bot.server_config.conf
        if str(ctx.guild.id) not in conf:
            conf[str(ctx.guild.id)] = {}
        conf[str(ctx.guild.id)]['disable_pastebin'] = False
        self.bot.server_config.update(conf)
        await ctx.send("Enabled!")

def setup(bot):
    bot.add_cog(Config(bot))
