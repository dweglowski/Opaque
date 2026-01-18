import { SocketAPI } from "./API.js";
import { UI } from "./UI.js"
import { CryptographyController } from "./Cryptography.js";


class Client {

    #api;
    #ui;
    #cryptography_controller

    #logged_in = false;

    #login_username = ""; // used to cache the username from login while awaiting the salt from server
    #login_password = ""; // used to cache the password from login while awaiting the salt from server

    #open_conversation_username = ""; // the username of the currently open conversation
    #open_conversation_public_key = ""; // the public key of the conversation currently open

    #update_post_analytics_current_data = {"-1":{},}; // used to store the latest recived post analytics data when updating post data
    
    constructor(){

        // initialise cryptography controller
        this.#cryptography_controller = new CryptographyController();


        // initialise and start socket api connection, pass in self as callback and cryptography controller
        this.#api = new SocketAPI(this, this.#cryptography_controller);
        
        // ui controller, pass in self as callback
        this.#ui = new UI(this);

    }

    
    /** Called when user clicks login, recives the correct salt from the server */
    login_start(username, password){
        this.#login_username = username;
        this.#login_password = password;
        this.#api.request_salt(username);
    }



    /** Called the moment the salt is recived for login */
    async login(salt){
        var username = this.#login_username;
        var password = this.#login_password;
        this.#login_password = "";

        var hash = await this.#cryptography_controller.hash(password, salt);
        
        this.#cryptography_controller.load_master_key(password);

        this.#api.login(username, hash);
    }

    login_success(){
        this.#logged_in=true;
    
        this.#request_user_encryption_keys();

        this.#ui.login_success();

        this.#ui.show_main_page();
    
        this.subsribe_to_posts();

        this.subscribe_to_messages();

        this.get_profile_info();
    }

