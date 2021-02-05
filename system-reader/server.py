import socket
import atexit

from constants import SOCKET_PORT, SOCKET_MAX_CONNECTION

atexit.register(print,"Program exited successfully!")

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
HOST = socket.gethostbyname(socket.gethostname())
try:
    s.bind(("", SOCKET_PORT))
    # s.bind((HOST, SOCKET_PORT))
    # s.bind((socket.gethostname(), SOCKET_PORT))
    # s.bind(("ws://192.168.0.165", SOCKET_PORT))
except socket.error as e:
    print(str(e))

s.listen(SOCKET_MAX_CONNECTION)
print(f"Listening on {socket.gethostname()}:{SOCKET_PORT}")

while True:
    client_socket, address = s.accept()
    print(f"Connection from {address} has been established")
    #client_socket.send(bytes("Welcome to server", "utf-8"))
    client_socket.send("Welcome to server".encode())
