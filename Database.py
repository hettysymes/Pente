import sqlite3
import pickle
from datetime import datetime
import Ui
from Game import Game, GameRecord

class HashTable:

    def __init__(self):
        self.__SIZE = 50
        self.__hashTable = [[] for _ in range(self.__SIZE)]

    def __hashFunction(self, key):
        total = 0
        for char in key:
            total += 3*ord(char)
        return total % self.__SIZE

    def addToTable(self, username, password):
        passwordHash = self.__hashFunction(password)
        self.__hashTable[passwordHash].append(username)

    def isInTable(self, username, password):
        passwordHash = self.__hashFunction(password)
        return username in self.__hashTable[passwordHash]

def connect():
    conn = sqlite3.connect('PenteDatabase.db')
    c = conn.cursor()
    return conn, c

def close(conn):
    conn.commit()
    conn.close()

def createTables():
    playerSQL = """
    CREATE TABLE Player(
    username TEXT PRIMARY KEY,
    whenSaved TEXT NOT NULL
    );"""

    hashtableSQL = """
    CREATE TABLE HashTable(
    id INTEGER PRIMARY KEY,
    hashTable BLOB NOT NULL
    );"""

    gameSQL = """
    CREATE TABLE Game(
	id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
	whenSaved TEXT NOT NULL,
	game BLOB NOT NULL,
    winner TEXT NOT NULL,
    computer INTEGER NOT NULL
    );"""

    playergameSQL = """
    CREATE TABLE PlayerGame(
	id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    gameId INTEGER NOT NULL,
    playerNo INTEGER NOT NULL
    );"""

    conn, c = connect()
    tableSQLDict = {"Player": playerSQL, "HashTable": hashtableSQL, "Game": gameSQL, "PlayerGame": playergameSQL}
    for tableName, sql in tableSQLDict.items():
        if not tableExists(tableName):
            c.execute(sql)
            if tableName == "HashTable":
                hashtable = pickle.dumps(HashTable())
                recordSQL = """
                INSERT INTO HashTable(id, hashTable)
                VALUES(1, ?);
                """
                editTable(recordSQL, (hashtable,))
    close(conn)

def tableExists(tableName):
    existsQuery = f"SELECT count(name) FROM sqlite_master WHERE type='table' AND name='{tableName}';"
    conn, c = connect()
    c.execute(existsQuery)
    if c.fetchone()[0]==1: 
	    res = True
    else:
	    res = False
    close(conn)
    return res

def editTable(recordSQL, values, getId=False):
    conn, c = connect()
    c.execute(recordSQL, values)
    if getId:
        id = c.lastrowid
    else:
        id = None
    close(conn)
    return id

def getRecords(recordQuery, values):
    conn, c = connect()
    c.execute(recordQuery, values)
    res = c.fetchall()
    close(conn)
    return res

def loadHashTable():
    recordQuery = """
    SELECT hashtable
    FROM HashTable
    WHERE id = 1;
    """
    [hashtable] = getRecords(recordQuery, ())[0]
    return pickle.loads(hashtable)

def saveHashTable(hashtable):
    updateQuery = f"""
    UPDATE HashTable
    SET hashTable = ?
    WHERE id = 1;
    """
    editTable(updateQuery, (pickle.dumps(hashtable),))

def checkPassword(username, password):
    hashtable = loadHashTable()
    return hashtable.isInTable(username, password)

def addPassword(username, password):
    hashtable = loadHashTable()
    hashtable.addToTable(username, password)
    saveHashTable(hashtable)

def savePlayer(username, password, whenSaved):
    addPassword(username, password)
    whenSaved = datetime.strftime(whenSaved, "%d/%m/%Y, %H:%M:%S")
    recordSQL = """
    INSERT INTO Player(username, whenSaved)
    VALUES(?, ?);
    """
    editTable(recordSQL, (username, whenSaved))

def getPlayer(username):
    recordSQL = """
    SELECT whenSaved
    FROM Player
    WHERE username = ?;
    """
    [whenSaved] = getRecords(recordSQL, (username,))[0]
    return [whenSaved]

