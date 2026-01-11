import WebServer
import Database
import Media
import typing
import time
import re
import uuid

from Datastructures import Trie, Graph
from Crypotography import CrypotgraphyController

# Define custom type hints
from ServerUtils import TYPE_POST, TYPE_POSTS


class ServerController:
    def __init__(self) -> None:
        """Constructor"""
        
        self.__init_cryptography()
        self.__init_web_server()
        self.__init_database()
        self.__init_media()

        # list of all connected client uuids
        self.__active_connection_uuids : typing.List[str] = []

        # storage for information about each session such as auth state and username etc.
        self.__uuid_session_storage : typing.Dict[str, typing.Dict[str, str | float | int | bool ]] = {}

        # storage for users subscribed to posts feed and their "send post to client" callback
        self.__post_feed_subscribers : typing.Dict[str, typing.Callable[[TYPE_POST], None]] = {}
        self.__messages_feed_subscribers : typing.Dict[str, typing.Callable[[TYPE_POST], None]] = {}

        # store all usernames in a quickly searchable way
        self.__username_trie : Trie = Trie("abcdefghijklmnopqrstuvwxyz0123456789_")
        self.__load_usernames()

        # store all connections in a quickly searchable way
        self.__friend_graph : Graph = Graph()
        self.__following_graph : Graph = Graph()
        self.__load_connections()


    def __init_cryptography(self) -> None:
        """Initialise the cryptography controller and all logic that should be done to achive this."""
        self.__cryptography_controller : CrypotgraphyController = CrypotgraphyController()
        self.__cryptography_controller.generate_server_tls_keys()

    def __init_web_server(self) -> None:
        """Initialise the webserver and all logic that should be done to achive this."""
        self.__webserver : WebServer.WebServerController = WebServer.WebServerController(self, self.__cryptography_controller)

    def __init_database(self) -> None:
        """Initialise the database and all logic that should be done to achive this."""
        self.__database : Database.DatabaseController = Database.DatabaseController()

    def __init_media(self) -> None:
        """Initialise the media controller and all logic that should be done to achive this."""
        self.__media : Media.MediaController = Media.MediaController(self.generate_uuid)

    def __load_usernames(self) -> None:
        """Loads all username into the trie."""
        usernames : typing.List[str] = self.__database.get_username_list()
        
        username : str
        for username in usernames:
            self.__add_user_to_trie(username)

    def __load_connections(self) -> None:
        """Loads all existing friends and followes into the graph."""
        # first load usernames into graphs
        usernames : typing.List[str] = self.__database.get_username_list()
        username : str
        for username in usernames:
            self.__friend_graph.add_user(username)
            self.__following_graph.add_user(username)

        # load all connections into graph
        connections : typing.List[typing.Tuple[str,str,bool,bool]] = self.__database.get_all_connections()

        for user, connected_user, isFriend, isFollowing in connections:
            if isFriend:
                self.__friend_graph.add_connection(user, connected_user)
            if isFollowing:
                self.__following_graph.add_connection(user, connected_user)

    def start(self) -> None:
        """Starts the server running."""
        self.__webserver.start()
        input("Press enter to stop..\n")
        self.__database.close()
        print("Safe to kill process")
        quit()

    def generate_uuid(self) -> str:
        """Generates a UUID (universally unique identifier) to be used throughout the program"""
        return str(uuid.uuid4())

    def generate_uuid_for_connection(self) -> str:
        """Generate a random UUID that isn't in use for active connections."""
        uuid : str = ""
        while not uuid or uuid in self.__active_connection_uuids:
            uuid = self.generate_uuid()

        return uuid     

    def add_new_connected_user(self, uuid : str) -> None:
        """Called when a new client connects, stores information about their session."""
        
        # ensure uuid is not already used, prevents race condition
        assert uuid not in self.__active_connection_uuids, "Error, invalid UUID, collision caused by race condition"

        self.__active_connection_uuids.append(uuid)

        self.__uuid_session_storage[uuid] = {}

        # load basic start info about user
        self.__uuid_session_storage[uuid]["username"] = "#anonymous_user"
        self.__uuid_session_storage[uuid]["time connected"] = time.time()

    def remove_connected_user(self, uuid : str) -> None:
        """Called when a client disconnects, clears associated session."""

        self.__uuid_session_storage.pop(uuid)
        self.__active_connection_uuids.remove(uuid)
        if uuid in self.__post_feed_subscribers:
            self.__post_feed_subscribers.pop(uuid)
        if uuid in self.__messages_feed_subscribers:
            self.__messages_feed_subscribers.pop(uuid)

        print(self.__active_connection_uuids,self.__uuid_session_storage)


    def __set_username(self, username : str, uuid : str) -> None:
        """Sets a client's username in session storage."""
        self.__uuid_session_storage[uuid]["username"] = username

    def get_username(self, uuid : str) -> str:
        """Gets a client's username from session storage."""
        return self.__uuid_session_storage[uuid]["username"]

    def get_password_salt(self, username: str, uuid: str) -> str:
        """Provides a hashing salt for a specific user"""
        # sanitize
        username = re.sub("[^a-zA-Z0-9_]","", username.lower())

        if not self.__check_username_exists(username):
            return ""

        return self.__database.get_password_salt(username)


    def login(self, username: str, hash : str, uuid: str) -> typing.Tuple[bool, str]:
        """Attempts to login a client, returns success, error code."""
        # sanitize
        username = re.sub("[^a-zA-Z0-9_]","", username.lower())

        if not self.__check_username_exists(username):
            return False, "InvalidUsername"

        # TODO: auth system
        if not self.__database.check_password_matches(hash, username):
            return False, "InvalidPassword"

        self.__set_username(username, uuid)

        return True, ""

    def signup(self, username: str, display_name: str, hash : str, salt : str, uuid: str) -> typing.Tuple[bool, str]:
        """Attempts to sign up client, returns success, error code."""
        # sanitize
        username = re.sub("[^a-zA-Z0-9_]","", username.lower())
        display_name = re.sub("[^a-zA-Z0-9_ ]","", display_name.lower())

        if self.__check_username_exists(username):
            return False, "InvalidUsername"


        self.__database.add_new_signup(username, hash, salt)
        self.__database.add_new_profile(username, display_name)
        self.__username_trie.add_string(username)

        self.__set_username(username, uuid)

        return True, ""

    def is_logged_in(self, uuid: str) -> bool:
        """Returns whether a user session has logged in."""
        return self.__uuid_session_storage[uuid]["username"] != "#anonymous_user"

    def __add_user_to_trie(self, username : str) -> None:
        """Adds a new username to the trie to quickly search for users."""
        print("adding ", username)
        self.__username_trie.add_string(username)

    def __check_username_exists(self, username : str) -> bool:
        username = username.lower()
        return self.__username_trie.check_string_exists(username)

    def profile_get_display_name(self, username : str) -> str:
        """Returns the display name of a user."""
        return self.__database.profile_get_displayname(username)

    def profile_get_profile_pictureid(self, username : str) -> str:
        """Returns the uuid for a user's profile picture."""
        pictureid : str = self.__database.profile_get_pictureid(username)
        return re.sub("[^0-9]*","", pictureid) # sanitize first

    def get_profile_info(self, uuid:str) -> typing.Dict[str, str]:
        username : str = self.get_username(uuid)

        displayname: str = self.profile_get_display_name(username)
        pictureID: str = self.profile_get_profile_pictureid(username)

        result : typing.Dict[str, str] = {
                "username": username,
                "displayname": displayname,
                "pictureid":pictureID,
            }
        return result

    def user_search(self, uuid : str, username : str) -> typing.Tuple[bool, typing.Dict[str,str]]:
        """Tries to find a user by username and returns basic info."""
        if not self.__check_username_exists(username):
            return False, {}

        display_name : str = self.__database.profile_get_displayname(username)
        pictureID : str = self.__database.profile_get_pictureid(username)

        isFriend: bool = self.is_friend(uuid, username)
        isFollowed: bool = self.is_following(uuid, username)


        resp : typing.Dict[str,str] = {
            "username": username,
            "displayname": display_name,
            "pictureid":pictureID,
            "isFriend":isFriend,
            "isFollowed":isFollowed,
        }

        return True, resp

    def user_search_suggestions(self, start_username : str) -> typing.List[str]:
        """Returns a list of the first N usernames which start with the string provided."""

        usernames : typing.List[str] = self.__username_trie.get_all_endings(start_username, max_num=5)

        return usernames



    def get_posts(self) -> TYPE_POSTS:
        """Gets and returns all posts from database."""
        return self.__database.get_posts()

    def subscribe_client_to_posts_feed(self, uuid : str, send_post_to_client_callback : typing.Callable[[TYPE_POST], None]) -> None:
        """Subscribes a client to a posts feed to recieve event update messages for each new post."""
        self.__post_feed_subscribers[uuid] = send_post_to_client_callback

    def __validate_post_is_for_client(self, post : TYPE_POST, uuid : str) -> None:

        client_username : str = self.get_username(uuid)

        users_to : str = ""
        if post["to"] == "@all" or client_username in post["to"].split("@"):
            return True

        return False
    def __validate_post_is_for_client(self, post : TYPE_POST, uuid : str) -> None:

        client_username : str = self.get_username(uuid)

        users_to : str = ""
        if post["to"] == "@all" or client_username in post["to"].split("@"):
            return True

        return False

    def __validate_message_is_for_client(self, message : TYPE_POST, uuid : str) -> None:

        client_username : str = self.get_username(uuid)

        if message["to"] == client_username or message["from"] == client_username:
            return True

        return False

    def __is_message_between_users(self, message : TYPE_POST, uuid:str, username : str) -> None:

        client_username : str = self.get_username(uuid)

        if (message["to"] == username and message["from"] == client_username) or (message["from"] == username and message["to"] == client_username):
            return True

        return False


    def __set_cache_filter_type(self, filter_type : str, uuid : str) -> None:
        """Sets a client's active filter type in session storage."""
        self.__uuid_session_storage[uuid]["filter_type"] = filter_type

    def __get_cache_filter_type(self, uuid : str) -> str:
        """Retruns the client's active filter type from session storage."""
        return self.__uuid_session_storage[uuid].get("filter_type","all")

    def send_existing_posts_to_client(self, uuid : str, filter_type : str = "all") -> str:
        """Sends all relevant existing posts to a client, applies filter in required"""
        all_posts : TYPE_POSTS = self.get_posts()

        send_post_to_client_callback : typing.Callable[[TYPE_POST], None] = self.__post_feed_subscribers[uuid]

        # cache filter_type for new messages
        self.__set_cache_filter_type(filter_type, uuid)

        if self.__check_filter_requires_sorting(filter_type):
            # sort posts by metric
            all_posts = self.__sort_posts(filter_type, all_posts)

        for post in all_posts:
            # only posts that are shared with user
            if self.__validate_post_is_for_client(post, uuid):
                # filter posts
                if self.__check_post_matches_filter(post, filter_type, uuid):
                    send_post_to_client_callback(post)

    def __check_filter_requires_sorting(self, filter_type: str) -> bool:
        """Returns whether a filter type requires sorting posts by any metric."""
        if filter_type == "new":
            return True
        if filter_type == "best":
            return True
        return False
    
    def __sort_posts(self, filter_type : str, posts : TYPE_POSTS) -> TYPE_POSTS:
        """Sorts a list of posts following specific criteria."""
        if filter_type == "new":
            return posts[::-1] # most recent first

        if filter_type == "best":
            # sort by star score
            star_scores : typing.Dict[str, float] = {}
            for post in posts:
                postid : str = post["id"]
                star_score : float = self.get_analytics_data_for_post(postid).get("star_score", 0.0)
                star_scores[postid] = star_score

            return sorted(posts, key = lambda post: star_scores[post["id"]], reverse=True)

        return posts

    def __check_post_matches_filter(self, post : TYPE_POST, filter_type : str, uuid : str) -> bool:
        """Returns whether a post matches a particular filter."""
        if filter_type == "all":
            return True
        if filter_type == "new":
            return True
        if filter_type == "best":
            return True
        
        if filter_type == "following":
            # return true only if the post owner is being followed by the client requesting them
            sender : str = post["from"]
            if self.is_following(uuid, sender):
                return True
            return False
        
        if filter_type == "friends":
            # return true only if the post owner is a friend of the client requesting them
            sender : str = post["from"]
            if self.is_friend(uuid, sender):
                return True
            return False
        
        if filter_type == "news":
            # return true if the post is tagged as a news post, done by checking for a #news tag
            if "#news" in post["content"].lower():
                return True
            return False
        
        return False


    def __send_new_post_to_relevant_users(self, post : TYPE_POST) -> None:
        """Sends a newly added post to all relevant active clients."""
        uuid : str
        send_post_to_client_callback : typing.Callable[[TYPE_POST], None]

        post["fromname"] = self.__database.profile_get_displayname(post["from"])

        for uuid in self.__post_feed_subscribers:

            if not self.__validate_post_is_for_client(post, uuid):
                continue
            
            filter_type : str = self.__get_cache_filter_type(uuid)
            if not self.__check_post_matches_filter(post, filter_type, uuid):
                continue

            # new post marked for this client, send update to client
            send_post_to_client_callback = self.__post_feed_subscribers[uuid]
            send_post_to_client_callback(post)



    def add_post(self, post : TYPE_POST, username : str) -> None:
        """Adds a new post to the database."""

        post["from"] = username

        post_id: int = self.__database.add_post(post)

        post["id"] = str(post_id)
        # ensure all clients recive this message
        self.__send_new_post_to_relevant_users(post)


    
    def get_messages(self) -> TYPE_POSTS:
        """Gets and returns all direct messages from the database"""
        return  self.__database.get_messages()


    def subscribe_client_to_messages_feed(self, uuid : str, send_message_to_client_callback : typing.Callable[[TYPE_POST], None]) -> None:
        """Subscribes a client to a messages feed to recieve event update messages for each new direct message."""
        self.__messages_feed_subscribers[uuid] = send_message_to_client_callback

    def __set_cache_client_active_message_tab(self, filter_type : str, uuid : str) -> None:
        """Stores which direct message conversation a client has open in session storage."""
        self.__uuid_session_storage[uuid]["active_conversation"] = filter_type

    def __get_cache_client_active_message_tab(self, uuid : str) -> str:
        """Retruns the client's active filter type from session storage."""
        return self.__uuid_session_storage[uuid].get("active_conversation","")

    def send_existing_messages_to_client(self, uuid : str, user_from : str) -> str:
        """Sends all relevant existing direct messages to a client from a specific user"""
        all_messages : TYPE_POSTS = self.get_messages()

        send_message_to_client_callback : typing.Callable[[TYPE_POST], None] = self.__messages_feed_subscribers[uuid]

        # cache open tab for new messages
        self.__set_cache_client_active_message_tab(user_from, uuid)

        client_username : str = self.get_username(uuid)

        
        for message in all_messages:
            # only messages between the 2 users
            if self.__validate_message_is_for_client(message, uuid):
                if self.__is_message_between_users(message, uuid, user_from):
                    message_copy : TYPE_POST = message.copy()
                    # Store whether you are the sender to display this info in the ui
                    if message["from"] == client_username:
                        message_copy["owned"] = True
                    else:
                        message_copy["owned"] = False
                    send_message_to_client_callback(message_copy)

    
    def __send_new_message_to_relevant_users(self, message : TYPE_POST) -> None:
        """Sends a newly added direct message to all relevant active clients of that user."""
        uuid : str
        send_message_to_client_callback : typing.Callable[[TYPE_POST], None]

        for uuid in self.__messages_feed_subscribers:

            if not self.__validate_message_is_for_client(message, uuid):
                continue
            
            if self.__get_cache_client_active_message_tab(uuid) != message["from"] and self.__get_cache_client_active_message_tab(uuid) != message["to"]:
                continue

            # new post marked for this client, send update to client
            
            message_copy : TYPE_POST = message.copy()
            # Store whether you are the sender to display this info in the ui
            client_username : str = self.get_username(uuid)
            if message["from"] == client_username:
                message_copy["owned"] = True
            else:
                message_copy["owned"] = False

            send_message_to_client_callback = self.__messages_feed_subscribers[uuid]
            send_message_to_client_callback(message_copy)
            
    def get_most_recent_conversations(self, uuid : str) -> typing.List[str]:
        """Returns a list of the most most recent conversations with this client"""
        all_messages : TYPE_POSTS = self.get_messages()

        client_username : str = self.get_username(uuid)

        # Store the time of the most recent message from each conversation to determine newest conversations
        most_recent_per_conversation : typing.Dict[str, float] = {}

        for message in all_messages:
            # only messages between the 2 users
            if self.__validate_message_is_for_client(message, uuid):
                user_with : str = ""
                if message["from"] == client_username:
                    user_with = message["to"]
                else:
                    user_with = message["from"]
                
                message_time: float = float(message["time"])
                if message_time > most_recent_per_conversation.get(user_with, 0.0):
                    most_recent_per_conversation[user_with] = message_time

        most_recent_conversations = sorted(most_recent_per_conversation.keys(), key = most_recent_per_conversation.get, reverse=True)

        return most_recent_conversations 


    def add_message(self, post : TYPE_POST, username : str) -> None:
        """Adds a new direct message to the database."""

        post["from"] = username
        post["time"] = time.time()

        self.__database.add_message(post)

        # send this message the client if they are online and have the chat open
        self.__send_new_message_to_relevant_users(post)


    def get_my_posts(self, uuid : str) -> TYPE_POSTS:
        """Returns all posts made by the current user along with analytics data."""
        username : str = self.get_username(uuid)
        all_posts : TYPE_POSTS = self.get_posts()

        my_posts : TYPE_POSTS = []

        post : TYPE_POST
        for post in all_posts:
            if post["from"] == username:
                post |= self.get_analytics_data_for_post(post["id"])
                my_posts.append(post)

        my_posts = my_posts[::-1] # most recent first
        return my_posts
    
    def get_analytics_data_for_post(self, postid : str) -> typing.Dict[str, int | str | float]:
        """Returns analytics data for a particular post."""
        # placeholder implementation
        data : typing.Dict[str, str] = self.__database.get_analytics_for_post(postid)
        data["star_score"] = data["star_score"] / (max(1, data["num_ratings"])) # average star score
        
        return data
    
    def update_analytics_data_for_post(self, postid : str, reactions_encrypted : str, avg_view_duration_seconds : float) -> None:
        """Updates analytics data for a particular post."""
        self.__database.update_reactions(postid, reactions_encrypted)
        self.__database.update_average_view_time(postid, avg_view_duration_seconds)

    def increment_post_analytics_view_count(self, postid : str) -> None:
        """Increments the view count for a particular post."""
        current_view_count : int = self.__database.get_analytics_for_post(postid).get("views",0)
        self.__database.update_view_count(postid, current_view_count + 1)

    def increment_post_analytics_star_score(self, postid : str, star_score : float) -> None:
        """Increments the star score for a particular post."""
        current_star_score : float = self.__database.get_analytics_for_post(postid).get("star_score",0.0)
        self.__database.update_star_score(postid, current_star_score + star_score)

    def get_profile_picture(self, uuid : str) -> bytes:
        """Finds and returns a profile picture stored on the server."""
        return self.__media.get_profile_picture(uuid)

    def upload_profile_picture(self, raw_data) -> str:
        """Uploads a new profile picture, returns the uuid."""
        return self.__media.upload_profile_picture(raw_data)

    def update_profile_picture(self, uuid, pictureUUID) -> None:
        username : str = self.get_username(uuid)
        self.__database.update_profile_picture(username, pictureUUID)

    def get_post_picture(self, uuid : str) -> bytes:
        """Finds and returns a post picture stored on the server."""
        return self.__media.get_post_picture(uuid)

    def upload_post_picture(self, raw_data) -> str:
        """Uploads a new post picture, returns the uuid."""
        return self.__media.upload_post_picture(raw_data)
    
    def add_friend(self, uuid : str, connected_username : str) -> None:
        """Adds another user as a friend of the current user."""
        username : str = self.get_username(uuid)
        self.__friend_graph.add_connection(username, connected_username)
        self.__database.add_connection(username, connected_username, friend = True)

    def add_following(self, uuid : str, connected_username : str) -> None:
        """Adds another user to the list of users followed by the current user."""
        username : str = self.get_username(uuid)
        self.__following_graph.add_connection(username, connected_username)
        self.__database.add_connection(username, connected_username, follow = True)

    def remove_friend(self, uuid : str, connected_username : str) -> None:
        """Removes a user from friend list of the current user."""
        username : str = self.get_username(uuid)
        self.__friend_graph.remove_connection(username, connected_username)
        self.__database.remove_connection(username, connected_username, friend = True)

    def remove_following(self, uuid : str, connected_username : str) -> None:
        """Removes another user from the list of users followed by the current user."""
        username : str = self.get_username(uuid)
        self.__following_graph.remove_connection(username, connected_username)
        self.__database.remove_connection(username, connected_username, follow = True)

    def handle_user_add_connection(self, uuid : str, connected_username : str, conenction_type : str, add : bool) -> None:
        """Adds or removes a friend or following conenction based on a user's request."""
        if conenction_type == "Friend":
            if add:
                self.add_friend(uuid, connected_username)
            else:
                self.remove_friend(uuid, connected_username)
        elif conenction_type == "Follow":
            if add:
                self.add_following(uuid, connected_username)
            else:
                self.remove_following(uuid, connected_username)

    def is_friend(self, uuid : str, connected_username : str) -> bool:
        """Returns whether a user is a friend of the current user."""
        username : str = self.get_username(uuid)
        return self.__friend_graph.is_connected(username, connected_username)

    def is_following(self, uuid : str, connected_username : str) -> bool:
        """Returns whether the current user is following a particular person."""
        username : str = self.get_username(uuid)
        return self.__following_graph.is_connected(username, connected_username)
    
    def set_keys(self, uuid: str, dm_public_key: str, dm_private_key: str, analytics_public_key: str, analytics_private_key: str) -> None:
        """Stores a user's cryptography keys in the database."""
        username : str = self.get_username(uuid)
        self.__database.add_encryption_keys(username, dm_public_key, dm_private_key, analytics_public_key, analytics_private_key)

    def get_dm_public_key(self, username: str) -> str:
        """Returns a user's direct message public key from the database."""
        return self.__database.get_dm_public_key(username)

    def get_analytics_public_key(self, username: str) -> str:
        """Returns a user's analytics public key from the database."""
        return self.__database.get_analytics_public_key(username)

    def get_user_encryption_keys(self, uuid: str) -> typing.Dict[str, str]:
        """Returns all encryption keys for a user including encrypted private keys."""
        username : str = self.get_username(uuid)
        return {
            "dm_public": self.__database.get_dm_public_key(username),
            "dm_private": self.__database.get_dm_private_key(username),
            "analytics_public": self.__database.get_analytics_public_key(username),
            "analytics_private": self.__database.get_analytics_private_key(username),
            }



if __name__ == "__main__":
    Server : ServerController = ServerController()
    Server.start()