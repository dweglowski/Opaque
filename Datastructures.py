"""A collection of datastructures used throughout the program"""

import typing

class Queue:
    """Custom implementation of a queue, FIFO datastructure"""
    def __init__(self) -> None:
        self.__list = [] # temporary logic, to be replaced later

    def __len__(self) -> int:
        return len(self.__list)
    
    def is_empty(self) -> bool:
        """Returns if queue has no items."""
        return len(self) == 0
    
    def clear(self) -> None:
        """Clears the queue, removing all items."""
        while not self.is_empty():
            self.dequeue()
    
    def enqueue(self, item: typing.Any) -> None:
        """Adds a new item to the end of the queue."""
        self.__list.append(item)

    def dequeue(self) -> typing.Any:
        """Removes an item from the front of the queue and returns it."""
        return self.__list.pop(0)
    
class Stack:
    """Custom implementation of a stack, LIFO datastructure"""
    def __init__(self) -> None:
        self.__list = [] # temporary logic, to be replaced later

    def __len__(self) -> int:
        return len(self.__list)
    
    def is_empty(self) -> bool:
        """Returns if stack has no items."""
        return len(self) == 0
    
    def clear(self) -> None:
        """Clears the stack, removing all items."""
        while not self.is_empty():
            self.pop()
    
    def push(self, item: typing.Any) -> None:
        """Adds a new item to the top of the stack."""
        self.__list.append(item)

    def pop(self) -> typing.Any:
        """Removes an item from the top of the stack and returns it."""
        return self.__list.pop()
    


class Trie:
    """Custom implementation of a trie."""
    def __init__(self, symbols : typing.List[str]) -> None:
        self.__valid_symbols : typing.List[str] = symbols
        
        self.__root = _TrieNode("",False,self.__valid_symbols)

    def add_string(self, string : str) -> None:
        """Adds a new string to the trie."""
        node : _TrieNode = self.__root
        child_node : _TrieNode = None
        letter : str
        for letter in string:
            child_node = node.get_child(letter)

            # if the node has no children under that branch, create a new child and add it
            if child_node is None:
                child_node = _TrieNode(letter, False, self.__valid_symbols)
                node.add_child(letter, child_node)
            
            node = child_node

        # set the last node to a final node since it represents the string provided
        node.set_valid_end()

    def check_string_exists(self, string : str) -> bool:
        """Goes through the trie and checks whether a specific string is stored within."""
        node : _TrieNode = self.__root
        child_node : _TrieNode = None
        letter : str
        for letter in string:
            child_node = node.get_child(letter)

            # if the node has no children under that branch, the string is deffinitly invalid
            if child_node is None:
                return False
            
            node = child_node
    
        # check if the last node to a final node since if it is, the string that reaches it is valid
        if node.is_valid_end():
            return True

        return False            
    
    def get_all_endings_from_node(self, start_node : typing.Self, max_num : int = -1) -> typing.List[str]:
        """Iterates over all possible endings from a specific node, ordered alphabetically."""
        reversed_symbols = self.__valid_symbols[::-1]

        matches : typing.List[str] = []

        stack : Stack[typing.Tuple[_TrieNode, str]] = Stack()

        stack.push((start_node, ""))

        num_found : int = 0

        while not stack.is_empty() and (max_num == -1 or num_found < max_num):
            node : _TrieNode
            string_before : str
            node, string_before = stack.pop()

            string_before = string_before + node.get_symbol()

            if node.is_valid_end():
                matches.append(string_before)
                num_found += 1

            for symbol in reversed_symbols:
                newNode : _TrieNode = node.get_child(symbol)
                if newNode is None:
                    continue


                # add to search
                stack.push((newNode, string_before))

        return matches


    def get_all_endings(self, string : str, max_num : int = -1) -> typing.List[str]:

        matches : typing.List[str] = []

        node : _TrieNode = self.__root
        child_node : _TrieNode = None
        letter : str
        for letter in string:
            child_node = node.get_child(letter)
            # if the node has no children under that branch, the start is invalid
            if child_node is None:
                return matches
            
            node=child_node
    
        # check if the last node to a final node since if it is, the string is already valid so add to matches
        # if node.is_valid_end():
        #     matches.append(string)

        for ending in self.get_all_endings_from_node(node, max_num):
            if len(ending) > 0 and len(string) > 0:
                ending = ending[1:]
            matches.append(string + ending)

        return matches
        
            


class _TrieNode:
    """Node used for implementation of a trie."""
    def __init__(self, symbol : str, is_valid_end : bool, symbols : typing.List[str]):
        self.__symbol : str = symbol # stores the character this node represents
        self.__is_valid_end : bool = is_valid_end # stores whether this node represents the end of a valid string

        self.__valid_symbols : typing.List[str] = symbols

        self.__children : typing.Dict[str, typing.Self] = {s : None for s in symbols} # reference to each child, starts with none

    def get_symbol(self) -> str:
        return self.__symbol

    def get_child(self, symbol : str) -> typing.Self:
        """Returns a reference to a child node down the branch that represents the symbol requested."""
        return self.__children[symbol]
    
    def is_valid_end(self) -> bool:
        """Returns whether this node marks the end to a valid string (doesn't mean that it has no more children)"""
        return self.__is_valid_end
    
    def set_valid_end(self) -> None:
        """Marks the node as a valid end to the trie."""
        self.__is_valid_end = True
    
    def add_child(self, symbol : str, node : typing.Self) -> None:
        """Adds a new child into the sub branch for that symbol."""
        self.__children[symbol] = node
    
        
            


