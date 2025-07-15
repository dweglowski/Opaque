
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
    
    def display_posts(self, posts : str) -> None:
        """Displays all posts in the command line interface."""
        print("Posts:")
        print(posts)
        print("\n\n")

    def get_new_post_content(self) -> str:
        """Gets post content from the user to create a new post."""
        content : str = input("Enter new post:\n")
        return content