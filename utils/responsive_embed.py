from utils.emojis import emoji_dict

async def responsive_embed(bot, embed_dict, ctx):
    default_embed = embed_dict[list(embed_dict.keys())[0]]
    emsg = await ctx.channel.send(embed=default_embed)
    _ = [print(msg.filename) for msg in emsg.attachments]
    def check(reaction, user):
        return reaction.emoji.name in embed_dict.keys() \
               and reaction.message.id == emsg.id \
               and user.id != bot.user.id
    for emoji in emoji_dict:
        if emoji in embed_dict:
            await emsg.add_reaction(emoji_dict[emoji])
    while 1:
        reaction, user = await bot.wait_for('reaction_add', check=check)
        await emsg.remove_reaction(reaction.emoji, user)
        new_embed = embed_dict[reaction.emoji.name]
        await emsg.edit(embed=new_embed)