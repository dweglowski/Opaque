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
    
    constructor(){

        // initialise cryptography controller
        this.#cryptography_controller = new CryptographyController();


        // initialise and start socket api connection, pass in self and cryptography controller as callback
        this.#api = new SocketAPI(this);

        // ui controller, pass in self as callback
        this.#ui = new UI(this);

    }

    start_signin_process(){
        this.#ui.start_signin_process()
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

        this.#api.login(username, hash);
    }

    login_success(){
        this.#logged_in=true;
    
        this.#ui.login_success();

        this.#ui.show_main_page();
    
        this.subsribe_to_posts();

        this.subscribe_to_messages();

        this.get_profile_info();
    }

    login_failed(reason){
        this.#ui.login_failed(reason);
    }
    
    async signup(username, display_name, password){
        var salt = this.#cryptography_controller.hash_generate_salt();
        
        var hash = await this.#cryptography_controller.hash(password, salt);

        this.#api.signup(username, display_name, hash, salt);
    }
    
    signup_success(){
        this.#ui.upload_signup_picture();

        this.#logged_in=true;
        
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
    }
    handle_recived_message(message){
        message["content"] = message["RecipientCopy"]; // TODO decrypt e2ee
        this.#ui.display_new_message(message);
    }

    add_message(content){
        var SenderCopy = content; // TODO encrypt e2ee
        var RecipientCopy = content; // TODO encrypt e2ee
        this.#api.add_message(SenderCopy, RecipientCopy, this.#open_conversation_username);
    }

    get_my_posts(){
        this.#api.get_my_posts();
    }
    my_posts_results(posts){
        var posts_with_decrypted_analytics = [];
        for (var i = 0; i < posts.length; i++) {
            var post = posts[i];
            // decrypt analytics data
            post = this.#decrypt_analytics_data(post);

            posts_with_decrypted_analytics.push(post);
        }
        
        this.#ui.display_my_posts(posts_with_decrypted_analytics);
    }

    #decrypt_analytics_data(post){
        var decrypted_post = post;
        decrypted_post["Views"] = post["views"];

        decrypted_post["Likes"] = 0;
        decrypted_post["Hearts"] = 0;
        decrypted_post["Laughs"] = 0;
        decrypted_post["Surprises"] = 0;
        decrypted_post["Sads"] = 0;
        decrypted_post["Angrys"] = 0;
        decrypted_post["Fire"] = 0;
        decrypted_post["Computers"] = 0;

        decrypted_post["avg_view_duration"] = 0;
        
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

    
    start(){
        this.start_signin_process();
    }

    




}



var main = new Client();

main.start();
