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
    }

    /** Initiate getting posts */
    get_posts(){
        this.#api.get_posts();
    }
    
    /** Update posts once recived from server */
    update_posts(posts){
        this.#ui.update_posts(posts);
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
