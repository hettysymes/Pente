from Game import Game
import Ui
from math import inf
from operator import itemgetter
from itertools import product
import random

# The Node class contains all information needed about a game state used by the minimax algorithm.
class Node:

    def __init__(self, row, col, root=False):
        self._row = row
        self._col = col
        self._children = []
        self._root = root

    @property
    def row(self):
        return self._row

    @property
    def col(self):
        return self._col

    @property
    def children(self):
        return self._children

    @property
    def root(self):
        return self._root

    def addChild(self, row, col):
        self._children.append(Node(row, col))

# Returns the number of rows of pieces of a given length belonging to a certain player on a given board.
def getNumberOfLines(board, lengths, player):
    boardsize = len(board)
    totals = [0 for _ in range(len(lengths))]
    for row in range(boardsize):
        for col in range(boardsize):
            if board[row][col] == Game.EMPTY:
                for i, length in enumerate(lengths):
                    if Game.inRow(board, row, col, [player]*length+[Game.EMPTY]):
                        totals[i] += 1
    return totals

def getNumberOfCaptureLines(board, player):
    total = 0
    opp = Game.P1 if player == Game.P2 else Game.P2
    boardsize = len(board)
    for row in range(boardsize):
        for col in range(boardsize):
            if board[row][col] == player and Game.inRow(board, row, col, [opp, opp, Game.EMPTY]):
                total += 1
            elif board[row][col] == Game.EMPTY and Game.inRow(board, row, col, [opp, opp, player]):
                total += 1
    return total

def getNumberOfWinOpportunities(board, captures, player, numberOfCaptureLines):
    winOpportunities = 0
    if numberOfCaptureLines + len(captures[player]) >= 5:
        winOpportunities += len(captures[player]) - numberOfCaptureLines
    for row in range(len(board)):
        for col in range(len(board)):
            if board[row][col] not in [player, Game.EMPTY]:
                continue
            validProducts = Game.getValidProducts([(0,1), (1,1), (1,0), (1,-1)], 4, row, col, len(board))
            for rc in validProducts:
                pieces = [board[row+i*rc[0]][col+i*rc[1]] for i in range(1, 5)]
                if board[row][col] == player and (pieces.count(player)==3 and pieces.count(Game.EMPTY)==1):
                    winOpportunities += 1
                elif board[row][col] == Game.EMPTY and (pieces.count(player)==4):
                    winOpportunities += 1
    return winOpportunities

# Returns the coordinates on the board which are next to an existing piece on the board.
def getNextTo(board):
    nextTo = set()
    products = list(product([0, 1, -1], repeat=2))
    products.remove((0, 0))
    for row in range(len(board)):
        for col in range(len(board)):
            if board[row][col] == Game.EMPTY:
                continue
            validProducts = Game.getValidProducts(products, 1, row, col, len(board))
            for rc in validProducts:
                foundPiece = board[row+rc[0]][col+rc[1]]
                if foundPiece == Game.EMPTY:
                    nextTo.add((row+rc[0], col+rc[1]))
    return list(nextTo)

def pickRandomMove(board):
    emptyCoords = []
    for row in range(len(board)):
        for col in range(len(board)):
            if board[row][col] == Game.EMPTY:
                emptyCoords.append((row, col))
    return random.choice(emptyCoords)

# Returns the value of a game state given the board and captures.
def getValue(board, captures):
    p1lines = getNumberOfLines(board, [1, 2, 3], Game.P1)
    p2lines = getNumberOfLines(board, [1, 2, 3], Game.P2)
    p1CaptureLines = getNumberOfCaptureLines(board, Game.P1)
    p2CaptureLines = getNumberOfCaptureLines(board, Game.P2)
    val = 30000*(len(captures[Game.P1]) - len(captures[Game.P2]))
    val += 10*(p1lines[0] - p2lines[0])
    val += 20*(p1lines[1] - p2lines[1])
    val += 50*(p1lines[2] - p2lines[2])
    val += 10000*(p1CaptureLines - p2CaptureLines)
    val += 999999999999*(getNumberOfWinOpportunities(board, captures, Game.P1, p1CaptureLines) - getNumberOfWinOpportunities(board, captures, Game.P2, p2CaptureLines))
    return val

