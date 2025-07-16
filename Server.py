import WebServer
import Database
import typing


# Define custom type hints
from ServerUtils import TYPE_POST, TYPE_POSTS


class ServerController:
    def __init__(self) -> None:
        """Constructor"""
        
        self.__init_web_server()
        self.__init_database()



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

    def add_post(self, post : TYPE_POST) -> None:
        """Adds a new post to the database."""
        return self.__database.add_post(post)
    

if __name__ == "__main__":
    Server : ServerController = ServerController()
    Server.start()