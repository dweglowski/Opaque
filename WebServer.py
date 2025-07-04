import threading
import socket
import random
import typing

class WebServerController:
    """Controls the web server, including both 
    the socket server for communicating with the client 
    and the flask server to serve GUI."""
    def __init__(self) -> None:
        """Constructor"""

        self.__socket_server : SocketServer = SocketServer()

    def start(self) -> None:
        """Start both servers."""
        self.__socket_server.start_listening()
    
class SocketServer:
    """Direct socket stream connections to the client."""

    SERVER_IP = "localhost"
    SERVER_PORT = 1234
    PROTOCOL_VERSION = "1.0"

    def __init__(self) -> None:
        """Constructor"""
        self.__client_connections : typing.Dict[str, socket.socket] = {}

        self.__init_socket()



    def __init_socket(self) -> None:
        """Initialise the socket server."""
        self.__server_socket = socket.socket()
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

            # start listening to the client in another thread
            threading.Thread(target=self.__handle_client_socket, args=(uuid,)).start()

            print("Successfull connection from" , addr, "with uuid:",uuid)

    def __generate_uuid(self) -> str:
        """Generate a random UUID to identify each connection."""
        return str(random.randint(0,1000000000000))

    def __process_handshake(self, client : socket.socket) -> tuple[bool, str | None]:
        """Processes the handshake with the client. 
        Returns whether the handshake was succesful and the UUID of the connection.
        Handshake:
        C: {Protocol verison}
        S: Success {UUID}
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
            uuid : str = self.__generate_uuid()

            client.send(uuid.encode())
            
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
                continue

            jsons : str = data.decode()

            responces : typing.List[str] = self.__handle_client_request(jsons, uuid)

            responce : str

            for responce in responces:
                client.send(responce.encode())


    def __handle_client_request(self, data : str, uuid : str) -> typing.List[str]:
        """Handles a single request from a client.
        Takes in data and uuid.
        Calls back to Server.ServerController to process request.
        Returns a list of json replies to be sent."""
        print(data)
        return ["{'action':'reply','text':'world'}"]


    