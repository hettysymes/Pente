from copy import deepcopy
from Game import Game, GameError, GameRecord, MoveStack
from colorama import Fore, Style
from enum import Enum, auto
from datetime import datetime
import Database
import Ai
from tkinter import *
from tkinter import ttk
from functools import partial
from PIL import Image, ImageDraw
from Client import Client
import threading

# The Player class defines different player types.
class Player(Enum):
    MAIN = auto()
    OPP = auto()
    GUEST = auto()
    COMP = auto()

# The Mode class defines different playing modes.
class Mode:
    PVP = "PVP"
    COMP = "COMP"
    LAN = "LAN"

# The Ui class contains attributes and methods shared by the two Uis: Terminal and Gui.
# Ui subclasses are run via the run method.
class Ui:

    def __init__(self):
        self._player = Player.GUEST
        self._opponent = Player.GUEST
        self._currPlayers = {Game.P1: Player.MAIN, Game.P2: Player.OPP}
        self._currGameRecord = None
        self._client = None
        self._compDifficulty = None

    @property
    def player(self):
        return self._player

    @player.setter
    def player(self, player):
        self._player = player

    @property
    def opponent(self):
        return self._opponent

    @opponent.setter
    def opponent(self, opponent):
        self._opponent = opponent

    @property
    def currPlayers(self):
        return self._currPlayers

    @currPlayers.setter
    def currPlayers(self, currPlayers):
        self._currPlayers = currPlayers

    @property
    def currGameRecord(self):
        return self._currGameRecord

    @currGameRecord.setter
    def currGameRecord(self, currGameRecord):
        self._currGameRecord = currGameRecord

    @property
    def client(self):
        return self._client

    @client.setter
    def client(self, client):
        self._client = client

    @property
    def compDifficulty(self):
        return self._compDifficulty

    @compDifficulty.setter
    def compDifficulty(self, compDifficulty):
        self._compDifficulty = compDifficulty

    # Given a player (one of Game.P1 and Game.P2), the function returns the username of that player number (or Player.GUEST if the player is not logged in, or Player.COMP if the player is a computer).
    def _getUsernameOfPlayerNumber(self, player):
        if self.currPlayers[player] == Player.MAIN:
            return self.player
        else:
            return self.opponent

    # Given a gameRecord (of the GameRecord datatype), returns a string summarising the information in the gameRecord.
    def _gameString(self, gameRecord):
        players = [Database.getPlayerGameUsername(gameRecord.id, Game.P1), Database.getPlayerGameUsername(gameRecord.id, Game.P2)]
        for i in range(2):
            if players[i] == False:
                if gameRecord.mode == Mode.COMP:
                    players[i] = "Computer"
                else:
                    players[i] = "Guest"
        mode = f"{players[0]} v.s. {players[1]}"
        whenSaved = datetime.strftime(gameRecord.whenSaved, "%d/%m/%Y, %H:%M:%S")
        if gameRecord.game.winner == Game.P1:
            status = "P1 won"
        elif gameRecord.game.winner == Game.P2:
            status = "P2 won"
        elif gameRecord.game.winner == Game.DRAW:
            status = "Draw"
        else:
            status = "ONGOING"
        return f"{gameRecord.name} - players: {mode}, saved on: {whenSaved}, status: {status}"

    # Given the username of a player, adds the player's result to their player profile by calling the database's addPlayerResult procedure.
    def _addUserResult(self, player):
        if self.currGameRecord.game.winner == Game.DRAW:
            Database.addPlayerResult(player, -1)
        elif player == self._getUsernameOfPlayerNumber(self.currGameRecord.game.winner):
            Database.addPlayerResult(player, True)
        else:
            Database.addPlayerResult(player, False)

    # Adds each player's result to their profile by calling the addUserResult procedure, and returns if any changes were made.
    def _addResultsToProfile(self):
        for player in [self.player, self.opponent]:
            if player in [Player.COMP, Player.GUEST]: continue
            self._addUserResult(player)
        return [self.player, self.opponent] != [Player.GUEST, Player.GUEST]

    # Writes the moves of a given game to a text file (with a given gameRecord) using Pente notation.
    @staticmethod
    def _exportGameMoves(gameRecord):
        boardsize = len(gameRecord.game.board)
        reverseMoveStack = MoveStack()
        moveStackCopy = deepcopy(gameRecord.game.moveStack)
        while not moveStackCopy.isEmpty():
            lastStack = moveStackCopy.pop()
            reverseMoveStack.push(lastStack[0], lastStack[1], lastStack[2])
        moveRecord = ""
        isPlayer1Turn = True
        lastCaptures = {Game.P1: [], Game.P2: []}
        while not reverseMoveStack.isEmpty():
            captures, row, col = reverseMoveStack.pop()
            capturesMade = True if lastCaptures != captures else False
            moveRecord += Game.getPenteMoveNotation(row, col, boardsize, capturesMade)
            if isPlayer1Turn:
                moveRecord += " "
            else:
                moveRecord += "\n"
            isPlayer1Turn = not isPlayer1Turn
            lastCaptures = captures
        with open(gameRecord.name+"_moveRecord"+".txt", "w+") as f:
            f.write(moveRecord)

    # Returns a string containing the rules of Pente
    @staticmethod
    def _getRulesText():
        return """
HOW TO PLAY PENTE

Pente is a board game where players take turns playing pieces on intersections of the board.
In this version of Pente, there will only be two players in total.

The first move for player 1 is forced, as they must move at the centre of the board.
Other than this, players can place their pieces on any empty intersection on the board.

A player can win in one of two ways:
1. They manage to make a row of 5 (or more) of their pieces on the board
2. They manage to capture 5 (or more) pairs of their opponent's pieces

Captures can be made by a player by placing their piece such that a pair of the opponent's pieces becomes trapped between two of the player's pieces.
This means that captures can only be made in pairs.
If, however, the opponent places their piece such that two of their pieces are trapped between two of the player's existing pieces, this does not count as a capture.
        
PENTE MOVE NOTATION

Pente moves are described in terms of positions relative to the centre of the board.
First, the x-position is described by writing R (right) or L (left), followed by the number of steps in that direction.
Then, the y-position is described by writing U (up) or D (down), again followed by the number of steps.
E.g. R3U2 refers to the position three to the right of and two above the centre of the board.
If the move is on one of the axes through the centre, one of the parts is ignored (e.g. U3 for directly up 3).
Moves made directly on the centre of the board is indicated by 0.
An asterisk (*) is made next to any move which causes a capture.
        """

    # Raises a NotImplementedError if the subclasses don't have a run function
    def run(self):
        raise NotImplementedError

