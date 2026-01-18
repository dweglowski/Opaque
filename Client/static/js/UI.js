export {UI};

class UI {

    #client_controller_callback;

    #state = "greeting";

    #user_search_username_viewed = "";

    #analytics_tracker_seen_yet = {}; // stores whether each post id has been seen yet to only add a single view per session
    #analytics_tracker_start_times = {}; // stores when the user started viewing each post id to calculate time spent viewing


    constructor(client_controller_callback){
        this.#client_controller_callback = client_controller_callback;

        document.getElementById("LoginButton").addEventListener("click", this.start_login_process.bind(this));
        document.getElementById("SignupButton").addEventListener("click", this.start_signup_process.bind(this));
        
    }

    start_login_process(){
        this.start_signin_process();
        document.getElementById("SwitchToLogin").click();
    }

    start_signup_process(){
        this.start_signin_process();
        document.getElementById("SwitchToSignup").click();
    }

    start_signin_process(){        
        document.getElementById("GreetingContainer").classList.add("Hidden");

        var login_container = document.getElementById("LoginPopup");
        var login_username_field = document.getElementById("LoginUsername");
        var login_password_field = document.getElementById("LoginPassword");
        var login_send = document.getElementById("LoginSend");
        var login_UserDoesntExist_message = document.getElementById("UserDoesntExist");
        var login_InvalidPassword_message = document.getElementById("InvalidPassword");
        
        var signup_container = document.getElementById("SignupPopup");
        var signup_username_field = document.getElementById("SignupUsername");
        var signup_displayname_field = document.getElementById("SignupDisplayname");
        var signup_password_field = document.getElementById("SignupPassword");
        var signup_send = document.getElementById("SignupSend");
        var signup_NotUniqueUsername_message = document.getElementById("NotUniqueUsername");



        var login_switch_to_signup = document.getElementById("SwitchToSignup");
        var signup_switch_to_login = document.getElementById("SwitchToLogin");
        login_switch_to_signup.addEventListener("click", (() => {login_container.classList.remove("PopupVisible"); login_container.classList.add("PopupHidden"); signup_container.classList.remove("PopupHidden"); signup_container.classList.add("PopupVisible");}));
        signup_switch_to_login.addEventListener("click", (() => {login_container.classList.remove("PopupHidden"); login_container.classList.add("PopupVisible"); signup_container.classList.remove("PopupVisible"); signup_container.classList.add("PopupHidden");}));
        
        login_send.addEventListener("click", this.login.bind(this)); // bind used to preserve "this"
        signup_send.addEventListener("click", this.signup.bind(this)); // bind used to preserve "this"
        
        
        var signup_profile_picture_upload = document.getElementById("SignupProfilePictureUpload");
        signup_profile_picture_upload.addEventListener("change", this.signup_profile_picture_added.bind(this));

        // add default image to profile picture
        this.#add_image_to_canvas_fixed_size("SignupProfilePicture", "/uploads/profile_pictures/0.png", 200, 200);
    }
    login(){
        document.getElementById("UserDoesntExist").style.display="none";
        document.getElementById("InvalidPassword").style.display="none";

        var username = document.getElementById("LoginUsername").value;
        var password = document.getElementById("LoginPassword").value;
        
        this.#client_controller_callback.login_start(username,password);
    }
    
    signup(){
        var username = document.getElementById("SignupUsername").value;
        var display_name = document.getElementById("SignupDisplayname").value;
        var password = document.getElementById("SignupPassword").value;
        
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
        document.getElementById("UserDoesntExist").style.display="none";
        document.getElementById("InvalidPassword").style.display="none";
        if (reason == "DoesntExist"){
            document.getElementById("UserDoesntExist").style.display="block";
        }
        else if (reason == "Password"){
            document.getElementById("InvalidPassword").style.display="block";
        }
    }
    
    login_success(){
        document.getElementById("LoginPopup").classList.remove("PopupVisible");
        document.getElementById("LoginPopup").classList.add("PopupHidden");
    }
    
    signup_failed(reason){
        if (reason == "NotUnique"){
            document.getElementById("NotUniqueUsername").style.display="block";
        }
    }
    
