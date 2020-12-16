# The Msg class defines the datatype of messages sent between the client and server.
class Msg:

    def __init__(self, sender, data=None, receiver=None):
        self.sender = sender
        self.data = data
        self.receiver = receiver

# The Cmd class defines the datatype of commands which can be sent as the data of messages between the client and server.
class Cmd:
    ADD = 1
    GETOPP = 2
    GETMOVE = 3
    REM = 4