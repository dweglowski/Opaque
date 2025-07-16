import typing
import json

# Define custom type hints
from ServerUtils import TYPE_POST, TYPE_POSTS

class DatabaseController:
    def __init__(self) -> None:
        pass

    def __read_posts_db(self) -> str:
        with open("Databases/TMP/posts.txt","r") as f:
            return f.read()

    def get_posts(self) -> TYPE_POSTS:
        """Returns the full content of the posts database."""
        posts_raw : typing.List[str] = self.__read_posts_db().splitlines()

        posts : TYPE_POSTS = []
        for post in posts_raw:
            posts.append(json.loads(post))

        return posts
    
    def add_post(self, post : TYPE_POST) -> None:
        """Adds a post to the database."""
        with open("Databases/TMP/posts.txt","a") as f:
            return f.write(json.dumps(post)+"\n")