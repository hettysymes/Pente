from abc import ABC, abstractmethod
from Game import Game, GameError
from colorama import Fore, Style

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
        pass

    def run(self):
        self.play()

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
        print("To enter a move, enter the row followed by the column e.g. 1A or 1a.\n")
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

if __name__ == "__main__":
    pass