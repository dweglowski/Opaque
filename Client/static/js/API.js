export {SocketAPI};

class SocketAPI {

    /* Logic used to interface with the server over the API */

    SERVER_IP = "localhost";
    SERVER_PORT = 1234
    PROTOCOL_VERSION = "1.5"

    #client_controller_callback;
    #cryptography_controller;

    #socket;
    #socket_connected = false;

    #client_secret;
    #connection_upgraded = false;

    constructor(client_controller_callback, cryptography_controller){
        this.#client_controller_callback = client_controller_callback;
        this.#cryptography_controller = cryptography_controller;

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

    async #send_data(data, encrypt = true){
        if (this.#socket_connected){
            if (encrypt && this.PROTOCOL_VERSION >= "1.6"){
                data = await this.#cryptography_controller.encrypt_websocket_data_tls(data);
            }

            this.#socket.send(data);
        }
    }

    /** Performs the required handshake with the server.
    C: {"action":"handshake", "version":"[Protocol verison]"}
    S: {"action":"handshake", "status":"healthy", "client_secret":"[Client secret]"} 
    C: {"action":"handshake", "result":"success", "client_secret":"[Client secret]"}
    S: {"action":"upgrade_channel", "method":"RSA", "public_key":"[Server public key]"}
    #### Start of encrypted communication ####
    C: {"action":"upgrade_channel", "result":"success", "public_key":"[Client public key]", "client_secret":"[Client secret]"}
    */
    #handshake(){
     
        var request_json = {
            "action":"handshake",
            "version":this.PROTOCOL_VERSION,
        };

        this.#socket.send(JSON.stringify(request_json), false);
        
    }
    #complete_handshake(handshake_reply){

        if (handshake_reply["status"] == "healthy"){
            // successful handshake, obtain client secret
            this.#client_secret = handshake_reply["client_secret"];

            var request_json = {
                "action":"handshake",
                "result":"success",
                "client_secret":this.#client_secret,
            };

            this.#socket.send(JSON.stringify(request_json), false);

            this.#socket_connected = true;
        }

    }

    async #complete_channel_upgrade(channel_upgrade_reply){
        await this.#cryptography_controller.set_tls_server_public_key(channel_upgrade_reply["public_key"]);
        
        // Generate TLS keys
        var client_public_key = await this.#cryptography_controller.generate_tls_keys();

        var request_json = {
            "action":"upgrade_channel",
            "result":"success",
            "public_key":client_public_key,
            "client_secret":this.#client_secret,
        };

        this.#send_data(JSON.stringify(request_json));
        this.#connection_upgraded = true;
    }





    async #handle_response(data){

        if (this.#connection_upgraded){
            // decrypt data
            data = await this.#cryptography_controller.decrypt_websocket_data_tls(data);
        }

        var json = JSON.parse(data);

        var action = json["action"];
        
        if (action == "handshake"){
            this.#complete_handshake(json);
        }
        else if (action == "upgrade_channel"){
            this.#complete_channel_upgrade(json);
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
                case "GetConversations":
                    var conversations = json["data"];
                    this.#client_controller_callback.get_conversations_results(conversations);
                    break;
                case "GetMyPosts":
                    var posts = json["data"];
                    this.#client_controller_callback.my_posts_results(posts);
                    break;
                case "GetEncryptionKeys":
                    var keys = json["data"];
                    this.#client_controller_callback.recived_user_encryption_keys(keys["dm_public"], keys["dm_private"], keys["analytics_public"], keys["analytics_private"]);
                    break;
                case "GetDmPublicKey":
                    var public_key = json["data"];
                    this.#client_controller_callback.handle_recived_conversation_public_key(public_key);
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
            else if (feed == "Messages"){
                var message = json["data"];
                this.#client_controller_callback.handle_recived_message(message);
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

    /** Requests encryption keys on login. */
    request_encryption_keys(){

        var request_json = {
            "action":"command",
            "command":"GetEncryptionKeys",
            "csec":this.#client_secret,
        };

        this.#send_data(JSON.stringify(request_json))
        
    }

    /** Set encryption keys on signup. */
    set_encryption_keys(dm_public, dm_private, analytics_public, analytics_private){

        var request_json = {
            "action":"command",
            "command":"SetEncryptionKeys",
            "csec":this.#client_secret,
            "dm_public":dm_public,
            "dm_private":dm_private,
            "analytics_public":analytics_public,
            "analytics_private":analytics_private,
        };

        this.#send_data(JSON.stringify(request_json))   
    }

    /** Request to public key for a conversation with another user */
    get_conversation_public_key(username){

        var request_json = {
            "action":"command",
            "command":"GetDmPublicKey",
            "csec":this.#client_secret,
            "username": username,
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

    /** Requests adding or removing a friend or following conenction. */
    add_user_connection(connected_user, connection_type, add){

        var request_json = {
            "action":"command",
            "command":"AddUserConnection",
            "csec":this.#client_secret,
            "username":connected_user,
            "type":connection_type,
            "add":add,
        };

        this.#send_data(JSON.stringify(request_json))

    }

    request_filtered_posts(filter_type){
        var request_json = {
            "action":"command",
            "command":"RequestFilteredPosts",
            "csec":this.#client_secret,
            "filter":filter_type,
        };

        this.#send_data(JSON.stringify(request_json))
    }



    /** Subscribes to recive update messages with new direct messages. */
    subscribe_to_messages(){

        var request_json = {
            "action":"subscribe",
            "feed":"Messages",
            "csec":this.#client_secret,
        };

        this.#send_data(JSON.stringify(request_json))

    }


    /** Requests a list of conversations the client has held. */
    get_conversations(){
        
        var request_json = {
            "action":"command",
            "command":"GetConversations",
            "csec":this.#client_secret,
        };
    
        this.#send_data(JSON.stringify(request_json))

    }

    /** Request direct messages from a specific conversation. */
    get_conversation_messages(conversation_username){
        var request_json = {
            "action":"command",
            "command":"RequestMessagesFromUser",
            "csec":this.#client_secret,
            "username":conversation_username,
        };
    
        this.#send_data(JSON.stringify(request_json))

    }

 

    /** Sends an add message request to the server. */
    add_message(SenderCopy, RecipientCopy, to){

        var request_json = {
            "action":"command",
            "command":"AddMessage",
            "csec":this.#client_secret,
            "data":{"SenderCopy": SenderCopy, "RecipientCopy": RecipientCopy, "to": to},
        };

        this.#send_data(JSON.stringify(request_json))

    }

    /** Requests a list of the client's posts with their analytics data. */
    get_my_posts(){

        var request_json = {
            "action":"command",
            "command":"GetMyPosts",
            "csec":this.#client_secret,
        };

        this.#send_data(JSON.stringify(request_json))
    }

    //** Increment view count for post */
    increment_post_analytics_view_count(post_id){

        var request_json = {
            "action":"analytics",
            "command":"IncrementPostAnalyticsViewCount",
            "csec":this.#client_secret,
            "postid":post_id,
        };

        this.#send_data(JSON.stringify(request_json))
    }

    /** Increment star rating for post */
    rate_post(post_id, rating_value){

        var request_json = {
            "action":"analytics",
            "command":"IncrementPostAnalyticsStarScore",
            "csec":this.#client_secret,
            "postid":post_id,
            "star_score":rating_value,
        };

        this.#send_data(JSON.stringify(request_json))
    }

}