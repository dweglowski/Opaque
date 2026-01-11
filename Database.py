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

    def _check_record_exists_with_primary_keys(self, k1 : str, k1Value : str, k2 : str, k2Value : str) -> bool:
        """Tests whether a specific record exists using a compound primary key"""

        if k1 not in self.COLUMNS:
            raise ValueError("Invalid column name")
        
        if k2 not in self.COLUMNS:
            raise ValueError("Invalid column name")

        return len(self.__db_cursor.execute(f'SELECT {k1} FROM {self.TABLE_NAME} WHERE "{k1}" = ? AND "{k2}" = ?', (k1Value, k2Value)).fetchall()) != 0
    
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

        self.__db_cursor.execute(f'UPDATE {self.TABLE_NAME} SET "{column}" = ? WHERE "{primaryKey}" = ?', (value, primaryKeyValue))
        self.__db.commit()
    
    def _update_by_compund_key(self, column : str, value : str, k1 : str, k1Value : str, k2 : str, k2Value : str) -> None:
        """Updates the value of a column with a compound primary key"""
        
        if column not in self.COLUMNS:
            raise ValueError("Invalid column name")
        if k1 not in self.COLUMNS:
            raise ValueError("Invalid column name")
        if k2 not in self.COLUMNS:
            raise ValueError("Invalid column name")

        self.__db_cursor.execute(f'UPDATE {self.TABLE_NAME} SET "{column}" = ? WHERE "{k1}" = ? AND "{k2}" = ?', (value, k1Value, k2Value))
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

    def _get_last_inserted_id(self) -> int:
        """Returns the last inserted row id"""
        return self.__db_cursor.lastrowid

    def close(self) -> None:
        self.__db_cursor.close()


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

    def read_posts(self) -> typing.List[typing.Tuple[str, str, str, int]]:
        """Reads the owner, users_to and content fields for all records"""
        return self._read_columns(["owner","users_to","content","id"])
        
    def add_post(self, owner : str, users_to : str, content: str) -> int:
        """Adds a new post to database with owner, users_to and content fields, id is sequentially allocated. Returns the id of the new post."""
        self._insert(["owner", "users_to", "content"],[owner, users_to, content])
        id : int = self._get_last_inserted_id()
        return id
        
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



class ConnectionsDatabaseInterface(DatabaseInterfaceBase):
    """Extends DatabaseInterfaceBase for accessing the conenctions database.

    Columns:
        PRIMARY KEY (username, user_connected)

        username:
            TEXT PRIMARY KEY
            INSERT and READ ONLY
        user_connected:
            TEXT
            INSERT and READ
            WRITE if username matches client
        isFriend:
            INTIGER
            INSERT and READ
            WRITE if username matches client
        isFollowing:
            INTIGER
            INSERT and READ
            WRITE if username matches client
    """

    DATABASE_NAME = "Connections"
    TABLE_NAME = "Connections"
    COLUMNS = ["username","user_connected","isFriend","isFollowing"]

    def __init__(self) -> None:
        super().__init__()

    def get_all_connections(self) -> typing.List[typing.Tuple[str,str,bool,bool]]:
        """Returns all connections in the form Username, User_Connected, Is_Friend, Is_Following"""
        return self._read_columns(["username","user_connected","isFriend","isFollowing"])

    def __check_connection_already_exists(self, username : str, connected_user : str) -> bool:
        return self._check_record_exists_with_primary_keys("username", username, "user_connected", connected_user)
    
    def add_connection(self, username : str, connected_user: str, friend : bool = False, follow : bool = False) -> None:
        """Adds a new connection or modifies an existing record to show a connection between 2 users, only adds connection types, does not remove previous connection"""
        if not self.__check_connection_already_exists(username,connected_user):
            self._insert(["username", "user_connected", "isFriend", "isFollowing"],[username, connected_user, False, False])

        if friend:
            self._update_by_compund_key("isFriend",1,"username",username,"user_connected",connected_user)
            
        if follow:
            self._update_by_compund_key("isFollowing",1,"username",username,"user_connected",connected_user)

    def remove_connection(self, username : str, connected_user: str, friend : bool = False, follow : bool = False) -> None:
        """Modifies an existing record to remove a connection between 2 users, remove if flag set high"""
        if not self.__check_connection_already_exists(username,connected_user):
            return

        if friend:
            self._update_by_compund_key("isFriend",0,"username",username,"user_connected",connected_user)

        if follow:
            self._update_by_compund_key("isFollowing",0,"username",username,"user_connected",connected_user)
        

