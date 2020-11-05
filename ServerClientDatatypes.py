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