# http://poeurl.com/api/?shrink={%22url%22:%22https://www.pathofexile.com/passive-skill-tree/AAAABAMBAHpwm6FR-zeDAx7quvfX0PW2-o5kpys3ZsMJ62PviLmT8h3v66EvGyUfQR1PDkiMNkuutUjbXq6zBUJJUZEHQnrsGNfPlS6-iocTf8ZFfjQKDXxfalgHj0ZwUvrSjun3wVF0b57G93gvOw3B86aZES-TJx0UzRYBb9-K0NBGcRhq8NUXL21sgKSQ1hV-D8QsnL46lSCDCYnTdwcOXL6Au_wtH0yzLL9JsUGWtAycpI_6NbmsmMEAsZC4yqKjXGuEb6brV8kRD9lb96YRUOv1VdYrCsNtUDAfGIt6avp88JJ0ZOf5N9AfhEjndG0ZO3zpAioLBx4spl3yfOXK0-L3EZbUQvVLLag=%22}
import json
import urllib.request



def shrink_tree_url(tree):
    """
    Shrink url with poeurl
    :param tree:
    :return:
    """
    # sanitize
    tree = tree.strip()

    # build requesturl
    param = '{"url":"' + tree + '"}'
    url = 'http://poeurl.com/api/?shrink=' + param

    contents = urllib.request.urlopen(url).read().decode('utf-8')

    contents = json.loads(contents)
    if contents['url']:
        return 'http://poeurl.com/' + contents['url']
    else:
        raise ValueError("Unable to retrieve URL")
