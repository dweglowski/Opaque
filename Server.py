import WebServer
import Database
import Media
import typing
import time
import re
import uuid

from Datastructures import Trie, Graph

# Define custom type hints
from ServerUtils import TYPE_POST, TYPE_POSTS


class ServerController:
    def __init__(self) -> None:
        """Constructor"""
        
        self.__init_web_server()
        self.__init_database()
        self.__init_media()

        # list of all connected client uuids
        self.__active_connection_uuids : typing.List[str] = []

        # storage for information about each session such as auth state and username etc.
        self.__uuid_session_storage : typing.Dict[str, typing.Dict[str, str | float | int | bool ]] = {}

        # storage for users subscribed to posts feed and their "send post to client" callback
        self.__post_feed_subscribers : typing.Dict[str, typing.Callable[[TYPE_POST], None]] = {}

        # store all usernames in a quickly searchable way
        self.__username_trie : Trie = Trie("abcdefghijklmnopqrstuvwxyz0123456789_")
        self.__load_usernames()

        # store all connections in a quickly searchable way
        self.__friend_graph : Graph = Graph()
        self.__following_graph : Graph = Graph()
        self.__load_connections()


    def __init_web_server(self) -> None:
        """Initialise the webserver and all logic that should be done to achive this."""
        self.__webserver : WebServer.WebServerController = WebServer.WebServerController(self)

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
        exit()

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

    def send_existing_posts_to_client(self, uuid : str) -> str:
        """Sends all relevant existing posts to a client"""
        all_posts : TYPE_POSTS = self.get_posts()

        send_post_to_client_callback : typing.Callable[[TYPE_POST], None] = self.__post_feed_subscribers[uuid]

        for post in all_posts:
            # only posts that are shared with user
            if self.__validate_post_is_for_client(post, uuid):
                send_post_to_client_callback(post)


    def __send_new_post_to_relevant_users(self, post : TYPE_POST) -> None:
        """Sends a newly added post to all relevant active clients."""
        uuid : str
        send_post_to_client_callback : typing.Callable[[TYPE_POST], None]

        post["fromname"] = self.__database.profile_get_displayname(post["from"])

        for uuid in self.__post_feed_subscribers:

            if not self.__validate_post_is_for_client(post, uuid):
                continue

            # new post marked for this client, send update to client
            send_post_to_client_callback = self.__post_feed_subscribers[uuid]
            send_post_to_client_callback(post)



    def add_post(self, post : TYPE_POST, username : str) -> None:
        """Adds a new post to the database."""

        post["from"] = username

        self.__database.add_post(post)

        # ensure all clients recive this message
        self.__send_new_post_to_relevant_users(post)




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




if __name__ == "__main__":
    Server : ServerController = ServerController()
    Server.start()