import asyncio
import copy
import re
import random
import poe.utils as utils
import time

from discord import File, Embed
from urllib.parse import quote_plus
from io import BytesIO
from poe import Client
from poe.models import PassiveSkill
from PIL import Image
from discord.ext import commands
from utils.poe_search import find_one, cache_pob_xml
from utils import pastebin
from utils.poeurl import shrink_tree_url
from utils.class_icons import class_icons
from utils.responsive_embed import responsive_embed
from poe import models
from discord.ext.commands import Cog


class PathOfExile(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.client = Client()
        self.re = re.compile(r'\[\[[^\]]+\]\]')
        self.rng = re.compile('\(.+?\)')
        self.reaction_emojis = ["{}\N{COMBINING ENCLOSING KEYCAP}".format(num) for num in range(1, 4)]
        self.reaction_emojis.append("❌")
        self.vendor_info = {
            "1": "Nessa (*Next to the player's stash*)",
            "2": "Yeena (*Inside the encampment, on the left side*)",
            "3": "Clarissa (*Left to the notice board*)",
            "4": "Petarus and Vanja (*Next to the bridge to the town's Waypoint*)",
            "5": "Lani",
            "6": "Lilly Roth (*Next to the player's Stash*)",
            "7": "Yeena",
            "8": "Clarissa (*Left to the notice board*)",
            "9": "Petarus and Vanja** (*Opposite of the Stash*)",
            "10": "Lani (*near the bridge to the ship*)",
            "Siosa": "Siosa (*in The Library after completing quest A fixture of Fate*)"
        }

    @commands.command()
    async def invite(self, ctx):
        """ Invite the bot. """
        em = Embed(title="Invite Zana", color=self.bot.user_color, url="https://discordapp.com/api/oauth2/authorize?client_id=474597240854282241&permissions=387136&scope=bot")
        await ctx.send(embed=em)

    async def _item_search(self, ctx, items):
        tasks = []
        for item in items:
            tasks.append(self.bot.loop.run_in_executor(None,
                                                       find_one, f"{item.strip('[[').strip(']]')}",
                                                       self.client, self.bot.loop))
        results = await asyncio.gather(*tasks)

        results = [x for x in results if x]
        new_selections = []
        for result in results:
            if isinstance(result, dict):
                if len(result['matches']) and len(result['matches']) > 2:
                    em = Embed(title="Item not found",
                               description=f"""Couldn't find anything for *"{result['name']}"*, did you mean:\n """ +
                                           "\n".join(f'\u2022 *{x[0]}*' for x in result['matches']))
                    msg = await ctx.channel.send(embed=em)

                    def check(reaction, user):
                        try:
                            return reaction.emoji in self.reaction_emojis \
                                   and reaction.message.id == msg.id \
                                   and user.id != self.bot.user.id
                        except:
                            return False

                    for emoji in self.reaction_emojis:
                        await msg.add_reaction(emoji)
                    try:
                        reaction, user = await self.bot.wait_for('reaction_add', check=check, timeout=20)
                    except asyncio.TimeoutError:
                        return await msg.delete()
                    if reaction.emoji == self.reaction_emojis[-1]:
                        return await msg.delete()
                    new_selections.append(result['matches'][self.reaction_emojis.index(reaction.emoji)][0])
                    await msg.delete()

        tasks = []
        print(new_selections)
        for new in new_selections:
            tasks.append(self.bot.loop.run_in_executor(None,
                                                       find_one, new,
                                                       self.client, self.bot.loop))
        new_results = await asyncio.gather(*tasks)

        results.extend(new_results)

        return results

    @commands.command()
    async def link(self, ctx):
        """ Link items decorated with [[]] in chat """
        item_matches = self.re.findall(ctx.message.content)
        if not item_matches:
            return
        tasks = []
        print(item_matches)

        # Because my poe lib is actually completely blocking, i wrote a find_once func and
        # I just run instances of find_ones in executor + gather

        for item in item_matches[:5]:
            tasks.append(self.bot.loop.run_in_executor(None,
                                                       find_one, f"{item.strip('[[').strip(']]')}",
                                                       self.client, self.bot.loop))

        results = await self._item_search(ctx, item_matches[:5])

        images = []
        meta = []

        print(results)

        for result in results:
            if isinstance(result, dict):
                if len(result['matches']) and len(result['matches']) < 2:
                    ctx.message.content = f"[[{result['matches'][0][0]}]]"
                    self.bot.loop.create_task(self.link.invoke(ctx))
                else:
                    continue
            if not isinstance(result, PassiveSkill):
                if result.base == "Prophecy":
                    flavor = 'prophecy'
                elif 'gem' in result.tags:
                    flavor = 'gem'
                    print(result.vendors)
                    dt = {'name': f"{result.name} vendors"}
                    venstr = ""
                    for vendor in result.vendors:
                        classes = "Available to all classes" if vendor['classes'] == '' else vendor['classes']
                        siosa = True if vendor['act'] == '3' and vendor['classes'] == '' else False
                        venstr += f"**Act {vendor['act']}** - {classes} - " \
                                  f"{self.vendor_info[vendor['act']] if not siosa else self.vendor_info['Siosa']}\n"
                    dt['value'] = venstr
                    meta.append(dt)
                elif 'divination_card' in result.tags:
                    # Lib has a different render function for div cards as they don't fit the standard stats and sorting
                    # method, might change in the future but would be extremely unneat code-wise.
                    r = utils.ItemRender('unique')
                    images.append(r.render_divcard(result))
                    try:
                        reward = await self.bot.loop.run_in_executor(None,
                                                                     find_one, result.reward,
                                                                     self.client, self.bot.loop)
                        if reward.base == "Prophecy":
                            i_render = utils.ItemRender('prophecy')
                            images.append(i_render.render(reward))
                        elif 'gem' in reward.tags:
                            i_render = utils.ItemRender('gem')
                            images.append(i_render.render(reward))
                        elif 'divination_card' in reward.tags:
                            i_render = utils.ItemRender('unique')
                            images.append(i_render.render_divcard(reward))
                        else:
                            i_render = utils.ItemRender(reward.rarity)
                            images.append(i_render.render(reward))
                    except:
                        pass
                    if result.drop.areas:
                        txt =  '\n'.join([f'\u2022 {x}' for x in result.drop.areas.split(',')])
                        if len(txt) <= 1024:
                            meta.append({'name': f"{result.name} Drop Locations",
                                         'value': txt})
                        else:
                            loc_list = result.drop.areas.split(',')
                            txt = '\n'.join([f'\u2022 {x}' for x in loc_list[:(len(loc_list) // 2) - 1]])
                            txt += f"\n[...More](http://pathofexile.gamepedia.com/{quote_plus(result.name).replace('+', '%20')})"
                            meta.append({'name': f"{result.name} Drop Locations",
                                         'value': txt})

                    continue
                else:
                    flavor = result.rarity
            else:
                flavor = 'normal'
            if 'divination_card' not in result.tags:
                r = utils.ItemRender(flavor)
                images.append(r.render(result))

        results = [x for x in results if not isinstance(x, dict)]

        # Stitch images together, traditionally 5 images tops, but as div cards can feature their reward as an image
        # Possible max images can be 10
        # R.I.P that one time where we stitched headhunters for image width of 69700
        if len(results) < 2 and isinstance(results[0], dict):
            return
        if len(images) > 1:
            box = [0, 0]
            for image in images:
                box[0] = box[0] + image.size[0]
                if image.size[1] > box[1]:
                    box[1] = image.size[1]
            box[0] = box[0] + (2*len(images))
            img = Image.new('RGBA', box, color='black')
            #img.show()
            paste_coords = [0, 0]
            for image in images:
                #image.show()
                img.paste(image.convert('RGBA'), box=paste_coords[:])
                paste_coords[0] = paste_coords[0] + image.size[0] + 2
        else:
            img = images[0]
        image_fp = BytesIO()
        img.save(image_fp, 'png')
        image_fp.seek(0)
        print("Image ready")

        em = Embed(color=self.bot.user_color)
        links = []
        for item in results:
            links.append(f"\u2022 [{item.name}](http://pathofexile.gamepedia.com/{quote_plus(item.name).replace('+','%20')})")
        em.add_field(name="Wiki Links", value='\n'.join(links))
        em.set_image(url="attachment://image.png")
        # Meta basically only used for gems to show vendor info, might add more stuff later, good base to build on
        if meta:
            for m in meta:
                em.add_field(name=m['name'], value=m['value'] or "None", inline=True)
        try:
            await ctx.channel.send(file=File(image_fp, filename='image.png'),
                                   embed=em)
        except:
            await ctx.error("`Attach Files` permission required", delete_after=2)


    # So I've designated items 2 categories: twoslot and oneslot
    # Weapons and rings are 2 slots, basically same type twice, so i can stitch them together in one embed
    # Oneslot is basic, render and fetch image and gems
    async def _twoslot_pob(self, equip, itemtype):
        embed = Embed(color=self.bot.user_color)
        if f'{itemtype} 1' in equip or f'{itemtype} 2' in equip:
            if f'{itemtype} 1' in equip and f'{itemtype} 2' in equip:
                rwp1 = utils.ItemRender(equip[f'{itemtype} 1']['object'].rarity)
                wp1 = rwp1.render(equip[f'{itemtype} 1']['object'])
                rwp2 = utils.ItemRender(equip[f'{itemtype} 2']['object'].rarity)
                wp2 = rwp2.render(equip[f'{itemtype} 2']['object'])
                box = list(wp1.size)
                if wp2.size[1] > box[1]:
                    box[1] = wp2.size[1]
                box[0] = box[0] + wp2.size[0] + 2
                img = Image.new('RGBA', box, color='black')
                img.paste(wp1.convert('RGBA'), box=(0, 0))
                img.paste(wp2.convert('RGBA'), box=(wp1.size[0]+2, 0))
            else:
                wp_n = f'{itemtype} 1' if f'{itemtype} 1' in equip else f'{itemtype} 2'
                rwp = utils.ItemRender(equip[wp_n]['object'].rarity)
                img = rwp.render(equip[wp_n]['object'])
            image_fp = BytesIO()
            img.save(image_fp, 'png')
            #img.show()
            #print(image_fp.tell())
            image_fp.seek(0)
            file = File(image_fp, filename=f'{itemtype.lower()}.png')
            # upload = await self.bot.dump_channel.send(file=file)
            # embed.set_image(url=upload.attachments[0].url)

            slot_list = []
            if f'{itemtype} 1' in equip and 'gems' in equip[f'{itemtype} 1']:
                slot_list.append(f'{itemtype} 1')
            if f'{itemtype} 2' in equip and 'gems' in equip[f'{itemtype} 2']:
                slot_list.append(f'{itemtype} 2')
            for slot in slot_list:
                val_list = []
                for gem in equip[slot]['gems']:
                    val_list.append(f" - {gem['level']}/{gem['quality']} {gem['name']}")
                value = '\n'.join(val_list)
                embed.add_field(name=f"{slot} Gems", value=value, inline=True)
            return {'file': file, 'embed': embed}
        else:
            return None

    async def _oneslot_pob(self, equip, itemtype):
        embed = Embed(color=self.bot.user_color)
        if itemtype in equip:
            wp_n = itemtype
            rwp = utils.ItemRender(equip[wp_n]['object'].rarity)
            img = rwp.render(equip[wp_n]['object'])
            image_fp = BytesIO()
            img.save(image_fp, 'png')
            #print(image_fp.tell())
            image_fp.seek(0)
            file = File(image_fp, filename=f"{itemtype.lower().replace(' ','')}.png")
            # upload = await self.bot.dump_channel.send(file=file)
            # embed.set_image(url=upload.attachments[0].url)
            #print(equip[wp_n])
            if 'gems' in equip[wp_n] and equip[wp_n]['gems']:
                val_list = []
                for gem in equip[wp_n]['gems']:
                    val_list.append(f" - {gem['level']}/{gem['quality']} {gem['name']}")
                value = '\n'.join(val_list)
                embed.add_field(name=f"{wp_n} Gems", value=value, inline=True)
            return {'file': file, 'embed': embed}
        else:
            return None

    # Jewels embed making, if its unique include the name as well, rare or magic jewel names don't matter really
    def _jewels_pob(self, equip):
        embed = Embed(color=self.bot.user_color)
        if 'jewels' in equip:
            for jewel in equip['jewels']:
                name = jewel['base'] if jewel['rarity'].lower() != 'unique' else f"{jewel['name']} {jewel['base']}"
                val_list = [f" - {stat}" for stat in jewel['stats']]
                value = '\n'.join(val_list)
                embed.add_field(name=name, value=value, inline=True)
            return embed
        else:
            return None

    # If i ever make a model for flasks in PoE.py this should turn into a much more detailed thing
    def _flasks_pob(self, equip):
        flasks = []
        for slot in equip:
            if slot.startswith("Flask"):
                if 'parsed' in equip[slot]:
                    access = equip[slot]['parsed']
                else:
                    access = equip[slot]
                if access['rarity'].lower() == "unique":
                    flasks.append(f"\u2022 {access['name']} {access['base']}")
                else:
                    flasks.append(f"\u2022 {access['base']}")

        if flasks:
            return Embed(color=self.bot.user_color, title="Flasks", description='\n'.join(flasks))
        else:
            return None

    # gem_groups exists because people will at times in PoB not slot a gem group into an item on the player
    # so these are say a 6 link you could put maybe in your weapon or your chest? basically unslotted
    def _gem_groups(self, equip):
        embed = Embed(color=self.bot.user_color)
        if 'gem_groups' in equip:
            for gem_title in equip['gem_groups']:
                name = gem_title
                val_list = []
                for gem in equip['gem_groups'][gem_title]:
                    val_list.append(f" - {gem['level']}/{gem['quality']} {gem['name']}")
                value = '\n'.join(val_list)
                embed.add_field(name=name, value=value, inline=True)
            return embed
        else:
            return None

    # Make standard first page of embed, differes for pob and charinfo, as the bool kwarg says
    async def _info_dict(self, stats, pob=True, pob_party=None):
        info = Embed(color=self.bot.user_color)
        print(stats)
        if pob_party:
            #print("yes party")
            info.description = f"[*Open in pob.party*]({pob_party})"
        else:
            info.description = ""
        if pob:
            if stats['ascendancy'] != "None":
                info.title = f"Level {stats['level']} {stats['class']}: {stats['ascendancy']}"
            else:
                info.title = f"Level {stats['level']} {stats['class']}"
        else:
            info.title = f"Level {stats['level']} {stats['class']} (Click to open skill tree)"
            info.description = f"{stats['league']} League"

        if pob:
            info.description += \
            f"\n\n𝐀𝐭𝐭𝐫𝐢𝐛𝐮𝐭𝐞𝐬: Str: {stats['str']} **|** "\
            f"Dex: {stats['dex']} **|** "\
            f"Int: {stats['int']}\n"\
            f"𝐂𝐡𝐚𝐫𝐠𝐞𝐬: Power: {stats['power_charges']} **|** " \
            f"Frenzy: {stats['frenzy_charges']} **|** " \
            f"Endurance: {stats['endurance_charges']}"

            if stats['bandit'] != "None":
                info.description += f"\n𝐁𝐚𝐧𝐝𝐢𝐭: {stats['bandit']}"

            offensive_stats_text =\
            f"𝐓𝐨𝐭𝐚𝐥 𝐃𝐏𝐒: {float(stats['total_dps']):,.1f}\n"\
            f"𝐂𝐫𝐢𝐭 𝐂𝐡𝐚𝐧𝐜𝐞: {float(stats['crit_chance']):.1f}%\n"\
            f"𝐄𝐟𝐟𝐞𝐜𝐭𝐢𝐯𝐞 𝐂𝐫𝐢𝐭 𝐂𝐡𝐚𝐧𝐜𝐞: {float(stats['effective_crit_chance']):.1f}%\n"\
            f"𝐂𝐡𝐚𝐧𝐜𝐞 𝐭𝐨 𝐇𝐢𝐭: {stats['chance_to_hit']}%"
            info.add_field(name="Offense", value=offensive_stats_text)

            defensive_stats_text =\
            f"𝐋𝐢𝐟𝐞: {stats['life']}\n"\
            f"𝐋𝐢𝐟𝐞 𝐑𝐞𝐠𝐞𝐧: {float(stats['life_regen']):.1f}\n"\
            f"𝐄𝐧𝐞𝐫𝐠𝐲 𝐒𝐡𝐢𝐞𝐥𝐝: {stats['es']}\n"\
            f"𝐄𝐒 𝐑𝐞𝐠𝐞𝐧: {float(stats['es_regen']):.1f}\n"\
            f"𝐃𝐞𝐠𝐞𝐧: {float(stats['degen']):.1f}"
            info.add_field(name="Defense", value=defensive_stats_text, inline=True)

            mitigation_stats_text=\
            f"𝐄𝐯𝐚𝐬𝐢𝐨𝐧: {stats['evasion']}\n"\
            f"𝐁𝐥𝐨𝐜𝐤: {stats['block']}%\n"\
            f"𝐒𝐩𝐞𝐥𝐥 𝐁𝐥𝐨𝐜𝐤: {stats['spell_block']}%\n"\
            f"𝐃𝐨𝐝𝐠𝐞: {stats['dodge']}%\n"\
            f"𝐒𝐩𝐞𝐥𝐥 𝐃𝐨𝐝𝐠𝐞: {stats['spell_dodge']}%"
            info.add_field(name="Mitigation", value=mitigation_stats_text, inline=True)

            resistances_text = \
            f"𝐅𝐢𝐫𝐞: {stats['fire_res']}%\n"\
            f"𝐂𝐨𝐥𝐝: {stats['cold_res']}%\n" \
            f"𝐋𝐢𝐠𝐡𝐭𝐧𝐢𝐧𝐠: {stats['light_res']}%\n" \
            f"𝐂𝐡𝐚𝐨𝐬: {stats['chaos_res']}%"
            info.add_field(name="Resistances", value=resistances_text, inline=True)

            # poeurl shortener is QUITE blocking, needs to be done this way or made into async but as long as it works
            async def tree_text(tree, dict):
                url = await self.bot.loop.run_in_executor(None, shrink_tree_url, dict[tree])
                return f"[{tree}]({url})"
            tasks = []
            for tree in stats['trees']:
                tasks.append(tree_text(tree, stats['trees']))
            tree_list = await asyncio.gather(*tasks)
            skill_trees = '\n'.join(tree_list)
            info.add_field(name="Other Skill Trees", value=skill_trees, inline=False)
        else:
            info.url = stats['tree_link']
        asc_list = [f"[{node}](https://pathofexile.gamepedia.com/{node.replace(' ', '_')})" for node in stats['asc_nodes']]
        asc_text = '\n'.join(asc_list)

        info.add_field(name="Ascendancies", value=asc_text, inline=True)
        ks_list = [f"[{node}](https://pathofexile.gamepedia.com/{node.replace(' ', '_')})" for node in
                    stats['keystones']]
        keystones = '\n'.join(ks_list)
        info.add_field(name="Keystones", value=keystones, inline=True)
        if pob:
            icon_url = class_icons[stats['ascendancy'].lower()] if stats['ascendancy'] != "None"\
                else class_icons[stats['class'].lower()]
        else:
            icon_url = class_icons[stats['class'].lower()]
        info.set_thumbnail(url=icon_url)
        info.set_footer(text="Don't want your pastebins converted? An admin can disable it using @Zana disable_pastebin")
        return info

    # The sauce that uploads images to a dump channel in discord to use it as free unlimited image hosting
    # Then link those images in my embeds fluently and form responsive_embed
    async def make_responsive_embed(self, stats, ctx, pob=True, party_url=None):
        responsive_dict = {}
        files = []
        weapons_dict = await self._twoslot_pob(stats['equipped'], 'Weapon')
        rings_dict = await self._twoslot_pob(stats['equipped'], 'Ring')
        armor_dict = await self._oneslot_pob(stats['equipped'], 'Body Armour')
        helmet_dict = await self._oneslot_pob(stats['equipped'], 'Helmet')
        amulet_dict = await self._oneslot_pob(stats['equipped'], 'Amulet')
        gloves_dict = await self._oneslot_pob(stats['equipped'], 'Gloves')
        boots_dict = await self._oneslot_pob(stats['equipped'], 'Boots')
        belt_dict = await self._oneslot_pob(stats['equipped'], 'Belt')
        jewels_dict = self._jewels_pob(stats)
        flasks_dict = self._flasks_pob(stats['equipped'])
        gem_groups_dict = self._gem_groups(stats['equipped'])
        responsive_dict['info'] = await self._info_dict(stats, pob, pob_party=party_url)
        #print(responsive_dict['info'].fields)
        if weapons_dict:
            responsive_dict['weapon'] = weapons_dict['embed']
            files.append(weapons_dict['file'])
        if rings_dict:
            responsive_dict['ring'] = rings_dict['embed']
            files.append(rings_dict['file'])
        if amulet_dict:
            responsive_dict['amulet'] = amulet_dict['embed']
            files.append(amulet_dict['file'])
        if armor_dict:
            responsive_dict['bodyarmour'] = armor_dict['embed']
            files.append(armor_dict['file'])
        if helmet_dict:
            responsive_dict['helmet'] = helmet_dict['embed']
            files.append(helmet_dict['file'])
        if gloves_dict:
            responsive_dict['gloves'] = gloves_dict['embed']
            files.append(gloves_dict['file'])
        if boots_dict:
            responsive_dict['boots'] = boots_dict['embed']
            files.append(boots_dict['file'])
        if belt_dict:
            responsive_dict['belt'] = belt_dict['embed']
            files.append(belt_dict['file'])
        if jewels_dict:
            responsive_dict['jewels'] = jewels_dict
        if flasks_dict:
            responsive_dict['flask'] = flasks_dict
        if gem_groups_dict:
            responsive_dict['gems'] = gem_groups_dict
        for key in responsive_dict:
            for index, field in enumerate(responsive_dict[key].fields):
                if field.value == '':
                    responsive_dict[key].set_field_at(index, name=field.name, value="None", inline=field.inline)
        if files:
            upload = await self.bot.dump_channel.send(files=files)
            for attachment in upload.attachments:
                responsive_dict[attachment.filename.split('.')[0]].set_image(url=attachment.url)
        await responsive_embed(self.bot, responsive_dict, ctx)

    @commands.command()
    async def characters(self, ctx, account=None):
        """ Get all characters on account """
        if not account:
            return await ctx.error("Incorrect number of arguments supplied!\n`@Zana characters <account_name>")

        async with self.bot.ses.get('https://www.pathofexile.com/character-window/'
                                    f'get-characters?accountName={account}') as resp:
            chars = await resp.json()
        if not isinstance(chars, list):
            return await ctx.error("Private account or incorrect account name.")
        char_dict = {}

        for char in chars:
            if char['league'] not in char_dict:
                char_dict[char['league']] = list()
            char_dict[char['league']].append(char)

        em = Embed(title=f"{account}'s Characters", color=self.bot.user_color)
        for league in char_dict:
            league_chars = []
            for char in char_dict[league]:
                txt = f"{char['name']} | {char['class']} | Level {char['level']}"
                league_chars.append(txt)
            fmt_chars = '\n'.join(league_chars)
            if len(fmt_chars) <= 1000:
                em.add_field(name=league, value = fmt_chars)
            else:
                em.add_field(name=league, value = '\n'.join(league_chars[:(len(league_chars)//2)-1]))
                em.add_field(name=f"{league} (cont.)", value='\n'.join(league_chars[(len(league_chars)//2) - 1:]))

        print()
        await ctx.send(embed=em)

    @commands.command()
    async def charinfo(self, ctx, character=None):
        """ Fetch character info for provided account and character """

        if not character:
            return await ctx.error("Incorrect number of arguments supplied!\n`@Zana charinfo <charname>")

        # A reddit user told me about this, pretty sweet
        async with self.bot.ses.get('https://www.pathofexile.com/character-window/get-account-name-'
                                    f'by-character?character={character}') as resp:
            account_d = await resp.json()

        if not 'accountName' in account_d:
            return await ctx.error("Invalid character name.")
        else:
            account = account_d['accountName']

        async with self.bot.ses.get('https://www.pathofexile.com/character-window'
                                    f'/get-items?accountName={account}&character={character}') as resp:
            items_json = await resp.json()
        async with self.bot.ses.get('https://www.pathofexile.com/character-window'
                                    f'/get-passive-skills?accountName={account}&character={character}') as resp:
            tree_json = await resp.json()
        stats = utils.parse_poe_char_api(items_json, self.client)
        tree_link, keystones, asc_nodes = utils.poe_skill_tree(tree_json['hashes'], items_json['character']['class'],
                                                               return_asc=True, return_keystones=True)
        stats['keystones'] = keystones
        stats['tree_link'] = tree_link
        stats['asc_nodes'] = asc_nodes
        await self.make_responsive_embed(stats, ctx, False)

    @commands.command()
    async def pob(self, ctx):
        """ Fetch character info for valid pob pastebin links posted in chat """
        # Pastebin util is from another discord pob parsing bot, why re-invent the wheel i guess?
        if "pastebin.com/" in ctx.message.content:
            paste_keys = pastebin.fetch_paste_key(ctx.message.content)
            if not paste_keys: return
            xml = None
            paste_key = paste_keys[0]
            try:
                xml = await self.bot.loop.run_in_executor(None, pastebin.get_as_xml, paste_key)
            except:
                return
            if not xml: return
            raw = await self.bot.loop.run_in_executor(None, pastebin.get_raw_data, f"https://pastebin.com/raw/{paste_key}")
            #print(raw)
            async with self.bot.ses.post("https://pob.party/kv/put?ver=latest", data=raw) as resp:
                try:
                    party_resp = await resp.json()
                except:
                    party_resp = None
            if party_resp:
                party_url = f"https://pob.party/share/{party_resp['url']}"
            else:
                party_url = None
        else:
            url = None
            for part in ctx.message.content.split(" "):
                if "pob.party/share/" in part:
                    url = part
                    break
            if not url:
                return

            key = url.split('/')[-1]
            async with self.bot.ses.get(f"https://pob.party/kv/get/{key}") as resp:
                try:
                    party_resp = await resp.json()
                except:
                    party_resp = None
            if not party_resp:
                return
            xml = pastebin.decode_to_xml(party_resp['data']).decode('utf-8')
            party_url = None
        #print(party_url)
        stats = await self.bot.loop.run_in_executor(None, cache_pob_xml, xml, self.client)
        await self.make_responsive_embed(stats, ctx, party_url=party_url)

    @commands.command()
    async def convert(self, ctx):
        """ Convert an item copied from PoB or PoETradeMacro to the Zana version """

        # Put my PoB item parser to good use
        try:
            pob_item = utils.parse_pob_item(ctx.message.content)
        except:
            print(ctx.message.content)
            return
        d = {}
        print(pob_item)
        await self.bot.loop.run_in_executor(None, utils._get_wiki_base, pob_item, d, self.client, "Chat Item")
        #print(d)
        #print(d['Chat Item'].energy_shield)
        #utils.modify_base_stats(d['Chat Item'])
        #print(d['Chat Item'].energy_shield)
        print("qual, ", d['Chat Item'].quality)
        renderer = utils.ItemRender(d['Chat Item'].rarity)
        img = renderer.render(d['Chat Item'])
        image_fp = BytesIO()
        img.save(image_fp, 'png')
        image_fp.seek(0)
        file = File(image_fp, filename=f"converted.png")
        upload = await self.bot.dump_channel.send(file=file)
        em = Embed()
        em.set_author(name=f"{ctx.author.name}#{ctx.author.discriminator}", icon_url=ctx.author.avatar_url)
        em.set_image(url=upload.attachments[0].url)
        em.set_footer(text="Don't want your items converted? An admin can disable it using @Zana disable_conversion")
        try:
            await ctx.send(embed=em)
        except:
            try:
                await ctx.send(f"**{ctx.author.name}#{ctx.author.discriminator}**:\n", file=file)
            except:
                await ctx.error("`Attach Files` permission required", delete_after=2)

    @commands.command()
    async def roll(self, ctx, * ,item: str=None):
        """ 'Divine' any Unique item and test your luck! """
        if not item:
            return await ctx.error("The correct format to use `roll` is\n`@Zana <itemname>`")
        unique = await self.bot.loop.run_in_executor(None,find_one, item, self.client, self.bot.loop)
        unique = copy.copy(unique)
        if not unique:
            return await ctx.error(f"Couldn't find {item} on the wiki!")
        if unique.rarity.lower() != 'unique':
            return await ctx.error("You can only roll unique items!")
        base = await self.bot.loop.run_in_executor(None,find_one, unique.base, self.client, self.bot.loop)
        base = copy.copy(base)
        implicits = utils.unescape_to_list(unique.implicits)
        explicits = utils.unescape_to_list(unique.explicits)
        decided_implicits = []
        decided_explicits = []
        for implicit in implicits:
            if '(' in implicit and ')' in implicit and 'hidden' not in implicit.lower():
                matches = self.rng.findall(implicit)
                match_dict = {}
                for match in matches:
                    stat = match[1:-1]
                    separator = stat.find('-', 1)
                    range_start = stat[:separator]
                    range_end = stat[separator+1:]
                    if '.' in range_start or '.' in range_end:
                        randomized_stat = random.uniform(float(range_start), float(range_end))
                    else:
                        randomized_stat = random.randint(int(range_start), int(range_end))
                    if randomized_stat == 0:
                        continue
                    match_dict[match] = randomized_stat
                    new_impl = implicit
                for rep in match_dict:
                    new_impl = new_impl.replace(rep, str(match_dict[rep]))
                    if match_dict[rep] < 0:
                        new_impl = new_impl.replace('+', '')
                        new_impl = new_impl.replace('increased', 'reduced')
                if match_dict:
                    decided_implicits.append(new_impl)
            else:
                decided_implicits.append(implicit)

        for explicit in explicits:
            if '(' in explicit and ')' in explicit and 'hidden' not in explicit.lower():
                matches = self.rng.findall(explicit)
                match_dict = {}
                print(matches)
                for match in matches:
                    stat = match[1:-1]
                    separator = stat.find('-', 1)
                    range_start = stat[:separator]
                    range_end = stat[separator+1:]
                    if '.' in range_start or '.' in range_end:
                        randomized_stat = random.uniform(float(range_start), float(range_end))
                    else:
                        randomized_stat = random.randint(int(range_start), int(range_end))
                    if randomized_stat == 0:
                        continue
                    match_dict[match] = randomized_stat
                new_expl = explicit
                for rep in match_dict:
                    new_expl = new_expl.replace(rep, str(match_dict[rep]))
                    if match_dict[rep] < 0:
                        new_expl = new_expl.replace('+', '')
                        new_expl = new_expl.replace('increased', 'reduced')
                if match_dict:
                    decided_explicits.append(new_expl)
            else:
                decided_explicits.append(explicit)
        escaped_implicits = '<br>'.join(decided_implicits)
        escaped_explicits = '<br>'.join(decided_explicits)
        base.implicits = escaped_implicits
        unique.implicits = escaped_implicits
        base.explicits = escaped_explicits
        unique.explicits = escaped_explicits
        print(unique.tags)
        try:
            utils.modify_base_stats(base)
            if 'weapon' in unique.tags:
                print("is wep")
                unique.attack_speed = base.attack_speed
                unique.critical_chance = base.critical_chance
                unique.range = base.range
                unique.fire_min = base.fire_min
                unique.fire_max = base.fire_max
                unique.cold_min = base.cold_min
                unique.cold_max = base.cold_max
                unique.lightning_min = base.lightning_min
                unique.lightning_max = base.lightning_max
                unique.chaos_min = base.chaos_min
                unique.chaos_max = base.chaos_max
                unique.physical_min = base.physical_min
                unique.physical_max = base.physical_max
            else:
                unique.armour = base.armour
                unique.evasion = base.evasion
                unique.energy_shield = base.energy_shield

        except:
            pass
        renderer = utils.ItemRender('unique')
        img = renderer.render(unique)
        image_fp = BytesIO()
        img.save(image_fp, 'png')
        image_fp.seek(0)
        try:
            f = File(image_fp, filename=f'image{round(time.time())}.png')
            await ctx.channel.send(file=f)
        except:
            await ctx.error("`Attach Files` permission required")

    async def _search_api(self, ctx, item_plus_league: str=None):
        if not item_plus_league:
            return await ctx.error("I need an item to price.")

        leagues = utils.get_active_leagues()
        league = None
        matched = False

        if ',' in item_plus_league:
            league = item_plus_league.split(',')[1].strip().title()
            for lg in leagues:
                if league == lg['id']:
                    matched = True
                    break
                elif league == lg['text']:
                    matched = True
                    league = lg['id']
            item = item_plus_league.split(',')[0].strip()
        else:
            item = item_plus_league

        if not league or not matched:
            em = Embed(title="No League Specified" if not league else f"No League named {league}",
                       description="Specify league by using the command as follows:\n"
                                   "`@Zana price Kaom's Heart, Metamorph`\nPlease choose a league for this query:\n" +
                       "\n".join(f'\u2022 *{x["id"]}*' for x in leagues))
            msg = await ctx.channel.send(embed=em)

            emojis = self.reaction_emojis
            emojis.insert(3, "4\N{COMBINING ENCLOSING KEYCAP}")
            def check(reaction, user):
                try:
                    return reaction.emoji in emojis \
                           and reaction.message.id == msg.id \
                           and user.id != self.bot.user.id
                except:
                    return False

            for emoji in emojis:
                await msg.add_reaction(emoji)
            try:
                reaction, user = await self.bot.wait_for('reaction_add', check=check, timeout=20)
            except asyncio.TimeoutError:
                return await msg.delete()
            if reaction.emoji == emojis[-1]:
                return await msg.delete()
            league = leagues[emojis.index(reaction.emoji)]['id']
            await msg.delete()

        results = await self._item_search(ctx, [item])
        return results[0], league
    @commands.command()
    async def price(self, ctx, *, item_plus_league: str=None):
        """ Calculate a fair price for an item in the most common listed currency. """
        verified_item, league = await self._search_api(ctx, item_plus_league)
        if isinstance(verified_item, dict):
            price = utils.item_price(verified_item['matches'][0][0], league).fair_price()
            iname = verified_item['matches'][0][0]
        else:
            price = utils.item_price(verified_item.name, league).fair_price()
            iname = verified_item.name

        em = Embed(title=f"💰 Fair price: *{iname}*",
                   description=f"{round(price['value'], 1)} {price['currency']}",
                   color=self.bot.user_color)
        return await ctx.send(embed=em)

    @commands.command()
    async def buy(self, ctx, *, item_plus_league: str=None):
        """ List the 3 lowest priced items with whisper and price info. """
        verified_item, league = await self._search_api(ctx, item_plus_league)
        if isinstance(verified_item, dict):
            price = utils.item_price(verified_item['matches'][0][0], league)
            iname = verified_item['matches'][0][0]
        else:
            price = utils.item_price(verified_item.name, league)
            iname = verified_item.name
        lowest = price.lowest()
        print(lowest)
        tasks = []
        for item in lowest:
            tasks.append(self.bot.loop.run_in_executor(None,
                                                       utils.parse_poe_char_api, {'items': [item['item']]},
                                                       self.client, True))
        results = await asyncio.gather(*tasks)
        files = {'files': [],
                 'indexes': []}
        sockets = {'sockets': [],
                   'indexes': []}
        for ind, item in enumerate(results):
            #print(item)
            if not item['equipped']['items_objects']:
                continue
            if 'sockets' in lowest[ind]['item'] and lowest[ind]['item']['sockets']:
                socks = {}
                for sock in lowest[ind]['item']['sockets']:
                    if not sock['group'] in socks:
                        socks[sock['group']] = []
                    socks[sock['group']].append(sock['sColour'])
                sock_strs = []
                for val in socks.values():
                    sock_strs.append('-'.join(val))
                sockets['sockets'].append('\n'.join(sock_strs))
                sockets['indexes'].append(ind)
            result = item['equipped']['items_objects']
            if not isinstance(result, PassiveSkill):
                if result.base == "Prophecy":
                    flavor = 'prophecy'
                elif 'gem' in result.tags:
                    flavor = 'gem'
                elif 'divination_card' in result.tags:
                    # Lib has a different render function for div cards as they don't fit the standard stats and sorting
                    # method, might change in the future but would be extremely unneat code-wise.
                    r = utils.ItemRender('unique')
                    img = r.render_divcard(result)
                else:
                    flavor = result.rarity
            else:
                flavor = 'normal'
            if 'divination_card' not in result.tags:
                r = utils.ItemRender(flavor)
                img = r.render(result)
            image_fp = BytesIO()
            img.save(image_fp, 'png')
            image_fp.seek(0)
            files['files'].append(File(image_fp, filename=f"{result.name.lower().replace(' ','')}{ind}.png"))
            files['indexes'].append(ind)

        if files:
            upload = await self.bot.dump_channel.send(files=files['files'])
            upload.attachments.reverse()
        else:
            upload = None
        #print(files)
        embed_dict = dict.fromkeys(self.reaction_emojis[:-1])
        #print(embed_dict)
        price = ', '.join([f"*{entry['listing']['price']['amount']} "
                           f"{entry['listing']['price']['currency']}*" for entry in lowest])
        sockets['sockets'].reverse()
        print(sockets, files)
        for ind, react in enumerate(embed_dict):
            em = Embed(title=f"Lowest 3 Listings for {iname}",
                       description=f"Prices: {price}", color=self.bot.user_color)
            try:
                if ind in files['indexes']:
                    em.set_image(url=upload.attachments.pop().url)
            except (IndexError, AttributeError):
                pass

            em.add_field(name="Price", value=f"{lowest[ind]['listing']['price']['amount']} "
                                             f"{lowest[ind]['listing']['price']['currency']}")
            if ind in sockets['indexes']:
                em.add_field(name="Sockets", value=sockets['sockets'].pop())
            em.add_field(name="Whisper", value=f"`{lowest[ind]['listing']['whisper']}`")
            embed_dict[react] = em

        #print(embed_dict)

        await responsive_embed(self.bot, embed_dict, ctx, timeout=60*5, use_dict_emojis=True)

def setup(bot):
    bot.add_cog(PathOfExile(bot))