import socket
import pickle
from ServerClientDatatypes import Msg, Cmd

class Client:

    def __init__(self, username):
        self._username = username
        self._opponent = None
        self._playerNo = None
        self._s = None

    @property
    def username(self):
        return self._username

    @property
    def opponent(self):
        return self._opponent

    @opponent.setter
    def opponent(self, opponent):
        self._opponent = opponent

    @property
    def playerNo(self):
        return self._playerNo

    @playerNo.setter
    def playerNo(self, playerNo):
        self._playerNo = playerNo

    @property
    def s(self):
        return self._s

    @s.setter
    def s(self, s):
        self._s = s

    def makeConnection(self):
        host = socket.gethostname()
        port = 8080

        self.s = socket.socket()
        self.s.connect((host, port))

        self.s.send(pickle.dumps(Msg(self.username, Cmd.ADD)))
        data = self.s.recv(1024)
    
    def getOpponent(self):
        self.s.send(pickle.dumps(Msg(self.username, Cmd.GETOPP)))
        self.opponent, self.playerNo = pickle.loads(self.s.recv(1024)).data

    def getMove(self):
        self.s.send(pickle.dumps(Msg(self.username, Cmd.GETMOVE)))
        move = pickle.loads(self.s.recv(1024)).data
        return move

    def makeMove(self, move):
        self.s.send(pickle.dumps(Msg(self.username, move, self.opponent)))

    def closeConnection(self):
        self.s.send(pickle.dumps(Msg(self.username, Cmd.REM)))
        data = self.s.recv(1024)
        self.s.close()