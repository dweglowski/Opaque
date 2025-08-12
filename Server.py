import WebServer
import Database
import typing
import random
import time
import re

# Define custom type hints
from ServerUtils import TYPE_POST, TYPE_POSTS


class ServerController:
    def __init__(self) -> None:
        """Constructor"""
        
        self.__init_web_server()
        self.__init_database()

        # list of all connected client uuids
        self.__active_connection_uuids : typing.List[str] = []

        # storage for information about each session such as auth state and username etc.
        self.__uuid_session_storage : typing.Dict[str, typing.Dict[str, str | float | int | bool ]] = {}

        # storage for users subscribed to posts feed and their "send post to client" callback
        self.__post_feed_subscribers : typing.Dict[str, typing.Callable[[TYPE_POST], None]] = {}


    def __init_web_server(self) -> None:
        """Initialise the webserver and all logic that should be done to achive this."""
        self.__webserver : WebServer.WebServerController = WebServer.WebServerController(self)

    def __init_database(self) -> None:
        """Initialise the database and all logic that should be done to achive this."""
        self.__database : Database.DatabaseController = Database.DatabaseController()

    def start(self) -> None:
        """Starts the server running."""
        self.__webserver.start()
        input("Press enter to stop..\n")
        self.__database.close()
        print("Safe to kill process")
        exit()


    def generate_uuid(self) -> str:
        """Generate a random UUID."""
        uuid : str = ""
        while not uuid or uuid in self.__active_connection_uuids:
            uuid = str(random.randint(0,1000000000000))

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
    

    def login(self, username: str, uuid: str) -> typing.Tuple[bool, str]:
        """Attempts to login a client, returns success, error code."""
        # sanitize
        username = re.sub("[^a-zA-Z0-9_]","", username.lower())
        
        if not self.__database.check_username_exists(username):
            return False, "InvalidUsername"
        
        # TODO: auth system

        self.__set_username(username, uuid)

        return True, ""

    def signup(self, username: str, display_name: str, uuid: str) -> typing.Tuple[bool, str]:
        """Attempts to sign up client, returns success, error code."""
        # sanitize
        username = re.sub("[^a-zA-Z0-9_]","", username.lower())
        display_name = re.sub("[^a-zA-Z0-9_ ]","", display_name.lower())

        if self.__database.check_username_exists(username):
            return False, "InvalidUsername"
        
        # TODO: auth system

        self.__database.add_new_signup(username)
        self.__database.add_new_profile(username, display_name)

        self.__set_username(username, uuid)

        return True, ""

    def is_logged_in(self, uuid: str) -> bool:
        """Returns whether a user session has logged in."""
        return self.__uuid_session_storage[uuid]["username"] != "#anonymous_user"
    
    def profile_get_display_name(self, username : str) -> str:
        """Returns the display name of a user."""
        return self.__database.profile_get_displayname(username)
    
    def get_profile_info(self, uuid:str) -> typing.Dict[str, str]:
        username : str = self.get_username(uuid)

        displayname: str = self.profile_get_display_name(username)

        result : typing.Dict[str, str] = {
                "username": username,
                "displayname": displayname,
            }
        return result
    
    def user_search(self, username : str) -> typing.Tuple[bool, typing.Dict[str,str]]:
        """Tries to find a user by username and returns basic info."""
        if not self.__database.check_username_exists(username):
            return False, {}
        
        display_name : str = self.__database.profile_get_displayname(username)

        resp : typing.Dict[str,str] = {
            "username": username,
            "displayname": display_name,
        }

        return True, resp



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
    

if __name__ == "__main__":
    Server : ServerController = ServerController()
    Server.start()