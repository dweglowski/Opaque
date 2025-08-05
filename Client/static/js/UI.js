


export {UI};

class UI {

    #client_controller_callback;

    #login_container;
    #login_username_field;
    #login_send;

    #posts_container;

    #new_post_field;
    #add_post_btn;

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

    show_main_page(){
        
        this.#new_post_field = document.getElementById("NewPost");

        this.#add_post_btn = document.getElementById("SendPost");
        this.#add_post_btn.addEventListener("click", this.#add_post.bind(this)); // bind used to preserve "this"


        this.#posts_container = document.getElementById("PostsContainer");

    }


    display_new_post(post){
        
        var user_from = post["from"];
        var users_to = post["to"];
        var content = post["content"];
        this.#display_post(user_from, users_to, content);


        this.#posts_container.scrollTop = this.#posts_container.scrollHeight;
    
    }

    #display_post(from, to, content){
        var message_container = document.createElement("div");
        message_container.className = "post";
        this.#posts_container.appendChild(message_container);

        var from_text = document.createElement("p");
        from_text.textContent = `From: ${from}`;
        message_container.appendChild(from_text);

        var to_text = document.createElement("p");
        to_text.textContent = `To: ${to}`;
        message_container.appendChild(to_text);

        var content_text = document.createElement("p");
        content_text.textContent = content;
        message_container.appendChild(content_text);

    }
    

    #add_post(){

        var to = "@all"; // change to user input when ui refreshed
        var content = this.#new_post_field.value;
        this.#new_post_field.value="";

        this.#client_controller_callback.add_post(content, to);
    }

}
