import typing
from enum import Enum


# Define custom type hints
from ClientUtils import TYPE_POST, TYPE_POSTS


# UI elements
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

        print("\n"*10)
        print("\033[2J\033[H",end="") # reset screen
        
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

        print(CORNERS.TL + CORNERS.HORZ * (DISPLAY_WIDTH - 2) + CORNERS.TR)

        for line in lines:
            print(CORNERS.VERT + line + " " * (DISPLAY_WIDTH - len(line) - 2) + CORNERS.VERT)

        print(CORNERS.BL + CORNERS.HORZ * (DISPLAY_WIDTH - 2) + CORNERS.BR)

    def get_new_post_content(self) -> str:
        """Gets post content from the user to create a new post."""
        print("\033[2J\033[H",end="") # reset screen
        print(CORNERS.TL + CORNERS.HORZ * 28 + CORNERS.TR)
        print(CORNERS.VERT + "   New Post   " + " " * 14 + CORNERS.VERT)
        print(CORNERS.VERT + " Content: " + " " * 18 + CORNERS.VERT)
        print(CORNERS.BL + CORNERS.HORZ * 28 + CORNERS.BR)
        content : str = input()


        print("\033[2J\033[H",end="") # reset screen
        
        return content
    
    def get_new_post_to(self) -> str:
        """Get the users that the new post should be shared with."""

        print("\033[2J\033[H",end="") # reset screen
        print(CORNERS.TL + CORNERS.HORZ * 28 + CORNERS.TR)
        print(CORNERS.VERT + "   New Post   " + " " * 14 + CORNERS.VERT)
        print(CORNERS.VERT + " To: " + " " * 23 + CORNERS.VERT)
        print(CORNERS.VERT + "    E.g. @User1@User2" + " " * 7 + CORNERS.VERT)
        print(CORNERS.VERT + " " + "_" * 26 + " " + CORNERS.VERT)
        print(CORNERS.BL + CORNERS.HORZ * 28 + CORNERS.BR)

        print("\033[5;3H",end="") # position cursor in box

        users_to : str = input()
        if users_to == "":
            users_to = "@all"

        print("\033[2J\033[H",end="") # reset screen

        return users_to
    
    def get_username(self) -> str:
        """Get a username from the user."""

        print("\033[2J\033[H",end="") # reset screen

        print(CORNERS.TL + CORNERS.HORZ * 28 + CORNERS.TR)
        print(CORNERS.VERT + " Username:" + " " * 18 + CORNERS.VERT)
        print(CORNERS.VERT + " " + "_" * 26 + " " + CORNERS.VERT)
        print(CORNERS.BL + CORNERS.HORZ * 28 + CORNERS.BR)

        print("\033[3;3H",end="") # position cursor in box

        username : str = input()

        print("\033[2J\033[H",end="") # reset screen

        if username == "":
            username = "#anonymous_user"
        return username