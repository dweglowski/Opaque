import typing
import json
import sqlite3

# Define custom type hints
from ServerUtils import TYPE_POST, TYPE_POSTS

class DatabaseController:
    def __init__(self) -> None:
        self.__posts_db : sqlite3.Connection = sqlite3.connect('Databases/Posts.db', check_same_thread=False)
        self.__posts_db_cursor : sqlite3.Cursor = self.__posts_db.cursor()
        self.__logins_db : sqlite3.Connection = sqlite3.connect('Databases/Logins.db', check_same_thread=False)
        self.__logins_db_cursor : sqlite3.Cursor = self.__logins_db.cursor()
        self.__profiles_db : sqlite3.Connection = sqlite3.connect('Databases/Profiles.db', check_same_thread=False)
        self.__profiles_db_cursor : sqlite3.Cursor = self.__profiles_db.cursor()

    def __read_posts_db(self) -> typing.List[typing.Tuple[str, str, str]]:
        return self.__posts_db_cursor.execute('SELECT "owner", "users_to", "content" FROM Posts').fetchall()
    
    def __read_logins_db(self) -> typing.List[typing.Tuple[str, str, str]]:
        return self.__logins_db_cursor.execute('SELECT "username", "password_hash", "password_salt" FROM Logins').fetchall()

    def __read_profiles_db(self) -> typing.List[typing.Tuple[str, str, str, str]]:
        return self.__profiles_db_cursor.execute('SELECT "username", "displayname", "bio", "photoid" FROM Profiles').fetchall()



    def get_posts(self) -> TYPE_POSTS:
        """Returns the full content of the posts database."""
        posts_raw : typing.List[typing.Tuple[str, str, str]] = self.__read_posts_db()

        posts : TYPE_POSTS = []
        for post in posts_raw:
            json_post = {
                "from": post[0],
                "fromname": self.profile_get_displayname(post[0]),
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



    def __logins_check_username(self, username) -> bool:
        return bool(self.__logins_db_cursor.execute('SELECT EXISTS (SELECT 1 FROM Logins WHERE username = ?)', (username,)).fetchone()[0])

    def check_username_exists(self, username : str) -> bool:
        """Checks whether a username is in login database."""
        username = username.lower()
        return self.__logins_check_username(username)
    
    def __add_login_to_db(self, username : str) -> None:
        self.__logins_db_cursor.execute('''
            INSERT INTO logins ("username", "password_hash", "password_salt") 
            VALUES (?, ?, ?)
        ''', (username, "", ""))
        self.__logins_db.commit()
    
    def add_new_signup(self, username : str) -> None:
        self.__add_login_to_db(username)


    def profile_get_displayname(self, username : str) -> str:
        return self.__profiles_db_cursor.execute("SELECT displayname FROM profiles WHERE username = ?", (username,)).fetchone()[0]
    
    def __add_profile_to_db(self, username : str, displayname : str) -> None:
        self.__profiles_db_cursor.execute('''
            INSERT INTO profiles ("username", "displayname", "bio", "photoid") 
            VALUES (?, ?, ?, ?)
        ''', (username, displayname, "", ""))
        self.__profiles_db.commit()
    
    def add_new_profile(self, username : str, displayname : str) -> None:
        self.__add_profile_to_db(username, displayname)
    
        
    def close(self) -> None:
        """Safely closes all databases"""
        self.__posts_db.close()