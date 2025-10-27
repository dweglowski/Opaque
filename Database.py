import typing
import json
import sqlite3

# Define custom type hints
from ServerUtils import TYPE_POST, TYPE_POSTS


class DatabaseInterfaceBase:
    """Creates an interface for a single database and implements access control"""
    DATABASE_NAME : str = ""
    TABLE_NAME : str = ""
    COLUMNS : typing.List[str] = []
    def __init__(self):
        self.__db = self.__open_database()
        self.__db_cursor : sqlite3.Cursor = self.__db.cursor()

    def __open_database(self) -> sqlite3.Connection:
        """Opens database file with sqlite3"""
        return sqlite3.connect(f'Databases/{self.DATABASE_NAME}.db', check_same_thread=False)
    
    def _read_columns(self, columns : typing.List[str]) -> typing.List[typing.Tuple[str, ...]]:
        """Takes a list of columns and returns all records with those columns"""
        for col in columns: # ensure valid columns and prevent injection
            if col not in self.COLUMNS:
                raise ValueError("Invalid column name")
            
        columns_str : str = ", ".join([f"\"{col}\"" for col in columns]) # generate sql str

        return self.__db_cursor.execute(f'SELECT {columns_str} FROM {self.TABLE_NAME}').fetchall()
    
    def _read_columns_condition(self, columns : typing.List[str], conditionColumn : str, conditionValue : str) -> typing.List[typing.Tuple[str, ...]]:
        """Takes a list of columns and returns records with those columns for all records where a condition is met (e.g. username = ?)"""

        for col in columns: # ensure valid columns and prevent injection
            if col not in self.COLUMNS:
                raise ValueError("Invalid column name")
        
        if conditionColumn not in self.COLUMNS:
            raise ValueError("Invalid column name")
            
        columns_str : str = ", ".join([f"\"{col}\"" for col in columns]) # generate sql str

        return self.__db_cursor.execute(f'SELECT {columns_str} FROM {self.TABLE_NAME} WHERE "{conditionColumn}" = ?', (conditionValue,)).fetchall()
    
    def _insert(self, columns : typing.List[str], values : typing.List[str]) -> None:
        """Takes a list of columns and values and inserts it into the table, if column not provides, sql will init it"""


        for col in columns: # ensure valid columns and prevent injection
            if col not in self.COLUMNS:
                raise ValueError("Invalid column name")
        

        columns_str : str = ", ".join([f"\"{col}\"" for col in columns]) # generate sql str
        values_str : str = ", ".join("?"*len(values)) # generate sql str


        self.__db_cursor.execute(f'INSERT INTO {self.TABLE_NAME} ({columns_str}) VALUES ({values_str})', values)
        self.__db.commit()
    
    def _update(self, column : str, value : str, primaryKey : str, primaryKeyValue : str) -> None:
        """Updates the value of a column for an id"""
        
        if column not in self.COLUMNS:
            raise ValueError("Invalid column name")
        if primaryKey not in self.COLUMNS:
            raise ValueError("Invalid column name")

        self.__db_cursor.execute(f'UPDATE {self.TABLE_NAME} SET "{column}" = ? WHERE "{primaryKey}" = ?', (value, primaryKey))
        self.__db.commit()
    
    def _update_condition(self, column : str, value : str, primaryKey : str, primaryKeyValue : str, conditionColumn : str, conditionValue : str) -> None:
        """Updates the value of a column for an id where a condition is met"""
        
        if column not in self.COLUMNS:
            raise ValueError("Invalid column name")
        if primaryKey not in self.COLUMNS:
            raise ValueError("Invalid column name")
        if conditionColumn not in self.COLUMNS:
            raise ValueError("Invalid column name")

        self.__db_cursor.execute(f'UPDATE {self.TABLE_NAME} SET "{column}" = ? WHERE "{primaryKey}" = ? AND "{conditionColumn}" = ?', (value, primaryKeyValue, conditionValue))
        self.__db.commit()


class PostsDatabaseInterface(DatabaseInterfaceBase):
    """Extends DatabaseInterfaceBase for accessing the posts database.
    
    Columns:
        id:
            INTEGER PRIMARY KEY
            INSERT and READ ONLY
        owner:
            TEXT
            INSERT and READ ONLY
        users_to:
            TEXT
            INSERT and READ
            WRITE if username = owner
        content:
            TEXT
            INSERT and READ (server will decide whether this value is sent on the client)
            WRITE if username = owner
    """

    DATABASE_NAME = "Posts"
    TABLE_NAME = "Posts"
    COLUMNS = ["id","owner","users_to","content"]

    def __init__(self) -> None:
        super().__init__()

    def read_posts(self) -> typing.List[typing.Tuple[str, str, str]]:
        """Reads the owner, users_to and content fields for all records"""
        return self._read_columns(["owner","users_to","content"])
        
    def add_post(self, owner : str, users_to : str, content: str) -> None:
        """Adds a new post to database with owner, users_to and content fields, id is sequentially allocated"""
        self._insert(["owner", "users_to", "content"],[owner, users_to, content])
        
    def edit_content(self, id: str, username : str, new_content: str) -> None:
        """Edits the content of a post by id if the owner of the post matches the username"""
        self._update_condition("content",new_content,"id",id,"owner",username)
        
    def edit_users_to(self, id: str, username : str, new_users_to: str) -> None:
        """Edits the users_to of a post by id if the owner of the post matches the username"""
        self._update_condition("users_to",new_users_to,"id",id,"owner",username)