def getImmediateMove(board, captures, player):
    move = [None, 0]
    opp = Game.P1 if player == Game.P2 else Game.P2
    for row in range(len(board)):
        for col in range(len(board)):
            if board[row][col] != Game.EMPTY:
                continue
            tempBoard, tempCaptures = Game.newState(board, captures, player, row, col)[:-1]
            if Game.getWinner(tempBoard, tempCaptures) == player:
                return True, (row, col)
            elif len(tempCaptures[player]) > len(captures[player]) and move[1] < 1:
                move = [(row, col), 1]
            tempBoard, tempCaptures = Game.newState(board, captures, opp, row, col)[:-1]
            if Game.getWinner(tempBoard, tempCaptures) == opp and move[1] < 2:
                move = [(row, col), 2]
            elif len(tempCaptures[opp]) > len(captures[opp]) and move[1] < 1:
                move = [(row, col), 1]
    if move[0] != None:
        return True, move[0]
    return False, ()

# Performs the minimax algorithm to a specified depth, and returns the calculated move for the AI.
def minimax(board, captures, player, node, depth, alpha=(-inf,), beta=(inf,), movesToAnalyse=3):

    winner = Game.getWinner(board, captures)
    if winner != Game.ONGOING:
        if winner == Game.P1:
            val = inf
        elif winner == Game.P2:
            val = -inf
        elif winner == Game.DRAW:
            val = 0
        return (val, node.row, node.col)

    if depth == 0:
        tempBoard, tempCaptures = Game.newState(board, captures, player, node.row, node.col)[:-1]
        return (getValue(tempBoard, tempCaptures), node.row, node.col)
    
    nextTo = getNextTo(board)
    if len(nextTo) == 0:
        nextTo.append(pickRandomMove(board))
    for row, col in nextTo:
        node.addChild(row, col)

    if player == Game.P1:
        maxEval = (-inf, node.children[0].row, node.children[0].col)
        childrenValues = []
        for child in node.children:
            tempBoard, tempCaptures, tempPlayer = Game.newState(board, captures, player, child.row, child.col)
            childrenValues.append([getValue(tempBoard, tempCaptures), tempBoard, tempCaptures, child])
        childrenValues.sort(key=itemgetter(0))
        for _ in range(movesToAnalyse):
            if len(childrenValues) == 0: break
            value, tempBoard, tempCaptures, child = childrenValues.pop()
            eval = minimax(tempBoard, tempCaptures, tempPlayer, child, depth-1, alpha, beta)
            maxEval = max([maxEval, eval], key=itemgetter(0))
            alpha = max([alpha, eval], key=itemgetter(0))
            if alpha[0] >= beta[0]:
                break
        return (maxEval[0], node.row, node.col) if not node.root else maxEval
    else:
        minEval = (inf, node.children[0].row, node.children[0].col)
        childrenValues = []
        for child in node.children:
            tempBoard, tempCaptures, tempPlayer = Game.newState(board, captures, player, child.row, child.col)
            childrenValues.append([getValue(tempBoard, tempCaptures), tempBoard, tempCaptures, child])
        childrenValues.sort(key=itemgetter(0), reverse=True)
        for _ in range(movesToAnalyse):
            if len(childrenValues) == 0: break
            value, tempBoard, tempCaptures, child = childrenValues.pop()
            eval = minimax(tempBoard, tempCaptures, tempPlayer, child, depth-1, alpha, beta)
            minEval = min([minEval, eval], key=itemgetter(0))
            beta = min([beta, eval], key=itemgetter(0))
            if beta[0] <= alpha[0]:
                break
        return (minEval[0], node.row, node.col) if not node.root else minEval

# Given a board, captures, and player the play function gets a move from the minimax algorithm for the AI to play and returns it.
def play(board, captures, player, difficulty):
    if difficulty == 1:
        return pickRandomMove(board)
    elif difficulty == 2:
        canMake, move = getImmediateMove(board, captures, player)
        if canMake:
            return move
        else:
            return pickRandomMove(board)
    else:
        root = Node(None, None, root=True)
        DEPTH = 2
        eval = minimax(board, captures, player, root, DEPTH)
        return eval[1], eval[2]

if __name__ == "__main__":
    pass