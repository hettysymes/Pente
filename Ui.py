from abc import ABC, abstractmethod
from Game import Game, GameError
from colorama import Fore, Style
from enum import Enum, auto
from datetime import datetime
import Database

class Ui (ABC):

    @abstractmethod
    def run(self):
        raise NotImplementedError

class Gui(Ui):

    def __init__(self):
        pass

    def run(self):
        pass

class Terminal(Ui):

    def __init__(self):
        self.__player = Player.GUEST
        self.__opponent = Player.GUEST

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

    def run(self):
        Database.createTables()
        self.displayMenu()

    def playGame(self):
        menu = """
        The other player will:
        1. Play as a guest
        2. Login
        """
        print(menu)
        if self.getChoice(1, 2) == 2:
            self.login(Player.OPP)
        self.play()

    def displayMenu(self):
        guestMethods = {1: self.playGame, 2: lambda: self.login(Player.MAIN), 3: self.createAccount, 4: quit}
        memberMethods = {1: self.playGame, 2: self.logout, 3: quit}

        while 1:

            guestMenu = """
            Welcome to Pente!

            Choose an option:
            1. Play
            2. Login
            3. Create Account
            4. Quit
            """

            memberMenu = f"""
            Welcome to Pente {self.player}!

            Choose an option:
            1. Play
            2. Logout
            3. Quit
            """

            if self.player == Player.GUEST:
                print(guestMenu)
                inp = self.getChoice(1, 4)
                guestMethods[inp]()
            else:
                print(memberMenu)
                inp = self.getChoice(1, 3)
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

    def play(self):
        game = Game(19)
        print("\nTo enter a move, enter the row followed by the column e.g. 1A or 1a.\n")
        while game.winner == Game.ONGOING:
            self.printState(game.board, game.captures)
            playerStr = "Player 1 to play" if game.player == Game.P1 else "Player 2 to play"
            print(playerStr)
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