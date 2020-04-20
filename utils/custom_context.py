import discord
from discord.ext import commands


class ZanaContext(commands.Context):
    async def error(self, err: str, delete_after=None):
        embed = discord.Embed(title=':x: Error', color=discord.Color.dark_red(), description=err.format())
        msg = await self.send(embed=embed, delete_after=delete_after)
        return msg

    async def reply(self, content: str, *, embed: discord.Embed = None):
        """ Replies with mention. """
        await self.send(f'{content}\n{self.author.mention}', embed=embed)
