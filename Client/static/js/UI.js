


export {UI};

class UI {

    #client_controller_callback;

    #MainContainer;

    #login_container;
    #login_username_field;
    #login_send;
    #login_UserDoesntExist_message;
    #login_switch_to_signup;

    #signup_container;
    #signup_username_field;
    #signup_displayname_field;
    #signup_send;
    #signup_switch_to_login;
    #signup_NotUniqueUsername_message;
    #signup_profile_picture_upload;
    #signup_profile_picture_canvas;

    #profile_display_name;

    #user_search_open_btn;
    #user_search_container;
    #user_search_username;
    #user_search_send_btn;
    #user_search_result_container;
    #user_search_result_close_btn;

    #posts_container;

    #new_post_field;
    #add_post_btn;

    constructor(client_controller_callback){
        this.#client_controller_callback = client_controller_callback;
    }

    start_signin_process(){
        this.#MainContainer = document.getElementById("MainContainer");
        this.#MainContainer.style.filter="blur(5px)";
        
        this.#login_container = document.getElementById("LoginPopup");
        this.#login_username_field = document.getElementById("LoginUsername");
        this.#login_send = document.getElementById("LoginSend");
        this.#login_UserDoesntExist_message = document.getElementById("UserDoesntExist");
        
        this.#signup_container = document.getElementById("SignupPopup");
        this.#signup_username_field = document.getElementById("SignupUsername");
        this.#signup_displayname_field = document.getElementById("SignupDisplayname");
        this.#signup_send = document.getElementById("SignupSend");
        this.#signup_NotUniqueUsername_message = document.getElementById("NotUniqueUsername");



        this.#login_switch_to_signup = document.getElementById("SwitchToSignup");
        this.#signup_switch_to_login = document.getElementById("SwitchToLogin");
        this.#login_switch_to_signup.addEventListener("click", (() => {this.#login_container.style.display="none";this.#signup_container.style.display="block"}));
        this.#signup_switch_to_login.addEventListener("click", (() => {this.#login_container.style.display="block";this.#signup_container.style.display="none"}));
        
        this.#login_send.addEventListener("click", this.login.bind(this)); // bind used to preserve "this"
        this.#signup_send.addEventListener("click", this.signup.bind(this)); // bind used to preserve "this"
        
        
        this.#signup_profile_picture_upload = document.getElementById("SignupProfilePictureUpload");
        this.#signup_profile_picture_upload.addEventListener("change", this.signup_profile_picture_added.bind(this));
        // add default image to profile picture
        this.#add_image_to_canvas("SignupProfilePicture", "/uploads/profile_pictures/0.png", 200, 200);
    }

    login(){
        var username = this.#login_username_field.value;
        
        this.#client_controller_callback.login(username);
    }
    
    signup(){
        var username = this.#signup_username_field.value;
        var display_name = this.#signup_displayname_field.value;
        
        this.#client_controller_callback.signup(username, display_name);

    }


