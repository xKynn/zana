import asyncio
import re
import random
import poe.utils as utils

from discord import File, Embed
from io import BytesIO
from poe import Client
from PIL import Image
from discord.ext import commands
from utils.poe_search import find_one, cache_pob_xml
from utils import pastebin
from utils.poeurl import shrink_tree_url
from utils.class_icons import class_icons
from utils.responsive_embed import responsive_embed


class PathOfExile:
    def __init__(self, bot):
        self.bot = bot
        self.client = Client()
        self.re = re.compile(r'\[\[[^\]]+\]\]')

    @commands.command()
    async def link(self, ctx):
        """ Link items decorated with [[]] in chat """
        item_matches = self.re.findall(ctx.message.content)
        if not item_matches:
            return
        tasks = []
        print(item_matches)
        for item in item_matches:
            tasks.append(self.bot.loop.run_in_executor(None,
                                                       find_one, item.strip('[[').strip(']]'),
                                                       self.client, self.bot.loop))
        results = await asyncio.gather(*tasks)
        results = [x for x in results if x]
        images = []
        for result in results:
            if result.base == "Prophecy":
                flavor = 'prophecy'
            elif 'gem' in result.tags:
                flavor = 'gem'
            else:
                flavor = result.rarity
            r = utils.ItemRender(flavor)
            images.append(r.render(result))
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
        await ctx.channel.send(file=File(image_fp, filename='image.png'))

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

    async def _info_dict(self, stats, pob=True):
        info = Embed(color=self.bot.user_color)
        if pob:
            if stats['ascendancy'] != "None":
                info.title = f"Level {stats['level']} {stats['class']}: {stats['ascendancy']}"
            else:
                info.title = f"Level {stats['level']} {stats['class']}"
        else:
            info.title = f"Level {stats['level']} {stats['class']} (Click to open skill tree)"
            info.description = f"{stats['league']} League"

        if pob:
            info.description = \
            f"𝐀𝐭𝐭𝐫𝐢𝐛𝐮𝐭𝐞𝐬: Str: {stats['str']} **|** "\
            f"Dex: {stats['dex']} **|** "\
            f"Int: {stats['int']}\n"\
            f"𝐂𝐡𝐚𝐫𝐠𝐞𝐬𝘴: Power: {stats['power_charges']} **|** " \
            f"Frenzy: {stats['frenzy_charges']} **|** " \
            f"Endurance: {stats['endurance_charges']}"

            offensive_stats_text =\
            f"𝐓𝐨𝐭𝐚𝐥 𝐃𝐏𝐒: {stats['total_dps']}\n"\
            f"𝐂𝐫𝐢𝐭 𝐂𝐡𝐚𝐧𝐜𝐞: {stats['crit_chance']}\n"\
            f"𝐄𝐟𝐟𝐞𝐜𝐭𝐢𝐯𝐞 𝐂𝐫𝐢𝐭 𝐂𝐡𝐚𝐧𝐜𝐞: {stats['crit_chance']}\n"\
            f"𝐂𝐡𝐚𝐧𝐜𝐞 𝐭𝐨 𝐇𝐢𝐭: {stats['chance_to_hit']}%"
            info.add_field(name="Offense", value=offensive_stats_text)

            defensive_stats_text =\
            f"𝐋𝐢𝐟𝐞: {stats['life']}\n"\
            f"𝐋𝐢𝐟𝐞 𝐑𝐞𝐠𝐞𝐧: {stats['life_regen']}\n"\
            f"𝐄𝐧𝐞𝐫𝐠𝐲 𝐒𝐡𝐢𝐞𝐥𝐝: {stats['es']}\n"\
            f"𝐄𝐒 𝐑𝐞𝐠𝐞𝐧: {stats['es_regen']}\n"\
            f"𝐄𝐯𝐚𝐬𝐢𝐨𝐧: {stats['degen']}"
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
        asc_text = '\n'.join(stats['asc_nodes'])
        info.add_field(name="Ascendancies", value=asc_text, inline=True)
        keystones = '\n'.join(stats['keystones'])
        info.add_field(name="Keystones", value=keystones, inline=True)
        if pob:
            icon_url = class_icons[stats['ascendancy'].lower()] if stats['ascendancy'] != "None"\
                else class_icons[stats['class'].lower()]
        else:
            icon_url = class_icons[stats['class'].lower()]
        info.set_thumbnail(url=icon_url)
        return info

    async def make_responsive_embed(self, stats, ctx, pob=True):
        embed_dict = {}
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
        gem_groups_dict = self._gem_groups(stats['equipped'])
        responsive_dict['info'] = await self._info_dict(stats, pob)
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
        if gem_groups_dict:
            responsive_dict['gems'] = gem_groups_dict
        for key in responsive_dict:
            for index, field in enumerate(responsive_dict[key].fields):
                if field.value == '':
                    responsive_dict[key].set_field_at(index, name=field.name, value="None", inline=field.inline)
        upload = await self.bot.dump_channel.send(files=files)
        for attachment in upload.attachments:
            responsive_dict[attachment.filename.split('.')[0]].set_image(url=attachment.url)
        await responsive_embed(self.bot, responsive_dict, ctx)

    @commands.command()
    async def charinfo(self, ctx, account, character):
        """ Fetch character info for provided account and character """
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
        paste_keys = pastebin.fetch_paste_key(ctx.message.content)
        if not paste_keys: return
        xml = None
        paste_key = paste_keys[0]
        try:
            xml = await self.bot.loop.run_in_executor(None, pastebin.get_as_xml, paste_key)
        except:
            return
        if not xml: return
        stats = await self.bot.loop.run_in_executor(None, cache_pob_xml, xml, self.client)
        await self.make_responsive_embed(stats, ctx)


def setup(bot):
    bot.add_cog(PathOfExile(bot))