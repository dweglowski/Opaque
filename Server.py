import WebServer
import Database
import typing
import random
import time

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

        print(self.__active_connection_uuids,self.__uuid_session_storage)


    def set_username(self, username : str, uuid : str) -> None:
        """Sets a client's username in session storage."""
        self.__uuid_session_storage[uuid]["username"] = username

    def get_username(self, uuid : str) -> str:
        """Gets a client's username from session storage."""
        return self.__uuid_session_storage[uuid]["username"]




    def get_posts(self) -> TYPE_POSTS:
        """Gets and returns all posts from database."""
        return self.__database.get_posts()
    
    def get_posts_for_user(self, username : str) -> TYPE_POSTS:
        """Gets and returns all posts that have a specific username in the TO field."""
        all_posts : TYPE_POSTS = self.get_posts()
        valid_posts : TYPE_POSTS = []

        for post in all_posts:
            # only posts that are shared with user
            if post["to"] == "@all" or username in post["to"].split("@"):
                valid_posts.append(post)
        
        return valid_posts

    def add_post(self, post : TYPE_POST, username : str) -> None:
        """Adds a new post to the database."""

        # TODO: sanitise post

        post["from"] = username

        return self.__database.add_post(post)
    
    

if __name__ == "__main__":
    Server : ServerController = ServerController()
    Server.start()