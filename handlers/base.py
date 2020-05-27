#!/usr/bin/env python3

import os

from aiohttp import web


class BaseHandler:
    def __init__(self, analyzer, clf_dir):
        self.analyzer = analyzer
        self.clf_dir = clf_dir

    def index(self, request):
        return web.Response(text='Please connect using socket.io too.')

    async def add_classifier(self, request):
        data = await request.post()
        pkl = data['clf']
        content = pkl.file.read()

        filename = os.path.join(self.clf_dir, pkl.filename)

        with open(filename, 'wb') as f:
            f.write(content)
            f.close()
        self.analyzer.load(filename)

        return web.Response(text='Saved classifier {}'.format(pkl.filename))
