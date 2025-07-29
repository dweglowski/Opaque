


export {UI};

class UI {

    #client_controller_callback;

    #login_container;
    #login_username_field;
    #login_send;

    constructor(client_controller_callback){
        this.#client_controller_callback = client_controller_callback;
    }

    start_signin_process(){
        this.#login_container = document.getElementById("LoginPopup");
        this.#login_username_field = document.getElementById("Username");
        this.#login_send = document.getElementById("LoginSend");

        this.#login_send.addEventListener("click", this.signin.bind(this)); // bind used to preserve "this"
    }

    signin(){
        var username = this.#login_username_field.value;
        
        this.#client_controller_callback.set_username(username);

        this.#login_container.style.display = "none";

    }

    


}
