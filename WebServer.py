import threading
import websockets
import asyncio
import typing
import json
import os
import flask
import websockets.asyncio
import websockets.asyncio.server



# Define custom type hints
from ServerUtils import TYPE_POST, TYPE_POSTS, TYPE_WEBSOCKET_CONNECTION, TYPE_JSON
from Server import ServerController


class WebServerController:
    """Controls the web server, including both 
    the socket server for communicating with the client 
    and the flask server to serve GUI."""
    def __init__(self, server_callback : ServerController) -> None:
        """Constructor"""

        self.__socket_server : WebsocketServerController = WebsocketServerController(server_callback)
        self.__webserver : GuiWebserver = GuiWebserver()

    def start(self) -> None:
        """Start both servers."""
        self.__socket_server.start_listening()
        self.__webserver.start()


class GuiWebserver:
    """Flask webserver to host the client facing website files."""

    HOST = "127.0.0.1"
    PORT = 5000

    def __init__(self) -> None:
        pass

    def start(self) -> None:
        threading.Thread(target=self.__start_threaded).start()
        
    def __start_threaded(self) -> None:

        template_dir : str = os.path.abspath('./Client/html')
        static_dir : str = os.path.abspath('./Client/static')

        self.app = flask.Flask(__name__, template_folder=template_dir, static_folder=static_dir)
        self.__define_endpoints()
        
        # TODO: switch to waitress before deploying anywhere beyond localhost
        assert self.HOST == "127.0.0.1", "Do not deploy flask server publicly with current config"
        self.app.run(host=self.HOST, port=self.PORT)
        #from waitress import serve
        # serve(self.app, host=self.HOST, port=self.PORT)

    def __add_endpoint(self, path : str, handler_function : typing.Callable, methods : typing.List[str] = ["Get"]) -> None:
        """Declares a new endpoint to flask and provides handler function."""
        self.app.add_url_rule(
            path, 
            view_func=handler_function, 
            methods=methods
        )

    def __define_endpoints(self) -> None:
        """Defines all the web endpoints and provides their handler functions."""

        self.__add_endpoint("/", self.__main_page)


    def __main_page(self):
        return flask.render_template("Main.html")


    
class WebsocketServerController:
    """Accepts and handles client websocket connections and creates a WebsocketServer for each connection."""

    SERVER_IP = "localhost"
    SERVER_PORT = 1234
    PROTOCOL_VERSION = "1.4"



    def __init__(self, server_callback : ServerController) -> None:
        """Constructor"""
        self.__server_callback : ServerController = server_callback

        self.__client_connections : typing.Dict[str, WebsocketServer] = {}


    def start_listening(self) -> None:
        """Open the threads nessesary for running."""
        threading.Thread(target=self.__start_listening_threaded).start()

    def __start_listening_threaded(self) -> None:
        """Starts the async connection listener in another thread."""
        asyncio.run(self.__listen_for_connections())


    async def __listen_for_connections(self) -> None:
        """Listen and accept incomming client conenctions."""
        
        async with websockets.serve(self.__handle_new_connection, self.SERVER_IP, self.SERVER_PORT):
            await asyncio.Future()


    async def __handle_new_connection(self, websocket : TYPE_WEBSOCKET_CONNECTION) -> None:
        """Handles a new client connecting and spawns a new WebsocketServer for the connection."""

        
        # handshake with the client
        successful : bool 
        uuid : str
        successful, uuid = await self.__process_handshake(websocket)

        if not successful:
            # handshake unsuccesful
            await websocket.close(code=1002, reason="Invalid handshake")
            return
        
        clientController : WebsocketServer = WebsocketServer(uuid, websocket, self.__server_callback, self)

        # add the client to list of connected clients
        self.__client_connections[uuid] = clientController
        self.__server_callback.add_new_connected_user(uuid)

        print("Successfull connection from", websocket.remote_address, "with uuid:",uuid)

        # start listening to the client
        await clientController.start_listening_to_client()


    async def __process_handshake(self, client : TYPE_WEBSOCKET_CONNECTION) -> tuple[bool, str | None]:
        """Processes the handshake with the client. 
        Returns whether the handshake was succesful and the UUID of the connection.
        Handshake:
        C: {"action":"handshake", "version":"[Protocol verison]"}
        S: {"action":"handshake", "result":"success", "client_secret":"[Client secret]"} 
        """

        data : str = await client.recv(decode=True)
        
        try:
            if not data:
                # No data recived, malformed handshake
                return False, None
            
            data_json : TYPE_JSON = json.loads(data)

            if data_json is None or data_json.get("action") != "handshake" or data_json.get("version") is None:
                # No data recived, malformed handshake
                return False, None
                 
            requested_version : str = data_json["version"]
            
            if requested_version != self.PROTOCOL_VERSION:
                # Protocol version mismatch, void connection
                return False, None
            
            # return a UUID
            uuid : str = self.__server_callback.generate_uuid()

            # TODO send client secret not uuid
            response : TYPE_JSON = {
                "action" : "handshake",
                "result" : "success",
                "client_secret" : uuid,
            }

            await client.send(json.dumps(response))
            
            # Valid handshake completed
            return True, uuid

        except:
            return False, None
        
    def handle_client_disconnect(self, uuid : str) -> None:
        """Logic called when a client disconnects."""
        print(uuid,"disconnected")
        self.__client_connections.pop(uuid)
        self.__server_callback.remove_connected_user(uuid)

    

    


