import sqlite3
import pickle
from datetime import datetime
import os
import Ui
from Game import Game, GameRecord

# The HashTable class enables usernames to be stored at indexes determined by their passwords in a table.
class HashTable:

    def __init__(self):
        self._SIZE = 50
        self._hashTable = [[] for _ in range(self._SIZE)]

    # Given a key, performs a hashing algorithm on the key and returns the hashed value.
    def __hashFunction(self, key):
        total = 0
        for char in key:
            total += 3*ord(char)
        return total % self._SIZE

    # Given a username and password, the username is stored in the hash table at the index specified by performing the hashFunction on the password.
    def addToTable(self, username, password):
        passwordHash = self.__hashFunction(password)
        self._hashTable[passwordHash].append(username)

    # Given a username and password, returns if the hash table stores the username in the table at the index specified by the hash of the password.
    def isInTable(self, username, password):
        passwordHash = self.__hashFunction(password)
        return username in self._hashTable[passwordHash]

# Returns if the database exists.
def exists():
    return os.path.exists("PenteDatabase.db")

# Connects with the database via the sqlite3 connect function.
def connect():
    conn = sqlite3.connect("PenteDatabase.db")
    c = conn.cursor()
    return conn, c

# Closes the connection with the database and commits the last made changes.
def close(conn):
    conn.commit()
    conn.close()

