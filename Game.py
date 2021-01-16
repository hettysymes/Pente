from copy import deepcopy
from itertools import product

# Defines an exception that is raised when an error in the game occurs.
class GameError(Exception):
    pass

# The Game class contains all properties, game constants, and methods required by a game.
class Game:

    P1 = 1
    P2 = 2
    EMPTY = 3
    DRAW = 4
    ONGOING = 5

    def __init__(self, boardsize):
        self._board = [[Game.EMPTY for _ in range(boardsize)] for _ in range(boardsize)]
        self._captures = {Game.P1: [], Game.P2: []}
        self._winner = Game.ONGOING
        self._player = Game.P1
        self._moveStack = MoveStack()

    @property
    def board(self):
        return self._board

    @board.setter
    def board(self, board):
        self._board = board

    @property
    def captures(self):
        return self._captures

    @captures.setter
    def captures(self, captures):
        self._captures = captures

    @property
    def winner(self):
        return self._winner

    @winner.setter
    def winner(self, winner):
        self._winner = winner

    @property
    def player(self):
        return self._player
    
    @player.setter
    def player(self, player):
        self._player = player

    @property
    def moveStack(self):
        return self._moveStack

    # The function is given a board, starting coordinate, and pattern. 
    # The inRow function checks if the pattern is found in the E, SE, S and SW directions from the coordinate.
    @staticmethod
    def inRow(board, row, col, pattern):
        validProducts = Game.getValidProducts([(0,1), (1,1), (1,0), (1,-1)], len(pattern), row, col, len(board))
        for rc in validProducts:
            pieces = [board[row+i*rc[0]][col+i*rc[1]] for i in range(1, len(pattern)+1)]
            if pieces == pattern:
                return True
        return False

    # Given a game state and a move to play, the newState function returns the new game state as a result of playing the move.
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

    # Given a board and captures, the getWinner function returns the player number who won if there's a winner, or Game.DRAW or Game.ONGOING otherwise.
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

    # Given a list of tuples representing directions in which to search for a pattern, returns the valid directions which don't take the search off the board.
    @staticmethod
    def getValidProducts(products, size, row, col, boardsize):
        validProducts = []
        for rc in products:
            if not Game.offBoard(row + rc[0]*size, col + rc[1]*size, boardsize):
                validProducts.append(rc)
        return validProducts

    # Given a coordinate and a boardsize, returns True if the coordinate is on the board or False otherwise.
    @staticmethod
    def offBoard(row, col, boardsize):
        return not ((0 <= row < boardsize) and (0 <= col < boardsize))

    # Given a coordinate of a potential new move on a board, the validateRowCol function raises a gameError if the move is not valid.
    @staticmethod
    def validateRowCol(row, col, board):
        if Game.offBoard(row, col, len(board)):
            raise GameError("Move is off the board")
        elif board[row][col] != Game.EMPTY:
            raise GameError("Position is not empty")

    # Given a move, the game goes onto its new state by calling the newState function, and updates the winner.
    # The move and the state of the captures are pushed onto the moveStack.
    def play(self, row, col):
        self.board, self.captures, self.player = Game.newState(self.board, self.captures, self.player, row, col)
        self.winner = Game.getWinner(self.board, self.captures)
        self.moveStack.push(deepcopy(self.captures), row, col)

    # Undoes the last move played.
    def undo(self):
        row, col = self.moveStack.pop()[1:]
        if self.moveStack.isEmpty():
            captures = {Game.P1: [], Game.P2: []}
        else:
            captures = self.moveStack.peek()[0]
        otherPlayer = self.player
        self.player = Game.P1 if self.player == Game.P2 else Game.P2
        while len(captures[self.player]) != len(self.captures[self.player]):
            lastPair = self.captures[self.player].pop()
            for cap in lastPair:
                self.board[cap[0]][cap[1]] = otherPlayer
        self.board[row][col] = Game.EMPTY

    # Given a Pente move, boardsize, and whether the move made any captures, the function will return the Pente notation of the move.
    @staticmethod
    def getPenteMoveNotation(row, col, boardsize, capturesMade):
        centre = boardsize//2
        changeInY, changeInX = row-centre, col-centre
        if changeInX == 0 and changeInY == 0:
            string = "0"
        else:
            if changeInX > 0:
                xExp = f"R{changeInX}"
            elif changeInX < 0:
                xExp = f"L{-changeInX}"
            else:
                xExp = ""
            if changeInY > 0:
                yExp = f"D{changeInY}"
            elif changeInY < 0:
                yExp = f"U{-changeInY}"
            else:
                yExp = ""
            string = xExp + yExp
        if capturesMade: string += "*"
        return string

# The MoveStack class is implemented as a stack used to store the captures and moves played in the game.
class MoveStack:

    def __init__(self):
        self._stack = []

    # Returns True if the stack is empty and False otherwise.
    def isEmpty(self):
        return len(self._stack) == 0

    # Given a dictionary of captures and a move, the push function pushes this together onto the top of the stack.
    def push(self, captures, row, col):
        self._stack.append((captures, row, col))

    # Removes the top item in the stack and returns it, or raises a game error if the stack is empty.
    def pop(self):
        if self.isEmpty():
            raise GameError("There have been no previous moves")
        return self._stack.pop()
    
    # Returns the top item in the stack without removing it, or raises a game error if the stack is empty.
    def peek(self):
        if self.isEmpty():
            raise GameError("There have been no previous moves")
        return self._stack[-1]

# The GameRecord class defines the datatype which all game information is stored as in the datatbase.
class GameRecord:

    def __init__(self, id=-1, name=-1, whenSaved=-1, game=-1, mode=-1):
        self.id = id
        self.name = name
        self.whenSaved = whenSaved
        self.game = game
        self.mode = mode