# The Gui class is a subclass of the Ui class, and contains all properties and methods required for the graphical user interface.
class Gui(Ui):

    def __init__(self):
        super().__init__()

        self._MAX_CANVAS_SIZE = 730
        self._currentBoard = None
        self._playing = False
        self._markLastPiece = False

        self._root = Tk()
        self._root.title("Pente")

        self._menuFrame = Frame(self.root)
        self._menuFrame.grid(row=0, column=0, sticky="EW")

        self._gameFrame = Frame(self.root)
        self._gameFrame.grid(row=0, column=1, sticky="EW")
        self._buttons = []

        self._optionFrame = Frame(self.root)
        self._optionFrame.grid(row=0, column=2, sticky="EW")

        self._headLabel = Label(self.gameFrame, bg="white", fg="black", font=("Helvetica", 18))
        self._headLabel.grid(row=0, column=0, sticky="NESW")

        self._playerNoPlayingLabel = None

        self._c = Canvas()
        self._p1CapLabel = Label(self.gameFrame, relief="ridge", font=("Helvetica", 18))
        self._p1CapLabel.grid(row=1, column=0, sticky="NESW")
        self._p2CapLabel = Label(self.gameFrame, relief="ridge", font=("Helvetica", 18))
        self._p2CapLabel.grid(row=3, column=0, sticky="NESW")

        self._updateOptionFrame()
        self._updateMenuFrame()
        self._updateGameFrame()

    @property
    def MAX_CANVAS_SIZE(self):
        return self._MAX_CANVAS_SIZE

    @property
    def currentBoard(self):
        return self._currentBoard

    @currentBoard.setter
    def currentBoard(self, currentBoard):
        self._currentBoard = currentBoard

    @property
    def playing(self):
        return self._playing

    @playing.setter
    def playing(self, playing):
        self._playing = playing

    @property
    def markLastPiece(self):
        return self._markLastPiece

    @markLastPiece.setter
    def markLastPiece(self, markLastPiece):
        self._markLastPiece = markLastPiece

    @property
    def root(self):
        return self._root

    @root.setter
    def root(self, root):
        self._root = root

    @property
    def menuFrame(self):
        return self._menuFrame

    @menuFrame.setter
    def menuFrame(self, menuFrame):
        self._menuFrame = menuFrame

    @property
    def gameFrame(self):
        return self._gameFrame

    @gameFrame.setter
    def gameFrame(self, gameFrame):
        self._gameFrame = gameFrame

    @property
    def buttons(self):
        return self._buttons

    @buttons.setter
    def buttons(self, buttons):
        self._buttons = buttons

    @property
    def optionFrame(self):
        return self._optionFrame

    @optionFrame.setter
    def optionFrame(self, optionFrame):
        self._optionFrame = optionFrame

    @property
    def headLabel(self):
        return self._headLabel

    @headLabel.setter
    def headLabel(self, headLabel):
        self._headLabel = headLabel

    @property
    def c(self):
        return self._c

    @c.setter
    def c(self, c):
        self._c = c

    @property
    def p1CapLabel(self):
        return self._p1CapLabel

    @p1CapLabel.setter
    def p1CapLabel(self, p1CapLabel):
        self._p1CapLabel = p1CapLabel
    
    @property
    def p2CapLabel(self):
        return self._p2CapLabel

    @p2CapLabel.setter
    def p2CapLabel(self, p2CapLabel):
        self._p2CapLabel = p2CapLabel

    @property
    def playerNoPlayingLabel(self):
        return self._playerNoPlayingLabel

    @playerNoPlayingLabel.setter
    def playerNoPlayingLabel(self, playerNoPlayingLabel):
        self._playerNoPlayingLabel = playerNoPlayingLabel

    # Starts running the GUI by calling Tkinter's mainloop subroutine.
    def run(self):
        self.root.mainloop()

    # Creates a window which displays the rules of the game.
    def _createDisplayRulesWin(self):
        displayRulesWin = Toplevel(self.root)
        displayRulesWin.title("Display rules")
        rules = Ui._getRulesText().split("\n")
        i = 0
        for line in rules:
            Label(displayRulesWin, text=line).grid(row=i, column=0, padx=10, pady=2)
            i += 1
        Button(displayRulesWin, text="Ok", command=displayRulesWin.destroy).grid(row=i, column=0, padx=10, pady=5)

    # Creates a notification window with a specified title, display text, and top level window, with one Ok button which destroys the window on being pressed.
    def _createNotificationWin(self, title, text, toplevel=-1):
        if toplevel == -1: toplevel = self.root
        notifWin = Toplevel(toplevel)
        notifWin.title(title)
        Label(notifWin, text=text).grid(row=0, column=0, padx=10, pady=5)
        Button(notifWin, text="Ok", command=notifWin.destroy).grid(row=1, column=0, padx=10, pady=5)

    # Creates a window that allows the user to choose which game mode to play.
    def _chooseGameMode(self):
        playGameWindow = Toplevel(self.root)
        playGameWindow.title("Play")
        Label(playGameWindow, text="Choose a game mode").grid(row=0, column=0, padx=10, pady=5)
        Button(playGameWindow, text="Player v.s. Player", command=partial(self._confirmOppLogin, playGameWindow)).grid(row=1, column=0, padx=5)
        Button(playGameWindow, text="Player v.s. Computer", command=partial(self._getComputerDifficulty, playGameWindow)).grid(row=2, column=0, padx=5)     
        if self.player != Player.GUEST:
            Button(playGameWindow, text="Player v.s. Player (LAN)", command=partial(self._connectLan, playGameWindow)).grid(row=3, column=0, padx=5)

    # If the Player v.s. Player mode is chosen, the window is changed to ask the user whether the opponent would like to login.
    def _confirmOppLogin(self, playGameWindow):
        for widget in playGameWindow.winfo_children(): widget.destroy()
        Label(playGameWindow, text="Would the other player like to login?").grid(row=0, column=0, columnspan=2, padx=10, pady=5)
        Button(playGameWindow, text="Yes", command=partial(self._createLoginWindow, Player.OPP, playGameWindow)).grid(row=1, column=0, padx=5)
        Button(playGameWindow, text="No", command=partial(self._choosePlayer, playGameWindow, Mode.PVP)).grid(row=1, column=1, padx=5)

    # Creates a window which allows the user to choose their computer difficulty.
    def _getComputerDifficulty(self, playGameWindow):
        for widget in playGameWindow.winfo_children(): widget.destroy()
        Label(playGameWindow, text="Choose the computer difficulty").grid(row=0, column=0, padx=10, pady=5)
        Button(playGameWindow, text="Easy", command=partial(self._setComputerDifficulty, playGameWindow, 1)).grid(row=1, column=0, padx=5)
        Button(playGameWindow, text="Medium", command=partial(self._setComputerDifficulty, playGameWindow, 2)).grid(row=2, column=0, padx=5)
        Button(playGameWindow, text="Hard", command=partial(self._setComputerDifficulty, playGameWindow, 3)).grid(row=3, column=0, padx=5)

    # Sets the computer difficulty and calls the choosePlayer procedure for the user to choose their player number.
    def _setComputerDifficulty(self, playGameWindow, difficulty):
        self.compDifficulty = difficulty
        self._choosePlayer(playGameWindow, Mode.COMP)

    # Creates a window that allows the player to choose whether they play as player 1 or player 2.
    def _choosePlayer(self, playGameWindow, mode):
        if mode == Mode.COMP:
            self.opponent = Player.COMP
        if (self.player == Player.GUEST) and (self.opponent == Player.GUEST):
            playGameWindow.destroy()
            self._playGame(Game.P1, mode)
        else:
            for widget in playGameWindow.winfo_children(): widget.destroy()
            if mode == Mode.COMP:
                txt = "Would you like to be player 1 or player 2?"
            else:
                if self.player == Player.GUEST:
                    player = "the guest"
                else:
                    player = self.player
                txt = f"Would {player} like to be player 1 or player 2?"
            Label(playGameWindow, text=txt).grid(row=0, column=0, columnspan=2, padx=10, pady=5)
            Button(playGameWindow, text="Player 1", command=partial(self._playNewGame, playGameWindow, Game.P1, mode)).grid(row=1, column=0, padx=5)
            Button(playGameWindow, text="Player 2", command=partial(self._playNewGame, playGameWindow, Game.P2, mode)).grid(row=1, column=1, padx=5)

    # Destroys the choose player window and calls the playGame function to start the game.
    def _playNewGame(self, playGameWindow, player, mode):
        playGameWindow.destroy()
        self._playGame(player, mode)

    # Creates a window providing the user the option to choose a saved game to load.
    def _createLoadGameWindow(self, viewGamesWindow):
        viewGamesWindow.destroy()
        games = Database.loadGames(self.player, Game.ONGOING)
        if not games:
            self._createNotificationWindow("Load game", "You have no ongoing games")
        else:
            loadGameWindow = Toplevel(self.root)
            loadGameWindow.title("Load game")
            Label(loadGameWindow, text="Select an ongoing game:").grid(row=0, column=0, padx=10, pady=5)
            values = []
            for gameRecord in games:
                values.append(self._gameString(gameRecord))
            comboBox = ttk.Combobox(loadGameWindow, values=values, width=100)
            comboBox.current(0)
            comboBox.grid(row=1, column=0, padx=10, pady=5)
            Button(loadGameWindow, text="Load game", command=partial(self._loadGame, loadGameWindow, comboBox.get(), games)).grid(row=2, column=0, padx=10, pady=5)

    # Given the game information of the game being loaded, accesses the database for the game record of the game being loaded by calling the database's loadGames function, and calls the playGame procedure to start the game.
    def _loadGame(self, loadGameWindow, gameInfo, games):
        for gameRecord in games:
            if self._gameString(gameRecord) == gameInfo:
                break
        self.currGameRecord = gameRecord
        players = [Database.getPlayerGameUsername(self.currGameRecord.id, Game.P1), Database.getPlayerGameUsername(self.currGameRecord.id, Game.P2)]
        mainPlayerPos = None
        for i, player in enumerate(players):
            pos = Game.P1 if i == 0 else Game.P2
            if player == self.player:
                mainPlayerPos = pos
            elif player == False:
                self.opponent = Player.COMP if self.currGameRecord.mode == Mode.COMP else Player.GUEST
            else:
                self.opponent = player
        loadGameWindow.destroy()
        self._playGame(mainPlayerPos, new=False)

    # Returns a list of the player 1 and player 2 usernames respectively (or 'Guest' if the player is not logged in, or 'Computer' if the player is the computer).
    # Used when displaying player information.
    def _getCurrPlayerStrings(self):
        players = []
        for player in [Game.P1, Game.P2]:
            p = self._getUsernameOfPlayerNumber(player)
            if p == Player.GUEST:
                players.append("Guest")
            elif p == Player.COMP:
                players.append("Computer")
            else:
                players.append(p)
        return players

    # Creates a window allowing the user to save their currently being played game to the database and enter a game name to save it as.
    def _createSaveGameWindow(self):
        saveGameWindow = Toplevel(self.root)
        saveGameWindow.title("Save game")
        players = self._getCurrPlayerStrings()
        winner = self.currGameRecord.game.winner
        if winner == Game.P1:
            gameStatus = "P1 won"
        elif winner == Game.P2:
            gameStatus = "P2 won"
        elif winner == Game.DRAW:
            gameStatus = "Draw"
        else:
            gameStatus = "ONGOING"
        Label(saveGameWindow, text="Save game").grid(row=0, column=0, columnspan=2, pady=10)
        Label(saveGameWindow, text="Player 1").grid(row=1, column=0, padx=5)
        Label(saveGameWindow, text=players[0]).grid(row=1, column=1, padx=5)
        Label(saveGameWindow, text="Player 2").grid(row=2, column=0, padx=5)
        Label(saveGameWindow, text=players[1]).grid(row=2, column=1, padx=5)
        Label(saveGameWindow, text="Game status").grid(row=3, column=0, padx=5)
        Label(saveGameWindow, text=gameStatus).grid(row=3, column=1, padx=5)
        Label(saveGameWindow, text="Save game as").grid(row=4, column=0, padx=5)
        gameNameEntry = Entry(saveGameWindow)
        gameNameEntry.grid(row=4, column=1, padx=5)
        statusLabel = Label(saveGameWindow, text="")
        statusLabel.grid(row=6, column=0, columnspan=2, pady=5)
        Button(saveGameWindow, text="Confirm", command=partial(self._saveGame, saveGameWindow, gameNameEntry, statusLabel)).grid(row=5, column=0, columnspan=2, pady=10)

    # Given a game name, calls the database's saveGame procedure to save the contents of the current game information with the game name to the database.
    def _saveGame(self, saveGameWindow, gameNameEntry, statusLabel):
        gameName = gameNameEntry.get()
        if gameName == "":
            statusLabel.config(text="Please enter a name to save the game as")
        else:
            self.currGameRecord.whenSaved, self.currGameRecord.name = datetime.now(), gameName
            p1 = self._getUsernameOfPlayerNumber(Game.P1)
            p2 = self._getUsernameOfPlayerNumber(Game.P2)
            Database.saveGame(p1, p2, self.currGameRecord)
            saveGameWindow.destroy()

    # Creates a window allowing the user to enter a username and password with which to create a new account.
    def _createAccountWindow(self):
        createAccountWindow = Toplevel(self.root)
        createAccountWindow.title("Create Account")
        Label(createAccountWindow, text="Create Account").grid(row=0, column=0, columnspan=2, pady=10)
        Label(createAccountWindow, text="Username").grid(row=1, column=0, padx=5)
        usernameEntry = Entry(createAccountWindow)
        usernameEntry.grid(row=1, column=1, padx=5)
        Label(createAccountWindow, text="Password").grid(row=2, column=0, padx=5)
        passwordEntry1 = Entry(createAccountWindow, show="*")
        passwordEntry1.grid(row=2, column=1, padx=5)
        Label(createAccountWindow, text="Confirm password").grid(row=3, column=0, padx=5)
        passwordEntry2 = Entry(createAccountWindow, show="*")
        passwordEntry2.grid(row=3, column=1, padx=5)
        statusLabel = Label(createAccountWindow, text="")
        statusLabel.grid(row=5, column=0, columnspan=2, pady=5)
        Button(createAccountWindow, text="Confirm", command=partial(self._createAccount, createAccountWindow, usernameEntry, passwordEntry1, passwordEntry2, statusLabel)).grid(row=4, column=0, columnspan=2, pady=10)

    # Given a username and password, creates a new account by creating a new entry in the database's Player table by calling its savePlayer procedure.
    def _createAccount(self, createAccountWindow, usernameEntry, passwordEntry1, passwordEntry2, statusLabel):
        username, password1, password2 = usernameEntry.get(), passwordEntry1.get(), passwordEntry2.get()
        if username == "" or password1 == "" or password2 == "":
            statusLabel.config(text="Please make sure no entries are blank")
        elif not Database.isUniqueUsername(username):
            statusLabel.config(text="That username has been taken. Please try again.")
        elif password1 != password2:
            statusLabel.config(text="Error: passwords do not match")
        else:
            Database.savePlayer(username, password1, datetime.now())
            self.player = username
            self._updateMenuFrame()
            self._updateHeadLabel()
            self._updateOptionFrame()
            createAccountWindow.destroy()

    # Undoes the last move in the currently being played game, and displays an error if not possible.
    def _undo(self):
        if not self.playing:
            self._createNotificationWin("Game ended", "The game has ended - you can no longer undo moves")
        elif self.currGameRecord.mode == Mode.PVP:
            try:
                self.currGameRecord.game.undo()
            except GameError as e:
                self._createNotificationWin("Error", f"{e}.")
            else:
                self._updateState()
        else:
            try:
                self.currGameRecord.game.undo()
                self.currGameRecord.game.undo()
            except GameError as e:
                self._createNotificationWin("Error", f"{e}.")
            else:
                self._updateState()

    # Updates how the option frame is displayed (the right-most frame in the GUI) depending on the current state of the game being played.
    def _updateOptionFrame(self):
        for widget in self.optionFrame.winfo_children(): widget.destroy()
        if self.playing:
            self.playerNoPlayingLabel = Label(self.optionFrame)
            self.playerNoPlayingLabel.grid(row=0, column=0, padx=10, pady=5)
            if self.currGameRecord.mode != Mode.LAN:
                Button(self.optionFrame, text="Undo", command=self._undo).grid(row=1, column=0, padx=10, pady=5)
            Button(self.optionFrame, text="Quit game", command=self._confirmQuit).grid(row=2, column=0, padx=10, pady=5)
            txt = "Switch Mark Last Piece OFF" if self.markLastPiece else "Switch Mark Last Piece ON"
            Button(self.optionFrame, text=txt, command=self._switchMarkPiece).grid(row=3, column=0, padx=10, pady=5)
            if self.currGameRecord.mode != Mode.LAN:
                Button(self.optionFrame, text="Get suggested move", command=self._createGetSuggestedMoveWin).grid(row=4, column=0, padx=10, pady=5)
            if self.currGameRecord.mode != Mode.PVP:
                if self.currPlayers[Game.P1] == Player.MAIN:
                    Label(self.optionFrame, text="YOU ARE PLAYER 1").grid(row=6, column=0, padx=10, pady=5)
                else:
                    Label(self.optionFrame, text="YOU ARE PLAYER 2").grid(row=6, column=0, padx=10, pady=5)
            if self.player != Player.GUEST or (self.opponent not in [Player.GUEST, Player.COMP]):
                if self.currGameRecord.id == -1:
                    command = self._createSaveGameWindow
                else:
                    command = self._createSavedGameConfirmationWindow
                if self.currGameRecord.mode != Mode.LAN:
                    Button(self.optionFrame, text="Save game", command=command).grid(row=5, column=0, padx=10, pady=5)
        else:
            Label(self.optionFrame, text="Start playing?").grid(row=0, column=0, padx=10, pady=5)

    # Creates a window which displays a suggested move for the player
    def _createGetSuggestedMoveWin(self):
        if not self.playing:
            self._createNotificationWin("Suggested move", "You can't get a suggested move when the game has ended")
            return
        suggestedMoveWin = Toplevel(self.root)
        suggestedMoveWin.title("Get suggested move")
        moveLabel = Label(suggestedMoveWin, text="Getting suggested move... (please don't exit the window)")
        moveLabel.grid(row=0, column=0, padx=10, pady=5)
        x = threading.Thread(target=self._getSuggestedMove, args=(suggestedMoveWin, moveLabel))
        x.start()
    
    # Displays the suggested move on the suggested move window
    def _getSuggestedMove(self, suggestedMoveWin, moveLabel):
        row, col = Ai.play(self.currGameRecord.game.board, self.currGameRecord.game.captures, self.currGameRecord.game.player, 3)
        moveLabel.config(text=f"Suggested move: {Game.getPenteMoveNotation(row, col, len(self.currGameRecord.game.board), False)}")
        Button(suggestedMoveWin, text="Ok", command=suggestedMoveWin.destroy).grid(row=1, column=0, padx=10, pady=5)

    # Switches the status of the "mark last piece" option and updates the GUI display
    def _switchMarkPiece(self):
        self.markLastPiece = not self.markLastPiece
        self._updateOptionFrame()
        self._updateState()

    # Updates the game by calling the database's updateGame procedure, and creates a notification window to notify the user that the game was updated.
    def _createSavedGameConfirmationWindow(self):
        self.currGameRecord.whenSaved = datetime.now()
        Database.updateGame(self.currGameRecord)
        self._createNotificationWin("Game saved", "Your game has been saved")
    
    # Updates how the menu frame is displayed (the left-most frame in the GUI) depending on whether the user is logged in or not.
    def _updateMenuFrame(self):
        for widget in self.menuFrame.winfo_children(): widget.destroy()
        if self.player == Player.GUEST:
            Label(self.menuFrame, text="Welcome to Pente!").grid(row=0, column=0, padx=10, pady=5)
            Button(self.menuFrame, text="Display rules", command=self._createDisplayRulesWin).grid(row=1, column=0, padx=10, pady=5)
            Button(self.menuFrame, text="Play new game", command=self._chooseGameMode).grid(row=2, column=0, padx=10, pady=5)
            Button(self.menuFrame, text="Login", command=partial(self._createLoginWindow, Player.MAIN, self.root)).grid(row=3, column=0, padx=10, pady=5)
            Button(self.menuFrame, text="Create Account", command=self._createAccountWindow).grid(row=4, column=0, padx=10, pady=5)
        else:
            Label(self.menuFrame, text=f"Welcome {self.player} to Pente!").grid(row=0, column=0, padx=10, pady=5)
            Button(self.menuFrame, text="Display rules", command=self._createDisplayRulesWin).grid(row=1, column=0, padx=10, pady=5)
            Button(self.menuFrame, text="Play new game", command=self._chooseGameMode).grid(row=2, column=0, padx=10, pady=5)
            Button(self.menuFrame, text="View games", command=self._createViewGamesWindow).grid(row=3, column=0, padx=10, pady=5)
            Button(self.menuFrame, text="View profile", command=self._createViewProfileWindow).grid(row=4, column=0, padx=10, pady=5)
            Button(self.menuFrame, text="Logout", command=self._logout).grid(row=5, column=0, padx=10, pady=5)

    # Creates a window which allows the user to view their player profile.
    def _createViewProfileWindow(self):
        viewProfileWindow = Toplevel(self.root)
        viewProfileWindow.title("View profile")
        whenSaved, numberOfWins, numberOfLosses, numberOfDraws, score = Database.getPlayer(self.player)
        numberOfSavedGames = len(Database.loadAllGames(self.player))
        numberOfOngoings = len(Database.loadGames(self.player, Game.ONGOING))
        totalNumberOfGames = sum([numberOfWins, numberOfLosses, numberOfDraws])
        rank = Database.getPlayerRank(self.player)
        Label(viewProfileWindow, text=f"{self.player}'s profile:").grid(row=0, column=0, padx=10, pady=10)
        Label(viewProfileWindow, text=f"Number of finished games: {totalNumberOfGames}").grid(row=1, column=0, padx=10, pady=5)
        Label(viewProfileWindow, text=f"Number of won games: {numberOfWins}").grid(row=2, column=0, padx=10, pady=5)
        Label(viewProfileWindow, text=f"Number of lost games: {numberOfLosses}").grid(row=3, column=0, padx=10, pady=5)
        Label(viewProfileWindow, text=f"Number of drawn games: {numberOfDraws}").grid(row=4, column=0, padx=10, pady=5)
        Label(viewProfileWindow, text=f"Number of saved games: {numberOfSavedGames}").grid(row=5, column=0, padx=10, pady=5)
        Label(viewProfileWindow, text=f"Number of ongoing games: {numberOfOngoings}").grid(row=6, column=0, padx=10, pady=5)
        Label(viewProfileWindow, text=f"Score: {score}").grid(row=7, column=0, padx=10, pady=10)
        Label(viewProfileWindow, text=f"Rank: {rank}").grid(row=8, column=0, padx=10, pady=5)
        Label(viewProfileWindow, text=f"Profile created on {datetime.strftime(whenSaved, '%d/%m/%Y, %H:%M:%S')}").grid(row=9, column=0, padx=10, pady=10)
        Button(viewProfileWindow, text="Ok", command=viewProfileWindow.destroy).grid(row=10, column=0, padx=10, pady=5)
    
    # Creates a window which allows the user to view their saved games, and to decide whether to load or delete any games.
    def _createViewGamesWindow(self):
        games = Database.loadAllGames(self.player)
        if not games:
            self._createNotificationWin("View games", "There are no games to view.")
        else:
            viewGamesWindow = Toplevel(self.root)
            viewGamesWindow.title("View games")
            Label(viewGamesWindow, text="Saved games:").grid(row=0, column=0, columnspan=3, padx=10, pady=5)
            for i, gameRecord in enumerate(games):
                Label(viewGamesWindow, text=f"{i+1}. {self._gameString(gameRecord)}").grid(row=i+1, column=0, columnspan=4, padx=10, pady=5)
            Button(viewGamesWindow, text="Load game", command=partial(self._createLoadGameWindow, viewGamesWindow)).grid(row=i+2, column=0, padx=10, pady=5)
            Button(viewGamesWindow, text="Delete game", command=partial(self._createDeleteGameWindow, viewGamesWindow, games)).grid(row=i+2, column=1, padx=10, pady=5)
            Button(viewGamesWindow, text="Export game moves", command=partial(self._createExportGameMovesWindow, viewGamesWindow, games)).grid(row=i+2, column=2, padx=10, pady=5)
            Button(viewGamesWindow, text="Go back", command=viewGamesWindow.destroy).grid(row=i+2, column=3, padx=10, pady=5)

    # Creates a window which allows the user to select a game to export a file of its moves from
    def _createExportGameMovesWindow(self, viewGamesWindow, games):
        viewGamesWindow.destroy()
        exportGameWindow = Toplevel(self.root)
        exportGameWindow.title("Export game moves")
        Label(exportGameWindow, text="Select a game:").grid(row=0, column=0, padx=10, pady=5)
        values = []
        for gameRecord in games:
            values.append(self._gameString(gameRecord))
        comboBox = ttk.Combobox(exportGameWindow, values=values, width=100)
        comboBox.current(0)
        comboBox.grid(row=1, column=0, padx=10, pady=5)
        Button(exportGameWindow, text="Export game moves", command=partial(self._exportGameMoveFile, exportGameWindow, comboBox.get(), games)).grid(row=2, column=0, padx=10, pady=5)

    # Given the game information to export a move record for, it creates the file using the Ui exportGameMoves procedure and creates a notification window.
    def _exportGameMoveFile(self, exportGameWindow, gameInfo, games):
        for gameRecord in games:
            if self._gameString(gameRecord) == gameInfo:
                break
        Ui._exportGameMoves(gameRecord)
        exportGameWindow.destroy()
        self._createNotificationWin("Game move record created", f"Game move record for '{gameRecord.name}' successfully created.")

    # Creates a window allowing the user to select a game to delete.
    def _createDeleteGameWindow(self, viewGamesWindow, games):
        viewGamesWindow.destroy()
        deleteGameWindow = Toplevel(self.root)
        deleteGameWindow.title("Delete game")
        Label(deleteGameWindow, text="Select a game:").grid(row=0, column=0, padx=10, pady=5)
        values = []
        for gameRecord in games:
            values.append(self._gameString(gameRecord))
        comboBox = ttk.Combobox(deleteGameWindow, values=values, width=100)
        comboBox.current(0)
        comboBox.grid(row=1, column=0, padx=10, pady=5)
        Button(deleteGameWindow, text="Delete game", command=partial(self._deleteGame, deleteGameWindow, comboBox.get(), games)).grid(row=2, column=0, padx=10, pady=5)

    # Give game information of the game to delete and a list of games, the function deletes the game from the database using the database's deleteGame procedure.
    def _deleteGame(self, deleteGameWindow, gameInfo, games):
        for gameRecord in games:
            if self._gameString(gameRecord) == gameInfo:
                break
        Database.deleteGame(gameRecord.id)
        deleteGameWindow.destroy()
        self._createNotificationWin("Game deleted", f"Game {gameRecord.name} successfully deleted.")

    # Creates a window asking for the user's confirmation to quit the currently being played game.
    def _confirmQuit(self):
        confirmQuitWindow = Toplevel(self.root)
        confirmQuitWindow.title("Quit?")
        Label(confirmQuitWindow, text="Are you sure you want to quit?").grid(row=0, column=0, columnspan=2)
        if self.currGameRecord.mode != Mode.LAN and self.playing:
            txt = "(any unsaved progress will be lost)"
        elif self.currGameRecord.mode == Mode.LAN and self.playing:
            txt = "(quitting early will mean you automatically lose the game)"
        else:
            txt = ""
        Label(confirmQuitWindow, text=txt).grid(row=1, column=0, columnspan=2)
        Button(confirmQuitWindow, text="Yes", command=partial(self._quitGame, confirmQuitWindow)).grid(row=2, column=0)
        Button(confirmQuitWindow, text="No", command=confirmQuitWindow.destroy).grid(row=2, column=1)

    # Quits the currently being played game and updates the GUI display appropriately.
    def _quitGame(self, confirmQuitWindow):
        if self.currGameRecord.mode == Mode.LAN and self.playing:
            if not self.client.requestingMove:
                self.client.makeMove((-1, -1))
                self.client.closeConnection()
                if self.playing:
                    self.currGameRecord.game.winner = Game.P1 if self.currPlayers[Game.P1] == Player.OPP else Game.P2
                self._addUserResult(self.player)
                self._createNotificationWin("Profile updated", "Your profile has been updated with the game result.")
            else:
                self._createNotificationWin("Quit Error", "You can only quit on your turn", confirmQuitWindow)
                return
        self.playing = False
        self._updateGameFrame()
        self._updateOptionFrame()
        confirmQuitWindow.destroy()

    # Logs out the currently logged in user and updates the GUI display appropriately.
    def _logout(self):
        self.player = Player.GUEST
        self._updateMenuFrame()
        self._updateHeadLabel()
        self._updateOptionFrame()

    # Creates a window allowing the user to enter a username and password to log into an existing account.
    def _createLoginWindow(self, player, toplevel):
        loginWindow = Toplevel(toplevel)
        loginWindow.title("Login")
        Label(loginWindow, text="Login").grid(row=0, column=0, columnspan=2, pady=10)
        Label(loginWindow, text="Username").grid(row=1, column=0, padx=5)
        usernameEntry = Entry(loginWindow)
        usernameEntry.grid(row=1, column=1, padx=5)
        Label(loginWindow, text="Password").grid(row=2, column=0, padx=5)
        passwordEntry = Entry(loginWindow, show="*")
        passwordEntry.grid(row=2, column=1, padx=5)
        statusLabel = Label(loginWindow, text="")
        statusLabel.grid(row=4, column=0, columnspan=2, pady=5)
        Button(loginWindow, text="Confirm", command=partial(self._login, loginWindow, player, usernameEntry, passwordEntry, statusLabel, toplevel)).grid(row=3, column=0, columnspan=2, pady=10)

    # Given a username and password, logs the user in by calling the database's checkPassword function to check that the username and passwords match.
    def _login(self, loginWindow, player, usernameEntry, passwordEntry, statusLabel, toplevel):
        username, password = usernameEntry.get(), passwordEntry.get()
        if Database.checkPassword(username, password):
                if player == Player.MAIN:
                    self.player = username
                    self._updateMenuFrame()
                else:
                    self.opponent = username
                if self.playing:
                    self._updateHeadLabel()
                    self._updateOptionFrame()
                loginWindow.destroy()
                if player == Player.OPP: self._choosePlayer(toplevel, Mode.PVP)
        else:
            statusLabel.config(text="Incorrect username or password")

    # Updates the head label (the central label at the top of the GUI) depending on the current game status.
    def _updateHeadLabel(self):
        if not self.playing:
            self.headLabel.config(text="PENTE", fg="black")
        else:
            players = self._getCurrPlayerStrings()
            self.headLabel.config(text=f"{players[0]} v.s. {players[1]}")

    # Given the player number of the user (mainPlayer), the game mode, and whether the game is new or loaded, the playGame function creates the board images and starts the game.
    def _playGame(self, mainPlayer, mode=Mode.PVP, new=True):
        self.playing = True
        self.currPlayers[mainPlayer] = Player.MAIN
        otherPlayer = Game.P1 if mainPlayer == Game.P2 else Game.P2
        self.currPlayers[otherPlayer] = Player.OPP
        if new:
            gridsize = 19
            self.currGameRecord = GameRecord(game=Game(gridsize), mode=mode)
        else:
            gridsize = len(self.currGameRecord.game.board)
        self.currentBoard = [[Game.EMPTY for _ in range(gridsize)] for _ in range(gridsize)]
        canvasSize = self.MAX_CANVAS_SIZE - (self.MAX_CANVAS_SIZE%gridsize)
        squareSize = canvasSize//(gridsize+1)
        self._createImages(squareSize)
        self._updateOptionFrame()
        self._updateGameFrame(squareSize, canvasSize, gridsize)
        if self.currGameRecord.mode == Mode.LAN:
            if self.currPlayers[self.currGameRecord.game.player] == Player.MAIN:
                self._play(gridsize//2, gridsize//2)
                self._updateState()
                self.client.makeMove((gridsize//2, gridsize//2))
            x = threading.Thread(target=self._lanGetDisplayMove)
            x.start()
        else:
            self._play(gridsize//2, gridsize//2)
            self._updateState()
            if self._getUsernameOfPlayerNumber(self.currGameRecord.game.player) == Player.COMP:
                self._playComputer()

    # Calls functions which create the images for the empty board cells and the player pieces.
    def _createImages(self, squareSize):
        self._createEmptyCellImage(squareSize)
        self._createPlayerImage(squareSize, "red", "player1.png")
        self._createPlayerImage(squareSize, "blue", "player2.png")
        self._createMarkedPlayerImage(squareSize, "red", "player1Marked.png")
        self._createMarkedPlayerImage(squareSize, "blue", "player2Marked.png")

    # Draws an image of an empty cell.
    def _createEmptyCellImage(self, squareSize):
        img = Image.new("RGBA", (squareSize+6, squareSize+6), (255, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.line((img.size[0]/2, 0, img.size[0]/2, img.size[1]), fill="black")
        draw.line((0, img.size[1]/2, img.size[0], img.size[1]/2), fill="black")
        img.save("emptyCell.png", "PNG")

    # Draws an image of a player piece of a specified colour.
    def _createPlayerImage(self, squareSize, colour, name):
        img = Image.new("RGBA", (squareSize+6, squareSize+6), (255, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.line((img.size[0]/2, 0, img.size[0]/2, img.size[1]), fill="black")
        draw.line((0, img.size[1]/2, img.size[0], img.size[1]/2), fill="black")
        draw.ellipse((img.size[0]/4, img.size[1]/4, img.size[0]*3/4, img.size[1]*3/4), fill=colour, outline="black")
        img.save(name, "PNG")

    # Draws an image of a player piece of a specified colour with black mark to indicate it was the last piece played.
    def _createMarkedPlayerImage(self, squareSize, colour, name):
        img = Image.new("RGBA", (squareSize+6, squareSize+6), (255, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.line((img.size[0]/2, 0, img.size[0]/2, img.size[1]), fill="black")
        draw.line((0, img.size[1]/2, img.size[0], img.size[1]/2), fill="black")
        draw.ellipse((img.size[0]/4, img.size[1]/4, img.size[0]*3/4, img.size[1]*3/4), fill=colour, outline="black")
        draw.ellipse((img.size[0]*7/16, img.size[1]*7/16, img.size[0]*9/16, img.size[1]*9/16), fill="black", outline="black")
        img.save(name, "PNG")

    # Creates a 2D array of Button objects which are positioned on the board.
    # Clicking a button indicates the user wants to place a piece at that position on the board.
    # When a button is pressed, the place function is called with the button position on the board passed in as arguments.
    def _getButtons(self, squareSize, gridsize):
        photoImg = PhotoImage(file="emptyCell.png")
        buttons = [[Button(self.gameFrame, width = squareSize, height = squareSize, image = photoImg, bg = "white", relief = FLAT, command = partial(self._place, y, x)) for x in range(gridsize)] for y in range(gridsize)]
        for y, buttonRow in enumerate(buttons):
            for x, button in enumerate(buttonRow):
                button.image = photoImg
                button_window = self.c.create_window(squareSize*(x+1), squareSize*(y+1), window=button)
        return buttons

    # Gets a move from the AI and plays it on the board.
    def _playComputer(self):
        row, col = Ai.play(self.currGameRecord.game.board, self.currGameRecord.game.captures, self.currGameRecord.game.player, self.compDifficulty)
        self._play(row, col)
        self._updateState()             

    # Called when a button on the board is clicked, with the arguments indicating the position on the board.
    # The place function calls the play function to play a piece at the specified position if the move is valid. The GUI display is updated to show this.
    # If the user is playing against the computer or Player v.s. Player LAN, the function also gets the next move from the opponent.
    def _place(self, row, col):
        if (self.currGameRecord.game.winner != Game.ONGOING) or (self.currGameRecord.mode != Mode.PVP and self.currPlayers[self.currGameRecord.game.player] == Player.OPP): return
        try:
            Game.validateRowCol(row, col, self.currGameRecord.game.board)
        except GameError as e:
            self._createNotificationWin("Error", f"{e}. Try again.")
        else:
            if self.currGameRecord.mode == Mode.LAN:
                self.client.makeMove((row, col))
                self._play(row, col)
                self._updateState()
                x = threading.Thread(target=self._lanGetDisplayMove)
                x.start()
            else:
                self._play(row, col)
                self._updateState()
                if self.currGameRecord.mode == Mode.COMP and self.currGameRecord.game.winner == Game.ONGOING:
                    self.root.after(1, self._playComputer)
            

    # Called after a user playing Player v.s. Player LAN places a piece on the board.
    # Gets the move from the opponent by calling the client's getMove function, and then plays and displays the new board state.
    # If the opponent has quit, the game display is cleared and the user is notified.
    def _lanGetDisplayMove(self):
        if not self.playing:
            return
        row, col = self.client.getMove()
        if (row, col) == (-1, -1):
            self.playing = False
            self._updateGameFrame()
            self._updateOptionFrame()
            self.currGameRecord.game.winner = Game.P1 if self.currPlayers[Game.P1] == Player.MAIN else Game.P2
            self._addUserResult(self.player)
            self._createNotificationWin("Opponent quit", "Your opponent has quit early - you have won the game (and your profile has been updated with the result)")
            return
        self._play(row, col)
        self._updateState()

    # Updates the display with the current game information such as the number of captured pieces and the board state.
    def _updateState(self):
        self.p1CapLabel.config(text=f"Player 1 captured pairs: {len(self.currGameRecord.game.captures[Game.P1])}")
        self.p2CapLabel.config(text=f"Player 2 captured pairs: {len(self.currGameRecord.game.captures[Game.P2])}")

        prevMoves = [None, None]
        try:
            lastStack = self.currGameRecord.game.moveStack.pop()
            prevMoves[0] = lastStack[1:]
        except:
            pass
        else:
            try:
                prevMoves[1] = self.currGameRecord.game.moveStack.peek()[1:]
            except:
                pass
            self.currGameRecord.game.moveStack.push(lastStack[0], lastStack[1], lastStack[2])

        for row in range(len(self.currGameRecord.game.board)):
            for col in range(len(self.currGameRecord.game.board)):
                if self.currGameRecord.game.board[row][col] == self.currentBoard[row][col] and (row, col) not in prevMoves:
                    continue
                if self.markLastPiece and prevMoves[0] == (row, col):
                    self._updateCell(row, col, self.currGameRecord.game.board[row][col], mark=True)
                elif self.markLastPiece and prevMoves[1] == (row, col):
                    self._updateCell(row, col, self.currGameRecord.game.board[row][col])
                else:
                    self._updateCell(row, col, self.currGameRecord.game.board[row][col])
        self.currentBoard = deepcopy(self.currGameRecord.game.board)

        if self.currGameRecord.game.player == Game.P1:
            self.playerNoPlayingLabel.config(text="Player 1 to play")
        else:
            self.playerNoPlayingLabel.config(text="Player 2 to play")

    # Updates the image displayed for a single board cell given its position and the piece it should hold.
    def _updateCell(self, row, col, piece, mark=False):
        if piece == Game.EMPTY:
            filename = "emptyCell.png"
        elif not mark:
            if piece == Game.P1:
                filename = "player1.png"
            else:
                filename = "player2.png"
        else:
            if piece == Game.P1:
                filename = "player1Marked.png"
            else:
                filename = "player2Marked.png"
        photoImg = PhotoImage(file=filename)
        button = self.buttons[row][col]
        button.configure(image=photoImg)
        button.image = photoImg

    # Updates the headLabel (the central label at the top of the GUI) to show the game winner.
    def _displayWin(self):
        if self.currGameRecord.game.winner == Game.P1:
            msg = "Player 1 WON!"
            colour = "red"
        elif self.currGameRecord.game.winner == Game.P2:
            msg = "Player 2 WON!"
            colour = "blue"
        else:
            msg = "It is a draw."
            colour = "black"

        self.headLabel.config(text=msg, fg=colour)

    # Updates the game frame (the central frame) to either display the default screen (when no game is playing), or a new board (if a game is being played).
    def _updateGameFrame(self, squareSize=None, canvasSize=None, gridsize=None):
        self.c.delete("all")
        self._updateHeadLabel()
        if not self.playing:
            bgColour = "#D3D3D3"
            self.p1CapLabel.config(text="", bg=bgColour)
            self.p2CapLabel.config(text="", bg=bgColour)
            self.c = Canvas(self.gameFrame, height=self.MAX_CANVAS_SIZE, width=self.MAX_CANVAS_SIZE, bg=bgColour)
            self.c.grid(row=2, column=0)
        else:
            self.p1CapLabel.config(bg="white", fg="red")
            self.p2CapLabel.config(bg="white", fg="blue")
            self.c = Canvas(self.gameFrame, height=canvasSize, width=canvasSize, bg="white")
            self.c.grid(row=2, column=0)
            for i in range(0, canvasSize, squareSize):
                self.c.create_line([(i, 0), (i, canvasSize)])
            for i in range(0, canvasSize, squareSize):
                self.c.create_line([(0, i), (canvasSize, i)])
            self.buttons = self._getButtons(squareSize, gridsize)
            self._updateState()

    # Given a move to play, calls the game method's play function to play the move.
    # If the game has ended, the winner is displayed. Otherwise the label stating which player number is playing is switched.
    def _play(self, row, col):
        self.currGameRecord.game.play(row, col)
        if self.currGameRecord.game.winner != Game.ONGOING:
            self._displayWin()
            self.playing = False
            if self.currGameRecord.mode != Mode.LAN:
                changesMade = self._addResultsToProfile()
                if changesMade:
                    if self.currGameRecord.id != -1:
                        self.currGameRecord.whenSaved = datetime.now()
                        Database.updateGame(self.currGameRecord)
                        txt = "Your profile has been updated with the game result, and your saved game has been updated."
                    else:
                        txt = "Your profile has been updated with the game result."
                    self._createNotificationWin("Profile updated", txt)
            else:
                self.client.closeConnection()
                self._addUserResult(self.player)
                self._createNotificationWin("Profile updated", "Your profile has been updated with the game result.")

    # Called when starting a Player v.s. Player LAN game.
    # Makes a connection between the client and server and gets an opponent using the client's methods.
    # Calls the playGame function to start the game.
    def _connectAndGetOpp(self):
        self.client.makeConnection()
        self.client.getOpponent()
        self.opponent = self.client.opponent
        self._playGame(self.client.playerNo, Mode.LAN)

    # Called when starting a Player v.s. Player LAN game.
    # Creates a new client and calls the connectAndGetOpp function to start the client-server interaction.
    def _connectLan(self, playGameWindow):
        playGameWindow.destroy()
        self.client = Client(self.player)
        self.headLabel.config(text="Waiting for opponent...")
        x = threading.Thread(target=self._connectAndGetOpp)
        x.start()
        
# The Terminal class is a subclass of the Ui class, and contains all properties and methods required for the terminal-based user interface.
class Terminal(Ui):

    def __init__(self):
        super().__init__()

    # Starts running the terminal UI by displaying the menu.
    def run(self):
        self._displayMenu()

    # Displays one of two possible game mode menus (one for guest and one for logged in accounts), asks for a choice from the user, and returns it.
    def _chooseMode(self):
        memberMenu = """
        Please choose a game mode:
        1. Player v.s. Player
        2. Player v.s. Computer
        3. Player v.s. Player (LAN)
        """
        guestMenu = """
        Please choose a game mode:
        1. Player v.s. Player
        2. Player v.s. Computer
        """
        if self.player == Player.GUEST:
            print(guestMenu)
            c = Terminal._getChoice(1, 2)
        else:
            print(memberMenu)
            c = Terminal._getChoice(1, 3)
        return [Mode.PVP, Mode.COMP, Mode.LAN][c-1]

    # Asks the user which player they would like to play as (providing both users are not using guest accounts).
    def _choosePlayer(self):
        if self.player == Player.GUEST and self.opponent == Player.GUEST:
            return Game.P1
        playerTitle = "the guest" if self.player == Player.GUEST else self.player
        print(f"Would {playerTitle} like to be player 1 or 2? (1/2) ")
        inp = Terminal._getChoice(1, 2)
        return [Game.P1, Game.P2][inp-1]

    # Prints a list of all games saved in the database and gives the user the option to select a game to load or delete.
    def _viewGames(self):
        games = Database.loadAllGames(self.player)
        if not games:
            print("There are no games to view.")
        else:
            for i, gameRecord in enumerate(games):
                print(f"{i+1}. {self._gameString(gameRecord)}")
            menu = """
            Choose an option:
            1. Load game
            2. Delete game
            3. Export game moves
            4. Go back
            """
            print(menu)
            inp = Terminal._getChoice(1, 4)
            if inp == 1:
                self._loadGame()
            elif inp == 2:
                self._deleteGame(games)
            elif inp == 3:
                self._exportGameMoveFile(games)

    # Gets the game mode and asks for additional information needed for the game.
    # Calls the play function to start the game.
    def _playGame(self):
        mode = self._chooseMode()
        self.currGameRecord = GameRecord(game=Game(19), mode=mode)
        if mode == Mode.LAN:
            self._connectLan()
            player = self.client.playerNo
        else:
            if mode == Mode.PVP:
                self.opponent = Player.GUEST
                menu = """
            The other player will:
            1. Play as a guest
            2. Login
                """
                print(menu)
                if Terminal._getChoice(1, 2) == 2:
                    self._login(Player.OPP)
            elif mode == Mode.COMP:
                self.opponent = Player.COMP
                menu = """
            Select difficulty level:
            1. Easy
            2. Medium
            3. Hard
                """
                print(menu)
                self.compDifficulty = Terminal._getChoice(1, 3)
            player = self._choosePlayer()
        otherPlayer = Game.P2 if player == Game.P1 else Game.P1
        self.currPlayers[player] = Player.MAIN
        self.currPlayers[otherPlayer] = Player.OPP
        self._play()

    # Displays one of two main menus (one for guest and one for logged in accounts), and asks for an option from the user.
    # The user's choice is used to call a relevant function to deal with the user's request.
    def _displayMenu(self):
        guestMethods = {1: self._displayRules, 2: self._playGame, 3: lambda: self._login(Player.MAIN), 4: self._createAccount, 5: quit}
        memberMethods = {1: self._displayRules, 2: self._playGame, 3: self._viewGames, 4: self._viewProfile, 5: self._logout, 6: quit}

        while 1:

            guestMenu = """
            Welcome to Pente!

            Choose an option:
            1. Display rules
            2. Play new game
            3. Login
            4. Create Account
            5. Quit
            """

            memberMenu = f"""
            Welcome to Pente {self.player}!

            Choose an option:
            1. Display rules
            2. Play new game
            3. View games
            4. View profile
            5. Logout
            6. Quit
            """

            if self.player == Player.GUEST:
                print(guestMenu)
                inp = Terminal._getChoice(1, 5)
                guestMethods[inp]()
            else:
                print(memberMenu)
                inp = Terminal._getChoice(1, 6)
                memberMethods[inp]()

    # Displays the player's profile information.
    def _viewProfile(self):
        whenSaved, numberOfWins, numberOfLosses, numberOfDraws, score = Database.getPlayer(self.player)
        numberOfSavedGames = len(Database.loadAllGames(self.player))
        numberOfOngoings = len(Database.loadGames(self.player, Game.ONGOING))
        totalNumberOfGames = sum([numberOfWins, numberOfLosses, numberOfDraws])
        rank = Database.getPlayerRank(self.player)
        profileString = f"""
            {self.player}'s profile:

            Number of finished games: {totalNumberOfGames}
            Number of won games: {numberOfWins}
            Number of lost games: {numberOfLosses}
            Number of drawn games: {numberOfDraws}
            Number of saved games: {numberOfSavedGames}
            Number of ongoing games: {numberOfOngoings}
            Score: {score}
            Rank: {rank}

            Profile created on {datetime.strftime(whenSaved, "%d/%m/%Y, %H:%M:%S")}
            """
        print(profileString)
        print()
        input("Press any key to go back > ")
        print()
        self._displayMenu()

    # Displays a message (the input parameter msg) and asks for an input from the user.
    # The input will only be valid if it is one of y or n, and the function will keep asking an input from the user if it isn't.
    # The function returns a boolean value: True for y (yes) or False for n (no).
    @staticmethod
    def _getYesNo(msg):
        inp = input(msg)
        while inp not in ["y", "n"]:
            inp = input("Invalid choice. Please enter y or n: ")
        if inp == "y":
            return True
        return False

    # Given two numeric bounds, the function asks for a number as an input.
    # If the input is either not an integer or not between the two bounds inclusive, it is considered invalid and the input is asked for again.
    # The input is then returned from the function.
    @staticmethod
    def _getChoice(lower, upper):
        while 1:
            try:
                inp = int(input("> "))
            except:
                print("That is not a valid choice. Please try again.")
                continue
            if lower <= inp <= upper:
                return inp
            print("That is not a valid choice. Please try again.")

    # Given a player that wants to log in, the login function logs the player in given their username and password are correct.
    # A username and password are checked to be correct by calling the database's checkPassword function.
    def _login(self, player):
        while 1:
            username = input("Username: ")
            if player == Player.OPP and self.player == username:
                if Terminal._getYesNo("That player is already logged in. Try again? (y/n) "):
                    continue
                else:
                    return
            password = input("Password: ")
            if Database.checkPassword(username, password):
                print("Login successful!")
                if player == Player.MAIN:
                    self.player = username
                else:
                    self.opponent = username
                return
            elif not Terminal._getYesNo("Username or password incorrect. Try again? (y/n) "):
                return

    # Logs out the currently logged in player.
    def _logout(self):
        self.player = Player.GUEST
        print("Logout successful.")

    # Creates an account by asking for a username and password for the user. The username must be checked to be unique by calling the isUniqueUsername database function.
    # The new account details are saved as a new Player entry to the database by calling the savePlayer database function.
    def _createAccount(self):
        while 1:
            username = input("Enter username: ")
            if not Database.isUniqueUsername(username):
                if Terminal._getYesNo("Sorry, that username has already been taken. Try again? (y/n) "):
                    continue
                else:
                    return
            password = input("Enter password: ")
            passwordConfirm = input("Confirm password: ")
            if password == passwordConfirm:
                Database.savePlayer(username, password, datetime.now())
                print("Account creation successful!")
                self.player = username
                return
            elif not Terminal._getYesNo("Passwords do not match. Try again? (y/n) "):
                return

    # Given a board and the captured pieces, the printState function returns a string defining how the board and captures are to be displayed on the screen.
    def _printState(self):
        boardsize = len(self.currGameRecord.game.board)
        boardString = "Board:\n\n"
        boardString += "   " + " ".join([chr(65+i) for i in range(boardsize)]) + "\n"
        for row in range(boardsize):
            space = " " if row+1 < 10 else ""
            boardString += space + str(row+1) + " "
            for col in range(boardsize):
                piece = self.currGameRecord.game.board[row][col]
                if piece == Game.EMPTY:
                    boardString += "+"
                elif piece == Game.P1:
                    boardString += f"{Fore.RED}O{Style.RESET_ALL}"
                else:
                    boardString += f"{Fore.BLUE}O{Style.RESET_ALL}"
                if col < boardsize-1:
                    boardString += "-"
            boardString += "\n"
        boardString += f"\nPlayer 1 captured pairs: {len(self.currGameRecord.game.captures[Game.P1])}\n"
        boardString += f"Player 2 captured pairs: {len(self.currGameRecord.game.captures[Game.P2])}\n"
        print(boardString)

    # Given a move, checks if the move is valid. If it is valid it will return the move, otherwise it will raise an error.
    def _getRowCol(self, move):
        if len(move) == 0:
            raise GameError("No move played")
        row, col = move[:-1], move[-1]
        try:
            row = int(row)
        except:
            raise GameError("Invalid move")
        if 97 <= ord(col) <= 122:
            col = chr(ord(col)-32)
        elif not (65 <= ord(col) <= 90):
            raise GameError("Invalid move")
        row -= 1
        col = ord(col)-65
        try:
            Game.validateRowCol(row, col, self.currGameRecord.game.board)
        except GameError:
            raise GameError("Invalid move")
        else:
            return row, col

    # Given a game to save, the saveGame function saves the game to the database by calling the database's own saveGame procedure.
    def _saveGame(self):
        self.currGameRecord.whenSaved = datetime.now()
        if self.currGameRecord.id != -1:
            Database.updateGame(self.currGameRecord)
        else:
            name = input("Enter name to save game as: ")
            self.currGameRecord.name = name
            Database.saveGame(self._getUsernameOfPlayerNumber(Game.P1), self._getUsernameOfPlayerNumber(Game.P2), self.currGameRecord)
        print("Game saved successfully.")

    # Given games, it gives the user a choice to choose which game to export moves for, and then does this by calling the Ui exportGameMoves function.
    def _exportGameMoveFile(self, games):
        print("Which game's moves would you like to export? (e.g. 1, 2...)")
        inp = Terminal._getChoice(1, len(games))
        gameRecord = games[inp-1]
        Ui._exportGameMoves(gameRecord)
        print(f"Game move record for '{gameRecord.name}' successfully created.")

    # Displays a list of the ongoing games on the screen, and asks the user to choose one to load.
    # Once a game has been chosen, the play function is called to play the loaded game.
    def _loadGame(self):
        games = Database.loadGames(self.player, Game.ONGOING)
        if not games:
            print("There are no ongoing games.")
        else:
            print("Ongoing games:")
            for i, gameRecord in enumerate(games):
                print(f"{i+1}. {self._gameString(gameRecord)}")
            print("Select a game (e.g. 1, 2...)")
            inp = Terminal._getChoice(1, i+1)
            self.currGameRecord = games[inp-1]
            self._play()

    # Given a list of games, the deleteGame function asks for a choice from the player for which game to delete.
    # The specified game from the list is then deleted by calling the database's deleteGame procedure.
    def _deleteGame(self, games):
        print("Which game would you like to delete? (e.g. 1, 2...)")
        inp = Terminal._getChoice(1, len(games))
        Database.deleteGame(games[inp-1].id)
        print(f"Game '{games[inp-1].name}' successfully deleted.")

    # Called when a non-move choice is entered by the user whilst playing a game: one of s (save) and u (undo).
    # The choice is then processed by the processChoice function given the choice and the game being played.
    def _processChoice(self, choice):
        if choice == "s":
            nonGuests = [player for player in [self.player, self.opponent] if player != Player.GUEST and player != Player.COMP]
            if nonGuests and self.currGameRecord.mode != Mode.LAN:
                    if len(nonGuests) > 1:
                        playerString = f"{nonGuests[0]}'s and {nonGuests[1]}'s accounts"
                    else:
                        playerString = f"{nonGuests[0]}'s account"
                    yes = Terminal._getYesNo(f"Would you like to save your game to {playerString}? (y/n) ")
                    if yes:
                        self._saveGame()
            else:
                print("Save not available")
        elif choice == "u":
            if self.currGameRecord.mode == Mode.PVP:
                try:
                    self.currGameRecord.game.undo()
                except GameError as e:
                    print(f"Error: {e}")
                else:
                    self._printState()
            elif self.currGameRecord.mode == Mode.COMP:
                try:
                    self.currGameRecord.game.undo()
                    self.currGameRecord.game.undo()
                except GameError as e:
                    print(f"Error: {e}")
                else:
                    self._printState()
            else:
                print("Undo not available for LAN games")
        elif choice == "h":
            if self.currGameRecord.mode == Mode.LAN:
                print("Suggested moves are not available for LAN games")
            else:
                print("Getting suggested move...")
                row, col = Ai.play(self.currGameRecord.game.board, self.currGameRecord.game.captures, self.currGameRecord.game.player, 3)
                print(f"Suggested move: {row+1}{chr(col+65)}")
        print()

    # Called to get a choice or a move from the user whilst playing the game. This is then returned from the function.
    def _getMove(self):
        while 1:
            choice = input("Enter move: ")
            if choice == "q":
                willQuit = True
                if self.currGameRecord.mode == Mode.LAN:
                    willQuit = Terminal._getYesNo("Are you sure? Quitting early will mean you automatically lose the game. (y/n) ")
                if not willQuit:
                    continue
                return choice, False, True
            elif choice in ["s", "u", "h"]:
                return choice, False, False
            else:
                try:
                    row, col = self._getRowCol(choice)
                    return (row, col), True, False
                except GameError as err:
                    print(f"Error: {err}. Try again.")

    # Performs a loop which asks for moves from the user and the opponent until either the game ends or the user quits.
    # After each move the new board state is displayed on the screen.
    def _play(self):
        print("\nTo enter a move, enter the row followed by the column e.g. 1A or 1a.")
        print("Other than entering a move you can type q to quit, s to save, u to undo, or h to get a suggested move.")
        print("Note: saves, undoes and suggested moves are not available for Player v.s. Player LAN games.\n")

        gridsize = len(self.currGameRecord.game.board)
        if self.currGameRecord.mode == Mode.LAN:
            if self.currPlayers[self.currGameRecord.game.player] == Player.MAIN:
                self.currGameRecord.game.play(gridsize//2, gridsize//2)
                self.client.makeMove((gridsize//2, gridsize//2))
        else:
            self.currGameRecord.game.play(gridsize//2, gridsize//2)
            if self._getUsernameOfPlayerNumber(self.currGameRecord.game.player) == Player.COMP:
                row, col = Ai.play(self.currGameRecord.game.board, self.currGameRecord.game.captures, self.currGameRecord.game.player, self.compDifficulty)
                print(f"COMPUTER PLAYED: {row+1}{chr(col+65)}")
                self.currGameRecord.game.play(row, col)

        while self.currGameRecord.game.winner == Game.ONGOING:
            self._printState()
            playerStr = "Player 1 to play" if self.currGameRecord.game.player == Game.P1 else "Player 2 to play"
            print(playerStr)
            if self._getUsernameOfPlayerNumber(self.currGameRecord.game.player) == Player.COMP:
                row, col = Ai.play(self.currGameRecord.game.board, self.currGameRecord.game.captures, self.currGameRecord.game.player, self.compDifficulty)
                print(f"COMPUTER PLAYED: {row+1}{chr(col+65)}")
                self.currGameRecord.game.play(row, col)
            elif self.currGameRecord.mode == Mode.LAN and self.currPlayers[self.currGameRecord.game.player] != Player.MAIN:
                print(f"Waiting for {self.client.opponent} to play...")
                row, col = self.client.getMove()
                if (row, col) == (-1, -1):
                    self.client.closeConnection()
                    self.currGameRecord.game.winner = Game.P1 if self.currPlayers[Game.P1] == Player.MAIN else Game.P2
                    self._addUserResult(self.player)
                    print("Your opponent has quit - you have automatically won the game.")
                    print()
                    print("Your profile has been updated with the game result.")
                    input("Press any key to continue > ")
                    return
                else:
                    self.currGameRecord.game.play(row, col)
                    print(f"{self.client.opponent} played: {row+1}{chr(col+65)}")
            else:
                choice, isMove, end = self._getMove()
                if not isMove:
                    self._processChoice(choice)
                    if end:
                        if self.currGameRecord.mode == Mode.LAN:
                            self.currGameRecord.game.winner = Game.P1 if self.currPlayers[Game.P1] == Player.OPP else Game.P2
                            self._addUserResult(self.player)
                            print("Your profile has been updated with the game result.")
                            self.client.makeMove((-1, -1))
                            self.client.closeConnection()
                        return
                else:
                    row, col = choice
                    self.currGameRecord.game.play(row, col)
                    if self.currGameRecord.mode == Mode.LAN: self.client.makeMove((row, col))
        self._printState()
        if self.currGameRecord.game.winner == Game.P1:
            print("Player 1 has won!")
        elif self.currGameRecord.game.winner == Game.P2:
            print("Player 2 has won!")
        else:
            print("It is a draw.")
        
        if self.currGameRecord.mode == Mode.LAN:
            self.client.closeConnection()
            self._addUserResult(self.player)
            print("Your profile has been updated with the game result.")
        else:
            changesMade = self._addResultsToProfile()
            if changesMade:
                if self.currGameRecord.id != -1:
                    self.currGameRecord.whenSaved = datetime.now()
                    Database.updateGame(self.currGameRecord)
                    txt = "Your profile has been updated with the game result, and your saved game has been updated."
                else:
                    txt = "Your profile has been updated with the game result."
                print(txt)
            input("Enter any key to go back > ")

    # Creates a new client instance, connects it to the server, and obtains an opponent.
    def _connectLan(self):
        self.client = Client(self.player)
        print("Waiting for connection...")
        self.client.makeConnection()
        print("Connected.")
        print("Waiting for opponent...")
        self.client.getOpponent()
        self.opponent = self.client.opponent
        playerNo = 1 if self.client.playerNo == Game.P1 else 2
        oppNo = 1 if playerNo == 2 else 2
        print(f"Opponent: {self.opponent} (player {oppNo})")
        print(f"You are player {playerNo}")

    # Prints the rules of the game, and returns the user to the main menu.
    def _displayRules(self):
        print(Ui._getRulesText())
        print()
        input("Press any key to go back > ")
        print()
        self._displayMenu()