class _GraphNode:
    """Node used for implementation of a graph."""
    def __init__(self, name : str):
        self.__name : str = name # stores the name this node represents

        self.__connections: typing.Set[str] = set() # username of any connection

    def get_name(self) -> str:
        return self.__name
    
    
    def add_connection(self, connected_user : str) -> None:
        """Adds a new connection to a user."""
        self.__connections.add(connected_user)
    

    def is_connected(self, user : str) -> bool:
        """Returns whether a user is connected to this user."""
        return user in self.__connections
    
    def remove_connection(self, connected_user : str) -> None:
        """Removes an existing connection to a user."""
        if not self.is_connected(connected_user):
            return
        self.__connections.remove(connected_user)

    def get_connections(self) -> typing.List[str]:
        """Returns a list of usernames of all connected """
        return list(self.__connections)



class Graph:
    """Custom implementation of a graph."""
    def __init__(self) -> None:
        
        # map between username and a node representing them in the graph
        self.__nodes : typing.Dict[str,_GraphNode] = {}

    def add_user(self, username : str) -> None:
        """Adds a user to the graph"""
        self.__nodes[username] = _GraphNode(username)

    def add_connection(self, username : str, connected_user: str) -> None:
        """Adds a new connection between 2 users"""
        user : _GraphNode = self.__nodes[username]
        user.add_connection(connected_user)

    def remove_connection(self, username : str, connected_user: str) -> None:
        """Removes an existing connection between 2 users"""
        user : _GraphNode = self.__nodes[username]
        user.remove_connection(connected_user)
        
    def is_connected(self, username : str, connected_user : str) -> bool:
        """Returns whether a user is connected to this user."""
        user : _GraphNode = self.__nodes[username]
        return user.is_connected(connected_user)
         
    
    def get_all_connected(self, username : str) -> typing.List[str]:
        """Returns all usernames connected to a particular user."""
        user : _GraphNode = self.__nodes[username]

        connected_usernames : typing.List[str] = []
        connected_username : str
        for connected_username in user.get_connections():
            connected_usernames.append(connected_username)

        return connected_usernames

    def get_all_connected_to(self, username : str) -> typing.List[str]:
        """Returns all usernames connected to a particular user, other direction"""
        connected_usernames : typing.List[str] = []
        other_username : str
        for other_username in self.__nodes:
            other_user : _GraphNode = self.__nodes[other_username]
            if other_user.is_connected(username):
                connected_usernames.append(other_username)

        return connected_usernames

    def get_all_connected_two_ways(self, username : str) -> typing.List[str]:
        """Returns all usernames connected to a particular user both ways"""
        user : _GraphNode = self.__nodes[username]

        connected_usernames : typing.List[str] = []
        connected_username : str
        for connected_username in user.get_connections():
            connected_usernames.append(connected_username)
        for other_username in self.__nodes:
            other_user : _GraphNode = self.__nodes[other_username]
            if other_user.is_connected(username):
                connected_usernames.append(other_username)

        return connected_usernames
    
    def get_mutual_nodes(self, username1 : str, username2 : str) -> typing.List[str]:
        """Returns a list of usernames who are connected to both users provided (all mutual nodes)."""
        user1 : _GraphNode = self.__nodes[username1]
        user2 : _GraphNode = self.__nodes[username2]

        connected_usernames1 : typing.List[str] = self.get_all_connected_two_ways(username1)
        connected_usernames2 : typing.List[str] = self.get_all_connected_two_ways(username2)

        mutual_nodes : typing.List[str] = []
        connected_username : str
        for connected_username in connected_usernames1:
            if connected_username in connected_usernames2:
                # in both so mutual connection
                if connected_username != username1 and connected_username != username2:
                    mutual_nodes.append(connected_username)

        return mutual_nodes

    def get_degrees_of_separation(self, username1 : str, username2 : str) -> int:
        """Uses breadth first search to determine the degrees of seperation from user1 to user2, done to a max depth of 4"""
        user1 : _GraphNode = self.__nodes[username1]

        queue : Queue = Queue()
        # stores (user, depth) 
        queue.enqueue((username1, 0))

        visited : typing.Set[str] = set()
        visited.add(username1)

        username : str
        depth : int
        while not queue.is_empty():
            username, depth = queue.dequeue()
            if username == username2:
                # found user, end early for efficiency
                return depth
            
            connected_username : str
            for connected_username in self.get_all_connected_two_ways(username):
                # only add to queue if not already visited
                if connected_username not in visited:
                    # max search depth of 4
                    if depth < 4:
                        visited.add(connected_username)
                        # adds to end of queue to search
                        queue.enqueue((connected_username, depth + 1))
        
        # could not find user within 4 connections, return max value of 5
        return 5
                    


        

