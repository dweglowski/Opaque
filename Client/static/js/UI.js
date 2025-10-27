export {UI};

class UI {

    #client_controller_callback;

    #MainContainer;

    #login_container;
    #login_username_field;
    #login_password_field;
    #login_send;
    #login_UserDoesntExist_message;
    #login_InvalidPassword_message;
    #login_switch_to_signup;

    #signup_container;
    #signup_username_field;
    #signup_displayname_field;
    #signup_password_field;
    #signup_send;
    #signup_switch_to_login;
    #signup_NotUniqueUsername_message;
    #signup_profile_picture_upload;
    #signup_profile_picture_canvas;

    #profile_display_name;

    #user_search_open_btn;
    #user_search_container;
    #user_search_username;
    #user_search_suggestions_container;
    #user_search_send_btn;
    #user_search_result_container;
    #user_search_result_close_btn;

    #posts_container;

    #new_post_field;
    #add_post_btn;

    #new_post_content_container;
    #new_post_content_container_close_btn;
    #new_post_add_content_btn;
    #new_post_images_container;
    #new_post_image_template;
    #new_post_image_upload;


    constructor(client_controller_callback){
        this.#client_controller_callback = client_controller_callback;
    }

    start_signin_process(){
        this.#MainContainer = document.getElementById("MainContainer");
        this.#MainContainer.style.filter="blur(5px)";
        
        this.#login_container = document.getElementById("LoginPopup");
        this.#login_username_field = document.getElementById("LoginUsername");
        this.#login_password_field = document.getElementById("LoginPassword");
        this.#login_send = document.getElementById("LoginSend");
        this.#login_UserDoesntExist_message = document.getElementById("UserDoesntExist");
        this.#login_InvalidPassword_message = document.getElementById("InvalidPassword");
        
        this.#signup_container = document.getElementById("SignupPopup");
        this.#signup_username_field = document.getElementById("SignupUsername");
        this.#signup_displayname_field = document.getElementById("SignupDisplayname");
        this.#signup_password_field = document.getElementById("SignupPassword");
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
        this.#add_image_to_canvas_fixed_size("SignupProfilePicture", "/uploads/profile_pictures/0.png", 200, 200);
    }

    login(){
        this.#login_UserDoesntExist_message.style.display="none";
        this.#login_InvalidPassword_message.style.display="none";

        
        var username = this.#login_username_field.value;
        var password = this.#login_password_field.value;
        
        this.#client_controller_callback.login_start(username,password);
    }
    
    signup(){
        var username = this.#signup_username_field.value;
        var display_name = this.#signup_displayname_field.value;
        var password = this.#signup_password_field.value;
        
        this.#client_controller_callback.signup(username, display_name, password);

    }


