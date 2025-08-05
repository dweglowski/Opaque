import { SocketAPI } from "./API.js";
import {UI} from "./UI.js"



class Client {

    #api;
    #ui;

    #signed_in = false;
    
    constructor(){
        
        // initialise and start socket api connection, pass in self as callback
        this.#api = new SocketAPI(this);

        // ui controller, pass in self as callback
        this.#ui = new UI(this);

    }

    start_signin_process(){
        this.#ui.start_signin_process()
    }
    
    set_username(username){
        this.#api.set_username(username);
        this.#signed_in=true;

        this.#ui.show_main_page();

        this.subsribe_to_posts();
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
