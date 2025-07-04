import socket

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# handshake
client_socket.connect(("localhost", 1234))
client_socket.sendall(b"1.0")
handshake_reply = client_socket.recv(1024)

print(handshake_reply)

# send hello world to server

client_socket.send(b"hello")

response = client_socket.recv(1024)

print(response)

client_socket.close()