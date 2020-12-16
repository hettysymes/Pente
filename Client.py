import socket
import pickle
from ServerClientDatatypes import Msg, Cmd

# The Client class contains all properties and methods required by the client.
# An instance of the Client class is created when a user wants to play Player v.s. Player LAN.
# The client sends/receives messages from the server, which controls the interaction between clients.
class Client:

    def __init__(self, username):
        self._username = username
        self._opponent = None
        self._playerNo = None
        self._s = None
        self._requestingMove = False

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

    @property
    def requestingMove(self):
        return self._requestingMove

    @requestingMove.setter
    def requestingMove(self, bool):
        self._requestingMove = bool

    # Makes a connection between the client and the server.
    def makeConnection(self):
        host = socket.gethostname()
        port = 8080

        self.s = socket.socket()
        self.s.connect((host, port))

        self.s.send(pickle.dumps(Msg(self.username, Cmd.ADD)))
        data = self.s.recv(1024)

    # Requests and receives an opponent from the server.
    def getOpponent(self):
        self.s.send(pickle.dumps(Msg(self.username, Cmd.GETOPP)))
        self.opponent, self.playerNo = pickle.loads(self.s.recv(1024)).data

    # Requests and receives the opponent's move from the server.
    def getMove(self):
        self.requestingMove = True
        self.s.send(pickle.dumps(Msg(self.username, Cmd.GETMOVE)))
        move = pickle.loads(self.s.recv(1024)).data
        self.requestingMove = False
        if not move:
            return (-1, -1)
        return move

    # Sends the player's move to the server.
    def makeMove(self, move):
        self.s.send(pickle.dumps(Msg(self.username, move, self.opponent)))

    # Closes the connection between the client and the server.
    def closeConnection(self):
        self.s.send(pickle.dumps(Msg(self.username, Cmd.REM, self.opponent)))
        self.s.close()