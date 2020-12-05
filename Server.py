import socket
import threading
import pickle
import time
from Game import Game
from ServerClientDatatypes import Msg, Cmd
import random

class Server:

    def __init__(self):
        self._onlineUsers = {}

    @property
    def onlineUsers(self):
        return self._onlineUsers

    @onlineUsers.setter
    def onlineUsers(self, onlineUsers):
        self._onlineUsers = onlineUsers

    def run(self):
        print("Server is running...")
        host = socket.gethostname()
        port = 8080

        s = socket.socket()
        s.bind((host, port))

        while 1:
            s.listen(1)
            c, addr = s.accept()
            x = threading.Thread(target=self.handleClient, args=(c,))
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

    def handleClient(self, c):
        while True:
            recvMsg = c.recv(1024)
            if not recvMsg:
                break
            msg = pickle.loads(recvMsg)
            if msg.data == Cmd.REM:
                if msg.receiver in self.onlineUsers:
                    self.onlineUsers[msg.receiver][2] = pickle.dumps(Msg(None, False))
                del self.onlineUsers[msg.sender]
                break
            elif msg.receiver != None and msg.receiver in self.onlineUsers:
                self.onlineUsers[msg.receiver][2] = recvMsg
            elif msg.data == Cmd.ADD:
                self.onlineUsers[msg.sender] = [c, None, None]
                c.send(pickle.dumps("ACK"))
            elif msg.data == Cmd.GETOPP:
                self.onlineUsers[msg.sender][1] = False
                self.getOpponent()
            elif msg.data == Cmd.GETMOVE:
                message = None
                while not message:
                    message = self.onlineUsers[msg.sender][2]
                    time.sleep(0.1)
                self.onlineUsers[msg.sender][0].send(message)
                self.onlineUsers[msg.sender][2] = None
        c.close()

if __name__ == "__main__":
    server = Server()
    server.run()