    signup_success(){
        document.getElementById("SignupPopup").classList.remove("PopupVisible");
        document.getElementById("SignupPopup").classList.add("PopupHidden");
    }

    #logout(){
        location.reload();
    }



    show_main_page(){
        
        this.#state="main";
        document.getElementById("MainContainer").classList.remove("Hidden");

        var new_post_field = document.getElementById("NewPost");

        var add_post_btn = document.getElementById("SendPost");
        add_post_btn.addEventListener("click", this.#add_post.bind(this)); // bind used to preserve "this"
        document.getElementById("NewPostCancel").addEventListener("click", this.show_posts_homepage.bind(this));
        document.getElementById("PostVisibilityPrivate").addEventListener("change", this.new_post_toggle_visibility.bind(this));
        document.getElementById("PostVisibilityPublic").addEventListener("change", this.new_post_toggle_visibility.bind(this));
        
        
        var posts_container = document.getElementById("PostsContainer");
        
        document.getElementById("NewPostButton").addEventListener("click", this.show_new_post_popup.bind(this));
        
        var new_post_content_container = document.getElementById("NewPostContentPopup");

        var new_post_content_container = document.getElementById("NewPostContentPopup");
        var new_post_image_template = document.getElementById("NewPostImageTemplateCanvas");
        var new_post_images_container = document.getElementById("NewPostImagesContainer");
        
        
        var new_post_image_upload = document.getElementById("NewPostImageUpload");
        new_post_image_upload.addEventListener("change", this.new_post_picture_added.bind(this));
        
        var filter_dropdown = document.getElementById("FilterDropdown");
        filter_dropdown.addEventListener("change", this.#start_filter.bind(this));


        this.#init_user_search();
        this.#init_messages_tab();
        this.#init_my_posts_tab();
        this.#init_navbar();
        
    }

    #init_navbar(){
        document.getElementById("NavbarHome").addEventListener("click", this.show_posts_homepage.bind(this));
        document.getElementById("NavbarUserSearch").addEventListener("click", this.show_user_search.bind(this));
        document.getElementById("NavbarMessages").addEventListener("click", this.show_messages_tab.bind(this));
        document.getElementById("NavbarMyPosts").addEventListener("click", this.show_my_posts_tab.bind(this));
    }

    #init_user_search(){
        var user_search_container = document.getElementById("UserSearchPopup");
        var user_search_result_container = document.getElementById("UserSearchResultPopup");
        
        document.getElementById("UserSearchAddFriend").addEventListener("click", this.user_search_add_friend.bind(this));
        document.getElementById("UserSearchRemoveFriend").addEventListener("click", this.user_search_remove_friend.bind(this));
        document.getElementById("UserSearchFollow").addEventListener("click", this.user_search_follow.bind(this));
        document.getElementById("UserSearchUnfollow").addEventListener("click", this.user_search_unfollow.bind(this));
    }
    #init_messages_tab(){
        var messages_tab_container = document.getElementById("MessagesTab");

        var messages_tab_close_btn = document.getElementById("MessagesTabClose");
        messages_tab_close_btn.addEventListener("click", this.#close_messages_tab.bind(this));
    }    
    #init_my_posts_tab(){
        var my_posts_tab_container = document.getElementById("MyPostsTab");
        
    }

    show_posts_homepage(){
        document.getElementById("MainContentArea").classList.remove("Hidden");
        document.getElementById("UserSearchContentArea").classList.add("Hidden");
        document.getElementById("NewPostContentArea").classList.add("Hidden");
        document.getElementById("MessagesContentArea").classList.add("Hidden");
        document.getElementById("MyPostsTab").classList.add("Hidden");
    }
    show_user_search(){
        document.getElementById("MainContentArea").classList.add("Hidden");
        document.getElementById("UserSearchContentArea").classList.remove("Hidden");
        document.getElementById("NewPostContentArea").classList.add("Hidden");
        document.getElementById("MessagesContentArea").classList.add("Hidden");
        document.getElementById("MyPostsTab").classList.add("Hidden");
        
        this.#open_user_search();
    }
    show_new_post_popup(){
        document.getElementById("NewPostContentArea").classList.remove("Hidden");
        document.getElementById("MainContentArea").classList.add("Hidden");
        document.getElementById("UserSearchContentArea").classList.add("Hidden");
        document.getElementById("MessagesContentArea").classList.add("Hidden");
        document.getElementById("MyPostsTab").classList.add("Hidden");
    }
    show_messages_tab(){
        document.getElementById("MainContentArea").classList.add("Hidden");
        document.getElementById("UserSearchContentArea").classList.add("Hidden");
        document.getElementById("NewPostContentArea").classList.add("Hidden");
        document.getElementById("MessagesContentArea").classList.remove("Hidden");
        document.getElementById("MyPostsTab").classList.add("Hidden");
        this.#open_messages_tab();
    }
    show_my_posts_tab(){
        document.getElementById("MainContentArea").classList.add("Hidden");
        document.getElementById("UserSearchContentArea").classList.add("Hidden");
        document.getElementById("NewPostContentArea").classList.add("Hidden");
        document.getElementById("MessagesContentArea").classList.add("Hidden");
        document.getElementById("MyPostsTab").classList.remove("Hidden");

        this.#open_my_posts_tab();
    }

    

    display_username(username, displayname){
        var profile_display_name = document.getElementById("DisplayName");
        profile_display_name.textContent=displayname;
        document.getElementById("ProfileIconTopRight").addEventListener("click", this.#toggle_ProfileIconTopRight_dropdown);
        document.getElementById("MyProfileButton").addEventListener("click", this.#user_search.bind(this, username))
        document.getElementById("MyProfileButton").addEventListener("click", this.#toggle_ProfileIconTopRight_dropdown)
        document.getElementById("LogoutButton").addEventListener("click", this.#logout.bind(this))
    }

    #toggle_ProfileIconTopRight_dropdown(){
        var dropdown = document.getElementById("ProfileIconTopRightDropdownMenu");
        if (dropdown.classList.contains("Hidden")){
            dropdown.classList.remove("Hidden");
        }
        else {
            dropdown.classList.add("Hidden");
        }
    }

    display_profile_picture_icon(pictureid){
        this.#add_image_to_canvas_fixed_size("MyProfilePicture", "/uploads/profile_pictures/"+pictureid+".png", 50, 50);
    }

    #open_user_search(){
        document.getElementById("UserSearchContainer").classList.remove("Hidden");
        document.getElementById("UserSearchResultContainer").classList.add("Hidden");

        var user_search_username = document.getElementById("SearchUsername");
        var user_search_suggestions_container = document.getElementById("UserSearchSuggestionsResult");

        if (user_search_username.dataset.eventListenerStarted != "true"){
            // Only add event listener once
            user_search_username.dataset.eventListenerStarted = "true";
            user_search_username.addEventListener("input", this.request_username_suggestions.bind(this));
        }
        this.request_username_suggestions();
    }


    request_username_suggestions(){
        var username = document.getElementById("SearchUsername").value;
        this.#client_controller_callback.user_search_suggestions(username);
    }

    username_suggestions_results(results){
        document.getElementById("UserSearchSuggestionsResult").innerHTML = "";
        results.forEach(user => {
            var p = document.createElement('p');
            p.textContent = user;
            p.className = "UserSearchSuggestion";
            let username = user;
            p.addEventListener("click", (() => {
                document.getElementById("SearchUsername").value = username;
                this.start_user_search();
            }));
            document.getElementById("UserSearchSuggestionsResult").appendChild(p);
        });
    }

    #user_search(username){
        this.#client_controller_callback.user_search(username);
    }
    
    start_user_search(){
        var username = document.getElementById("SearchUsername").value;
        this.#user_search(username);
    }

    user_search_result(result){

        this.show_user_search();

        document.getElementById("UserSearchContainer").classList.add("Hidden");
        document.getElementById("UserSearchResultContainer").classList.remove("Hidden");
        
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

        document.getElementById("SearchResultFriendsCount").textContent = result["num_friends"];
        document.getElementById("SearchResultFollowersCount").textContent = result["num_followers"];
        document.getElementById("SearchResultDegreeOfSeparation").textContent = result["degree_of_separation"];
        document.getElementById("SearchResultMutualFriends").innerHTML = result["mutual_friends"].join("<br>");

        var user_search_result_close_btn = document.getElementById("UserSearchResultClose");
        user_search_result_close_btn.addEventListener("click", this.user_search_result_close.bind(this)); // bind used to preserve "this"
    }

    user_search_result_close(){
        document.getElementById("UserSearchContainer").classList.remove("Hidden");
        document.getElementById("UserSearchResultContainer").classList.add("Hidden");
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

    #start_filter(){
        var filter_type = document.getElementById("FilterDropdown").value;

        // clear all existing posts
        document.getElementById("PostsContainer").innerHTML = "";

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
            _this.#add_new_canvas_with_image(document.getElementById("NewPostImageTemplateCanvas"), img_data, 1000, 1000);
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
        
        var image_canvases = document.getElementById("NewPostImagesContainer").children;

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

        var filter_dropdown = document.getElementById("FilterDropdown");
        var posts_container = document.getElementById("PostsContainer");

        if (filter_dropdown.value == "best" || filter_dropdown.value == "new"){
            // scroll top
            posts_container.scrollTop = 0;
        }
        else{
            // scroll bottom
            posts_container.scrollTop = posts_container.scrollHeight;
        }
    
    }

    #display_post(from, from_display_name, to, content, post_id){
        var message_container = document.createElement("div");
        message_container.className = "post";
        var posts_container = document.getElementById("PostsContainer");
        posts_container.appendChild(message_container);

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


        // start rating system
        var rating_container = document.createElement("div");
        rating_container.className = "post_ratings";
        message_container.appendChild(rating_container);
        for (var i = 1; i <= 5; i++) {
            let value = i; // prevents it changing in event listener

            var star_button = document.createElement("button");
            star_button.textContent = "☆";
            star_button.id = "StarScoreButton"+post_id+"_"+i;
            
            star_button.addEventListener("click", (() => {
                this.#star_rating_onclick(post_id, value);
            }).bind(this));
            
            rating_container.appendChild(star_button);
        }


        // reactions container
        var reactions_container = document.createElement("div");
        reactions_container.className = "post_reactions";
        message_container.appendChild(reactions_container);
        var reaction_types = ["Likes", "Hearts", "Laughs", "Surprises", "Sads", "Angrys", "Fire", "Computers"];
        var reaction_emojis = ["👍","❤️","😂","😮","😢","😡","🔥","💻"];
        for (var i = 0; i < reaction_types.length; i++) {
            let reaction_type = reaction_types[i];
            var reaction_button = document.createElement("button");
            reaction_button.textContent = reaction_emojis[i];
            reaction_button.id = "ReactionButton"+post_id+"_"+reaction_type;
            reaction_button.addEventListener("click", (() => {
                this.#reaction_button_onclick(post_id, reaction_type);
            }).bind(this));
            reactions_container.appendChild(reaction_button);
        }
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


    new_post_toggle_visibility(){
        var private_radio = document.getElementById("PostVisibilityPrivate");
        var user_selection = document.getElementById("NewPostUserSelection");
        if (private_radio.checked){
            user_selection.classList.remove("Hidden");
        }
        else {
            user_selection.classList.add("Hidden");
        }
    }


    #add_post(){

        var to = "@all";
        if (document.getElementById("PostVisibilityPrivate").checked){
            to = document.getElementById("NewPostAllowedUsers").value;
        }
        
        var content = document.getElementById("NewPostContent").value;
        document.getElementById("NewPostContent").value="";

        this.#client_controller_callback.add_post(content, to);

        this.show_posts_homepage();
    }


    #open_messages_tab(){
        
        if (document.getElementById("MessagesAddNew").dataset.eventListenerStarted != "true"){
            document.getElementById("MessagesAddNew").dataset.eventListenerStarted = "true";
            document.getElementById("MessagesAddNew").addEventListener("click", this.start_new_conversation.bind(this));
        }
        if (document.getElementById("ChatSendMessage").dataset.eventListenerStarted != "true"){
            document.getElementById("ChatSendMessage").dataset.eventListenerStarted = "true";
            document.getElementById("ChatSendMessage").addEventListener("click", this.add_message.bind(this));
        }

        this.#client_controller_callback.get_conversations();

    }
    #close_messages_tab(){
        this.show_posts_homepage();
    }

    display_conversations(conversations){
        var conversations_container = document.getElementById("ConversationsContainer");
        conversations_container.innerHTML="";

        conversations.forEach(username => {
            var a = document.createElement('a');
            a.textContent = username;
            a.href="#messages/"+username;
            let conversation_open_link = a;
            a.addEventListener("click", (() => {
                this.open_conversation(username);
                for (let link of conversations_container.children){
                    link.classList.remove("active");
                }
                conversation_open_link.classList.add("active");
            }));
            conversations_container.appendChild(a);
        });
    }

    start_new_conversation(){
        var username = document.getElementById("NewConversationUsername").value.toLowerCase();
        this.open_conversation(username);
    }

    open_conversation(username){
        this.#client_controller_callback.open_conversation(username);
        document.getElementById("ChatMessagesContainer").innerHTML = "";
        document.getElementById("ChatTitle").textContent = "Chat with " + username;
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
        this.#client_controller_callback.get_my_posts();
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

            var reactions_row = document.createElement("div");
            reactions_row.className = "post_analytics_reactions_row";
            analytics_container.appendChild(reactions_row);

            var reaction_emojis = ["👍","❤️","😂","😮","😢","😡","🔥","💻"];

            var likes_text = document.createElement("p");
            likes_text.textContent = `${reaction_emojis[0]} ${post["Likes"]}`;
            reactions_row.appendChild(likes_text);

            var hearts_text = document.createElement("p");
            hearts_text.textContent = `${reaction_emojis[1]} ${post["Hearts"]}`;
            reactions_row.appendChild(hearts_text);
            
            var laughs_text = document.createElement("p");
            laughs_text.textContent = `${reaction_emojis[2]} ${post["Laughs"]}`;
            reactions_row.appendChild(laughs_text);

            var surprises_text = document.createElement("p");
            surprises_text.textContent = `${reaction_emojis[3]} ${post["Surprises"]}`;
            reactions_row.appendChild(surprises_text);

            var sads_text = document.createElement("p");
            sads_text.textContent = `${reaction_emojis[4]} ${post["Sads"]}`;
            reactions_row.appendChild(sads_text);

            var angrys_text = document.createElement("p");
            angrys_text.textContent = `${reaction_emojis[5]} ${post["Angrys"]}`;
            reactions_row.appendChild(angrys_text);

            var fire_text = document.createElement("p");
            fire_text.textContent = `${reaction_emojis[6]} ${post["Fire"]}`;
            reactions_row.appendChild(fire_text);

            var computers_text = document.createElement("p");
            computers_text.textContent = `${reaction_emojis[7]} ${post["Computers"]}`;
            reactions_row.appendChild(computers_text);

            var avg_view_duration_text = document.createElement("p");
            avg_view_duration_text.textContent = `Avg View Duration: ${post["avg_view_duration"]} seconds`;
            analytics_container.appendChild(avg_view_duration_text);

            var stars_text = document.createElement("p");
            var stars = post["Stars"];
            if (stars < 1){
                stars = 1;
            }
            else if (stars > 5){
                stars = 5;
            }
            stars = stars.toFixed(1);
            stars_text.textContent = `Stars: ${stars}`;
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
                duration_seconds = Math.ceil(duration_seconds);
                this.#client_controller_callback.increment_post_view_duration(post_id, duration_seconds);
            }

            delete this.#analytics_tracker_start_times[post_id];
        }
    }
    #star_rating_onclick(post_id, rating_value){
        this.#client_controller_callback.rate_post(post_id, rating_value);

        // update buttons after rating
        for (var i = 1; i <= 5; i++) {
            var star_button = document.getElementById("StarScoreButton"+post_id+"_"+i);
            if (i <= rating_value){
                star_button.textContent = "★";
            }
            else {
                star_button.textContent = "☆";
            }
        }
    }

    #reaction_button_onclick(post_id, reaction_type){
        this.#client_controller_callback.add_post_reaction(post_id, reaction_type);

        // dissable buttons after reaction
        for (var i = 1; i <= 5; i++) {
            var reaction_button = document.getElementById("ReactionButton"+post_id+"_"+reaction_type);
            if (reaction_button){
                reaction_button.disabled = true;
            }
        }
    }

}