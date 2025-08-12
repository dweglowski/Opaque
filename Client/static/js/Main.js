import { SocketAPI } from "./API.js";
import {UI} from "./UI.js"



class Client {

    #api;
    #ui;

    #logged_in = false;
    
    constructor(){
        
        // initialise and start socket api connection, pass in self as callback
        this.#api = new SocketAPI(this);

        // ui controller, pass in self as callback
        this.#ui = new UI(this);

    }

    start_signin_process(){
        this.#ui.start_signin_process()
    }
    
    login(username){
        this.#api.login(username);
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
    
    signup(username, display_name){
        this.#api.signup(username, display_name);
    }
    
    signup_success(){
        this.#logged_in=true;
        
        this.#ui.signup_success();

        this.#ui.show_main_page();
        
        this.subsribe_to_posts();

        this.get_profile_info();
    }

    signup_failed(reason){
        this.#ui.signup_failed(reason);
    }

    get_profile_info(){
        this.#api.get_profile_info();
    }

    recived_profile_info(username, display_name){
        this.#ui.display_username(username, display_name);
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
    add_post(content, to){
        this.#api.add_post(content, to);
    }

    
    start(){
        this.start_signin_process();
    }

    




}



var main = new Client();

main.start();
