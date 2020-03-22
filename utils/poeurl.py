# Original from https://github.com/FWidm/discord-pob
# http://poeurl.com/api/?shrink={%22url%22:%22https://www.pathofexile.com/passive-skill-tree/AAAABAMBAHpwm6FR-zeDAx7quvfX0PW2-o5kpys3ZsMJ62PviLmT8h3v66EvGyUfQR1PDkiMNkuutUjbXq6zBUJJUZEHQnrsGNfPlS6-iocTf8ZFfjQKDXxfalgHj0ZwUvrSjun3wVF0b57G93gvOw3B86aZES-TJx0UzRYBb9-K0NBGcRhq8NUXL21sgKSQ1hV-D8QsnL46lSCDCYnTdwcOXL6Au_wtH0yzLL9JsUGWtAycpI_6NbmsmMEAsZC4yqKjXGuEb6brV8kRD9lb96YRUOv1VdYrCsNtUDAfGIt6avp88JJ0ZOf5N9AfhEjndG0ZO3zpAioLBx4spl3yfOXK0-L3EZbUQvVLLag=%22}
import json

import aiohttp


async def shrink_tree_url(tree):
    """
    Shrink url via poeurl.com
    :param tree:
    :return:
    """
    # build request url
    params = '{"url":"' + tree.strip() + '"}'
    url = 'http://poeurl.com/api/?shrink=' + params

    async with aiohttp.ClientSession() as client:
        async with client.get(url) as session:
            response = await session.text()
            response = json.loads(response)

    url = response.get('url')
    if not url:
        raise ValueError("Unable to retrieve URL")

    return 'http://poeurl.com/' + url
