import typing
from enum import Enum


# Define custom type hints
from ClientUtils import TYPE_POST, TYPE_POSTS

class CLI:
    """A simple command line interface for accessing the client's logic."""
    def __init__(self) -> None:
        pass

        
    def get_action(self) -> str:
        """Determines which action the user wants to perform."""
        action : str = input("Enter 'r' to read posts or 'w' to write a new post or 'q' to quit.\nr/w/q: ")
        if action == "r":
            return "Read"
        elif action == "w":
            return "Write"
        elif action == "q":
            return "Quit"
        return ""
    
    def display_posts(self, posts : TYPE_POSTS) -> None:
        """Displays all posts in the command line interface."""
        print("\n"*5)
        print("Posts: ")
        
        post : TYPE_POST
        for post in posts:
            user_from : str = post["from"]
            users_to : str = post["to"]
            content : str = post["content"]
            self.__display_post(user_from, users_to, content)

    def __display_post(self, user_from : str, users_to : str, content : str) -> None:
        """Displays a single post and its content in the command line interface."""
        
        DISPLAY_WIDTH : int = 40


        lines : typing.List[str] = []

        lines.append("From: "+user_from)
        lines.append("To: "+users_to)

        line : str = ""
        for word in content.split(" "):
            if len(line) + len(word) + 1 > DISPLAY_WIDTH - 2:
                lines.append(line)
                line = word
            else:
                line += " " + word
        lines.append(line)



        class CORNERS(Enum):
            TL : str = "╭"
            TR : str = "╮"
            BL : str = "╰"
            BR : str = "╯"
            VERT : str = "│"
            HORZ : str = "─"

            # functions for concat
            def __mul__(self, other):
                return self.value * other
            def __add__(self, other):
                return self.value + str(other)
            def __radd__(self, other):
                return str(other) + self.value

        print(CORNERS.TL + CORNERS.HORZ * (DISPLAY_WIDTH - 2) + CORNERS.TR)

        for line in lines:
            print(CORNERS.VERT + line + " " * (DISPLAY_WIDTH - len(line) - 2) + CORNERS.VERT)

        print(CORNERS.BL + CORNERS.HORZ * (DISPLAY_WIDTH - 2) + CORNERS.BR)

    def get_new_post_content(self) -> str:
        """Gets post content from the user to create a new post."""
        content : str = input("Enter new post:\n")
        return content
    
    def get_new_post_to(self) -> str:
        """Get the users that the new post should be shared with."""
        users_to : str = input("Enter usernames to send post to e.g. @User1@User2. Leave blank to share with all.\n")
        if users_to == "":
            users_to = "@all"
        return users_to