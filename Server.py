import WebServer


class ServerController:
    def __init__(self) -> None:
        """Constructor"""
        
        self.__init_web_server()



    def __init_web_server(self) -> None:
        """Initialise the webserver and all logic that should be done to achive this."""
        self.__webserver : WebServer.WebServerController = WebServer.WebServerController()


    def start(self) -> None:
        """Starts the server running."""
        self.__webserver.start()
        input("Press enter to stop..\n")

if __name__ == "__main__":
    Server : ServerController = ServerController()
    Server.start()