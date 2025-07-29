import { SocketAPI } from "./API.js";
import {UI} from "./UI.js"



class Client {

    #api;
    #ui;

    #signed_in = false;
    
    constructor(){
        
        // initialise and start socket api connection
        this.#api = new SocketAPI();

        // ui controller, pass in self as callback
        this.#ui = new UI(this);

    }

    start_signin_process(){
        this.#ui.start_signin_process()
    }
    
    set_username(username){
        this.#api.set_username(username);
        this.#signed_in=true;
    }

    get_posts(){
        var posts = this.api.get_posts();
    }

    
    start(){
        this.start_signin_process();
    }

    




}



var main = new Client();

main.start();


// import ClientCLI
// import ClientAPI
// import typing

// # Define custom type hints
// from ClientUtils import TYPE_POST, TYPE_POSTS




// class Client:
//     """Controls all the client logic"""
//     def __init__(self) -> None:
//         self.cli : ClientCLI.CLI = ClientCLI.CLI()
//         self.api : ClientAPI.SocketAPI = ClientAPI.SocketAPI()

//     def cli_mainloop(self) -> None:
//         """The main loop running used for the cli"""

//         self.api.connect()

//         self.__set_username()

//         while 1:
//             action : str = self.cli.get_action()
            
//             if action == "Read":
//                 self.__read_posts()
//             elif action == "Write":
//                 self.__write_post()
//             elif action == "Quit":
//                 self.__quit()
//                 break
//             else:
//                 pass

//     def __set_username(self) -> None:
//         username : str = self.cli.get_username()
//         self.api.set_username(username)

//     def __read_posts(self) -> None:
//         posts : TYPE_POSTS = self.api.get_posts()
//         self.cli.display_posts(posts)

//     def __write_post(self) -> None:
//         users_to : str = self.cli.get_new_post_to()
//         post_content : str = self.cli.get_new_post_content()
//         post : TYPE_POST = {"to" : users_to, "content" : post_content}
//         self.api.add_post(post)

//     def __quit(self) -> None:
//         self.api.close()

// if __name__ == "__main__":
//     client : Client = Client()
//     client.cli_mainloop()