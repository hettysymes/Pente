from abc import ABC, abstractmethod
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
        self.root = Tk()
        self.gridsize = 19
        self.canvasSize = 19*40
        self.squareSize = int(self.canvasSize/(self.gridsize+1))
        self.createImages()
        self.p1CapLabel = Label(self.root, text="Player 1 captured pairs: 0", bg="white", fg="red", font=("Helvetica", 18))
        self.p1CapLabel.grid(row=0, column=0, sticky="NESW")
        self.p2CapLabel = Label(self.root, text="Player 2 captured pairs: 0", bg="white", fg="blue", font=("Helvetica", 18))
        self.p2CapLabel.grid(row=2, column=0, sticky="NESW")
        self.c = Canvas(self.root, height=self.canvasSize, width=self.canvasSize, bg='white')
        self.c.grid(row=1, column=0)
        self.buttons = self.getButtons()
        self.c.bind('<Configure>', self.createGrid)
        self.game = Game(19)
        self.stop = False

    def run(self):
        self.root.mainloop()

    def createImages(self):
        self.createEmptyCellImage()
        self.createPlayerImage("red", "player1.png")
        self.createPlayerImage("blue", "player2.png")

    def createEmptyCellImage(self):
        img = Image.new('RGBA', (self.squareSize+6, self.squareSize+6), (255, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.line((img.size[0]/2, 0, img.size[0]/2, img.size[1]), fill="black")
        draw.line((0, img.size[1]/2, img.size[0], img.size[1]/2), fill="black")
        img.save('emptyCell.png', 'PNG')

    def createPlayerImage(self, colour, name):
        img = Image.new('RGBA', (self.squareSize+6, self.squareSize+6), (255, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.line((img.size[0]/2, 0, img.size[0]/2, img.size[1]), fill="black")
        draw.line((0, img.size[1]/2, img.size[0], img.size[1]/2), fill="black")
        draw.ellipse((img.size[0]/4, img.size[1]/4, img.size[0]*3/4, img.size[1]*3/4), fill=colour, outline="black")
        img.save(name, 'PNG')

    def getButtons(self):
        photoImg = PhotoImage(file="emptyCell.png")
        buttons = [[Button(self.root, width = self.squareSize, height = self.squareSize, image = photoImg, bg = "white", relief = FLAT, command = partial(self.place, (x, y))) for x in range(self.gridsize)] for y in range(self.gridsize)]
        for y, buttonRow in enumerate(buttons):
            for x, button in enumerate(buttonRow):
                button.image = photoImg
                button_window = self.c.create_window(self.squareSize*(x+1), self.squareSize*(y+1), window=button)
        return buttons

    def place(self, coords):
        if self.stop: return
        row, col = coords
        try:
            Game.validateRowCol(row, col, self.game.board)
        except GameError as e:
            print(f"Error: {e}")
            print("Try again")
        else:
            self.play(row, col)
            self.updateState()

    def updateState(self):
        if not self.stop:
            self.p1CapLabel.config(text=f"Player 1 captured pairs: {len(self.game.captures[Game.P1])}")
            self.p2CapLabel.config(text=f"Player 2 captured pairs: {len(self.game.captures[Game.P2])}")

        for row in range(len(self.game.board)):
            for col in range(len(self.game.board)):
                self.updateCell(row, col, self.game.board[row][col])

    def updateCell(self, row, col, piece):
        if piece == Game.EMPTY:
            filename = "emptyCell.png"
        elif piece == Game.P1:
            filename = "player1.png"
        elif piece == Game.P2:
            filename = "player2.png"
        photoImg = PhotoImage(file=filename)
        button = self.buttons[col][row]
        button.configure(image=photoImg)
        button.image = photoImg

    def displayWin(self):
        if self.game.winner == Game.P1:
            msg = "Player 1 WON!"
            colour = "red"
        elif self.game.winner == Game.P2:
            msg = "Player 2 WON!"
            colour = "blue"
        else:
            msg = "It is a draw."
            colour = "gray"

        self.p1CapLabel.config(text=msg, fg=colour)
        self.p2CapLabel.config(text=msg, fg=colour)

    def createGrid(self, event=None):
        w = self.c.winfo_width()
        h = self.c.winfo_height()

        for i in range(0, w, self.squareSize):
            self.c.create_line([(i, 0), (i, h)])

        for i in range(0, h, self.squareSize):
            self.c.create_line([(0, i), (w, i)])

    def play(self, row, col):
        self.game.play(row, col)
        if self.game.winner != Game.ONGOING:
            if self.game.winner == Game.P1:
                print("Player 1 has won!")
            elif self.game.winner == Game.P2:
                print("Player 2 has won!")
            else:
                print("It is a draw.")
            self.displayWin()
            self.stop = True

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
        whenSaved = datetime.strftime(gameRecord.whenSaved, "%m/%d/%Y, %H:%M:%S")
        if gameRecord.winner == Game.P1:
            status = "P1 won"
        elif gameRecord.winner == Game.P2:
            status = "P2 won"
        elif gameRecord.winner == Game.DRAW:
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
        self.currGameRecord.whenSaved, self.currGameRecord.game, self.currGameRecord.winner = datetime.now(), game, game.winner
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