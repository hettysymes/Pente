import sqlite3
import pickle
from datetime import datetime

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

    conn, c = connect()
    tableSQLDict = {"Player": playerSQL, "HashTable": hashtableSQL}
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
    whenSaved = datetime.strftime(whenSaved, "%m/%d/%Y, %H:%M:%S")
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

if __name__ == "__main__":
    pass