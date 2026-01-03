import threading
import websockets
import asyncio
import typing
import json
import os
import io
import flask
import werkzeug.datastructures
import websockets.asyncio
import websockets.asyncio.server
from hashlib import sha256
from Datastructures import Queue



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
        self.__webserver : GuiWebserver = GuiWebserver(server_callback)

    def start(self) -> None:
        """Start both servers."""
        self.__socket_server.start_listening()
        self.__webserver.start()


class GuiWebserver:
    """Flask webserver to host the client facing website files."""

    HOST = "127.0.0.1"
    PORT = 5000

    def __init__(self, server_callback : ServerController) -> None:
        """Constructor"""
        self.__server_callback : ServerController = server_callback

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
        self.__add_endpoint("/uploads/profile_pictures/<path>", self.get_profile_picture)
        self.__add_endpoint("/upload/profile_picture/", self.upload_profile_picture, ["Post"])
        self.__add_endpoint("/uploads/post_pictures/<path>", self.get_post_picture)
        self.__add_endpoint("/upload/post_picture/", self.upload_post_picture, ["Post"])


    def __main_page(self):
        return flask.render_template("Main.html")
    
    def get_profile_picture(self, path: str):

        uuid : str = path.strip(".png")
        
        file_data : bytes = self.__server_callback.get_profile_picture(uuid)

        return flask.send_file(
            io.BytesIO(file_data),
            mimetype="image/png"
        )
    
    def upload_profile_picture(self):

        img : werkzeug.datastructures.FileStorage = flask.request.files['image']

        # read file, up to a max of 1MB (prevents reading to large of a buffer for profile pic)
        MAX_SIZE = 1 * 1024 * 1024
        file_data : bytes = img.stream.read(MAX_SIZE)

        uuid : str = self.__server_callback.upload_profile_picture(file_data)
        if uuid == "":
            # failed for some reason, e.g. too big file or invalid file type
            return flask.abort(415)
        
        return uuid
    
      
    def get_post_picture(self, path: str):

        uuid : str = path.strip(".png")
        
        file_data : bytes = self.__server_callback.get_post_picture(uuid)

        return flask.send_file(
            io.BytesIO(file_data),
            mimetype="image/png"
        )

    def upload_post_picture(self):
        img : werkzeug.datastructures.FileStorage = flask.request.files['image']

        # read file, up to a max of 10MB (prevents reading to large of a buffer)
        MAX_SIZE = 10 * 1024 * 1024
        file_data : bytes = img.stream.read(MAX_SIZE)

        uuid : str = self.__server_callback.upload_post_picture(file_data)
        if uuid == "":
            # failed for some reason, e.g. too big file or invalid file type
            return flask.abort(415)
        
        return uuid



    
