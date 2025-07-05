import socket

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# handshake
client_socket.connect(("localhost", 1234))
client_socket.sendall(b"1.0")
handshake_reply = client_socket.recv(1024)

print(handshake_reply)

# get messages

client_socket.send(b'{"command":"GetPosts"}')

response = client_socket.recv(1024)

print(response)


# add message

msg = input("Enter message: ")

client_socket.send(b'{"command":"AddPost","data":"'+msg.encode()+b'"}')

response = client_socket.recv(1024)

print(response)


# get messages

client_socket.send(b'{"command":"GetPosts"}')

response = client_socket.recv(1024)

print(response)

client_socket.close()