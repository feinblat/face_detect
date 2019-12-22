import dataclasses
import logging
import os
from json import JSONDecodeError

from aiohttp import web

from best_smile_handler import BestSmileHandler, ImageNotExistException

MAX_ITEMS_TO_PROCESS = 100


class InvalidPathException(Exception):
    def __init__(self, path):
        self._path = path

    def __str__(self):
        return f'{self._path} is invalid path'


class BestSmileWebServer:
    def __init__(self, api_key: str, base_path: str):
        app = web.Application()
        app.router.add_post("/", self._request_handler)
        self._best_smile_worker = BestSmileHandler(key=api_key, base_path=base_path)
        self._base_path = os.path.abspath(base_path)
        self.app = app
        self._log = logging.getLogger('BestSmileWebServer')

    async def _request_handler(self, request: web.Request):
        """
        :param request: the request has to contain json with lists of paths
        :return:
        """
        content_type = request.headers.get('content-type')
        if not content_type or content_type.lower() != 'application/json':
            raise web.HTTPUnsupportedMediaType(text='content-type should be application/json')
        if not request.can_read_body:
            raise web.HTTPBadRequest(text='Api requires a Json list of images paths')
        try:
            req_json = await request.json()
        except JSONDecodeError:
            raise web.HTTPBadRequest(text='error decoding json')
        if not isinstance(req_json, list):
            raise web.HTTPBadRequest(text='unexpected json: list expected')
        if len(req_json) == 0:
            raise web.HTTPBadRequest(text=f'the request is empty')
        elif len(req_json) > 100:
            raise web.HTTPBadRequest(text=f'the request is too big >{MAX_ITEMS_TO_PROCESS}')
        try:
            for path in req_json:
                self._validate_path(path)
        except InvalidPathException:
            raise web.HTTPBadRequest(text='request contains invalid path')
        try:
            result = await self._best_smile_worker.handle_request(req_json)
        except ImageNotExistException as e:
            raise web.HTTPBadRequest(text=f'file {e.path} does not exist')
        return web.json_response(dataclasses.asdict(result))

    def _validate_path(self, path):
        """
        security check for directory traversal attacks
        :param path:
        :return:
        """
        if not os.path.abspath(os.path.join(self._base_path, path)).startswith(self._base_path):
            raise InvalidPathException(path)