class MessagesDatabaseInterface(DatabaseInterfaceBase):
    """Extends DatabaseInterfaceBase for accessing the messages database.
    Columns:
        id:
            INTEGER PRIMARY KEY
            INSERT and READ ONLY
        owner:
            TEXT
            INSERT and READ ONLY
        user_to:
            TEXT
            INSERT and READ
            WRITE if username = owner
        SenderCopy:
            TEXT
            INSERT and READ (server will decide whether this value is sent on the client)
            WRITE if username = owner
        RecipientCopy:
            TEXT
            INSERT and READ (server will decide whether this value is sent on the client)
            WRITE if username = owner
        time:
            REAL
            INSERT and READ
            WRITE if username = owner
    """

    DATABASE_NAME = "Messages"
    TABLE_NAME = "Messages"
    COLUMNS = ["id","owner","user_to","SenderCopy","RecipientCopy","time"]

    def __init__(self) -> None:
        super().__init__()

    def read_messages(self) -> typing.List[typing.Tuple[str, str, str, str, float]]:
        """Reads the owner, users_to and content fields for all records"""
        return self._read_columns(["owner","user_to","SenderCopy","RecipientCopy","time"])
        
    def add_message(self, owner : str, user_to : str, SenderCopy: str, RecipientCopy: str, time: float) -> None:
        """Adds a new message to database with owner, users_to and content fields, id is sequentially allocated"""
        self._insert(["owner", "user_to", "SenderCopy", "RecipientCopy", "time"],[owner, user_to, SenderCopy, RecipientCopy, time])
        
    def edit_content(self, id: str, username : str, new_sender_copy: str, new_recipient_copy: str) -> None:
        """Edits the content of a message by id if the owner of the message matches the username"""
        self._update_condition("SenderCopy",new_sender_copy,"id",id,"owner",username)
        self._update_condition("RecipientCopy",new_recipient_copy,"id",id,"owner",username)


class AnalyticsDatabaseInterface(DatabaseInterfaceBase):
    """Extends DatabaseInterfaceBase for accessing the analytics database.
    Columns:
        id:
            INTEGER PRIMARY KEY
            INSERT and READ ONLY
        views:
            INTEGER
            INSERT, READ and WRITE
        reactions_encrypted:
            TEXT
            INSERT, READ and WRITE
        average_view_time_encrypted:
            TEXT
            INSERT, READ and WRITE
        star_score:
            REAL
            INSERT, READ and WRITE
        num_ratings:
            INTEGER
            INSERT, READ and WRITE
    """

    DATABASE_NAME = "Analytics"
    TABLE_NAME = "Analytics"
    COLUMNS = ["id","views","reactions_encrypted","average_view_time_encrypted","star_score","num_ratings"]

    def __init__(self) -> None:
        super().__init__()

    def get_analytics_for_post(self, post_id: str) -> typing.Tuple[int, str, str, float, int]:
        """Reads the analytics fields for a specific post id"""
        record : typing.Tuple[int, str, str, float, int] = self._read_columns_condition(["views","reactions_encrypted","average_view_time_encrypted","star_score","num_ratings"],"id",post_id)[0]
        return record
        
    def add_analytics(self, post_id: int) -> None:
        """Adds new analytics data to the database for a specific post id"""
        self._insert(["id", "views", "reactions_encrypted", "average_view_time_encrypted", "star_score", "num_ratings"], [post_id, 0, "", "", 0.0, 0])
        
    def update_reactions(self, id: int, reactions_encrypted: str) -> None:
        """Edits the encrypted reactions of a post by id"""
        self._update("reactions_encrypted", reactions_encrypted, "id", id)

    def update_average_view_time(self, id: int, average_view_time_encrypted: str) -> None:
        """Edits the encrypted average view time of a post by id"""
        self._update("average_view_time_encrypted", average_view_time_encrypted, "id", id)

    def update_star_score(self, id: int, star_score: float) -> None:
        """Edits the star score of a post by id"""
        self._update("star_score", star_score, "id", id)
        self._update("num_ratings", self._read_columns_condition(["num_ratings"],"id",id)[0][0] + 1, "id", id)

    def update_views(self, id: int, views: int) -> None:
        """Edits the views of a post by id"""
        self._update("views", views, "id", id)