# Creates a new database.
def createDatabase():
    playerSQL = """
    CREATE TABLE Player(
    username TEXT PRIMARY KEY,
    whenSaved TEXT NOT NULL,
    numberOfWins INTEGER NOT NULL,
    numberOfLosses INTEGER NOT NULL,
    numberOfDraws INTEGER NOT NULL,
    score INTEGER NOT NULL
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
    mode TEXT NOT NULL
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
        c.execute(sql)
        if tableName == "HashTable":
            hashtable = pickle.dumps(HashTable())
            recordSQL = """
            INSERT INTO HashTable(id, hashTable)
            VALUES(1, ?);
            """
            editTable(recordSQL, (hashtable,))
    close(conn)

# The SQL, values to be used in the SQL, and whether the id of the last row added is required to be returned is passed in as parameters.
# THe SQL is executed with the values, and if the id of the last row is required, this is returned. Otherwise, nothing is returned.
def editTable(recordSQL, values, getId=False):
    conn, c = connect()
    c.execute(recordSQL, values)
    if getId:
        id = c.lastrowid
    else:
        id = None
    close(conn)
    return id

# Given a recordQuery (written in SQL) and values to be used in the SQL, the getRecords function returns the records specified by the recordQuery.
def getRecords(recordQuery, values=()):
    conn, c = connect()
    c.execute(recordQuery, values)
    res = c.fetchall()
    close(conn)
    return res

# Loads the hash table from the database and returns it.
def loadHashTable():
    recordQuery = """
    SELECT hashtable
    FROM HashTable
    WHERE id = 1;
    """
    [hashtable] = getRecords(recordQuery, ())[0]
    return pickle.loads(hashtable)

# Given a hash table, the saveHashTable function updates the existing hash table in the database with the new one.
def saveHashTable(hashtable):
    updateQuery = f"""
    UPDATE HashTable
    SET hashTable = ?
    WHERE id = 1;
    """
    editTable(updateQuery, (pickle.dumps(hashtable),))

# Given a username and password, returns whether there is such a match found in the hash table stored in the database.
def checkPassword(username, password):
    hashtable = loadHashTable()
    return hashtable.isInTable(username, password)

# Given a username and password, the function loads the hash table from the database, adds the new match to the table, and saves it back to the database.
def addPassword(username, password):
    hashtable = loadHashTable()
    hashtable.addToTable(username, password)
    saveHashTable(hashtable)

# Given a username, password, and whenSaved (the datetime the account was created) the username and password is added to the hash table, and a new Player entry is made in the database's Player table.
def savePlayer(username, password, whenSaved):
    addPassword(username, password)
    whenSaved = datetime.strftime(whenSaved, "%d/%m/%Y, %H:%M:%S")
    recordSQL = """
    INSERT INTO Player(username, whenSaved, numberOfWins, numberOfLosses, numberOfDraws, score)
    VALUES(?, ?, 0, 0, 0, 0);
    """
    editTable(recordSQL, (username, whenSaved))

# Given a username, the details of the Player entry specified by username is returned from the function.
def getPlayer(username):
    recordSQL = """
    SELECT whenSaved, numberOfWins, numberOfLosses, numberOfDraws, score
    FROM Player
    WHERE username = ?;
    """
    whenSaved, numberOfWins, numberOfLosses, numberOfDraws, score = getRecords(recordSQL, (username,))[0]
    whenSaved = datetime.strptime(whenSaved, "%d/%m/%Y, %H:%M:%S")
    return [whenSaved, numberOfWins, numberOfLosses, numberOfDraws, score]

def addPlayerResult(username, didWin):
    if didWin == True:
        field = "numberOfWins"
        scoreAdd = 5
    elif didWin == False:
        field = "numberOfLosses"
        scoreAdd = 1
    else:
        field = "numberOfDraws"
        scoreAdd = 3
    selectSQL = f"""
    SELECT {field}, score
    FROM Player
    WHERE username = ?;
    """
    updateSQL = f"""
    UPDATE Player
    SET {field} = ?, score = ?
    WHERE username = ?;
    """
    num, score = getRecords(selectSQL, (username,))[0]
    editTable(updateSQL, (num+1, score+scoreAdd, username))

def getPlayerRank(username):
    recordSQL = """
    SELECT username
    FROM Player
    ORDER BY score DESC;
    """
    playerUsernames = getRecords(recordSQL)
    return playerUsernames.index((username,))+1

# Given a username, the function returns if there are any existing Player entries in the Player table with that username.
def isUniqueUsername(username):
    recordSQL = """
    SELECT username
    FROM Player
    WHERE username = ?;
    """
    players = getRecords(recordSQL, (username,))
    return players == []

# Given the usernames of the players and the game record, the saveGame function saves the game into the Game table, and also associates it with the Player entries in the PlayerGame table.
def saveGame(username1, username2, gameRecord):
    name = gameRecord.name
    whenSaved = gameRecord.whenSaved.strftime("%d/%m/%Y, %H:%M:%S")
    game = pickle.dumps(gameRecord.game)
    winner = gameRecord.game.winner
    mode = gameRecord.mode

    recordSQL = """
    INSERT INTO Game(name, whenSaved, game, winner, mode)
    VALUES(?, ?, ?, ?, ?);
    """
    
    gameId = editTable(recordSQL, (name, whenSaved, game, winner, mode), getId=True)

    invalidUsernames = [Ui.Player.GUEST, Ui.Player.COMP]
    if username1 not in invalidUsernames:
        savePlayerGame(username1, gameId, Game.P1)
    if username2 not in invalidUsernames:
        savePlayerGame(username2, gameId, Game.P2)

# Given a game record, updates the game with the same id in the Game table with the new game information.
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

# Given a list of game details, the function converts each game detail into its correct format, before returning them all as part of a single game record.
def parseGames(games):
    parsedGames = []
    for game in games:
        g = list(game) #[id, name, whenSaved, game, winner, mode]
        g[2] = datetime.strptime(g[2], "%d/%m/%Y, %H:%M:%S") #whenSaved
        g[3] = pickle.loads(g[3]) #game
        gameRecord = GameRecord(g[0], g[1], g[2], g[3], g[5])
        parsedGames.append(gameRecord)
    return parsedGames
        
# Given a username and a winner, the function returns all games which were played by the player with the username and had the specified winner.
def loadGames(username, winner):
    recordSQL = """
    SELECT Game.id, Game.name, Game.whenSaved, Game.game, Game.winner, Game.mode
    FROM Game
    INNER JOIN PlayerGame ON PlayerGame.gameId = Game.id
    WHERE PlayerGame.username = ? AND Game.winner = ?
    ORDER BY Game.whenSaved DESC;
    """
    games = getRecords(recordSQL, (username, winner))
    return parseGames(games)

# Given a username, returns all the games that were played by the player with the username.
def loadAllGames(username):
    recordSQL = """
    SELECT Game.id, Game.name, Game.whenSaved, Game.game, Game.winner, Game.mode
    FROM Game
    INNER JOIN PlayerGame ON PlayerGame.gameId = Game.id
    WHERE PlayerGame.username = ?
    ORDER BY Game.whenSaved DESC;
    """
    games = getRecords(recordSQL, (username,))
    return parseGames(games)

# Given an id of a game, returns the information of the game stored in the Game table with that id.
def getGame(id):
    recordSQL = """
    SELECT Game.id, Game.name, Game.whenSaved, Game.game, Game.winner, Game.mode
    FROM Game
    WHERE id = ?;
    """
    game = getRecords(recordSQL, (id,))
    return parseGames(game)[0]

# Given a username, game id, and a player number, the savePlayerGame creates a new entry in the PlayerGame table which relates a Player entry to a Game entry, and also which player number the player played as in the game.
def savePlayerGame(username, gameId, playerNo):
    recordSQL = """
    INSERT INTO PlayerGame(username, gameId, playerNo)
    VALUES(?, ?, ?)
    """
    editTable(recordSQL, (username, gameId, playerNo))

# Given a game id and a player number, returns the username of the player who played as that player number in that game.
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

# Given a game id, the function deletes the game with that game id from the Game table, along with any related PlayerGame entries.
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