    /** Adds a picture */
    #add_image_to_canvas_fixed_size(canvas_name, img_data, width, height){
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
            _this.#add_image_to_canvas_fixed_size("SignupProfilePicture", img_data, 200, 200);
        };
        reader.readAsDataURL(file);
    }

    signup_profile_picture_added(event){
        this.#signup_add_profile_picture_to_canvas(event.target.files[0]);
    }


    async upload_signup_picture(){
        // get image data as scaled png file from canvas
        var image_data_url = document.getElementById("SignupProfilePicture").toDataURL('image/png');
        var res = await fetch(image_data_url);
        var blob = await res.blob();
        
        // once we have a png image, upload it to the server
        await this.#client_controller_callback.upload_profile_picture(blob);

    }


    
    login_failed(reason){
        this.#login_UserDoesntExist_message.style.display="none";
        this.#login_InvalidPassword_message.style.display="none";
        if (reason == "DoesntExist"){
            this.#login_UserDoesntExist_message.style.display="block";
        }
        else if (reason == "Password"){
            this.#login_InvalidPassword_message.style.display="block";
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
        
        
        this.#new_post_content_container = document.getElementById("NewPostContentPopup");

        this.#new_post_content_container = document.getElementById("NewPostContentPopup");
        this.#new_post_image_template = document.getElementById("NewPostImageTemplateCanvas");
        this.#new_post_images_container = document.getElementById("NewPostImagesContainer");
        
        this.#new_post_add_content_btn = document.getElementById("NewPostAddContent");
        this.#new_post_add_content_btn.addEventListener("click", this.#open_content_select_menu.bind(this));
        this.#new_post_content_container_close_btn = document.getElementById("NewPostContentClose");
        this.#new_post_content_container_close_btn.addEventListener("click", this.#close_content_select_menu.bind(this));
        
        this.#new_post_image_upload = document.getElementById("NewPostImageUpload");
        this.#new_post_image_upload.addEventListener("change", this.new_post_picture_added.bind(this));
        

        
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
        this.#add_image_to_canvas_fixed_size("MyProfilePicture", "/uploads/profile_pictures/"+pictureid+".png", 50, 50);
    }
    
    
    #open_user_search(){
        this.#user_search_container.style.display="block";
        this.#MainContainer.style.filter="blur(5px)";

        this.#user_search_username = document.getElementById("SearchUsername");
        this.#user_search_suggestions_container = document.getElementById("UserSearchSuggestionsResult");

        this.#user_search_username.addEventListener("input", this.request_username_suggestions.bind(this));
    }

    request_username_suggestions(){
        var username = this.#user_search_username.value;
        this.#client_controller_callback.user_search_suggestions(username);
    }

    username_suggestions_results(results){
        this.#user_search_suggestions_container.innerHTML = "";
        results.forEach(user => {
            var p = document.createElement('p');
            p.textContent = user;
            this.#user_search_suggestions_container.appendChild(p);
        });
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
        this.#add_image_to_canvas_fixed_size("UserSearchProfilePicture", "/uploads/profile_pictures/"+profile_pictureid+".png", 200, 200);
        

        this.#user_search_result_close_btn = document.getElementById("UserSearchResultClose");
        this.#user_search_result_close_btn.addEventListener("click", this.user_search_result_close.bind(this)); // bind used to preserve "this"
    }
    
    user_search_result_close(){
        this.#user_search_result_container.style.display="none";
        this.#MainContainer.style.filter="";
    }

    #open_content_select_menu(){
        console.log(this.#new_post_content_container);
        this.#new_post_content_container.style.display="block";
    }
    
    #close_content_select_menu(){
        this.#new_post_content_container.style.display="none";
        
    }

    

    /** Adds a new canvas element from a template and add an image to it */
    #add_new_canvas_with_image(template, img_data, max_width, max_height){
        var img = new Image();
        img.onload = function () {
            var height = img.height;
            var width = img.width;

            // if (height > max_height || width > max_width){
            var scale = Math.min(max_width / width, max_height / height); // get the scaling ratio
            width = Math.floor(width * scale);
            height = Math.floor(height * scale);
            // }

            // duplicate the template and add the new canvas below
            var canvas = template.cloneNode();
            template.after(canvas);
            canvas.style.display="block";
            canvas.width = width;
            canvas.height = height;
            canvas.style.width = width/5+"px";
            canvas.style.height = height/5+"px";

            // canvas.getContext('2d').imageSmoothingEnabled = false;
            canvas.getContext('2d').drawImage(img, 0, 0, width, height);
        }
        img.src = img_data;
    }

    #new_post_add_picture_to_canvas(file){
        var reader = new FileReader();
        const _this = this;
        reader.onload = function(){
            var img_data = reader.result;
            _this.#add_new_canvas_with_image(_this.#new_post_image_template, img_data, 1000, 1000);
        };
        reader.readAsDataURL(file);
    }

    new_post_picture_added(event){
        this.#new_post_add_picture_to_canvas(event.target.files[0]);
    }
    async upload_post_picture_and_get_uuid(canvas_element){
        // get image data as scaled png file from canvas
        
        var image_data_url = canvas_element.toDataURL('image/png');
        var res = await fetch(image_data_url);
        var blob = await res.blob();
        // once we have a png image, upload it to the server
        var uuid = await this.#client_controller_callback.upload_post_picture(blob);
        
        return uuid;
    }

    /** Uploads all pictures and returns a list of UUIDs  */
    async upload_all_post_pictures(){
        var uuids = [];
        
        var image_canvases = this.#new_post_images_container.children;

        // iterate over every image canvas with image except for the first one (which is the template)
        for (var i = 1; i < image_canvases.length; i++) {

            var image_canvas = image_canvases[i];
            var id = await this.upload_post_picture_and_get_uuid(image_canvas);
            uuids.push(id);
            
        }
        return uuids;
        
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

        
        var images = [...content.matchAll(/\{\{picture:([\w-]+)\}\}/g)];
        
        for (var i = 0; i < images.length; i++) {

            var imgid = images[i][1];

            var img = document.createElement("img");
            img.src = "/uploads/post_pictures/"+imgid+".png";
            img.style.width="500px";
            message_container.appendChild(img);
        }

        content = content.replace(/\{\{picture:[\w-]+\}\}/g,"");


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