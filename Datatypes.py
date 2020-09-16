class GameRecord:

    def __init__(self, id=-1, name=-1, whenSaved=-1, game=-1, mode=-1):
        self.id = id
        self.name = name
        self.whenSaved = whenSaved
        self.game = game
        self.mode = mode

class Msg:

    def __init__(self, sender, data=None, receiver=None):
        self.sender = sender
        self.data = data
        self.receiver = receiver

class Cmd:
    ADD = 1
    GETOPP = 2
    GETMOVE = 3
    REM = 4