class WebsocketServerController:
    """Accepts and handles client websocket connections and creates a WebsocketServer for each connection."""

    SERVER_IP = "localhost"
    SERVER_PORT = 1234
    PROTOCOL_VERSION = "1.5"



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
            uuid : str = self.__server_callback.generate_uuid_for_connection()
            
            # sets the client secret to a hash of the uuid to prevent exposing internal uuid to client
            client_secret : str = sha256(uuid.encode()).hexdigest()

            response : TYPE_JSON = {
                "action" : "handshake",
                "result" : "success",
                "client_secret" : client_secret,
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

    RESPONSE_SESSION_MISSMATCH_ERROR : str = json.dumps({"action":"error","reason":"Session missmatch, invalid client secret"})
    RESPONSE_UNAUTHENTICATED_ERROR : str = json.dumps({"action":"error","reason":"Not authenticated"})

    def __init__(self, uuid : str, websocket : TYPE_WEBSOCKET_CONNECTION, server_callback : ServerController, controller_callback : WebsocketServerController) -> None:
        """Constructor"""

        self.__uuid : str = uuid

        self.__websocket : TYPE_WEBSOCKET_CONNECTION = websocket

        self.__server_callback : ServerController = server_callback
        self.__controller_callback : WebsocketServerController = controller_callback

        self.__connected : bool = True

        # create message queue for processing data in and data out
        self.__queue_data_out : Queue[str] = Queue()
        self.__queue_data_in : Queue[str] = Queue()

    async def start_listening_to_client(self) -> None:
        """Start revice and send mainloops for communicating with client."""
        await asyncio.gather(
            self.__send_data(),
            self.__receive_data(),
            self.__handle_data_mainloop()
        )

    async def __receive_data(self) -> None:
        async for message in self.__websocket:
            self.__queue_data_in.enqueue(message)

        # client disconnected once loop exited
        self.__handle_disconnect()

    async def __send_data(self) -> None:
        while True:
            if len(self.__queue_data_out) == 0:
                # queue empty, wait then try again
                await asyncio.sleep(0.1)
                continue
            
            data : str = self.__queue_data_out.dequeue()
            await self.__websocket.send(data)

    def __send_response(self, data : str) -> None:
        """Adds data to a the outbound send queue."""
        self.__queue_data_out.enqueue(data)

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
                await asyncio.sleep(0.1)
                continue

            json_data : str = self.__queue_data_in.dequeue()

            self.__handle_client_request(json_data)

    def __validate_session(self, client_secret : str) -> bool:
        """Used to ensure that the client matches their session's uuid."""
        if client_secret == sha256(self.__uuid.encode()).hexdigest():
            return True
        else:
            return False
        
    def __validate_authenticated_user(self) -> bool:
        """Used to ensure that the client matches their session's uuid."""
        return self.__server_callback.is_logged_in(self.__uuid)
   
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
        
        if not self.__validate_session(client_secret):
            return self.RESPONSE_SESSION_MISSMATCH_ERROR

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
        
        if not self.__validate_session(client_secret):
            return self.RESPONSE_SESSION_MISSMATCH_ERROR

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
    

    def __handle_request_salt(self, json_data : typing.Dict) -> None:
        """Logic to provide a password salt to the user"""

        client_secret : str = json_data["csec"]
        
        if not self.__validate_session(client_secret):
            return self.RESPONSE_SESSION_MISSMATCH_ERROR

        username : str = json_data["username"]

        response_json : dict = {}

        salt: str = self.__server_callback.get_password_salt(username, self.__uuid)

    
        response_json = {
            "action":"result",
            "command":"RequestPasswordSalt",
            "data":salt,
        }

        self.__send_response(json.dumps(response_json))
    

    def __handle_login(self, json_data : typing.Dict) -> None:
        """Logic to handle a login request from the client"""

        client_secret : str = json_data["csec"]
        
        if not self.__validate_session(client_secret):
            return self.RESPONSE_SESSION_MISSMATCH_ERROR

        username : str = json_data["username"]
        hash : str = json_data["hash"]

        response_json : dict = {}

        success : bool
        fail_reason : str

        success, fail_reason = self.__server_callback.login(username, hash, self.__uuid)

        if not success:
            response_json = {
                "action":"result",
                "command":"Login",
                "success":False,
                "reason":fail_reason,
            }

        else:
            response_json = {
                "action":"result",
                "command":"Login",
                "success":True
            }

        self.__send_response(json.dumps(response_json))

    def __handle_signup(self, json_data : typing.Dict) -> None:
        """Logic to handle a signup request from the client"""

        # TODO: replace with auth system

        client_secret : str = json_data["csec"]
        
        if not self.__validate_session(client_secret):
            return self.RESPONSE_SESSION_MISSMATCH_ERROR


        username : str = json_data["username"]
        display_name : str = json_data["displayname"]
        hash : str = json_data["hash"]
        salt : str = json_data["salt"]

        success : bool
        fail_reason : str

        success, fail_reason = self.__server_callback.signup(username, display_name, hash, salt, self.__uuid)

        if not success:
            response_json = {
                "action":"result",
                "command":"Signup",
                "success":False,
                "reason":fail_reason,
            }

        else:

            response_json : dict = {
                "action":"result",
                "command":"Signup",
                "success":True
            }

        self.__send_response(json.dumps(response_json))

    def __handle_update_profile_picture(self, json_data : typing.Dict) -> None:
        """Logic to handle an update profile picture request from the client"""

        client_secret : str = json_data["csec"]
        
        if not self.__validate_session(client_secret):
            return self.RESPONSE_SESSION_MISSMATCH_ERROR
        
        if not self.__validate_authenticated_user():
            return self.RESPONSE_UNAUTHENTICATED_ERROR
        
        pictureUUID : str = json_data["pictureUUID"]

        self.__server_callback.update_profile_picture(self.__uuid, pictureUUID)

        response_json = {
            "action":"result",
            "command":"UpdateProfilePicture",
            "success":True,
        }


        self.__send_response(json.dumps(response_json))

    def __handle_get_profile_info(self, json_data : typing.Dict) -> None:
        """Logic to handle a get profile info request from the client"""

        client_secret : str = json_data["csec"]
        
        if not self.__validate_session(client_secret):
            return self.RESPONSE_SESSION_MISSMATCH_ERROR
        
        if not self.__validate_authenticated_user():
            return self.RESPONSE_UNAUTHENTICATED_ERROR

        data: typing.Dict[str,str] = self.__server_callback.get_profile_info(self.__uuid)

        response_json = {
            "action":"result",
            "command":"GetProfileInfo",
            "data":data,
        }


        self.__send_response(json.dumps(response_json))

    def __handle_user_search(self, json_data : typing.Dict) -> None:
        """Logic to handle a user search request from the client"""

        client_secret : str = json_data["csec"]
        
        if not self.__validate_session(client_secret):
            return self.RESPONSE_SESSION_MISSMATCH_ERROR
        
        username = json_data["username"]

        success: bool
        user_info: typing.Dict[str,str] 
        success, user_info = self.__server_callback.user_search(self.__uuid, username)

        response_json = {
            "action":"result",
            "command":"UserSearch",
            "success": success,
            "data":user_info,
        }


        self.__send_response(json.dumps(response_json))

    def __handle_user_search_suggestions(self, json_data : typing.Dict) -> None:
        """Logic to handle providing suggestions for user search"""

        client_secret : str = json_data["csec"]
        
        if not self.__validate_session(client_secret):
            return self.RESPONSE_SESSION_MISSMATCH_ERROR
        
        partial_username = json_data["username"]

        potential_usernames: typing.List[str] = self.__server_callback.user_search_suggestions(partial_username)

        response_json = {
            "action":"result",
            "command":"UserSearchSuggestions",
            "data":potential_usernames,
        }

        self.__send_response(json.dumps(response_json))

    def __handle_user_add_connection(self, json_data : typing.Dict) -> None:
        """Logic to handle adding and removing connections between users"""

        client_secret : str = json_data["csec"]
        
        if not self.__validate_session(client_secret):
            return self.RESPONSE_SESSION_MISSMATCH_ERROR
        
        connected_username : str = json_data["username"]
        connection_type : str = json_data["type"]
        add : bool = json_data["add"]

        self.__server_callback.handle_user_add_connection(self.__uuid, connected_username, connection_type, add)

        response_json = {
            "action":"result",
            "command":"AddUserConnection",
            "success":True,
        }

        self.__send_response(json.dumps(response_json))

    def __handle_post_filter_request(self, json_data : typing.Dict) -> None:
        """Called when a user request filter posts"""

        client_secret : str = json_data["csec"]
        
        if not self.__validate_session(client_secret):
            return self.RESPONSE_SESSION_MISSMATCH_ERROR
        
        filter_type : str = json_data["filter"]


        # catch up on all existing posts
        self.__server_callback.send_existing_posts_to_client(self.__uuid, filter_type = filter_type)

        response_json = {
            "action":"result",
            "command":"RequestFilteredPosts",
            "success":True,
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

                    case "RequestPasswordSalt":
                        
                        self.__handle_request_salt(json_data)

                    case "Login":
                        
                        self.__handle_login(json_data)

                    case "Signup":
                        
                        self.__handle_signup(json_data)

                    case "UpdateProfilePicture":
                        
                        self.__handle_update_profile_picture(json_data)

                    case "GetProfileInfo":
                        
                        self.__handle_get_profile_info(json_data)

                    case "UserSearch":
                        
                        self.__handle_user_search(json_data)

                    case "UserSearchSuggestions":
                        
                        self.__handle_user_search_suggestions(json_data)

                    case "AddUserConnection":
                        
                        self.__handle_user_add_connection(json_data)

                    case "RequestFilteredPosts":
                        
                        self.__handle_post_filter_request(json_data)

            elif action == "subscribe":

                feed : str = json_data["feed"]

                match (feed):
                    case "Posts":
                        self.__handle_subscribe_to_posts(json_data)

        except Exception as e:
            print(e)
            return '{"action":"error", "reason":"Malformed request"}'
