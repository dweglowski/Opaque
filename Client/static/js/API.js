export {SocketAPI};

class SocketAPI {

    /* Logic used to interface with the server over the API */

    SERVER_IP = "localhost";
    SERVER_PORT = 1234
    PROTOCOL_VERSION = "1.4"

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

            var success = false;
            
            switch (command){
                case "Login":
                    success = json["success"];
                    if (success){
                        this.#client_controller_callback.login_success();
                    }
                    else {
                        var reason = json["reason"];
                        if (reason == "InvalidUsername"){
                            this.#client_controller_callback.login_failed("DoesntExist");
                        }
                        else if (reason == "InvalidPassword"){
                            this.#client_controller_callback.login_failed("Password");
                        }
                        else {
                            this.#client_controller_callback.login_failed("Generic");
                        }
                    }

                    break;
                case "RequestPasswordSalt":
                    var salt = json["data"];
                    this.#client_controller_callback.login(salt);
                    
                    break;
                case "Signup":
                    success = json["success"];
                    if (success){
                        this.#client_controller_callback.signup_success();
                    }
                    else {
                        var reason = json["reason"];
                        if (reason == "InvalidUsername"){
                            this.#client_controller_callback.signup_failed("NotUnique");
                        }
                        else {
                            this.#client_controller_callback.signup_failed("Generic");
                        }
                    }

                    break;
                case "GetProfileInfo":
                    var data = json["data"];
                    var username = data["username"]
                    var display_name = data["displayname"]
                    var pictureid = data["pictureid"]
                    this.#client_controller_callback.recived_profile_info(username, display_name, pictureid);
                    break;
                case "UserSearchSuggestions":
                    var suggestions = json["data"];
                    this.#client_controller_callback.user_search_suggestions_results(suggestions);
                    break;
                case "UserSearch":
                    success = json["success"];
                    if (success){
                        var data = json["data"];
                        this.#client_controller_callback.user_search_result(data);

                    }
                    break;
                case "AddPost":
                    break;
                case "UpdateProfilePicture":
                    break;
                }
            }
        else if (action == "subscribe"){
            
            var feed = json["feed"];
            
            switch (command){
                case "Posts":
                    console.log("Subscribed to posts!!!")
                    break;
                }
            }
        else if (action == "update"){

            var feed = json["feed"];
                
            if (feed == "Posts"){
                var post = json["data"];
                this.#client_controller_callback.handle_recived_post(post);
            }
        }
    }


    /** Requests the password salt for a user. */
    request_salt(username){

        var request_json = {
            "action":"command",
            "command":"RequestPasswordSalt",
            "csec":this.#client_secret,
            "username":username,
        };

        this.#send_data(JSON.stringify(request_json))

    }
    
    /** Sends a login request to the server. */
    login(username, hash){

        var request_json = {
            "action":"command",
            "command":"Login",
            "csec":this.#client_secret,
            "username":username,
            "hash": hash,
        };

        this.#send_data(JSON.stringify(request_json))

    }

    /** Sends a signup request to the server. */
    signup(username, display_name, hash, salt){

        var request_json = {
            "action":"command",
            "command":"Signup",
            "csec":this.#client_secret,
            "username":username,
            "displayname":display_name,
            "hash":hash,
            "salt":salt,
        };

        this.#send_data(JSON.stringify(request_json))

    }

    /** Request profile info from the server. */
    get_profile_info(){

        var request_json = {
            "action":"command",
            "command":"GetProfileInfo",
            "csec":this.#client_secret,
        };

        this.#send_data(JSON.stringify(request_json))
        
    }
    
    /** Requests suggestions for user search. */
    get_user_search_suggestions(username){
        
        var request_json = {
            "action":"command",
            "command":"UserSearchSuggestions",
            "csec":this.#client_secret,
            "username": username,
        };
    
        this.#send_data(JSON.stringify(request_json))

    }
    
    /** Start a user search. */
    user_search(username){
        
        var request_json = {
            "action":"command",
            "command":"UserSearch",
            "csec":this.#client_secret,
            "username": username,
        };
    
        this.#send_data(JSON.stringify(request_json))

    }

    /** Subscribes to recive update messages with new posts. */
    subscribe_to_posts(){

        var request_json = {
            "action":"subscribe",
            "feed":"Posts",
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



    /** Uploads a profile picture to the server through a psot request */
    async upload_profile_picture(blob){
        var form_data = new FormData();
        form_data.append('image', blob, 'profile.png');


        var response = await fetch('/upload/profile_picture', {
            method: 'POST',
            body: form_data
        })
        if (response.status == 200) {
            var id = await response.text();
            this.#client_controller_callback.update_profile_picture(id);
        }
    }

    /** Uploads a picture from a post to the server through a post request  */
    async upload_post_picture(blob){
        var form_data = new FormData();
        form_data.append('image', blob, 'profile.png');

        var response = await fetch('/upload/post_picture', {
            method: 'POST',
            body: form_data
        })
        if (response.status == 200) {
            var id = await response.text();
            return id
        }
    }

    

    /** Sends an update profile picture request to the server with the new picture id. */
    update_profile_picture(picture_id){

        var request_json = {
            "action":"command",
            "command":"UpdateProfilePicture",
            "csec":this.#client_secret,
            "pictureUUID":picture_id,
        };

        this.#send_data(JSON.stringify(request_json))

    }

}
