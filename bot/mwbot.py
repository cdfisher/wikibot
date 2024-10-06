#!/usr/bin/env python
# -*- coding: latin-1 -*-
import requests
import mwparserfromhell
import urllib3

urllib3.disable_warnings()

API_URL = 'https://oldschool.runescape.wiki/api.php'


class Mwbot():

    # debug determines if there should be extra status messages
    def __init__(self, creds_file='creds.file', debug=False, api_url=API_URL):
        self.debug = debug
        self.api_url = api_url
        with open(creds_file) as f:
            self.username, self.password = f.read().split('\n')
        self.session, self.token = self.login()

    def login(self):
        session = requests.Session()
        r1 = session.get(self.api_url, params={
            'format': 'json',
            'action': 'query',
            'meta': 'tokens',
            'type': 'login',
        }, verify=False)

        r2 = session.post(self.api_url, data={
            'format': 'json',
            'action': 'login',
            'lgname': self.username,
            'lgpassword': self.password,
            'lgtoken': r1.json()['query']['tokens']['logintoken'],
        })
        if r2.json()['login']['result'] != 'Success':
            raise RuntimeError(r2.json()['login']['reason'])

        r3 = session.get(self.api_url, params={
            'format': 'json',
            'action': 'query',
            'meta': 'tokens',
        })
        return session, r3.json()['query']['tokens']['csrftoken']

    def query(self, params):
        res = self.session.get(self.api_url, params=params)
        return res

    def parse(self, title):
        url = "https://oldschool.runescape.wiki/w/" + str(title) + "?action=raw"
        data = {
            "action": "query",
            "prop": "revisions",
            "rvlimit": 1,
            "rvprop": "content",
            "format": "json",
            "titles": title
        }
        req = self.session.get(url, data=data)
        print(req)
        text = req.text
        return mwparserfromhell.parse(text)

    def post(self, summary, title, text, baserevid=None):
        data = {
            'format': 'json',
            'action': 'edit',
            'assert': 'user',
            'bot': 1,
            'minor': 1,
            'text': text,
            'summary': summary,
            'title': title,
            'token': self.token,
        }
        if baserevid:
            data['baserevid'] = baserevid

        r4 = self.session.post(self.api_url, data=data)

        # print(r4.headers)

        return r4

    def move(self, reason, from_page, to_page, make_redirect=True):
        params = {
            'action': 'move',
            'format': 'json',
            'from': from_page,
            'to': to_page,
            'reason': reason,
            'token': self.token,
        }

        if not make_redirect:
            params['noredirect'] = 'true'

        return self.session.post(self.api_url, data=params)

    def delete(self, reason, title):
        params = {
            'action': 'delete',
            'format': 'json',
            'title': title,
            'reason': reason,
            'token': self.token,
        }

        return self.session.post(self.api_url, data=params)

    def hide_log(self, logid, hide, reason):
        params = {
            'action': 'revisiondelete',
            'format': 'json',
            'type': 'logging',
            'reason': reason,
            'hide': hide,
            'ids': logid,
            'token': self.token,
        }

        return self.session.post(self.api_url, data=params)

    def categorymembers(self, titles):
        params = {
            "action": "query",
            "format": "json",
            "list": "categorymembers",
            "cmlimit": "max",
            "cmtitle": titles,
        }
        res = self.query(params).json()
        output = res["query"]["categorymembers"]
        while "continue" in res:
            params["cmcontinue"] = res["continue"]["cmcontinue"]
            res = self.query(params).json()
            output.extend(res["query"]["categorymembers"])

            if self.debug:
                print('Category query:', len(output))

        return output

    # NOTE: PrefixSearch is not the same as PrefixIndex.
    # You probably don't want this ever.
    def prefixsearch(self, prefix):
        params = {
            "action": "query",
            "format": "json",
            "list": "prefixsearch",
            "pslimit": "max",
            "pssearch": prefix,
        }
        res = self.query(params).json()
        output = res["query"]["prefixsearch"]
        while "continue" in res:
            params["psoffset"] = res["continue"]["psoffset"]
            res = self.query(params).json()
            output.extend(res["query"]["prefixsearch"])

            if self.debug:
                print('Prefixsearch query:', len(output))

        return output

    def prefixindex(self, prefix, ns='0'):
        params = {
            "action": "query",
            "format": "json",
            "list": "allpages",
            "aplimit": "max",
            "apnamespace": str(ns),
            "apprefix": prefix,
        }
        res = self.query(params).json()
        print(res)
        output = res["query"]["allpages"]
        while "continue" in res:
            params["apcontinue"] = res["continue"]["apcontinue"]
            res = self.query(params).json()
            output.extend(res["query"]["allpages"])

            if self.debug:
                print('PrefixIndex query:', len(output))

        return output

    def transcludedin(self, titles, namespace='*'):
        params = {
            "action": "query",
            "format": "json",
            "prop": "transcludedin",
            "tilimit": "max",
            "tiprop": "pageid",
            "titles": titles,
            "tinamespace": namespace,
        }
        res = self.query(params).json()
        page_output = list(res["query"]["pages"].values())[0]
        if "transcludedin" not in page_output:
            return []
        output = page_output["transcludedin"]
        while "continue" in res:
            params["ticontinue"] = res["continue"]["ticontinue"]
            res = self.query(params).json()
            pages = res["query"]["pages"]
            new_output = list(pages.values())[0]["transcludedin"]
            output.extend(new_output)

            if self.debug:
                print('transcludedin query:', len(output))

        return output

    def transcludedin_generator(self, titles):
        params = {
            "action": "query",
            "format": "json",
            "generator": "transcludedin",
            "gtilimit": "max",
            "titles": titles,
            "prop": "revisions",
            "rvprop": "content",
        }
        res = self.query(params).json()
        output = {}
        pages = res["query"]["pages"]
        for pageid, page in pages.items():
            if 'revisions' in page:
                output[page['pageid']] = page

        while "continue" in res:
            # print('CONTINUE',res["continue"])
            if "gticontinue" in res["continue"]:
                params["gticontinue"] = res["continue"]["gticontinue"]
            if "rvcontinue" in res["continue"]:
                params["rvcontinue"] = res["continue"]["rvcontinue"]
            res = self.query(params).json()
            pages = res["query"]["pages"]
            for pageid, page in pages.items():
                if 'revisions' in page:
                    output[page['pageid']] = page

            if self.debug:
                print('transcludedin query:', len(output))

        return output

    def revisions(self, ids):
        params = {
            "action": "query",
            "prop": "revisions",
            "rvprop": "content|ids",
            "format": "json",
            "pageids": ids
        }
        return self.query(params).json()

    def revisions_by_title(self, titles):
        params = {
            "action": "query",
            "prop": "revisions",
            "rvprop": "user|content|ids",
            "rvlimit": "max",
            "format": "json",
            "rvslots": "*",
            "titles": titles
        }
        return self.query(params).json()

    def allpages(self, ns=0, apfilterredir="nonredirects"):
        params = {
            "action": "query",
            "format": "json",
            "list": "allpages",
            "aplimit": "max",
            "apfilterredir": apfilterredir,
            "apnamespace": ns,
        }
        res = self.query(params).json()
        if 'query' not in res:
            return []
        output = res["query"]["allpages"]
        while "continue" in res:
            params["apcontinue"] = res["continue"]["apcontinue"]
            res = self.query(params).json()
            pages = res["query"]["allpages"]
            output.extend(pages)

            if self.debug:
                print('allpages query:', len(output))

        return output

    def allpages_generator(self, ns=0):
        params = {
            "action": "query",
            "format": "json",
            "generator": "allpages",
            "gaplimit": "max",
            "gapfilterredir": "nonredirects",
            "gapnamespace": ns,
            "prop": "revisions",
            "rvprop": "content",
        }
        res = self.query(params).json()
        output = {}
        pages = res["query"]["pages"]
        for pageid, page in pages.items():
            if 'revisions' in page:
                output[page['pageid']] = page

        while "continue" in res:
            # print('CONTINUE',res["continue"])
            if "gapcontinue" in res["continue"]:
                params["gapcontinue"] = res["continue"]["gapcontinue"]
            if "rvcontinue" in res["continue"]:
                params["rvcontinue"] = res["continue"]["rvcontinue"]
            res = self.query(params).json()
            pages = res["query"]["pages"]
            for pageid, page in pages.items():
                if 'revisions' in page:
                    output[page['pageid']] = page

            if self.debug:
                print('allpages query:', len(output))

        return output

    def imageinfo(self, pageids):
        params = {
            "action": "query",
            "format": "json",
            "prop": "imageinfo",
            "iiprop": "size|user|timestamp",
            "pageids": pageids,
        }
        res = self.query(params).json()
        return res

    def imageinfo_by_title(self, titles):
        if type(titles) == type([]):
            titles = '|'.join(titles)
        params = {
            "action": "query",
            "format": "json",
            "prop": "imageinfo",
            "iiprop": "size|user|timestamp",
            "titles": titles,
        }
        res = self.query(params).json()
        return res

    def backlinks(self, pageid):
        params = {
            "action": "query",
            "format": "json",
            "list": "backlinks",
            "bllimit": "max",
            "blredirect": "true",
            "blfilterredir": "nonredirects",
            "blpageid": pageid,
        }
        res = self.query(params).json()
        output = res["query"]["backlinks"]
        while "continue" in res:
            params["blcontinue"] = res["continue"]["blcontinue"]
            res = self.query(params).json()
            pages = res["query"]["backlinks"]
            output.extend(pages)

            if self.debug:
                print('backlinks query:', len(output))

        return output

    def links(self, pageids):
        params = {
            "action": "query",
            "format": "json",
            "generator": "links",
            "gpllimit": "max",
            "pageids": pageids,
            "redirects": "true",
        }
        res = self.query(params).json()
        output = res["query"]["pages"]

        while "continue" in res:
            params["gplcontinue"] = res["continue"]["gplcontinue"]
            res = self.query(params).json()
            pages = res["query"]["pages"]
            new_output = list(pages.values())
            output.extend(new_output)

            if self.debug:
                print('links query:', len(output))

        return output

    def thanks(self):
        params = {
            "action": "query",
            "format": "json",
            "list": "logevents",
            "letype": "thanks",
            "lelimit": "max",
        }
        res = self.query(params).json()
        output = res["query"]["logevents"]

        while "continue" in res:
            params["lecontinue"] = res["continue"]["lecontinue"]
            res = self.query(params).json()
            pages = res["query"]["logevents"]
            new_output = list(pages.values())
            output.extend(new_output)

            if self.debug:
                print('thanks query:', len(output))

        return output

    # https://oldschool.runescape.wiki/api.php?action=query&list=logevents&titles=Talk:Cormorant
    def logevents_by_title(self, title):
        params = {
            "action": "query",
            "format": "json",
            "list": "logevents",
            "letitle": title,
        }
        return self.query(params).json()
