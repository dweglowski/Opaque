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
    #user_search_username_event_listener_started = false;
    #user_search_suggestions_container;
    #user_search_send_btn;
    #user_search_result_container;
    #user_search_result_close_btn;
    #user_search_username_viewed;


    #messages_tab_open_btn;
    #messages_tab_container;
    #messages_tab_close_btn;
    #messages_tab_new_conversation_btn_event_listener_started = false;
    #messages_tab_send_btn_event_listener_started = false;

    #my_posts_tab_open_btn;
    #my_posts_tab_container;
    #my_posts_tab_close_btn;


    #filter_dropdown;

    #posts_container;

    #new_post_field;
    #add_post_btn;

    #new_post_content_container;
    #new_post_content_container_close_btn;
    #new_post_add_content_btn;
    #new_post_images_container;
    #new_post_image_template;
    #new_post_image_upload;


    #analytics_tracker_seen_yet = {}; // stores whether each post id has been seen yet to only add a single view per session
    #analytics_tracker_start_times = {}; // stores when the user started viewing each post id to calculate time spent viewing


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
        
        document.getElementById("UserSearchAddFriend").addEventListener("click", this.user_search_add_friend.bind(this));
        document.getElementById("UserSearchRemoveFriend").addEventListener("click", this.user_search_remove_friend.bind(this));
        document.getElementById("UserSearchFollow").addEventListener("click", this.user_search_follow.bind(this));
        document.getElementById("UserSearchUnfollow").addEventListener("click", this.user_search_unfollow.bind(this));
        
        this.#filter_dropdown = document.getElementById("FilterDropdown");
        this.#filter_dropdown.addEventListener("change", this.#start_filter.bind(this));
        




        this.#messages_tab_container = document.getElementById("MessagesTab");

        this.#messages_tab_open_btn = document.getElementById("MessagesTabOpen");
        this.#messages_tab_open_btn.addEventListener("click", this.#open_messages_tab.bind(this));
        this.#messages_tab_close_btn = document.getElementById("MessagesTabClose");
        this.#messages_tab_close_btn.addEventListener("click", this.#close_messages_tab.bind(this));



        this.#my_posts_tab_container = document.getElementById("MyPostsTab");

        this.#my_posts_tab_open_btn = document.getElementById("MyPostsTabOpen");
        this.#my_posts_tab_open_btn.addEventListener("click", this.#open_my_posts_tab.bind(this));
        this.#my_posts_tab_close_btn = document.getElementById("MyPostsTabClose");
        this.#my_posts_tab_close_btn.addEventListener("click", this.#close_my_posts_tab.bind(this));
        
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

        if (!this.#user_search_username_event_listener_started){
            this.#user_search_username_event_listener_started = true;
            this.#user_search_username.addEventListener("input", this.request_username_suggestions.bind(this));
        }
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

        this.#user_search_username_viewed = result["username"];
        
        var profile_pictureid = result["pictureid"]
        this.#add_image_to_canvas_fixed_size("UserSearchProfilePicture", "/uploads/profile_pictures/"+profile_pictureid+".png", 200, 200);
        

        if (result["isFriend"]){
            document.getElementById("UserSearchAddFriend").style.display = "none";
            document.getElementById("UserSearchRemoveFriend").style.display = "block";
            document.getElementById("UserSearchFollow").style.display = "none";
            document.getElementById("UserSearchUnfollow").style.display = "none";
        }
        else if (result["isFollowed"]){
            document.getElementById("UserSearchAddFriend").style.display = "block";
            document.getElementById("UserSearchRemoveFriend").style.display = "none";
            document.getElementById("UserSearchFollow").style.display = "none";
            document.getElementById("UserSearchUnfollow").style.display = "block";
            
        }
        else {
            document.getElementById("UserSearchAddFriend").style.display = "block";
            document.getElementById("UserSearchRemoveFriend").style.display = "none";
            document.getElementById("UserSearchFollow").style.display = "block";
            document.getElementById("UserSearchUnfollow").style.display = "none";
            
        }

        this.#user_search_result_close_btn = document.getElementById("UserSearchResultClose");
        this.#user_search_result_close_btn.addEventListener("click", this.user_search_result_close.bind(this)); // bind used to preserve "this"
    }
    
    user_search_result_close(){
        this.#user_search_result_container.style.display="none";
        this.#MainContainer.style.filter="";
    }

    /** Called when friend button is pressed, uses the stored username of profile viewed to add a connection */
    user_search_add_friend(){
        this.#client_controller_callback.add_friend(this.#user_search_username_viewed);
        document.getElementById("UserSearchAddFriend").style.display = "none";
        document.getElementById("UserSearchRemoveFriend").style.display = "block";
        document.getElementById("UserSearchFollow").style.display = "none";
        document.getElementById("UserSearchUnfollow").style.display = "none";
    }
    /** Called when unfriend button is pressed, uses the stored username of profile viewed to add a connection */
    user_search_remove_friend(){
        this.#client_controller_callback.remove_friend(this.#user_search_username_viewed);
        document.getElementById("UserSearchAddFriend").style.display = "block";
        document.getElementById("UserSearchRemoveFriend").style.display = "none";
        document.getElementById("UserSearchFollow").style.display = "block";
        document.getElementById("UserSearchUnfollow").style.display = "none";
    }
    /** Called when follow button is pressed, uses the stored username of profile viewed to add a connection */
    user_search_follow(){
        this.#client_controller_callback.follow_user(this.#user_search_username_viewed);
        document.getElementById("UserSearchAddFriend").style.display = "block";
        document.getElementById("UserSearchRemoveFriend").style.display = "none";
        document.getElementById("UserSearchFollow").style.display = "none";
        document.getElementById("UserSearchUnfollow").style.display = "block";
    }
    /** Called when unfollow button is pressed, uses the stored username of profile viewed to add a connection */
    user_search_unfollow(){
        this.#client_controller_callback.unfollow_user(this.#user_search_username_viewed);
        document.getElementById("UserSearchAddFriend").style.display = "block";
        document.getElementById("UserSearchRemoveFriend").style.display = "none";
        document.getElementById("UserSearchFollow").style.display = "block";
        document.getElementById("UserSearchUnfollow").style.display = "none";
    }

    #open_content_select_menu(){
        console.log(this.#new_post_content_container);
        this.#new_post_content_container.style.display="block";
    }
    
    #close_content_select_menu(){
        this.#new_post_content_container.style.display="none";
        
    }

    #start_filter(){
        var filter_type = this.#filter_dropdown.value;

        // clear all existing posts
        this.#posts_container.innerHTML = "";

        this.#client_controller_callback.request_filtered_posts(filter_type);
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
        var post_id = post["id"];
        this.#display_post(user_from, user_from_display_name, users_to, content, post_id);

        if (this.#filter_dropdown.value == "best" || this.#filter_dropdown.value == "new"){
            // scroll top
            this.#posts_container.scrollTop = 0;
        }
        else{
            // scroll bottom
            this.#posts_container.scrollTop = this.#posts_container.scrollHeight;
        }
    
    }

    #display_post(from, from_display_name, to, content, post_id){
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

        // analytics tracker, tracks when post is in view
        var analytics_tracker = document.createElement("div");
        analytics_tracker.className = "post_analytics_tracker";
        message_container.appendChild(analytics_tracker);
        analytics_tracker.style.height="1px";
        const _this = this;
        
        // if comes into view, record a view and when leaves view, record time spent
        var observer = new IntersectionObserver(function(entries) {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    // post is in view
                    if (!(post_id in _this.#analytics_tracker_start_times)){
                        // post just came into view
                        _this.#analytics_tracker_onview(post_id);
                    }
                }
                else {
                    if (post_id in _this.#analytics_tracker_start_times){
                        // post just left view
                        _this.#analytics_tracker_onview_end(post_id);
                    }
                }
            });
        });

        observer.observe(analytics_tracker);

    }
    

    #add_post(){

        var to = "@all"; // change to user input when ui refreshed
        var content = this.#new_post_field.value;
        this.#new_post_field.value="";

        this.#client_controller_callback.add_post(content, to);
    }


    #open_messages_tab(){
        this.#messages_tab_container.style.display="block";
        this.#MainContainer.style.filter="blur(5px)";

        if (!this.#messages_tab_new_conversation_btn_event_listener_started){
            document.getElementById("MessagesAddNew").addEventListener("click", this.start_new_conversation.bind(this));
            this.#messages_tab_new_conversation_btn_event_listener_started = true;
        }
        if (!this.#messages_tab_send_btn_event_listener_started){
            document.getElementById("ChatSendMessage").addEventListener("click", this.add_message.bind(this));
            this.#messages_tab_send_btn_event_listener_started = true;
        }

        this.#client_controller_callback.get_conversations();

    }
    #close_messages_tab(){
        this.#messages_tab_container.style.display="none";
        this.#MainContainer.style.filter="";
    }

    display_conversations(conversations){
        var conversations_container = document.getElementById("ConversationsContainer");
        conversations_container.innerHTML="";

        conversations.forEach(username => {
            var a = document.createElement('a');
            a.textContent = username;
            a.href="#messages/"+username;
            a.addEventListener("click", (() => {
                this.open_conversation(username);
            }));
            conversations_container.appendChild(a);
        });
    }

    start_new_conversation(){
        var username = document.getElementById("NewConversationUsername").value;
        this.open_conversation(username);
    }

    open_conversation(username){
        this.#client_controller_callback.open_conversation(username);
        document.getElementById("ChatMessagesContainer").innerHTML = "";
    }
    display_new_message(message){
        var chat_container = document.getElementById("ChatMessagesContainer");

        var owned = message["owned"];
        var time = message["time"];
        var content = message["content"];

        var message_element = document.createElement("div");
        message_element.className = "chat_message";
        chat_container.appendChild(message_element);

        var content_text = document.createElement("p");
        content_text.textContent = content;
        message_element.appendChild(content_text);

        var time_string = "";
        var time_now = Date.now()/1000;
        var time_diff = time_now - time;
        if (time_diff < 60){
            time_string = Math.floor(time_diff)+" seconds ago";
        }
        else if (time_diff < 3600){
            time_string = Math.floor(time_diff/60)+" minutes ago";
        }
        else if (time_diff < 86400){
            time_string = Math.floor(time_diff/3600)+" hours ago";
        }
        else {
            var date = new Date(time * 1000);
            time_string = date.toLocaleDateString() + " " + date.toLocaleTimeString();
        }

        var time_text = document.createElement("p");
        time_text.className = "chat_message_time";
        time_text.textContent = time_string;
        time_text.style.fontSize = "0.7em";
        message_element.appendChild(time_text);
        
        if (owned){
            message_element.style.textAlign = "right";
        }
        else {
            message_element.style.textAlign = "left";
        }

        // scroll to bottom
        chat_container.scrollTop = chat_container.scrollHeight;
    }

    add_message(){
        var content = document.getElementById("NewMessage").value;
        document.getElementById("NewMessage").value = "";
        this.#client_controller_callback.add_message(content);
    }

    #open_my_posts_tab(){
        this.#my_posts_tab_container.style.display="block";
        this.#MainContainer.style.filter="blur(5px)";
        this.#client_controller_callback.get_my_posts();
    }
    #close_my_posts_tab(){
        this.#my_posts_tab_container.style.display="none";
        this.#MainContainer.style.filter="";
    }


    display_my_posts(posts){
        var my_posts_container = document.getElementById("MyPostsContainer");
        my_posts_container.innerHTML="";

        posts.forEach(post => {
            var from = post["from"];
            var from_display_name = post["fromname"];
            var to = post["to"];
            var content = post["content"];

            var message_container = document.createElement("div");
            message_container.className = "post";
            my_posts_container.appendChild(message_container);

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


            var analytics_container = document.createElement("div");
            analytics_container.className = "post_analytics";
            message_container.appendChild(analytics_container);

            var views_text = document.createElement("p");
            views_text.textContent = `Views: ${post["Views"]}`;
            analytics_container.appendChild(views_text);

            var likes_text = document.createElement("p");
            likes_text.textContent = `Likes: ${post["Likes"]}`;
            analytics_container.appendChild(likes_text);

            var hearts_text = document.createElement("p");
            hearts_text.textContent = `Hearts: ${post["Hearts"]}`;
            analytics_container.appendChild(hearts_text);
            
            var laughs_text = document.createElement("p");
            laughs_text.textContent = `Laughs: ${post["Laughs"]}`;
            analytics_container.appendChild(laughs_text);

            var surprises_text = document.createElement("p");
            surprises_text.textContent = `Surprises: ${post["Surprises"]}`;
            analytics_container.appendChild(surprises_text);

            var sads_text = document.createElement("p");
            sads_text.textContent = `Sads: ${post["Sads"]}`;
            analytics_container.appendChild(sads_text);

            var angrys_text = document.createElement("p");
            angrys_text.textContent = `Angrys: ${post["Angrys"]}`;
            analytics_container.appendChild(angrys_text);

            var fire_text = document.createElement("p");
            fire_text.textContent = `Fire: ${post["Fire"]}`;
            analytics_container.appendChild(fire_text);

            var computers_text = document.createElement("p");
            computers_text.textContent = `Computers: ${post["Computers"]}`;
            analytics_container.appendChild(computers_text);

            var avg_view_duration_text = document.createElement("p");
            avg_view_duration_text.textContent = `Avg View Duration: ${post["avg_view_duration"]} seconds`;
            analytics_container.appendChild(avg_view_duration_text);

            var stars_text = document.createElement("p");
            stars_text.textContent = `Stars: ${post["Stars"]}`;
            analytics_container.appendChild(stars_text);

        });
    }




    #analytics_tracker_onview(post_id){
        
        this.#analytics_tracker_start_times[post_id] = Date.now();
    }
    #analytics_tracker_onview_end(post_id){
        if (post_id in this.#analytics_tracker_start_times){
            var start_time = this.#analytics_tracker_start_times[post_id];
            delete this.#analytics_tracker_start_times[post_id];

            var end_time = Date.now();
            var duration_seconds = (end_time - start_time) / 1000;

            if (duration_seconds > 0.5){
                // only count views longer than 0.5 seconds
                if (!(post_id in this.#analytics_tracker_seen_yet)){
                    this.#analytics_tracker_seen_yet[post_id] = true;
                    this.#client_controller_callback.increment_post_analytics_view_count(post_id);
                }

                // this.#client_controller_callback.record_post_view_duration(post_id, duration_seconds);
                console.log("Post "+post_id+" viewed for "+duration_seconds+" seconds.");
            }

            delete this.#analytics_tracker_start_times[post_id];
        }
    }

}