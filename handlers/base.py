#!/usr/bin/env python3

import os

from aiohttp import web


class BaseHandler:
    def __init__(self, analyzer, bool_clf_dir, type_clf_dir):
        self.analyzer = analyzer
        self.bool_clf_dir = bool_clf_dir
        self.type_clf_dir = type_clf_dir

    def index(self, request):
        return web.Response(text='Please connect using socket.io too.')

    async def add_bool_classifier(self, request):
        data = await request.post()
        pkl = data['clf']
        content = pkl.file.read()

        filename = os.path.join(self.bool_clf_dir, pkl.filename)

        with open(filename, 'wb') as f:
            f.write(content)
            f.close()
        self.analyzer.load_bool(filename)

        return web.Response(text='Saved classifier {}'.format(pkl.filename))

    async def add_type_classifier(self, request):
        data = await request.post()
        pkl = data['clf']
        content = pkl.file.read()

        filename = os.path.join(self.type_clf_dir, pkl.filename)

        with open(filename, 'wb') as f:
            f.write(content)
            f.close()
        self.analyzer.load_type(filename)

        return web.Response(text='Saved classifier {}'.format(pkl.filename))
