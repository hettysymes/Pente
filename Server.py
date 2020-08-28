import socket
import threading
import pickle
import time
from Game import Game
import random

class Msg:

    def __init__(self, sender, data=None, receiver=None):
        self.sender = sender
        self.data = data
        self.receiver = receiver

class Client:

    def __init__(self, username):
        self.username = username
        self.opponent = None
        self.playerNo = None
        self.s = None

    def makeConnection(self):
        host = socket.gethostname()
        port = 8080

        self.s = socket.socket()
        self.s.connect((host, port))

        self.s.send(pickle.dumps(Msg(self.username, "ADD")))
        data = self.s.recv(1024)
    
    def getOpponent(self):
        self.s.send(pickle.dumps(Msg(self.username, "GETOPP")))
        self.opponent, self.playerNo = pickle.loads(self.s.recv(1024)).data

    def getMove(self):
        self.s.send(pickle.dumps(Msg(self.username, "GETMOVE")))
        move = pickle.loads(self.s.recv(1024)).data
        return move

    def makeMove(self, move):
        self.s.send(pickle.dumps(Msg(self.username, move, self.opponent)))

    def closeConnection(self):
        self.s.send(pickle.dumps(Msg(self.username, "REM")))
        data = self.s.recv(1024)
        self.s.close()

class Server:

    def __init__(self):
        self.onlineUsers = {}

    def run(self):
        print("Server is running...")
        host = socket.gethostname()
        port = 8080

        s = socket.socket()
        s.bind((host, port))

        while 1:
            s.listen(1)
            c, addr = s.accept()
            x = threading.Thread(target=self.handle_client, args=(c,))
            x.start()

    def getOpponent(self):
        notPlaying = []
        for username, status in self.onlineUsers.items():
            if status[1] == False: notPlaying.append(username)
        while len(notPlaying) > 1:
            u1 = notPlaying.pop()
            u2 = notPlaying.pop()
            self.onlineUsers[u1][1], self.onlineUsers[u2][1] = True, True
            playerIndex = random.randint(0, 1)
            p1, p2 = [Game.P1, Game.P2][playerIndex], [Game.P1, Game.P2][not playerIndex]
            self.onlineUsers[u1][0].send(pickle.dumps(Msg(None, (u2, p1))))
            self.onlineUsers[u2][0].send(pickle.dumps(Msg(None, (u1, p2))))

    def handle_client(self, c):
        while True:
            recvMsg = c.recv(1024)
            msg = pickle.loads(recvMsg)
            if not msg:
                break
            if msg.receiver != None:
                self.onlineUsers[msg.receiver][2] = recvMsg
            elif msg.data == "ADD":
                self.onlineUsers[msg.sender] = [c, None, None]
                c.send(pickle.dumps("ACK"))
            elif msg.data == "GETOPP":
                self.onlineUsers[msg.sender][1] = False
                self.getOpponent()
            elif msg.data == "GETMOVE":
                message = None
                while not message:
                    message = self.onlineUsers[msg.sender][2]
                    time.sleep(0.1)
                self.onlineUsers[msg.sender][0].send(message)
                self.onlineUsers[msg.sender][2] = None
            elif msg.data == "REM":
                del self.onlineUsers[msg.sender]
                c.send(pickle.dumps("ACK"))

if __name__ == "__main__":
    server = Server()
    server.run()