    /** Adds a picture */
    #add_image_to_canvas(canvas_name, img_data, width, height){
        var img = new Image();
        img.onload = function () {
            var canvas = document.getElementById(canvas_name);
            canvas.getContext('2d').drawImage(img, 0, 0, width, height);
        }
        img.src = img_data;
    }
    
    #signup_add_profile_picture_to_canvas(file){
        var reader = new FileReader();
        const _this = this;
        reader.onload = function(){
            var img_data = reader.result;
            _this.#add_image_to_canvas("SignupProfilePicture", img_data, 200, 200);
        };
        reader.readAsDataURL(file);
    }

    signup_profile_picture_added(event){
        this.#signup_add_profile_picture_to_canvas(event.target.files[0]);
    }


    upload_signup_picture(){
        // get image data as scaled png file from canvas
        var image_data_url = document.getElementById("SignupProfilePicture").toDataURL('image/png');
        fetch(image_data_url)
            .then(res => res.blob())
            .then(blob => {
                // once we have a png image, upload it to the server
                this.#client_controller_callback.upload_profile_picture(blob);
        });
    }


    
    login_failed(reason){
        if (reason == "DoesntExist"){
            this.#login_UserDoesntExist_message.style.display="block";
        }
    }
    
    login_success(){
        this.#login_container.style.display = "none";
        this.#MainContainer.style.filter="";
    }
    
    signup_failed(reason){
        if (reason == "NotUnique"){
            this.#signup_NotUniqueUsername_message.style.display="block";
        }
    }
    
    signup_success(){
        this.#signup_container.style.display = "none";
        this.#MainContainer.style.filter="";
    }

    show_main_page(){
        
        this.#new_post_field = document.getElementById("NewPost");

        this.#add_post_btn = document.getElementById("SendPost");
        this.#add_post_btn.addEventListener("click", this.#add_post.bind(this)); // bind used to preserve "this"
        
        
        this.#posts_container = document.getElementById("PostsContainer");

        
        this.#user_search_container = document.getElementById("UserSearchPopup");
        this.#user_search_result_container = document.getElementById("UserSearchResultPopup");
        this.#user_search_open_btn = document.getElementById("UserSearchOpen");
        this.#user_search_open_btn.addEventListener("click", this.#open_user_search.bind(this)); // bind used to preserve "this"
        this.#user_search_send_btn = document.getElementById("UserSearchSend");
        this.#user_search_send_btn.addEventListener("click", this.start_user_search.bind(this));
        
    }

    display_username(username, displayname){
        this.#profile_display_name = document.getElementById("DisplayName");
        this.#profile_display_name.textContent=displayname;
        this.#profile_display_name.addEventListener("click", this.#user_search.bind(this, username));
    }

    display_profile_picture_icon(pictureid){
        this.#add_image_to_canvas("MyProfilePicture", "/uploads/profile_pictures/"+pictureid+".png", 50, 50);
    }
    
    
    #open_user_search(){
        this.#user_search_container.style.display="block";
        this.#MainContainer.style.filter="blur(5px)";

        this.#user_search_username = document.getElementById("SearchUsername");
        this.#user_search_username = document.getElementById("SearchUsername");
    }
    
    #user_search(username){
        this.#client_controller_callback.user_search(username);
    }
    
    start_user_search(){
        var username = this.#user_search_username.value;
        this.#user_search(username);
    }
    
    user_search_result(result){
        
        this.#user_search_container.style.display = "none";
        this.#user_search_result_container.style.display = "block";
        
        document.getElementById("SearchResultUsername").textContent = result["username"];
        document.getElementById("SearchResultDisplayname").textContent = result["displayname"];
        
        var profile_pictureid = result["pictureid"]
        this.#add_image_to_canvas("UserSearchProfilePicture", "/uploads/profile_pictures/"+profile_pictureid+".png", 200, 200);
        

        this.#user_search_result_close_btn = document.getElementById("UserSearchResultClose");
        this.#user_search_result_close_btn.addEventListener("click", this.user_search_result_close.bind(this)); // bind used to preserve "this"
    }
    
    user_search_result_close(){
        this.#user_search_result_container.style.display="none";
        this.#MainContainer.style.filter="";
    }



    display_new_post(post){
        
        var user_from = post["from"];
        var user_from_display_name = post["fromname"];
        var users_to = post["to"];
        var content = post["content"];
        this.#display_post(user_from, user_from_display_name, users_to, content);


        this.#posts_container.scrollTop = this.#posts_container.scrollHeight;
    
    }

    #display_post(from, from_display_name, to, content){
        var message_container = document.createElement("div");
        message_container.className = "post";
        this.#posts_container.appendChild(message_container);

        var from_text = document.createElement("a");
        from_text.href="#profile";
        from_text.textContent = `From: ${from_display_name}`;
        from_text.addEventListener("click", this.#user_search.bind(this, from));
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