class CryptographyKeysDatabaseInterface(DatabaseInterfaceBase):
    """Extends DatabaseInterfaceBase for accessing the cryptography keys database.
    Columns:
        username:
            TEXT PRIMARY KEY
            INSERT and READ ONLY
        dm_public_key:
            TEXT
            INSERT and READ ONLY
        dm_private_key:
            TEXT
            INSERT
            READ if username matches client
        analytics_public_key:
            TEXT
            INSERT and READ ONLY
        analytics_private_key:
            TEXT
            INSERT
            READ if username matches client
    """

    DATABASE_NAME = "CryptographyKeys"
    TABLE_NAME = "CryptographyKeys"
    COLUMNS = ["username","dm_public_key","dm_private_key","analytics_public_key","analytics_private_key"]

    def __init__(self) -> None:
        super().__init__()

    def insert_keys(self, username: str, dm_public_key: str, dm_private_key: str, analytics_public_key: str, analytics_private_key: str) -> None:
        """Adds new keys to the database for a specific username"""
        self._insert(["username", "dm_public_key", "dm_private_key", "analytics_public_key", "analytics_private_key"], [username, dm_public_key, dm_private_key, analytics_public_key, analytics_private_key])
        
    def get_dm_public_key(self, username: str) -> str:
        """Reads the dm public key for a specific username"""
        return self._read_columns_condition(["dm_public_key"],"username",username)[0][0]
    
    def get_dm_private_key(self, username: str) -> str:
        """Reads the dm private key for a specific username"""
        return self._read_columns_condition(["dm_private_key"],"username",username)[0][0]
    
    def get_analytics_public_key(self, username: str) -> str:
        """Reads the analytics public key for a specific username"""
        return self._read_columns_condition(["analytics_public_key"],"username",username)[0][0]
    
    def get_analytics_private_key(self, username: str) -> str:
        """Reads the analytics private key for a specific username"""
        return self._read_columns_condition(["analytics_private_key"],"username",username)[0][0]




