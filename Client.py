import ClientCLI
import ClientAPI
import typing

# Define custom type hints
from ClientUtils import TYPE_POST, TYPE_POSTS




class Client:
    """Controls all the client logic"""
    def __init__(self) -> None:
        self.cli : ClientCLI.CLI = ClientCLI.CLI()
        self.api : ClientAPI.SocketAPI = ClientAPI.SocketAPI()

    def cli_mainloop(self) -> None:
        """The main loop running used for the cli"""

        self.api.connect()

        self.__set_username()

        while 1:
            action : str = self.cli.get_action()
            
            if action == "Read":
                self.__read_posts()
            elif action == "Write":
                self.__write_post()
            elif action == "Quit":
                self.__quit()
                break
            else:
                pass

    def __set_username(self) -> None:
        username : str = self.cli.get_username()
        self.api.set_username(username)

    def __read_posts(self) -> None:
        posts : TYPE_POSTS = self.api.get_posts()
        self.cli.display_posts(posts)

    def __write_post(self) -> None:
        users_to : str = self.cli.get_new_post_to()
        post_content : str = self.cli.get_new_post_content()
        post : TYPE_POST = {"to" : users_to, "content" : post_content}
        self.api.add_post(post)

    def __quit(self) -> None:
        self.api.close()

if __name__ == "__main__":
    client : Client = Client()
    client.cli_mainloop()