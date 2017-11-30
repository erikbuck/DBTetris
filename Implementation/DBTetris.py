from datetime import date, datetime
import sqlite3

##
connection = sqlite3.connect('tetris.db', isolation_level="EXCLUSIVE")
connection.execute('pragma foreign_keys')
cursor = connection.cursor()

def create_tables(cursor):
   """ """
   
   with connection:
      
      cursor.execute('SELECT SQLITE_VERSION()')
      data = cursor.fetchone()
      print "SQLite version: %s" % data

      ## BlockGroups
      cursor.executescript("""
                  CREATE TABLE IF NOT EXISTS BlockGroups(
                     groupId INTEGER PRIMARY KEY AUTOINCREMENT);
                  """)

      ## Blocks
      cursor.executescript("""
                  CREATE TABLE IF NOT EXISTS Blocks(
                     blockId INTEGER PRIMARY KEY AUTOINCREMENT,
                     posX INT, 
                     posY INT,
                     groupId INT,
                     red INT,
                     green INT,
                     blue INT,
                     FOREIGN KEY(groupId) REFERENCES BlockGroups(groupId));
                  """)
      
      ## Falling Blocks
      cursor.executescript("""
                  CREATE TABLE IF NOT EXISTS FallingBlocks(
                     fallingBlockId INTEGER PRIMARY KEY AUTOINCREMENT,
                     posX INT, 
                     posY INT,
                     angleDeg INT,
                     contentsId INT,
                     FOREIGN KEY(contentsId) REFERENCES BlockGroups(groupId));
                  """)

      
      ## Games
      cursor.executescript("""
                  CREATE TABLE IF NOT EXISTS Games(
                     gameId INTEGER PRIMARY KEY AUTOINCREMENT,
                     date TEXT,
                     score INT,
                     isOver INT,
                     boardId INT,
                     fallingBlockId INT,
                     FOREIGN KEY(boardId) REFERENCES BlockGroups(groupId),
                     FOREIGN KEY(fallingBlockId) REFERENCES FallingBlocks(fallingBlockId));
                  """)

######################################################################
######################################################################
if __name__ == "__main__":
   print 'Please start the game from Game.py'