class DatabaseController:
    def __init__(self) -> None:
        self.__posts_db : PostsDatabaseInterface = PostsDatabaseInterface()
        self.__logins_db : LoginsDatabaseInterface = LoginsDatabaseInterface()
        self.__profiles_db : ProfileDatabaseInterface = ProfileDatabaseInterface()
        self.__connections_db : ConnectionsDatabaseInterface = ConnectionsDatabaseInterface()
        self.__messages_db : MessagesDatabaseInterface = MessagesDatabaseInterface()
        self.__analytics_db : AnalyticsDatabaseInterface = AnalyticsDatabaseInterface()
        self.__cryptography_db : CryptographyKeysDatabaseInterface = CryptographyKeysDatabaseInterface()



    def get_posts(self) -> TYPE_POSTS:
        """Returns the full content of the posts database."""
        posts_raw : typing.List[typing.Tuple[str, str, str, int]] = self.__posts_db.read_posts()
        # print(posts_raw)
        posts : TYPE_POSTS = []
        for post in posts_raw:
            json_post = {
                "from": post[0],
                "fromname": self.profile_get_displayname(post[0]),
                "to": post[1],
                "content": post[2],
                "id": post[3],
            }
            posts.append(json_post)

        return posts
    
    def add_post(self, post : TYPE_POST) -> int:
        """Adds a post to the database, returns post id."""
        owner : str = post["from"]
        users_to : str = post["to"]
        content: str = post["content"]
        id: int = self.__posts_db.add_post(owner, users_to, content)

        # Add empty analytics record for post
        self.__analytics_db.add_analytics(id)

        return id


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
    

    def get_all_connections(self) -> typing.List[typing.Tuple[str,str,bool,bool]]:
        """Returns all connections in the form Username, User_Connected, Is_Friend, Is_Following"""
        return self.__connections_db.get_all_connections()
    
    def add_connection(self, username : str, connected_user: str, friend : bool = False, follow : bool = False) -> None:
        """Adds a new connection between 2 users"""
        self.__connections_db.add_connection(username, connected_user, friend, follow)

    def remove_connection(self, username : str, connected_user: str, friend : bool = False, follow : bool = False) -> None:
        """Removes an existing connection between 2 users"""
        self.__connections_db.remove_connection(username, connected_user, friend, follow)


    def get_messages(self) -> TYPE_POSTS:
        """Returns the full content of the messages database."""
        messages_raw : typing.List[typing.Tuple[str, str, str, float]] = self.__messages_db.read_messages()
        # print(posts_raw)
        messages : TYPE_POSTS = []
        for message in messages_raw:
            json_post = {
                "from": message[0],
                "to": message[1],
                "SenderCopy": message[2],
                "RecipientCopy": message[3],
                "time": message[4],
            }
            messages.append(json_post)

        return messages
    
    def add_message(self, message : TYPE_POST) -> None:
        """Adds a message to the database."""
        owner : str = message["from"]
        users_to : str = message["to"]
        SenderCopy: str = message["SenderCopy"]
        RecipientCopy: str = message["RecipientCopy"]
        time: float = message["time"]
        self.__messages_db.add_message(owner, users_to, SenderCopy, RecipientCopy, time)

    def get_analytics_for_post(self, post_id: str) -> typing.Dict[str, typing.Union[int, str, float]]:
        """Reads the analytics fields for a specific post id"""
        record : typing.Tuple[int, str, str, float, int] = self.__analytics_db.get_analytics_for_post(post_id)
        analytics : typing.Dict[str, typing.Union[int, str, float]] = {
            "views": record[0],
            "reactions_encrypted": record[1],
            "average_view_time_encrypted": record[2],
            "star_score": record[3],
            "num_ratings": record[4],
        }
        return analytics
    
    def get_post_owner(self, post_id: str) -> str:
        """Returns the owner of a specific post id"""
        owner: str = self.__posts_db._read_columns_condition(["owner"],"id",post_id)[0][0]
        return owner

    def update_view_count(self, post_id: int, views: int) -> None:
        """Updates the view count for a specific post id"""
        self.__analytics_db.update_views(post_id, views)

    def update_reactions(self, post_id: int, reactions_encrypted: str) -> None:
        """Updates the encrypted reactions for a specific post id"""
        self.__analytics_db.update_reactions(post_id, reactions_encrypted)
    
    def update_average_view_time(self, post_id: int, average_view_time_encrypted: str) -> None:
        """Updates the encrypted average view time for a specific post id"""
        self.__analytics_db.update_average_view_time(post_id, average_view_time_encrypted)

    def update_star_score(self, post_id: int, star_score: float) -> None:
        """Updates the star score for a specific post id"""
        self.__analytics_db.update_star_score(post_id, star_score)

    def add_encryption_keys(self, username: str, dm_public_key: str, dm_private_key: str, analytics_public_key: str, analytics_private_key: str) -> None:
        """Adds keys to the database on signup"""
        self.__cryptography_db.insert_keys(username, dm_public_key, dm_private_key, analytics_public_key, analytics_private_key)

    def get_dm_public_key(self, username: str) -> str:
        """Returns the public key for a user's direct messages"""
        return self.__cryptography_db.get_dm_public_key(username)
    
    def get_dm_private_key(self, username: str) -> str:
        """Returns the encrypted form of the private key to decrypt the user's direct messages"""
        return self.__cryptography_db.get_dm_private_key(username)
    
    def get_analytics_public_key(self, username: str) -> str:
        """Returns the public key for incrementing analytics on a user's post"""
        return self.__cryptography_db.get_analytics_public_key(username)
    
    def get_analytics_private_key(self, username: str) -> str:
        """Returns the encrypted form of the private key to decrypt the user's post analytics"""
        return self.__cryptography_db.get_analytics_private_key(username)

    def close(self) -> None:
        """Safely closes all databases"""
        self.__posts_db.close()
        self.__logins_db.close()
        self.__profiles_db.close()
        self.__connections_db.close()
        self.__messages_db.close()
        self.__analytics_db.close()
        self.__cryptography_db.close()
