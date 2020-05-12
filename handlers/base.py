#!/usr/bin/env python3

from aiohttp import web


class BaseHandler:
    def __init__(self):
        pass

    def index(self, request):
        return web.Response(text='Please connect using socket.io too.')
