import threading
import socket
import typing
import json
from flask import Flask



# Define custom type hints
from ServerUtils import TYPE_POST, TYPE_POSTS
from Server import ServerController


class WebServerController:
    """Controls the web server, including both 
    the socket server for communicating with the client 
    and the flask server to serve GUI."""
    def __init__(self, server_callback : ServerController) -> None:
        """Constructor"""

        self.__socket_server : SocketServer = SocketServer(server_callback)
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
        self.app = Flask(__name__)
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

        self.__add_endpoint("/", self.__hello)


    def __hello(self):
        return 'Hello, World!'


    
class SocketServer:
    """Direct socket stream connections to the client."""

    SERVER_IP = "localhost"
    SERVER_PORT = 1234
    PROTOCOL_VERSION = "1.2"


    RESPONSE_UNAUTHENTICATED_ERROR : str = json.dumps({"error":"Unauthenticated request"})



    def __init__(self, server_callback : ServerController) -> None:
        """Constructor"""
        self.__server_callback : ServerController = server_callback

        self.__client_connections : typing.Dict[str, socket.socket] = {}


        self.__init_socket()



    def __init_socket(self) -> None:
        """Initialise the socket server."""
        self.__server_socket : socket.socket = socket.socket()
        self.__server_socket.bind((self.SERVER_IP, self.SERVER_PORT))
        self.__server_socket.listen(1)


    def start_listening(self) -> None:
        """Open the threads nessesary for running."""
        threading.Thread(target=self.__listen_for_connections).start()


    def __listen_for_connections(self) -> None:
        """Listen and accept incomming client conenctions."""
        
        client_socket : socket.socket
        
        while True:
            client_socket, addr = self.__server_socket.accept()
            
            # handshake with the client
            successful : bool 
            uuid : str
            successful, uuid = self.__process_handshake(client_socket)

            if not successful:
                # handshake unsuccesful
                client_socket.close()
                continue

            # add the client to list of connected clients
            self.__client_connections[uuid] = client_socket
            self.__server_callback.add_new_connected_user(uuid)

            # start listening to the client in another thread
            threading.Thread(target=self.__handle_client_socket, args=(uuid,)).start()

            print("Successfull connection from" , addr, "with uuid:",uuid)

    def __process_handshake(self, client : socket.socket) -> tuple[bool, str | None]:
        """Processes the handshake with the client. 
        Returns whether the handshake was succesful and the UUID of the connection.
        Handshake:
        C: {Protocol verison}
        S: Success {Client secret}
        """

        data : bytes = client.recv(1024)
        
        try:
            if not data:
                # No data recived, malformed handshake
                return False, None
        
            requested_version : str = data.decode("utf-8")
            
            if requested_version != self.PROTOCOL_VERSION:
                # Protocol version mismatch, void connection
                return False, None
            
            # return a UUID
            uuid : str = self.__server_callback.generate_uuid()

            # TODO send client secret not uuid
            client.send(("Success " + uuid).encode())
            
            # Valid handshake completed
            return True, uuid

        except:
            return False, None
    
    def __handle_client_socket(self, uuid : str) -> None:
        """Mainloop for handling and maintaining a socket connection with a client."""
        
        client : socket.socket = self.__client_connections[uuid]
        
        buffer_size : int = 1024

        while True:
            
            data : bytes = client.recv(buffer_size)

            if not data:
                # Connection closed
                break

            jsons : str = data.decode()

            responce : str = self.__handle_client_request(jsons, uuid)

            client.send(responce.encode())

        self.__handle_client_disconnect(uuid)

    def __handle_client_disconnect(self, uuid : str) -> None:
        """Logic called when a client disconnects."""

        client : socket.socket = self.__client_connections[uuid]
        client.close()

        self.__client_connections.pop(uuid)
        self.__server_callback.remove_connected_user(uuid)

    def __validate_authed_user(self, uuid : str, client_secret : str) -> bool:
        """Used to ensure that the client is authenticated under their respective uuid."""
        # TODO: change to keeping uuid private and checking client secret matches stored data about uuid
        if client_secret == uuid:
            return True
        else:
            return False

    def __handle_get_posts(self, json_data : typing.Dict, uuid : str) -> str:
        """Logic to handle a 'get posts' request from the client"""

        client_secret : str = json_data["csec"]
        
        if not self.__validate_authed_user(uuid, client_secret):
            return self.RESPONSE_UNAUTHENTICATED_ERROR

        username : str = self.__server_callback.get_username(uuid)

        posts : TYPE_POSTS = self.__server_callback.get_posts_for_user(username)
        response_json : dict = {
            "command":"PostDataResponse",
            "data":posts
        }

        return json.dumps(response_json)
    

    def __handle_add_post(self, json_data : typing.Dict, uuid : str) -> str:
        """Logic to handle a 'add post' request from the client"""

        client_secret : str = json_data["csec"]
        
        if not self.__validate_authed_user(uuid, client_secret):
            return self.RESPONSE_UNAUTHENTICATED_ERROR

        username : str = self.__server_callback.get_username(uuid)

        post : TYPE_POST = json_data["data"]
        self.__server_callback.add_post(post, username)

        response_json : dict = {
            "command":"AddPostResponse",
            "success":True
        }

        return json.dumps(response_json)
    

    def __handle_set_username(self, json_data : typing.Dict, uuid : str) -> str:
        """Logic to handle a 'set username' request from the client"""

        # TODO: replace with auth system

        client_secret : str = json_data["csec"]
        
        if not self.__validate_authed_user(uuid, client_secret):
            return self.RESPONSE_UNAUTHENTICATED_ERROR


        username : str = json_data["username"]

        self.__server_callback.set_username(username, uuid)

        response_json : dict = {
            "command":"SetUsernameResponse",
            "success":True
        }

        return json.dumps(response_json)


    def __handle_client_request(self, data : str, uuid : str) -> str:
        """Handles a single request from a client.
        Takes in data and uuid.
        Calls back to Server.ServerController to process request.
        Returns a json reply."""

        
        try:

            json_data : json.JSONDecoder = json.loads(data)

            command : str = json_data["command"]

            response : str = ""

            match (command):
                case "GetPosts":
                    
                    response = self.__handle_get_posts(json_data, uuid)

                case "AddPost":
                    
                    response = self.__handle_add_post(json_data, uuid)

                case "SetUsername":
                    
                    response = self.__handle_set_username(json_data, uuid)

            return response


        except Exception as e:
            print(e)
            return '{"error":"Malformed request"}'

    