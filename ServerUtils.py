import typing

import websockets.asyncio.server

# define custom types for server

TYPE_POST = typing.Dict[str,str]
TYPE_POSTS = typing.List[TYPE_POST]
TYPE_WEBSOCKET_CONNECTION = websockets.asyncio.server.ServerConnection
TYPE_JSON = (typing.Dict | typing.List)