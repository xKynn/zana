from asyncio import TimeoutError

from utils.emojis import emoji_dict


async def responsive_embed(bot, embed_dict, ctx, timeout=None, use_dict_emojis=False):
    """ Store Embed objects in a dict, and as the reactions come in
    serve the embed the reaction corresponds to. """
    default_embed = embed_dict[list(embed_dict.keys())[0]]
    emsg = await ctx.channel.send(embed=default_embed)
    emsg_id = emsg.id
    pmessage = ctx.channel.get_partial_message(emsg_id)

    def check(_payload):
        if isinstance(_payload.emoji, str):
            emote_name = _payload.emoji
        else:
            emote_name = _payload.emoji.name
        try:
            check_one = emote_name in embed_dict.keys()
            check_two = _payload.message_id == emsg_id
            check_thr = _payload.user_id != bot.user.id
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
            payload = await bot.wait_for('raw_reaction_add', check=check, timeout=timeout)
            member = await ctx.guild.fetch_member(payload.user_id)
        except TimeoutError:
            return await emsg.delete()
        try:
            await emsg.remove_reaction(payload.emoji, member)
        except Exception:
            try:
                await pmessage.remove_reaction(payload.emoji, member)
            except Exception:
                pass

        if isinstance(payload.emoji, str):
            name = payload.emoji
        else:
            name = payload.emoji.name
        new_embed = embed_dict[name]
        await emsg.edit(embed=new_embed)
