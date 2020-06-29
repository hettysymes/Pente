from copy import deepcopy
from itertools import product

class GameError(Exception):
    pass

class Game:

    P1 = "P1"
    P2 = "P2"
    EMPTY = "EMPTY"
    DRAW = "DRAW"
    ONGOING = "ONGOING"

    def __init__(self, boardsize):
        self.__board = [[Game.EMPTY for _ in range(boardsize)] for _ in range(boardsize)]
        self.__captures = {Game.P1: [], Game.P2: []}
        self.__winner = Game.ONGOING
        self.__player = Game.P1

    @property
    def board(self):
        return self.__board

    @board.setter
    def board(self, board):
        self.__board = board

    @property
    def captures(self):
        return self.__captures

    @captures.setter
    def captures(self, captures):
        self.__captures = captures

    @property
    def winner(self):
        return self.__winner

    @winner.setter
    def winner(self, winner):
        self.__winner = winner

    @property
    def player(self):
        return self.__player
    
    @player.setter
    def player(self, player):
        self.__player = player

    @staticmethod
    def inRow(board, row, col, pattern):
        validProducts = Game.getValidProducts([(0,1), (1,1), (1,0), (1,-1)], len(pattern), row, col, len(board))
        for rc in validProducts:
            pieces = [board[row+i*rc[0]][col+i*rc[1]] for i in range(1, len(pattern)+1)]
            if pieces == pattern:
                return True
        return False

    @staticmethod
    def newState(board, captures, player, row, col):
        board, captures = deepcopy(board), deepcopy(captures)
        board[row][col] = player
        opponent = Game.P2 if player == Game.P1 else Game.P1
        pattern = [opponent, opponent, player]
        products = list(product([0, 1, -1], repeat=2))
        products.remove((0, 0))
        validProducts = Game.getValidProducts(products, 3, row, col, len(board))
        for rc in validProducts:
            pieces = [board[row+i*rc[0]][col+i*rc[1]] for i in range(1, 4)]
            if pieces == pattern:
                captures[player].append([(row+i*rc[0], col+i*rc[1]) for i in range(1, 3)])
                for i in range(1, 3):
                    board[row+i*rc[0]][col+i*rc[1]] = Game.EMPTY
        return board, captures, opponent

    @staticmethod
    def getWinner(board, captures):
        for player in [Game.P1, Game.P2]:
            if len(captures[player]) >= 5:
                return player
        fullboard = True
        boardsize = len(board)
        for row in range(boardsize):
            for col in range(boardsize):
                player = board[row][col]
                if player == Game.EMPTY:
                    fullboard = False
                    continue
                if Game.inRow(board, row, col, [player]*4):
                    return player
        if fullboard:
            return Game.DRAW
        return Game.ONGOING

    @staticmethod
    def getValidProducts(products, size, row, col, boardsize):
        validProducts = []
        for rc in products:
            if not Game.offBoard(row + rc[0]*size, col + rc[1]*size, boardsize):
                validProducts.append(rc)
        return validProducts

    @staticmethod
    def offBoard(row, col, boardsize):
        return not ((0 <= row < boardsize) and (0 <= col < boardsize))

    @staticmethod
    def validateRowCol(row, col, board):
        if Game.offBoard(row, col, len(board)):
            raise GameError("Move is off the board")
        elif board[row][col] != Game.EMPTY:
            raise GameError("Position is not empty")        

    def play(self, row, col):
        self.board, self.captures, self.player = Game.newState(self.board, self.captures, self.player, row, col)
        self.winner = Game.getWinner(self.board, self.captures)

if __name__ == "__main__":
    pass