class WebsocketServer:
    """Direct websocket connection to a single client and logic required to handle it."""

    RESPONSE_UNAUTHENTICATED_ERROR : str = json.dumps({"action":"error","reason":"Unauthenticated request"})

    def __init__(self, uuid : str, websocket : TYPE_WEBSOCKET_CONNECTION, server_callback : ServerController, controller_callback : WebsocketServerController) -> None:
        """Constructor"""

        self.__uuid : str = uuid

        self.__websocket : TYPE_WEBSOCKET_CONNECTION = websocket

        self.__server_callback : ServerController = server_callback
        self.__controller_callback : WebsocketServerController = controller_callback

        self.__connected : bool = True

        # create message queue for processing data in and data out
        self.__queue_data_out : typing.List[str] = []
        self.__queue_data_in : typing.List[str] = []

    async def start_listening_to_client(self) -> None:
        """Start revice and send mainloops for communicating with client."""
        await asyncio.gather(
            self.__send_data(),
            self.__receive_data(),
            self.__handle_data_mainloop()
        )

    async def __receive_data(self) -> None:
        async for message in self.__websocket:
            self.__queue_data_in.append(message)

        # client disconnected once loop exited
        self.__handle_disconnect()

    async def __send_data(self) -> None:
        while True:
            if len(self.__queue_data_out) == 0:
                # queue empty, wait then try again
                await asyncio.sleep(0.1)
                continue
            
            data : str = self.__queue_data_out.pop(0)
            await self.__websocket.send(data)

    def __send_response(self, data : str) -> None:
        """Adds data to a the outbound send queue."""
        self.__queue_data_out.append(data)

    def __handle_disconnect(self) -> None:
        """Called when the cleint disconnects, stops all loops."""
        self.__connected = False

        self.__queue_data_in.clear()
        self.__queue_data_out.clear()

        self.__controller_callback.handle_client_disconnect(self.__uuid)

    async def __handle_data_mainloop(self) -> None:
        """Mainloop constantly cheackign for reviced data in the queue, handling it and addind response to outbound queue."""
        
        while self.__connected:
            
            if len(self.__queue_data_in) == 0:
                # queue empty, wait then try again
                await asyncio.sleep(1)
                continue

            json_data : str = self.__queue_data_in.pop(0)

            self.__handle_client_request(json_data)

    def __validate_authed_user(self, client_secret : str) -> bool:
        """Used to ensure that the client is authenticated under their respective uuid."""
        # TODO: change to keeping uuid private and checking client secret matches stored data about uuid
        if client_secret == self.__uuid:
            return True
        else:
            return False
   
    def send_post_to_client(self, post : TYPE_POST) -> None:
        """Sends an update to the client containing another post."""
        
        response_json : dict = {
            "action":"update",
            "feed":"Posts",
            "data":post,
        }

        self.__send_response(json.dumps(response_json))


    def __handle_subscribe_to_posts(self, json_data : typing.Dict) -> None:
        """Logic to handle subscribing to posts"""

        client_secret : str = json_data["csec"]
        
        if not self.__validate_authed_user(client_secret):
            return self.RESPONSE_UNAUTHENTICATED_ERROR

        self.__server_callback.subscribe_client_to_posts_feed(self.__uuid, self.send_post_to_client)

        response_json : dict = {
            "action":"subscribe",
            "feed":"Posts",
            "success":True,
        }

        self.__send_response(json.dumps(response_json))

        # catch up on all existing posts
        self.__server_callback.send_existing_posts_to_client(self.__uuid)
        

    def __handle_add_post(self, json_data : typing.Dict) -> None:
        """Logic to handle a 'add post' request from the client"""

        client_secret : str = json_data["csec"]
        
        if not self.__validate_authed_user(client_secret):
            return self.RESPONSE_UNAUTHENTICATED_ERROR

        username : str = self.__server_callback.get_username(self.__uuid)

        post : TYPE_POST = json_data["data"]

        # reduce risk of json injection
        sanitised_post : TYPE_POST = {
            "to": post["to"],
            "content": post["content"], 
            }

        self.__server_callback.add_post(sanitised_post, username)

        response_json : dict = {
            "action":"result",
            "command":"AddPost",
            "success":True
        }

        self.__send_response(json.dumps(response_json))
    

    def __handle_set_username(self, json_data : typing.Dict) -> None:
        """Logic to handle a 'set username' request from the client"""

        # TODO: replace with auth system

        client_secret : str = json_data["csec"]
        
        if not self.__validate_authed_user(client_secret):
            return self.RESPONSE_UNAUTHENTICATED_ERROR


        username : str = json_data["username"]

        self.__server_callback.set_username(username, self.__uuid)

        response_json : dict = {
            "action":"result",
            "command":"SetUsername",
            "success":True
        }

        self.__send_response(json.dumps(response_json))

    def __handle_client_request(self, data : str) -> None:
        """Handles a single request from a client.
        Takes in data and uuid.
        Calls back to Server.ServerController to process request."""

        try:

            json_data : TYPE_JSON = json.loads(data)

            action : str = json_data["action"]

            if action == "command":

                command : str = json_data["command"]

                match (command):

                    case "AddPost":
                        
                        self.__handle_add_post(json_data)

                    case "SetUsername":
                        
                        self.__handle_set_username(json_data)

            elif action == "subscribe":

                feed : str = json_data["feed"]

                match (feed):
                    case "Posts":
                        self.__handle_subscribe_to_posts(json_data)

        except Exception as e:
            print(e)
            return '{"action":"error", "reason":"Malformed request"}'

    