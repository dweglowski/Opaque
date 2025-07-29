export {SocketAPI};

class SocketAPI {

    /* Logic used to interface with the server over the API */

    SERVER_IP = "localhost";
    SERVER_PORT = 1234
    PROTOCOL_VERSION = "1.3"

    #socket;
    #socket_connected = false;

    #client_secret;

    constructor(){
        this.#init_socket_connection();
    }

    /** Initialise the socket connection. */
    #init_socket_connection(){

        // creates socket and conencts 
        this.#socket = new WebSocket(`ws://${this.SERVER_IP}:${this.SERVER_PORT}`);

        // mark as active when connection opens
        this.#socket.addEventListener("open", (event) => {
            this.#handshake();
        });
        
        // add callback to handle recived data
        this.#socket.addEventListener("message", (event) => {
            this.#handle_response(event.data);
        });
    }

    #send_data(data){
        if (this.#socket_connected){
            this.#socket.send(data);
        }
    }

    /** Performs the required handshake with the server.
    C: {"action":"handshake", "version":"[Protocol verison]"}
    S: {"action":"handshake", "result":"success", "client_secret":"[Client secret]"} 
    */
    #handshake(){
     
        var request_json = {
            "action":"handshake",
            "version":this.PROTOCOL_VERSION,
        };

        this.#socket.send(JSON.stringify(request_json));
        
    }
    #complete_handshake(handshake_reply){

        if (handshake_reply["result"] == "success"){
            // successful handshake, obtain client secret
            this.#client_secret = handshake_reply["client_secret"];
            this.#socket_connected = true;
            console.log(handshake_reply);
        }

    }

    #handle_response(data){

        var json = JSON.parse(data);

        var action = json["action"];

        if (action == "handshake"){
            this.#complete_handshake(json);
        }
        else if (action == "result"){

            var command = json["command"];

            switch (command){
                case "SetUsername":
                    console.log("Username set!!!!!");
                    break;
            }
        }

    }


    /** Sends a username change request to the server. */
    set_username(username){

        var request_json = {
            "action":"command",
            "command":"SetUsername",
            "csec":this.#client_secret,
            "username":username,
        };

        this.#send_data(JSON.stringify(request_json))

    }

}




/*

import socket
import json
import typing

# Define custom type hints
from ClientUtils import TYPE_POST, TYPE_POSTS


class SocketAPI:
    """Websocket connection to the server."""
    SERVER_IP = "localhost"
    SERVER_PORT = 1234
    PROTOCOL_VERSION = "1.2"


    

    def get_posts(self) -> TYPE_POSTS:
        """Request all posts from the server."""
        
         # compose request json
        request_json : dict = {
                        "command":"GetPosts",
                        "csec": self.client_secret
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
                        "csec":self.client_secret,
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

*/