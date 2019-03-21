import discord
from discord.ext import commands


class ZanaContext(commands.Context):
    async def error(self, err: str, delete_after=None):
        em = discord.Embed(title=':x: Error',
                           color=discord.Color.dark_red(),
                           description=err.format())

        m = await self.send(embed=em, delete_after=delete_after)
        return m
        
    async def reply(self, content: str, *, embed: discord.Embed = None):
        """ replies with mention """
        await self.send(f'{content}\n{self.author.mention}', embed=embed)
