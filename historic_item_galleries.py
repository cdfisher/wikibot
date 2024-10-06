# MIT License
#
# Copyright (c) 2024 Chris Fisher ("cdfisher")
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import re
import sys

import bot.mwbot as mw
import requests
import mwparserfromhell

from gallery_entry import GalleryListEntry

API_URL = 'https://oldschool.runescape.wiki/api.php'

# load user agent from file
try:
    with open(".\\bot\\agent.txt", 'r') as uafile:
        agent = uafile.read().strip(" \r\n")
except FileNotFoundError:
    # if no user agent available, exit with an error
    print('User agent file not found')
    sys.exit(1)

# Log into bot using credentials for wiki bot account
try:
    bot = mw.Mwbot(creds_file='.\\bot\\creds.file')
except FileNotFoundError:
    # if no credentials are found, exit with an error
    print('File with bot account credentials not found')
    sys.exit(1)

bot.login()

# get set of page IDs for pages using {{Infobox Item}}
members = bot.transcludedin('Template: Infobox Item')

id_set = set()
for _ in members:
    for k in _.keys():
        id_set.add(_[k])


# Fetch page contents and name fron the page ID
def parse(page_id: int):
    params = {
        "action": "query",
        "prop": "revisions",
        "rvprop": "content",
        "rvslots": "main",
        "rvlimit": 1,
        "pageids": page_id,
        "format": "json",
        "formatversion": "2",
    }
    headers = {"User-Agent": agent}
    req = requests.get(API_URL, headers=headers, params=params)
    try:
        res = req.json()
        pagename = res["query"]["pages"][0]["title"]
        revision = res["query"]["pages"][0]["revisions"][0]
        text = revision["slots"]["main"]["content"]
        return mwparserfromhell.parse(text), pagename
    except requests.exceptions.JSONDecodeError:
        print(f'JSONDecodeError for ID {page_id}, \n{req}')
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    except:
        print(f'Exception from ID {page_id}\n')


# Check if page has a "Gallery (Historical)" section
def has_gallery(page):
    headings = page.filter_headings(recursive=True)
    for h in headings:
        # matching on "historic" instead of "gallery" because there are some non-historical galleries on
        # pages, which isn't what we're after here
        if re.search(r"historic", str(h.title), re.IGNORECASE) is not None:
            print(h.title)
            return True, str(h.title)
    return False, ""


entries = []

i = 0
n_ids = len(id_set)
for _ in id_set:
    i += 1

    print(f'Checking page {i} of {n_ids}) {_}')

    try:
        mwtext, name = parse(_)
        # Ignore the two common cases one might expect to see outside of mainspace
        if name.startswith('User:') or name.startswith('Template:'):
            print(f'Skipping page: {name}')
            continue
    except requests.exceptions.JSONDecodeError as e:
        print(f'JSONDecodeError for ID {_}')
        continue
    except TypeError:
        print(f'Exception for ID {_}')
        continue

    print(f'Page: {name}')

    templates = mwtext.filter_templates(recursive=True)

    for t in templates:
        if t.name.matches('Infobox Item'):
            # check if there's a "release param" that contains "2007"
            # we want prior to 10 August 2007 but this is a good rough approach for now
            if t.has('release'):
                val = t.get('release').value.strip(' \n')
                val = re.sub("(<!--.*?-->)", "", val, flags=re.DOTALL)
                if re.search(r"200[0-7]", val) is not None:
                    gal, head = has_gallery(mwtext)
                    if gal:
                        entries.append(GalleryListEntry(name, head, val))


                # check for multiple versions
                n = 0
                while True:
                    n += 1
                    if t.has(f'version{n}'):
                        if t.has(f'release{n}'):
                            val = t.get(f'release{n}').value.strip(' \n')
                            val = re.sub("(<!--.*?-->)", "", val, flags=re.DOTALL)
                            if re.search(r"200[0-7]", val) is not None:
                                # call the check for gallery func
                                gal, head = has_gallery(mwtext)
                                if gal:
                                    entries.append(GalleryListEntry(name, head, val))

                        else:
                            continue
                    else:
                        break

            else:
                # check for multiple versions
                n = 0
                while True:
                    n += 1
                    if t.has(f'version{n}'):
                        if t.has(f'release{n}'):
                            val = t.get(f'release{n}').value.strip(' \n')
                            val = re.sub("(<!--.*?-->)", "", val, flags=re.DOTALL)
                            if re.search(r"200[0-7]", val) is not None:
                                # call the check for gallery func
                                gal, head = has_gallery(mwtext)
                                if gal:
                                    entries.append(GalleryListEntry(name, head, val))

                        else:
                            continue
                    else:
                        break

        else:
            continue


with open('galleries.csv', 'w') as outfile:
    outfile.write("page_name,header,release\n")
    for e in entries:
        outfile.write(f"{e}\n")