    /** On login, request encryption keys */
    #request_user_encryption_keys(){
        this.#api.request_encryption_keys();
    }

    /** When encryption keys are recived, load them into cryptography controller */
    recived_user_encryption_keys(dm_public, dm_encrypted_private, analytics_public, analytics_encrypted_private){
        this.#cryptography_controller.load_direct_messaging_e2e_keys(dm_public, dm_encrypted_private);
        this.#cryptography_controller.load_analytics_keys(analytics_public, analytics_encrypted_private);
    }


    login_failed(reason){
        this.#ui.login_failed(reason);
    }
    
    async signup(username, display_name, password){
        var salt = this.#cryptography_controller.hash_generate_salt();
        
        var hash = await this.#cryptography_controller.hash(password, salt);

        this.#cryptography_controller.load_master_key(password);

        this.#api.signup(username, display_name, hash, salt);
    }
    
    signup_success(){
        this.#ui.upload_signup_picture();

        this.#logged_in=true;

        this.#create_user_encryption_keys();
        
        this.#ui.signup_success();

        this.#ui.show_main_page();
        
        this.subsribe_to_posts();

        this.subscribe_to_messages();

        this.get_profile_info();

        setTimeout(() => {
            // allow for time for profile photo to update and then refresh profile info
            this.get_profile_info();
        }, 1000); 
    }

    /** On signup create all encryption keys and send to server */
    async #create_user_encryption_keys(){
        var dm_keys = await this.#cryptography_controller.generate_direct_messaging_e2e_keys();
        var analytics_keys = await this.#cryptography_controller.generate_analytics_keys();

        this.#api.set_encryption_keys(dm_keys["public_key"], dm_keys["encrypted_private_key"], analytics_keys["public_key"], analytics_keys["encrypted_private_key"]);

    }

    signup_failed(reason){
        this.#ui.signup_failed(reason);
    }


    async upload_profile_picture(blob){
        await this.#api.upload_profile_picture(blob);
    }

    update_profile_picture(picture_id){
        this.#api.update_profile_picture(picture_id);
    }



    /** Uplaods a photo and recives the UUID of the picture */
    async upload_post_picture(blob){
        return this.#api.upload_post_picture(blob);
    }

    get_profile_info(){
        this.#api.get_profile_info();
    }

    recived_profile_info(username, display_name, pictureid){
        this.#ui.display_username(username, display_name);
        this.#ui.display_profile_picture_icon(pictureid);
    }

    user_search_suggestions(username){
        this.#api.get_user_search_suggestions(username);
    }
    user_search_suggestions_results(results){
        this.#ui.username_suggestions_results(results);
    }

    user_search(username){
        this.#api.user_search(username);
    }

    user_search_result(result){
        this.#ui.user_search_result(result);
    }


    add_friend(username){
        this.#api.add_user_connection(username, "Friend", true)    
    }
    remove_friend(username){
        this.#api.add_user_connection(username, "Friend", false)    
    }
    follow_user(username){
        this.#api.add_user_connection(username, "Follow", true)    
    }
    unfollow_user(username){
        this.#api.add_user_connection(username, "Follow", false)    
    }

    request_filtered_posts(filter_type){
        this.#api.request_filtered_posts(filter_type);
    }

    get_conversations(){
        this.#api.get_conversations();
    }
    get_conversations_results(conversations){
        this.#ui.display_conversations(conversations);
    }

    open_conversation(username){
        this.#open_conversation_username = username;
        this.#api.get_conversation_messages(username);

        // request public key for e2ee
        this.#open_conversation_public_key = "";
        this.#api.get_conversation_public_key(username);
    }
    handle_recived_conversation_public_key(public_key){
        this.#open_conversation_public_key = public_key;
    }

    async handle_recived_message(message){
        // select correct copy to decrypt, if owned, decrypt sender copy with otherwise decrypt recipient copy
        var encrypted_content = "";
        if (message["owned"] == true){
            encrypted_content = message["SenderCopy"];
        }
        else{
            encrypted_content = message["RecipientCopy"];
        }

        // decrypt message content with private key
        var content = await this.#cryptography_controller.decrypt_direct_message(encrypted_content);

        message["content"] = content;
        this.#ui.display_new_message(message);
    }

    async add_message(content){
        // wait until the client's public key has be fetched from the server
        while (this.#open_conversation_public_key == ""){
            await new Promise(resolve => setTimeout(resolve, 100));
        }

        // encrypt message with e2ee, one copy for sender and one for recipient
        var SenderCopy = await this.#cryptography_controller.encrypt_direct_message_sender_copy(content);
        var RecipientCopy = await this.#cryptography_controller.encrypt_direct_message_recipient_copy(this.#open_conversation_public_key, content);

        this.#api.add_message(SenderCopy, RecipientCopy, this.#open_conversation_username);
    }

    get_my_posts(){
        this.#api.get_my_posts();
    }
    async my_posts_results(posts){
        var posts_with_decrypted_analytics = [];
        for (var i = 0; i < posts.length; i++) {
            var post = posts[i];
            // decrypt analytics data
            post = await this.#decrypt_analytics_data(post);

            posts_with_decrypted_analytics.push(post);
        }
        
        this.#ui.display_my_posts(posts_with_decrypted_analytics);
    }

    async #decrypt_analytics_data(post){
        var decrypted_post = post;
        decrypted_post["Views"] = post["views"];


        var reactions_encrypted = post["reactions_encrypted"];
        // decrypt reactions with homomorphic encryption
        var reactions_vector = await (this.#cryptography_controller.decrypt_analytics(reactions_encrypted));
        
        var reactions = ["Likes", "Hearts", "Laughs", "Surprises", "Sads", "Angrys", "Fire", "Computers"];

        for (var i = 0; i < reactions.length; i++) {
            var reaction_type = reactions[i];
            var start_power = BigInt(this.#convert_reaction_to_integer(reaction_type));
            var reaction_count = Number((reactions_vector / start_power) % BigInt(10**5));
            decrypted_post[reaction_type] = reaction_count;
        }

        var view_duration_encrypted = post["average_view_time_encrypted"];
        // decrypt view duration with homomorphic encryption
        var view_duration_decrypted = await (this.#cryptography_controller.decrypt_analytics(view_duration_encrypted));
        var avaerage_view_duration_seconds = Number(view_duration_decrypted) / Number(post["views"]);
        if (isNaN(avaerage_view_duration_seconds)){
            avaerage_view_duration_seconds = 0;
        }

        decrypted_post["avg_view_duration"] = avaerage_view_duration_seconds;
        
        decrypted_post["Stars"] = post["star_score"];
        // clamp stars to 0-5
        if (post["Stars"] < 0){
            post["Stars"] = 0;
        }
        if (post["Stars"] > 5){
            post["Stars"] = 5;
        }

        return decrypted_post;
    }

    increment_post_analytics_view_count(post_id){
        this.#api.increment_post_analytics_view_count(post_id);
    }

    rate_post(post_id, rating_value){
        var noisy_star_score = this.#cryptography_controller.apply_differential_privacy_to_star_score(rating_value);
        this.#api.rate_post(post_id, noisy_star_score);
    }

    handle_recived_post_analytics(analytics){
        this.#update_post_analytics_current_data[analytics["postid"]] = analytics;
    }

    /** Updates the view duration of a post securely using homomorphic encryption */
    async increment_post_view_duration(post_id, duration){
        // retrieve current analytics data for post
        this.#update_post_analytics_current_data[post_id] = "";
        this.#api.get_post_analytics(post_id);
        
        // wait until analytics data is recived
        while (this.#update_post_analytics_current_data[post_id] == ""){
            await new Promise(resolve => setTimeout(resolve, 100));
        }

        var current_analytics = this.#update_post_analytics_current_data[post_id];
        
        // encrypt duration and add using homomorphic encryption

        var public_key = current_analytics["encryption_public_key"];

        var current_view_duration_encrypted = current_analytics["average_view_time_encrypted"];

        
        var new_view_duration_encrypted = await this.#cryptography_controller.add_int_to_analytics_with_key(public_key, current_view_duration_encrypted, duration);


        current_analytics["avg_view_duration_seconds"] = new_view_duration_encrypted;
        this.#update_post_analytics_current_data[post_id] = current_analytics;

        this.#api.set_post_analytics(post_id, current_analytics);
    }

    async #initialise_post_analytics(post_id){
        var encrypted_reactions_start = await this.#cryptography_controller.get_encrypted_reactions_start();
        var encrypted_view_duration_start = await this.#cryptography_controller.get_encrypted_view_duration_start();
        this.#api.set_post_analytics(post_id, {
            "reactions_encrypted" : encrypted_reactions_start,
            "avg_view_duration_seconds": encrypted_view_duration_start,
        });
    }

    /** Converts a reaction into the correct power of 10 to add to reactions total */
    #convert_reaction_to_integer(reaction_type){
        /* Store reactions to a single intiger
           5 digits per reaction type
           10 digits of scratch space to allow for adding some noise each time to prevent brute force decryption
           Computers Fire Angrys Sads Surprises Laughs Hearts Likes
        */

        switch(reaction_type){
            case "Likes":
                return 1n;
            case "Hearts":
                return 10n**5n;
            case "Laughs":
                return 10n**10n;
            case "Surprises":
                return 10n**15n;
            case "Sads":
                return 10n**20n;
            case "Angrys":
                return 10n**25n;
            case "Fire":
                return 10n**30n;
            case "Computers":
                return 10n**35n;
            case "scratch":
                return 10n**40n;
            default:
                return 0n;
        }
    }

    /** Adds a reaction to a post securely using homomorphic encryption */
    async add_post_reaction(post_id, reaction_type){
        // retrieve current analytics data for post
        this.#update_post_analytics_current_data[post_id] = "";
        this.#api.get_post_analytics(post_id);
        
        // wait until analytics data is recived
        while (this.#update_post_analytics_current_data[post_id] == ""){
            await new Promise(resolve => setTimeout(resolve, 100));
        }

        var current_analytics = this.#update_post_analytics_current_data[post_id];
        
        // get integer representation of reaction
        var reaction_integer = this.#convert_reaction_to_integer(reaction_type);

        // generate random noise to prevent brute force decryption
        var noise_integer = this.#convert_reaction_to_integer("scratch") * BigInt(this.#cryptography_controller.secure_random_int(1, 1000).toString());

        var total_integer = reaction_integer + noise_integer;

        // encrypt duration and add using homomorphic encryption

        var public_key = current_analytics["encryption_public_key"];

        var current_reactions_state = current_analytics["reactions_encrypted"];

        
        var new_reactions_encrypted = await this.#cryptography_controller.add_int_to_analytics_with_key(public_key, current_reactions_state, total_integer);

        current_analytics["reactions_encrypted"] = new_reactions_encrypted;

        current_analytics["avg_view_duration_seconds"] = current_analytics["average_view_time_encrypted"];

        this.#update_post_analytics_current_data[post_id] = current_analytics;

        this.#api.set_post_analytics(post_id, current_analytics);
    }




    /** Initiate getting posts */
    subsribe_to_posts(){
        this.#api.subscribe_to_posts();
    }
    /** Initiate getting direct messages */
    subscribe_to_messages(){
        this.#api.subscribe_to_messages();
    }

    /** Displays a newly recived post once recived from server */
    handle_recived_post(post){
        this.#ui.display_new_post(post);
    }

    /** Initiate getting posts */
    async add_post(content, to){

        // add each image to the post
        var pictures = await this.#ui.upload_all_post_pictures();
        for (var i = 0; i < pictures.length; i++) {
            var uuid = pictures[i];
            content+=" {{picture:"+uuid+"}}"
        }

        this.#api.add_post(content, to);
    }

    post_added_successfully(post_id){
        this.#initialise_post_analytics(post_id);
    }


}



var main = new Client();