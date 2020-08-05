from abc import ABC, abstractmethod
from copy import deepcopy
from Game import Game, GameError, GameRecord
from colorama import Fore, Style
from enum import Enum, auto
from datetime import datetime
import Database
import Ai
from tkinter import *
from functools import partial
from PIL import Image, ImageDraw

class Ui (ABC):

    @abstractmethod
    def run(self):
        raise NotImplementedError

class Gui(Ui):

    def __init__(self):
        self.MAX_CANVAS_SIZE = 730
        self.player = Player.GUEST
        self.opponent = Player.GUEST
        self.currGameRecord = None
        self.currPlayers = {Game.P1: Player.MAIN, Game.P2: Player.OPP}
        self.currentBoard = None
        self.playing = False

        self.root = Tk()
        self.root.title("Pente")

        self.menuFrame = Frame(self.root)
        self.menuFrame.grid(row=0, column=0, sticky="EW")

        self.gameFrame = Frame(self.root)
        self.gameFrame.grid(row=0, column=1, sticky="EW")

        self.optionFrame = Frame(self.root)
        self.optionFrame.grid(row=0, column=2, sticky="EW")

        self.headLabel = Label(self.gameFrame, bg="white", fg="black", font=("Helvetica", 18))
        self.headLabel.grid(row=0, column=0, sticky="NESW")

        self.c = Canvas()
        self.p1CapLabel = Label(self.gameFrame, relief="ridge", font=("Helvetica", 18))
        self.p1CapLabel.grid(row=1, column=0, sticky="NESW")
        self.p2CapLabel = Label(self.gameFrame, relief="ridge", font=("Helvetica", 18))
        self.p2CapLabel.grid(row=3, column=0, sticky="NESW")

        self.updateMenuFrame()
        self.updateGameFrame()
        self.updateOptionFrame()

    def getPlayer(self, player):
        p = self.currPlayers[player]
        return self.player if p == Player.MAIN else self.opponent

    def chooseGameMode(self):
        playGameWindow = Toplevel(self.root)
        playGameWindow.title("Play")
        Label(playGameWindow, text="Choose a game mode").grid(row=0, column=0, padx=10, pady=5)
        Button(playGameWindow, text="Player v.s. Player", command=partial(self.confirmOppLogin, playGameWindow)).grid(row=1, column=0, padx=5)
        Button(playGameWindow, text="Player v.s. Computer", command=partial(self.choosePlayer, playGameWindow, True)).grid(row=2, column=0, padx=5)     

    def confirmOppLogin(self, playGameWindow):
        for widget in playGameWindow.winfo_children(): widget.destroy()
        Label(playGameWindow, text="Would the other player like to login?").grid(row=0, column=0, columnspan=2, padx=10, pady=5)
        Button(playGameWindow, text="Yes", command=partial(self.createLoginWindow, Player.OPP, playGameWindow)).grid(row=1, column=0, padx=5)
        Button(playGameWindow, text="No", command=partial(self.choosePlayer, playGameWindow, False)).grid(row=1, column=1, padx=5)

    def choosePlayer(self, playGameWindow, computer):
        playGameWindow.destroy()
        if computer:
            self.opponent = Player.COMP
        if (self.player == Player.GUEST) and (self.opponent == Player.GUEST):
            self.playGame(Game.P1, computer)
        else:
            choosePlayerWindow = Toplevel(self.root)
            choosePlayerWindow.title("Choose player")
            if computer:
                txt = "Would you like to be player 1 or player 2?"
            else:
                if self.player == Player.GUEST:
                    player = "the guest"
                else:
                    player = self.player
                txt = f"Would {player} like to be player 1 or player 2?"
            Label(choosePlayerWindow, text=txt).grid(row=0, column=0, columnspan=2, padx=10, pady=5)
            Button(choosePlayerWindow, text="Player 1", command=partial(self.playNewGame, choosePlayerWindow, Game.P1, computer)).grid(row=1, column=0, padx=5)
            Button(choosePlayerWindow, text="Player 2", command=partial(self.playNewGame, choosePlayerWindow, Game.P2, computer)).grid(row=1, column=1, padx=5)

    def playNewGame(self, choosePlayerWindow, player, computer):
        choosePlayerWindow.destroy()
        self.playGame(player, computer)

    def gameString(self, gameRecord):
        players = [Database.getPlayerGameUsername(gameRecord.id, Game.P1), Database.getPlayerGameUsername(gameRecord.id, Game.P2)]
        for i in range(2):
            if players[i] == False:
                if gameRecord.computer:
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
        return f"{gameRecord.name:25s}{mode:25s}saved on {whenSaved:25s}status: {status}"

    def createLoadGameWindow(self):
        loadGameWindow = Toplevel(self.root)
        loadGameWindow.title("Load game")
        games = Database.loadGames(self.player, Game.ONGOING)
        if not games:
            Label(loadGameWindow, text="You have no ongoing games").grid(row=0, column=0, padx=10, pady=5)
        else:
            Label(loadGameWindow, text="Ongoing games:").grid(row=0, column=0, padx=10, pady=5)
            for i, gameRecord in enumerate(games):
                Button(loadGameWindow, text=f"{i+1}. {self.gameString(gameRecord)}", command=partial(self.loadGame, loadGameWindow, gameRecord)).grid(row=i+1, column=0, padx=5)
            Label(loadGameWindow, text="Select a game to load").grid(row=i+2, column=0, padx=10, pady=5)

    def loadGame(self, loadGameWindow, gameRecord):
        self.currGameRecord = gameRecord
        players = [Database.getPlayerGameUsername(self.currGameRecord.id, Game.P1), Database.getPlayerGameUsername(self.currGameRecord.id, Game.P2)]
        mainPlayerPos = None
        for i, player in enumerate(players):
            pos = Game.P1 if i == 0 else Game.P2
            if player == self.player:
                mainPlayerPos = pos
            elif player == False:
                self.opponent = Player.COMP if self.currGameRecord.computer else Player.GUEST
            else:
                self.opponent = player
        loadGameWindow.destroy()
        self.playGame(mainPlayerPos, new=False)

    def getCurrPlayerStrings(self):
        players = []
        for player in [self.currPlayers[Game.P1], self.currPlayers[Game.P2]]:
            p = self.player if player == Player.MAIN else self.opponent
            if p == Player.GUEST:
                players.append("Guest")
            elif p == Player.COMP:
                players.append("Computer")
            else:
                players.append(p)
        return players

    def createSaveGameWindow(self):
        saveGameWindow = Toplevel(self.root)
        saveGameWindow.title("Save game")
        players = self.getCurrPlayerStrings()
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
        Button(saveGameWindow, text="Confirm", command=partial(self.saveGame, saveGameWindow, gameNameEntry, statusLabel)).grid(row=5, column=0, columnspan=2, pady=10)

    def saveGame(self, saveGameWindow, gameNameEntry, statusLabel):
        gameName = gameNameEntry.get()
        if gameName == "":
            statusLabel.config(text="Please enter a name to save the game as")
        else:
            self.currGameRecord.whenSaved, self.currGameRecord.name = datetime.now(), gameName
            p1 = self.player if self.currPlayers[Game.P1] == Player.MAIN else self.opponent
            p2 = self.player if self.currPlayers[Game.P2] == Player.MAIN else self.opponent
            Database.saveGame(p1, p2, self.currGameRecord)
            saveGameWindow.destroy()

    def createAccountWindow(self):
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
        Button(createAccountWindow, text="Confirm", command=partial(self.createAccount, createAccountWindow, usernameEntry, passwordEntry1, passwordEntry2, statusLabel)).grid(row=4, column=0, columnspan=2, pady=10)

    def createAccount(self, createAccountWindow, usernameEntry, passwordEntry1, passwordEntry2, statusLabel):
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
            self.updateMenuFrame()
            self.updateHeadLabel()
            self.updateOptionFrame()
            createAccountWindow.destroy()

    def undo(self):
        try:
            self.currGameRecord.game.undo()
        except GameError as e:
            self.headLabel.config(text=f"Error: {e}.")
            self.root.after(1500, self.updateHeadLabel)
        else:
            self.updateState()

    def updateOptionFrame(self):
        for widget in self.optionFrame.winfo_children(): widget.destroy()
        if self.playing:
            Button(self.optionFrame, text="Undo", command=self.undo).grid(row=0, column=0, padx=10, pady=5)
            Button(self.optionFrame, text="Quit game", command=self.confirmQuit).grid(row=1, column=0, padx=10, pady=5)
            if self.player != Player.GUEST or (self.opponent not in [Player.GUEST, Player.COMP]):
                if self.currGameRecord.id == -1:
                    command = self.createSaveGameWindow
                else:
                    self.currGameRecord.whenSaved = datetime.now()
                    command = lambda: Database.updateGame(self.currGameRecord)
                Button(self.optionFrame, text="Save game", command=command).grid(row=2, column=0, padx=10, pady=5)
        else:
            Label(self.optionFrame, text="Start playing?").grid(row=0, column=0, padx=10, pady=5)

    def updateMenuFrame(self):
        for widget in self.menuFrame.winfo_children(): widget.destroy()
        if self.player == Player.GUEST:
            Label(self.menuFrame, text="Welcome to Pente!").grid(row=0, column=0, padx=10, pady=5)
            Button(self.menuFrame, text="Play new game", command=self.chooseGameMode).grid(row=1, column=0, padx=10, pady=5)
            Button(self.menuFrame, text="Login", command=partial(self.createLoginWindow, Player.MAIN, self.root)).grid(row=2, column=0, padx=10, pady=5)
            Button(self.menuFrame, text="Create Account", command=self.createAccountWindow).grid(row=3, column=0, padx=10, pady=5)
        else:
            Label(self.menuFrame, text=f"Welcome {self.player} to Pente!").grid(row=0, column=0, padx=10, pady=5)
            Button(self.menuFrame, text="Play new game", command=self.chooseGameMode).grid(row=1, column=0, padx=10, pady=5)
            Button(self.menuFrame, text="Load game", command=self.createLoadGameWindow).grid(row=2, column=0, padx=10, pady=5)
            Button(self.menuFrame, text="Logout", command=self.logout).grid(row=3, column=0, padx=10, pady=5)

    def confirmQuit(self):
        confirmQuitWindow = Toplevel(self.root)
        confirmQuitWindow.title("Quit?")
        Label(confirmQuitWindow, text="Are you sure you want to quit?").grid(row=0, column=0, columnspan=2)
        Label(confirmQuitWindow, text="(any unsaved progress will be lost)").grid(row=1, column=0, columnspan=2)
        Button(confirmQuitWindow, text="Yes", command=partial(self.quitGame, confirmQuitWindow)).grid(row=2, column=0)
        Button(confirmQuitWindow, text="No", command=confirmQuitWindow.destroy).grid(row=2, column=1)

    def quitGame(self, confirmQuitWindow):
        self.playing = False
        self.updateGameFrame()
        self.updateOptionFrame()
        confirmQuitWindow.destroy()

    def logout(self):
        self.player = Player.GUEST
        self.updateMenuFrame()
        self.updateHeadLabel()
        self.updateOptionFrame()

    def createLoginWindow(self, player, toplevel):
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
        Button(loginWindow, text="Confirm", command=partial(self.login, loginWindow, player, usernameEntry, passwordEntry, statusLabel, toplevel)).grid(row=3, column=0, columnspan=2, pady=10)

    def login(self, loginWindow, player, usernameEntry, passwordEntry, statusLabel, toplevel):
        username, password = usernameEntry.get(), passwordEntry.get()
        if Database.checkPassword(username, password):
                if player == Player.MAIN:
                    self.player = username
                    self.updateMenuFrame()
                else:
                    self.opponent = username
                if self.playing:
                    self.updateHeadLabel()
                    self.updateOptionFrame()
                loginWindow.destroy()
                if player == Player.OPP: self.choosePlayer(toplevel, False)
        else:
            statusLabel.config(text="Incorrect username or password")

    def updateHeadLabel(self):
        if not self.playing:
            self.headLabel.config(text="PENTE", fg="black")
        else:
            players = self.getCurrPlayerStrings()
            self.headLabel.config(text=f"{players[0]} v.s. {players[1]}")

    def playGame(self, mainPlayer, computer=None, new=True):
        self.playing = True
        self.currPlayers[mainPlayer] = Player.MAIN
        otherPlayer = Game.P1 if mainPlayer == Game.P2 else Game.P2
        self.currPlayers[otherPlayer] = Player.OPP
        if new:
            gridsize = 19
            self.currGameRecord = GameRecord(game=Game(gridsize), computer=computer)
        else:
            gridsize = len(self.currGameRecord.game.board)
        self.currentBoard = [[Game.EMPTY for _ in range(gridsize)] for _ in range(gridsize)]
        canvasSize = self.MAX_CANVAS_SIZE - (self.MAX_CANVAS_SIZE%gridsize)
        squareSize = canvasSize//(gridsize+1)
        self.createImages(squareSize)
        self.updateGameFrame(squareSize, canvasSize, gridsize)
        self.updateOptionFrame()
        if self.getPlayer(self.currGameRecord.game.player) == Player.COMP: self.playComputer()

    def run(self):
        Database.createTables()
        self.root.mainloop()

    def createImages(self, squareSize):
        self.createEmptyCellImage(squareSize)
        self.createPlayerImage(squareSize, "red", "player1.png")
        self.createPlayerImage(squareSize, "blue", "player2.png")

    def createEmptyCellImage(self, squareSize):
        img = Image.new("RGBA", (squareSize+6, squareSize+6), (255, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.line((img.size[0]/2, 0, img.size[0]/2, img.size[1]), fill="black")
        draw.line((0, img.size[1]/2, img.size[0], img.size[1]/2), fill="black")
        img.save("emptyCell.png", "PNG")

    def createPlayerImage(self, squareSize, colour, name):
        img = Image.new("RGBA", (squareSize+6, squareSize+6), (255, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.line((img.size[0]/2, 0, img.size[0]/2, img.size[1]), fill="black")
        draw.line((0, img.size[1]/2, img.size[0], img.size[1]/2), fill="black")
        draw.ellipse((img.size[0]/4, img.size[1]/4, img.size[0]*3/4, img.size[1]*3/4), fill=colour, outline="black")
        img.save(name, "PNG")

    def getButtons(self, squareSize, gridsize):
        photoImg = PhotoImage(file="emptyCell.png")
        buttons = [[Button(self.gameFrame, width = squareSize, height = squareSize, image = photoImg, bg = "white", relief = FLAT, command = partial(self.place, y, x)) for x in range(gridsize)] for y in range(gridsize)]
        for y, buttonRow in enumerate(buttons):
            for x, button in enumerate(buttonRow):
                button.image = photoImg
                button_window = self.c.create_window(squareSize*(x+1), squareSize*(y+1), window=button)
        return buttons

    def playComputer(self):
        row, col = Ai.play(self.currGameRecord.game.board, self.currGameRecord.game.captures, self.currGameRecord.game.player)
        self.play(row, col)
        self.updateState()

    def place(self, row, col):
        if (self.currGameRecord.game.winner != Game.ONGOING) or (self.getPlayer(self.currGameRecord.game.player) == Player.COMP): return
        try:
            Game.validateRowCol(row, col, self.currGameRecord.game.board)
        except GameError as e:
            self.headLabel.config(text=f"Error: {e}. Try again.")
            self.root.after(1500, self.updateHeadLabel)
        else:
            self.play(row, col)
            self.updateState()
            if self.currGameRecord.computer and self.currGameRecord.game.winner == Game.ONGOING:
                self.root.after(1, self.playComputer)

    def updateState(self):
        self.p1CapLabel.config(text=f"Player 1 captured pairs: {len(self.currGameRecord.game.captures[Game.P1])}")
        self.p2CapLabel.config(text=f"Player 2 captured pairs: {len(self.currGameRecord.game.captures[Game.P2])}")

        for row in range(len(self.currGameRecord.game.board)):
            for col in range(len(self.currGameRecord.game.board)):
                if self.currGameRecord.game.board[row][col] == self.currentBoard[row][col]:
                    continue
                self.updateCell(row, col, self.currGameRecord.game.board[row][col])
        self.currentBoard = deepcopy(self.currGameRecord.game.board)

    def updateCell(self, row, col, piece):
        if piece == Game.EMPTY:
            filename = "emptyCell.png"
        elif piece == Game.P1:
            filename = "player1.png"
        elif piece == Game.P2:
            filename = "player2.png"
        photoImg = PhotoImage(file=filename)
        button = self.buttons[row][col]
        button.configure(image=photoImg)
        button.image = photoImg

    def displayWin(self):
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

    def updateGameFrame(self, squareSize=None, canvasSize=None, gridsize=None):
        self.c.delete("all")
        self.updateHeadLabel()
        if not self.playing:
            bgColour = "#D3D3D3"
            self.p1CapLabel.config(text="", bg=bgColour)
            self.p2CapLabel.config(text="", bg=bgColour)
            self.c = Canvas(self.gameFrame, height=self.MAX_CANVAS_SIZE, width=self.MAX_CANVAS_SIZE, bg=bgColour)
            self.c.grid(row=2, column=0)
        else:
            self.p1CapLabel.config(text="Player 1 captured pairs: 0", bg="white", fg="red")
            self.p2CapLabel.config(text="Player 2 captured pairs: 0", bg="white", fg="blue")
            self.c = Canvas(self.gameFrame, height=canvasSize, width=canvasSize, bg="white")
            self.c.grid(row=2, column=0)
            for i in range(0, canvasSize, squareSize):
                self.c.create_line([(i, 0), (i, canvasSize)])
            for i in range(0, canvasSize, squareSize):
                self.c.create_line([(0, i), (canvasSize, i)])
            self.buttons = self.getButtons(squareSize, gridsize)
            self.updateState()

    def play(self, row, col):
        self.currGameRecord.game.play(row, col)
        if self.currGameRecord.game.winner != Game.ONGOING:
            self.displayWin()

class Terminal(Ui):

    def __init__(self):
        self.__player = Player.GUEST
        self.__opponent = Player.GUEST
        self.__currGameRecord = None
        self.__currPlayers = {Game.P1: Player.GUEST, Game.P2: Player.GUEST}

    @property
    def player(self):
        return self.__player

    @player.setter
    def player(self, player):
        self.__player = player

    @property
    def opponent(self):
        return self.__opponent

    @opponent.setter
    def opponent(self, opponent):
        self.__opponent = opponent

    @property
    def currGameRecord(self):
        return self.__currGameRecord
    
    @currGameRecord.setter
    def currGameRecord(self, currGameRecord):
        self.__currGameRecord = currGameRecord

    @property
    def currPlayers(self):
        return self.__currPlayers

    def run(self):
        Database.createTables()
        self.displayMenu()

    def chooseMode(self):
        menu = """
        Please choose a game mode:
        1. Player v.s. Player
        2. Player v.s. Computer
        """
        print(menu)
        return not (self.getChoice(1, 2)%2)

    def choosePlayer(self):
        if self.player == Player.GUEST and self.opponent == Player.GUEST:
            return Game.P1
        playerTitle = "the guest" if self.player == Player.GUEST else self.player
        print(f"Would {playerTitle} like to be player 1 or 2? (1/2) ")
        inp = self.getChoice(1, 2)
        return [Game.P1, Game.P2][inp-1]

    def viewGames(self):
        games = Database.loadAllGames(self.player)
        if not games:
            print("There are no games to view.")
        else:
            for i, gameRecord in enumerate(games):
                print(f"{i+1}. {self.gameString(gameRecord)}")
            menu = """
            Choose an option:
            1. Load game
            2. Delete game
            3. Go back
            """
            print(menu)
            inp = self.getChoice(1, 3)
            if inp == 1:
                self.loadGame()
            elif inp == 2:
                self.deleteGame(games)

    def playGame(self):
        compMode = self.chooseMode()
        self.currGameRecord = GameRecord(game=Game(19), computer=compMode)
        if not compMode:
            self.opponent = Player.GUEST
            menu = """
            The other player will:
            1. Play as a guest
            2. Login
            """
            print(menu)
            if self.getChoice(1, 2) == 2:
                self.login(Player.OPP)
        else:
            self.opponent = Player.COMP
        player = self.choosePlayer()
        otherPlayer = Game.P2 if player == Game.P1 else Game.P1
        self.currPlayers[player] = self.player
        self.currPlayers[otherPlayer] = self.opponent
        print("Enter moves as the row immediately followed by the column, e.g. 3A or 3a.")
        self.play()

    def displayMenu(self):
        guestMethods = {1: self.playGame, 2: lambda: self.login(Player.MAIN), 3: self.createAccount, 4: quit}
        memberMethods = {1: self.playGame, 2: self.viewGames, 3: self.logout, 4: quit}

        while 1:

            guestMenu = """
            Welcome to Pente!

            Choose an option:
            1. Play new game
            2. Login
            3. Create Account
            4. Quit
            """

            memberMenu = f"""
            Welcome to Pente {self.player}!

            Choose an option:
            1. Play new game
            2. View games
            3. Logout
            4. Quit
            """

            if self.player == Player.GUEST:
                print(guestMenu)
                inp = self.getChoice(1, 4)
                guestMethods[inp]()
            else:
                print(memberMenu)
                inp = self.getChoice(1, 4)
                memberMethods[inp]()

    def getYesNo(self, msg):
        inp = input(msg)
        while inp not in ["y", "n"]:
            inp = input("Invalid choice. Please enter y or n: ")
        if inp == "y":
            return True
        return False

    def getChoice(self, lower, upper):
        while 1:
            try:
                inp = int(input("> "))
            except:
                print("That is not a valid choice. Please try again.")
                continue
            if lower <= inp <= upper:
                return inp
            print("That is not a valid choice. Please try again.")

    def login(self, player):
        while 1:
            username = input("Username: ")
            if player == Player.OPP and self.player == username:
                if self.getYesNo("That player is already logged in. Try again? (y/n) "):
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
            elif not self.getYesNo("Username or password incorrect. Try again? (y/n) "):
                return

    def logout(self):
        self.player = Player.GUEST
        print("Logout successful.")

    def createAccount(self):
        while 1:
            username = input("Enter username: ")
            if not Database.isUniqueUsername(username):
                if self.getYesNo("Sorry, that username has already been taken. Try again? (y/n) "):
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
            elif not self.getYesNo("Passwords do not match. Try again? (y/n) "):
                return

    def printState(self, board, captures):
        boardsize = len(board)
        boardString = "Board:\n\n"
        boardString += "   " + " ".join([chr(65+i) for i in range(boardsize)]) + "\n"
        for row in range(boardsize):
            space = " " if row+1 < 10 else ""
            boardString += space + str(row+1) + " "
            for col in range(boardsize):
                piece = board[row][col]
                if piece == Game.EMPTY:
                    boardString += "+"
                elif piece == Game.P1:
                    boardString += f"{Fore.RED}O{Style.RESET_ALL}"
                else:
                    boardString += f"{Fore.BLUE}O{Style.RESET_ALL}"
                if col < boardsize-1:
                    boardString += "-"
            boardString += "\n"
        boardString += f"\nPlayer 1 captured pairs: {len(captures[Game.P1])}\n"
        boardString += f"Player 2 captured pairs: {len(captures[Game.P2])}\n"
        print(boardString)

    def gameString(self, gameRecord):
        players = [Database.getPlayerGameUsername(gameRecord.id, Game.P1), Database.getPlayerGameUsername(gameRecord.id, Game.P2)]
        for i in range(2):
            if players[i] == False:
                if gameRecord.computer:
                    players[i] = "computer"
                else:
                    players[i] = "guest"
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
        
        return f"{gameRecord.name:25s}{mode:25s}saved on {whenSaved:25s}status: {status}"

    def getRowCol(self, board):
        while True:
            move = input("\nEnter move: ")
            if len(move) == 0:
                print("\nPlease enter a move.")
                continue
            row, col = move[:-1], move[-1]
            try:
                row = int(row)
            except:
                print("\nThat is an invalid move. Please try again.")
                continue
            if 97 <= ord(col) <= 122:
                col = chr(ord(col)-32)
            elif not (65 <= ord(col) <= 90):
                print("\nThat is an invalid move. Please try again.")
                continue
            row -= 1
            col = ord(col)-65
            try:
                Game.validateRowCol(row, col, board)
            except GameError as err:
                print(f"\nError: {err}. Please try again.")
            else:
                return row, col

    def saveGame(self, game):
        self.currGameRecord.whenSaved, self.currGameRecord.game = datetime.now(), game
        if self.currGameRecord.id != -1:
            Database.updateGame(self.__currGameRecord)
        else:
            name = input("Enter name to save game as: ")
            self.currGameRecord.name = name
            Database.saveGame(self.currPlayers[Game.P1], self.currPlayers[Game.P2], self.__currGameRecord)
        print("Game saved successfully.")

    def loadGame(self):
        games = Database.loadGames(self.player, Game.ONGOING)
        if not games:
            print("There are no ongoing games.")
        else:
            print("Ongoing games:")
            for i, gameRecord in enumerate(games):
                print(f"{i+1}. {self.gameString(gameRecord)}")
            print("Select a game (e.g. 1, 2...)")
            inp = self.getChoice(1, i+1)
            self.__currGameRecord = games[inp-1]
            self.play()

    def deleteGame(self, games):
        print("Which game would you like to delete? (e.g. 1, 2...)")
        inp = self.getChoice(1, len(games))
        Database.deleteGame(games[inp-1].id)
        print(f"Game '{games[inp-1].name}' successfully deleted.")

    def chooseContinue(self, game):
        while 1:
            inp = input("Press q to quit, u to undo, and any other key to continue > ")
            if inp == "q":
                nonGuests = [player for player in [self.player, self.opponent] if player != Player.GUEST and player != Player.COMP]
                if nonGuests:
                        if len(nonGuests) > 1:
                            playerString = f"{nonGuests[0]}'s and {nonGuests[1]}'s accounts"
                        else:
                            playerString = f"{nonGuests[0]}'s account"
                        yes = self.getYesNo(f"Would you like to save your game to {playerString}? (y/n) ")
                        if yes:
                            self.saveGame(game)
                return False
            elif inp == "u":
                try:
                    game.undo()
                except GameError as e:
                    print(f"Error: {e}")
                else:
                    self.printState(game.board, game.captures)
            else:
                return True

    def play(self):
        game = self.currGameRecord.game
        print("\nTo enter a move, enter the row followed by the column e.g. 1A or 1a.\n")
        while game.winner == Game.ONGOING:
            self.printState(game.board, game.captures)
            if not self.chooseContinue(game): return
            playerStr = "Player 1 to play" if game.player == Game.P1 else "Player 2 to play"
            print(playerStr)
            if self.currPlayers[game.player] == Player.COMP:
                row, col = Ai.play(game.board, game.captures, game.player)
            else:
                row, col = self.getRowCol(game.board)
            game.play(row, col)
        self.printState(game.board, game.captures)
        if game.winner == Game.P1:
            print("Player 1 has won!")
        elif game.winner == Game.P2:
            print("Player 2 has won!")
        else:
            print("It is a draw.")

class Player(Enum):
    MAIN = auto()
    OPP = auto()
    GUEST = auto()
    COMP = auto()

if __name__ == "__main__":
    pass