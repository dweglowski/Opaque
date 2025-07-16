import socket
import json
import typing

# Define custom type hints
from ClientUtils import TYPE_POST, TYPE_POSTS


class SocketAPI:
    """Websocket connection to the server."""
    SERVER_IP = "localhost"
    SERVER_PORT = 1234
    PROTOCOL_VERSION = "1.1"

    def __init__(self) -> None:
        pass

    def __init_socket_connection(self) -> None:
        """Initialise the socket connection."""
        self.client_socket : socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
    def connect(self) -> None:
        """Start the connection to the server."""
        self.__init_socket_connection()
        self.__handshake()

    def __handshake(self) -> None:
        """Performs the required handshake with the server."""
        """
        C: {Protocol verison}
        S: Success {UUID}
        """
        self.client_socket.connect((self.SERVER_IP, self.SERVER_PORT))
        self.client_socket.sendall(self.PROTOCOL_VERSION.encode())
        handshake_reply : bytes = self.client_socket.recv(1024)

        handshake_reply_str : str = handshake_reply.decode()

        if handshake_reply_str.startswith("Success "):
            # Successful handshake, obtain UUID
            self.uuid = handshake_reply_str.split(" ")[1]

    def get_posts(self, username : str) -> TYPE_POSTS:
        """Request all posts from the server."""
        
         # compose request json
        request_json : dict = {
                        "command":"GetPosts",
                        "username": username
                    }
        
        request = json.dumps(request_json).encode()

        # send request
        self.client_socket.send(request)

        # await response
        response : str = self.client_socket.recv(1024)

        # decode response and extract posts
        response_json : json.JSONDecoder = json.loads(response)

        posts : TYPE_POSTS = response_json["data"]

        return posts

    def add_post(self, post : TYPE_POST) -> None:
        """Sends a new post to the server."""

        # compose request json
        request_json : dict = {
                        "command":"AddPost",
                        "data":post
                    }
        
        request = json.dumps(request_json).encode()

        # send request
        self.client_socket.send(request)

        # await confirmation
        response = self.client_socket.recv(1024)

    def close(self) -> None:
        """Terminates the server connection."""
        self.client_socket.close()