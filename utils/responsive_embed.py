from asyncio import TimeoutError

from utils.emojis import emoji_dict


async def responsive_embed(bot, embed_dict, ctx, timeout=None, use_dict_emojis=False):
    """ Store Embed objects in a dict, and as the reactions come in
    serve the embed the reaction corresponds to. """
    default_embed = embed_dict[list(embed_dict.keys())[0]]
    emsg = await ctx.channel.send(embed=default_embed)

    def check(_reaction, _user):
        if isinstance(_reaction.emoji, str):
            emote_name = _reaction.emoji
        else:
            emote_name = _reaction.emoji.name
        try:
            check_one = emote_name in embed_dict.keys()
            check_two = _reaction.message.id == emsg.id
            check_thr = _user.id != bot.user.id
            return all([check_one, check_two, check_thr])
        except Exception:
            return False

    if not use_dict_emojis:
        for emoji in emoji_dict:
            if emoji in embed_dict:
                await emsg.add_reaction(emoji_dict[emoji])
    else:
        for emoji in embed_dict:
            await emsg.add_reaction(emoji)

    while True:
        try:
            reaction, user = await bot.wait_for('reaction_add', check=check, timeout=timeout)
        except TimeoutError:
            return await emsg.delete()
        try:
            await emsg.remove_reaction(reaction.emoji, user)
        except Exception:
            pass
        if isinstance(reaction.emoji, str):
            name = reaction.emoji
        else:
            name = reaction.emoji.name
        new_embed = embed_dict[name]
        await emsg.edit(embed=new_embed)
