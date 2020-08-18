import socket
import threading
import pickle
from enum import Enum, auto

class Msg:

    def __init__(self, sender, data=None, receiver=None):
        self.sender = sender
        self.data = data
        self.receiver = receiver

class Cmd(Enum):
    ADD = auto()
    REM = auto()

def client(username):
    host = socket.gethostname()
    port = 8080

    s = socket.socket()
    s.connect((host, port))

    s.send(pickle.dumps(Msg(username, Cmd.ADD)))
    data = pickle.loads(s.recv(1024)).data
    print(data)

    print("Waiting for other player...")
    opp = pickle.loads(s.recv(1024)).data
    print("Opponent: ", opp)

    if username<opp:
        data = pickle.loads(s.recv(1024)).data
        print("Opponent move: ", data)

    while 1:
        move = input("Move: ")
        s.send(pickle.dumps(Msg(username, move, opp)))
        data = pickle.loads(s.recv(1024)).data
        print("Opponent move: ", data)

    s.close()

onlineUsers = {}

def server():
    host = socket.gethostname()
    port = 8080

    s = socket.socket()
    s.bind((host, port))

    while 1:
        s.listen(1)
        c, addr = s.accept()
        x = threading.Thread(target=handle_client, args=(c,))
        x.start()

def makeConnection():
    global onlineUsers
    notPlaying = []
    for username, status in onlineUsers.items():
        if not status[1]: notPlaying.append(username)
    while len(notPlaying) > 1:
        u1 = notPlaying.pop()
        u2 = notPlaying.pop()
        onlineUsers[u1][1], onlineUsers[u2][1] = True, True
        onlineUsers[u1][0].send(pickle.dumps(Msg("Server", u2)))
        onlineUsers[u2][0].send(pickle.dumps(Msg("Server", u1)))

def handle_client(c):
    while True:
        recvMsg = c.recv(1024)
        msg = pickle.loads(recvMsg)
        if not msg:
            break
        global onlineUsers
        if msg.receiver != None:
            onlineUsers[msg.receiver][0].send(recvMsg)
        elif msg.data == Cmd.ADD:
            onlineUsers[msg.sender] = [c, False]
            c.send(pickle.dumps(Msg("Server", "Successfully added to current online players")))
            makeConnection()
        elif msg.data == Cmd.REM:
            del onlineUsers[msg.sender]
            c.send(pickle.dumps(Msg("Server", "Successfully deleted from current online players")))        

inp = input("Client or server (c/s)? ")
if inp == "s":
    server()
else:
    username = input("Username: ")
    client(username)
