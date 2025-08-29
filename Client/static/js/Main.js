import { SocketAPI } from "./API.js";
import {UI} from "./UI.js"



class Client {

    #api;
    #ui;

    #logged_in = false;

    #login_username = ""; // used to cache the username from login while awaiting the salt from server
    #login_password = ""; // used to cache the password from login while awaiting the salt from server
    
    constructor(){
        
        // initialise and start socket api connection, pass in self as callback
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

    /** Hashes the password before it is sent to the server, uses PBKDF2 for security */
    async #hash(password, salt){
        var iterations = 500_000;
        var hash = 'SHA-256';
        var length = 64;

        var enc = new TextEncoder();
        var key = await crypto.subtle.importKey(
            'raw',
            enc.encode(password),
            'PBKDF2',
            false,
            ['deriveBits']
        );
        
        enc = new TextEncoder();
        var hash = await crypto.subtle.deriveBits(
          { name: 'PBKDF2', hash: hash, salt: enc.encode(salt), iterations : iterations },
          key,
          length * 8
        )

        return btoa(String.fromCharCode(...new Uint8Array(hash)));
    }

    /** Generates the salt for a new user */
    #hash_generate_salt() {
        var salt = crypto.getRandomValues(new Uint8Array(32));
        return btoa(String.fromCharCode(...salt));
    }


    /** Called the moment the salt is recived for login */
    async login(salt){
        var username = this.#login_username;
        var password = this.#login_password;
        this.#login_password = "";

        var hash = await this.#hash(password, salt);

        this.#api.login(username, hash);
    }

    login_success(){
        this.#logged_in=true;
    
        this.#ui.login_success();

        this.#ui.show_main_page();
    
        this.subsribe_to_posts();

        this.get_profile_info();
    }

    login_failed(reason){
        this.#ui.login_failed(reason);
    }
    
    async signup(username, display_name, password){
        var salt = this.#hash_generate_salt();
        
        var hash = await this.#hash(password, salt);

        this.#api.signup(username, display_name, hash, salt);
    }
    
    signup_success(){
        this.#ui.upload_signup_picture();

        this.#logged_in=true;
        
        this.#ui.signup_success();

        this.#ui.show_main_page();
        
        this.subsribe_to_posts();

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

    user_search(username){
        this.#api.user_search(username);
    }

    user_search_result(result){
        this.#ui.user_search_result(result);
    }


    /** Initiate getting posts */
    subsribe_to_posts(){
        this.#api.subscribe_to_posts();
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