class LoginsDatabaseInterface(DatabaseInterfaceBase):
    """Extends DatabaseInterfaceBase for accessing the logins database.
    
    Columns:
        username:
            TEXT PRIMARY KEY
            INSERT and READ ONLY
        password_hash:
            TEXT
            INSERT and EQUAL (no read)
        password_salt:
            TEXT
            INSERT and READ ONLY
    """

    DATABASE_NAME = "Logins"
    TABLE_NAME = "Logins"
    COLUMNS = ["username","password_hash","password_salt"]

    def __init__(self) -> None:
        super().__init__()

    # def check_username_exists(self, username : str) -> bool:
    #     """Checks whether a username is in database."""
    #     # get all usernames matching requested username
    #     valid_unames : typing.List[typing.Tuple[str]] = self._read_columns_condition(["username"],"username",username)
    #     return len(valid_unames) > 0
    
    def get_username_list(self) -> typing.List[str]:
        """Returns all usernames in the database for the server to process."""
        usernames : typing.List[typing.Tuple[str]] = self._read_columns(["username"])
        return [record[0] for record in usernames]

    def get_salt(self, username : str) -> str:
        """Returns the password salt for a specific user"""
        return self._read_columns_condition(["password_salt"],"username",username)[0][0]

    def validate_hash(self, username : str, hash : str) -> bool:
        """Compares a password hash from a login attempt with actual hash and returns whether it is a match"""
        is_match : bool = self._read_columns_condition(["password_hash"],"username",username)[0][0] == hash
        return bool(is_match) # force it to be bool (no chance of leak)
        
    def add_user(self, username : str, password_hash : str, password_salt: str) -> None:
        """Adds a new user to database with username, password_hash and salt"""
        self._insert(["username", "password_hash", "password_salt"],[username, password_hash, password_salt])


class ProfileDatabaseInterface(DatabaseInterfaceBase):
    """Extends DatabaseInterfaceBase for accessing the profile database.

    Columns:
        username:
            TEXT PRIMARY KEY
            INSERT and READ ONLY
        displayname:
            TEXT
            INSERT and READ
            WRITE if username matches client
        bio:
            TEXT
            INSERT and READ
            WRITE if username matches client
        photoid:
            TEXT
            INSERT and READ
            WRITE if username matches client
    """

    DATABASE_NAME = "Profiles"
    TABLE_NAME = "Profiles"
    COLUMNS = ["username","displayname","bio","photoid"]

    def __init__(self) -> None:
        super().__init__()

    def get_displayname(self, username : str) -> str:
        return self._read_columns_condition(["displayname"],"username",username)[0][0] # first matching record, first col
    
    def get_pictureid(self, username : str) -> str:
        return self._read_columns_condition(["photoid"],"username",username)[0][0] # first matching record, first col
    
    def get_bio(self, username : str) -> str:
        return self._read_columns_condition(["bio"],"username",username)[0][0] # first matching record, first col
        
    def add_profile(self, username : str, displayname : str,) -> None:
        """Adds a new profile to database with username display_name bio photoid"""
        self._insert(["username", "displayname", "bio", "photoid"],[username, displayname, "","0"])
    
    def edit_pictureid(self, username : str, new_photoid: str) -> None:
        """Edits the photoid of a user"""
        self._update("photoid",new_photoid,"username",username)    
    
    def edit_bio(self, username : str, new_bio: str) -> None:
        """Edits the bio of a user"""
        self._update("bio",new_bio,"username",username)
    
    def edit_displayname(self, username : str, new_displayname: str) -> None:
        """Edits the displayname of a user"""
        self._update("displayname",new_displayname,"username",username)
        




class DatabaseController:
    def __init__(self) -> None:
        self.__posts_db : PostsDatabaseInterface = PostsDatabaseInterface()
        self.__logins_db : LoginsDatabaseInterface = LoginsDatabaseInterface()
        self.__profiles_db : ProfileDatabaseInterface = ProfileDatabaseInterface()



    def get_posts(self) -> TYPE_POSTS:
        """Returns the full content of the posts database."""
        posts_raw : typing.List[typing.Tuple[str, str, str]] = self.__posts_db.read_posts()
        # print(posts_raw)
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
    
    def add_post(self, post : TYPE_POST) -> None:
        """Adds a post to the database."""
        owner : str = post["from"]
        users_to : str = post["to"]
        content: str = post["content"]
        self.__posts_db.add_post(owner, users_to, content)



    # def check_username_exists(self, username : str) -> bool:
    #     """Checks whether a username is in login database."""
    #     username = username.lower()
    #     return self.__logins_db.check_username_exists(username)

    def get_username_list(self) -> typing.List[str]:
        """Returns a list of all registered usernames."""
        return self.__logins_db.get_username_list()
    
    def get_password_salt(self, username : str) -> str:
        """Returns the hash salt for a specific username."""
        return self.__logins_db.get_salt(username)
    
    def check_password_matches(self, hash: str, username: str) -> bool:
        """Returns whether password hash matches user's hash in db"""
        return self.__logins_db.validate_hash(username, hash)
    
    def add_new_signup(self, username : str, hash : str, salt : str) -> None:
        self.__logins_db.add_user(username,hash,salt)


    def profile_get_displayname(self, username : str) -> str:
        return self.__profiles_db.get_displayname(username)
    
    def profile_get_pictureid(self, username : str) -> str:
        return self.__profiles_db.get_pictureid(username)
    
    
    def add_new_profile(self, username : str, displayname : str) -> None:
        self.__profiles_db.add_profile(username, displayname)

    def update_profile_picture(self, username, pictureUUID) -> None:
        """Updates the pictureid with a uuid pointing to an uploaded profile picture"""
        self.__profiles_db.edit_pictureid(username, pictureUUID)
    
        
    def close(self) -> None:
        """Safely closes all databases"""
        self.__posts_db.close()