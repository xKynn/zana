from utils.emojis import emoji_dict

async def responsive_embed(bot, embed_dict, ctx):
    """ Store Embed objects in a dict, and as the reactions come in
    serve the embed the reaction corresponds to. """
    default_embed = embed_dict[list(embed_dict.keys())[0]]
    emsg = await ctx.channel.send(embed=default_embed)
    def check(reaction, user):
        try:
            return reaction.emoji.name in embed_dict.keys() \
                   and reaction.message.id == emsg.id \
                   and user.id != bot.user.id
        except:
            return False
    for emoji in emoji_dict:
        if emoji in embed_dict:
            await emsg.add_reaction(emoji_dict[emoji])
    while 1:
        reaction, user = await bot.wait_for('reaction_add', check=check)
        await emsg.remove_reaction(reaction.emoji, user)
        new_embed = embed_dict[reaction.emoji.name]
        await emsg.edit(embed=new_embed)