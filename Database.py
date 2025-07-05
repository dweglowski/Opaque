class DatabaseController:
    def __init__(self) -> None:
        pass

    def __read_posts_db(self) -> str:
        with open("Databases/TMP/posts.txt","r") as f:
            return f.read()

    def get_posts(self) -> str:
        """Returns the full content of the posts database."""
        return self.__read_posts_db()
    
    def add_post(self, msg) -> None:
        """Adds a post to the database."""
        with open("Databases/TMP/posts.txt","a") as f:
            return f.write(msg+"\n")