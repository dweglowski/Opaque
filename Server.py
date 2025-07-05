import WebServer
import Database
import typing



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

    def get_posts(self) -> str:
        """Gets and returns all posts from database."""
        return self.__database.get_posts()

    def add_post(self, post : str) -> None:
        """Adds a new post to the database."""
        return self.__database.add_post(post)
    

if __name__ == "__main__":
    Server : ServerController = ServerController()
    Server.start()