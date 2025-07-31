export {SocketAPI};

class SocketAPI {

    /* Logic used to interface with the server over the API */

    SERVER_IP = "localhost";
    SERVER_PORT = 1234
    PROTOCOL_VERSION = "1.3"

    #client_controller_callback;

    #socket;
    #socket_connected = false;

    #client_secret;

    
    constructor(client_controller_callback){
        this.#client_controller_callback = client_controller_callback;

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
                case "GetPosts":
                    var posts = json["data"];
                    this.#client_controller_callback.update_posts(posts);
                    break;
                case "AddPost":
                    this.#client_controller_callback.get_posts();
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

    /** Sends a get posts request to the server. */
    get_posts(){

        var request_json = {
            "action":"command",
            "command":"GetPosts",
            "csec":this.#client_secret,
        };

        this.#send_data(JSON.stringify(request_json))

    }

    /** Sends an add post request to the server. */
    add_post(content, to){

        var request_json = {
            "action":"command",
            "command":"AddPost",
            "csec":this.#client_secret,
            "data":{"to": to, "content": content},
        };

        this.#send_data(JSON.stringify(request_json))

    }

}
