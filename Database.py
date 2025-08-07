import typing
import json
import sqlite3

# Define custom type hints
from ServerUtils import TYPE_POST, TYPE_POSTS

class DatabaseController:
    def __init__(self) -> None:
        self.__posts_db : sqlite3.Connection = sqlite3.connect('Databases/Posts.db', check_same_thread=False)
        self.__posts_db_cursor : sqlite3.Cursor = self.__posts_db.cursor()

    def __read_posts_db(self) -> typing.List[typing.Tuple[str, str, str]]:
        return self.__posts_db_cursor.execute('SELECT "owner", "users_to", "content" FROM Posts')

    def get_posts(self) -> TYPE_POSTS:
        """Returns the full content of the posts database."""
        posts_raw : typing.List[typing.Tuple[str, str, str]] = self.__read_posts_db()

        posts : TYPE_POSTS = []
        for post in posts_raw:
            json_post = {
                "from": post[0],
                "to": post[1],
                "content": post[2],
            }
            posts.append(json_post)

        return posts
    
    def __add_post_to_db(self, owner : str, users_to : str, content: str) -> None:
        self.__posts_db_cursor.execute('''
            INSERT INTO posts ("owner", "users_to", "content") 
            VALUES (?, ?, ?)
        ''', (owner, users_to, content))
        self.__posts_db.commit()

    def add_post(self, post : TYPE_POST) -> None:
        """Adds a post to the database."""
        owner : str = post["from"]
        users_to : str = post["to"]
        content: str = post["content"]
        self.__add_post_to_db(owner, users_to, content)
        
    def close(self) -> None:
        """Safely closes all databases"""
        self.__posts_db.close()