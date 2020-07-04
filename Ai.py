from Game import Game
import Ui
from math import inf
from operator import itemgetter
from itertools import product

class Node:

    def __init__(self, row, col, root=False):
        self.__row = row
        self.__col = col
        self.__children = []
        self.__root = root

    @property
    def row(self):
        return self.__row

    @property
    def col(self):
        return self.__col

    @property
    def children(self):
        return self.__children

    @property
    def root(self):
        return self.__root

    def addChild(self, row, col):
        self.__children.append(Node(row, col))

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

def getValue(board, captures):
    p1lines = getNumberOfLines(board, [1, 2, 3, 4], Game.P1)
    p2lines = getNumberOfLines(board, [1, 2, 3, 4], Game.P2)
    val = 300*len(captures[Game.P1]) - 300*len(captures[Game.P2])
    val += 10*p1lines[0] - 10*p2lines[0]
    val += 20*p1lines[1] - 20*p2lines[1]
    val += 50*p1lines[2] - 50*p2lines[2]
    val += 999999*p1lines[3] - 999999*p2lines[3]
    return val

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

def minimax(board, captures, player, node, depth, alpha=(-inf,), beta=(inf,)):
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
        success = False
        for row in range(len(board)):
            for col in range(len(board)):
                if board[row][col] == Game.EMPTY:
                    nextTo.append((row, col))
                    success = True
                    break
            if success: break
    for row, col in nextTo:
        node.addChild(row, col)

    if player == Game.P1:
        maxEval = (-inf, node.children[0].row, node.children[0].col)
        for child in node.children:
            tempBoard, tempCaptures, tempPlayer = Game.newState(board, captures, player, child.row, child.col)
            eval = minimax(tempBoard, tempCaptures, tempPlayer, child, depth-1, alpha, beta)
            maxEval = max([maxEval, eval], key=itemgetter(0))
            alpha = max([alpha, eval], key=itemgetter(0))
            if alpha[0] >= beta[0]:
                break
        return (maxEval[0], node.row, node.col) if not node.root else maxEval
    else:
        minEval = (inf, node.children[0].row, node.children[0].col)
        for child in node.children:
            tempBoard, tempCaptures, tempPlayer = Game.newState(board, captures, player, child.row, child.col)
            eval = minimax(tempBoard, tempCaptures, tempPlayer, child, depth-1, alpha, beta)
            minEval = min([minEval, eval], key=itemgetter(0))
            beta = min([beta, eval], key=itemgetter(0))
            if beta[0] <= alpha[0]:
                break
        return (minEval[0], node.row, node.col) if not node.root else minEval

def play(board, captures, player):
    root = Node(None, None, root=True)
    DEPTH = 2
    eval = minimax(board, captures, player, root, DEPTH)
    return eval[1], eval[2]

if __name__ == "__main__":
    pass