def isUniqueUsername(username):
    recordSQL = """
    SELECT username
    FROM Player
    WHERE username = ?;
    """
    players = getRecords(recordSQL, (username,))
    return players == []

def saveGame(username1, username2, gameRecord):
    name = gameRecord.name
    whenSaved = gameRecord.whenSaved.strftime("%d/%m/%Y, %H:%M:%S")
    game = pickle.dumps(gameRecord.game)
    winner = gameRecord.game.winner
    computer = gameRecord.computer

    recordSQL = """
    INSERT INTO Game(name, whenSaved, game, winner, computer)
    VALUES(?, ?, ?, ?, ?);
    """
    
    gameId = editTable(recordSQL, (name, whenSaved, game, winner, computer), getId=True)

    invalidUsernames = [Ui.Player.GUEST, Ui.Player.COMP]
    if username1 not in invalidUsernames:
        savePlayerGame(username1, gameId, Game.P1)
    if username2 not in invalidUsernames:
        savePlayerGame(username2, gameId, Game.P2)

def updateGame(gameRecord):
    whenSaved = gameRecord.whenSaved.strftime("%d/%m/%Y, %H:%M:%S")
    game = pickle.dumps(gameRecord.game)
    winner = gameRecord.game.winner
    id = gameRecord.id
    recordSQL = """
    UPDATE Game
    SET whenSaved = ?, game = ?, winner = ?
    WHERE id = ?;
    """
    editTable(recordSQL, (whenSaved, game, winner, id))

def parseGames(games):
    parsedGames = []
    for game in games:
        g = list(game) #[id, name, whenSaved, game, winner, computer]
        g[2] = datetime.strptime(g[2], "%d/%m/%Y, %H:%M:%S") #whenSaved
        g[3] = pickle.loads(g[3]) #game
        gameRecord = GameRecord(g[0], g[1], g[2], g[3], g[5])
        parsedGames.append(gameRecord)
    return parsedGames

def loadGames(username, winner):
    recordSQL = """
    SELECT Game.id, Game.name, Game.whenSaved, Game.game, Game.winner, Game.computer
    FROM Game
    INNER JOIN PlayerGame ON PlayerGame.gameId = Game.id
    WHERE PlayerGame.username = ? AND Game.winner = ?
    ORDER BY Game.whenSaved DESC;
    """
    games = getRecords(recordSQL, (username, winner))
    return parseGames(games)

def loadAllGames(username):
    recordSQL = """
    SELECT Game.id, Game.name, Game.whenSaved, Game.game, Game.winner, Game.computer
    FROM Game
    INNER JOIN PlayerGame ON PlayerGame.gameId = Game.id
    WHERE PlayerGame.username = ?
    ORDER BY Game.whenSaved DESC;
    """
    games = getRecords(recordSQL, (username,))
    return parseGames(games)

def getGame(id):
    recordSQL = """
    SELECT Game.id, Game.name, Game.whenSaved, Game.game, Game.winner, Game.computer
    FROM Game
    WHERE id = ?;
    """
    game = getRecords(recordSQL, (id,))
    return parseGames(game)[0]

def savePlayerGame(username, gameId, playerNo):
    recordSQL = """
    INSERT INTO PlayerGame(username, gameId, playerNo)
    VALUES(?, ?, ?)
    """
    editTable(recordSQL, (username, gameId, playerNo))

def getPlayerGameUsername(gameId, playerNo):
    recordSQL = """
    SELECT username
    FROM PlayerGame
    WHERE gameId = ? AND playerNo = ?;
    """
    records = getRecords(recordSQL, (gameId, playerNo))
    if not records:
        return False
    return records[0][0]

def deleteGame(gameId):
    recordSQL = """
    DELETE FROM Game
    WHERE Game.id = ?;
    """
    editTable(recordSQL, (gameId,))

    recordSQL = """
    DELETE FROM PlayerGame
    WHERE PlayerGame.gameId = ?;
    """
    editTable(recordSQL, (gameId,))

if __name__ == "__main__":
    pass