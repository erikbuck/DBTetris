from datetime import date, datetime
import DBTetris
from DBTetrisFallingBlock import DBTetrisFallingBlock as FallingBlock
import sqlite3

GAME_BOARD_WIDTH = 11
GAME_BOARD_HEIGHT = 22


class DBTetrisGame(object):
   """ """

   ###################################################################
   def __init__(self, ownId = None):
      """ This initializer fetches the tuple for the most recent 
          game that is not over. If every game in the database is
          over, a new game is created as a transaction involving
          multiple steps. """
      self._fallingBlock = None
      self.__isGameOver = False
      
      if None == ownId:
         ## See if there is an ongoing Game to be continued
         DBTetris.cursor.execute("""SELECT * FROM Games WHERE isOver = 0;""")
         games = DBTetris.cursor.fetchall()
         if 0 < len(games):
            # Load the game state from the last selected tuple.
            gameTuple = games[-1] ## Grab the last/most recent game
            print 'Resuming Game from ' + gameTuple[1]
            self.ownId = gameTuple[0]
            self.boardId = gameTuple[4]
            self._fallingBlock = FallingBlock(DBTetris.cursor,
               0, 0, gameTuple[5])
         
         else:
            DBTetris.cursor.execute("""BEGIN EXCLUSIVE TRANSACTION""")
            ## Create BlockGroup to store board
            DBTetris.cursor.execute("""INSERT INTO BlockGroups VALUES(NULL);""")
            self.boardId = DBTetris.cursor.lastrowid
            
            gameTuple = (str(date.today()), 0, 0, self.boardId)
            ## Create Game
            DBTetris.cursor.execute("""INSERT INTO Games
               (date, score, isOver, boardId)
               VALUES(?,?,?,?)""", gameTuple)
            self.ownId = DBTetris.cursor.lastrowid

            DBTetris.connection.commit()               ## <-- Commit

      else:
         self.ownId = ownId
         DBTetris.cursor.execute("""SELECT ? FROM Games""", (self.ownId,))
         gameTuple = DBTetris.cursor.fetchone()
         self.boardId = gameTuple[4]
         self._fallingBlock = FallingBlock(DBTetris.cursor,
               0, 0, gameTuple[5])

   ###################################################################
   def addFallingBlock(self):
      """ """
      self._fallingBlock = FallingBlock(DBTetris.cursor,
            GAME_BOARD_WIDTH//2,
            GAME_BOARD_HEIGHT)
      DBTetris.cursor.execute("""UPDATE Games SET fallingBlockId = ?  
         WHERE gameId = ?""",
         (self._fallingBlock.ownId, self.ownId))

   ###################################################################
   def setGameOver(self):
      """ """
      DBTetris.cursor.execute("""UPDATE Games SET isOver = 1
            WHERE gameId = ?; """, (self.ownId,))

   
   ###################################################################
   def getIsOver(self):
      """ """
      ## Get the all-time high score
      DBTetris.cursor.execute("""SELECT isOver FROM Games WHERE gameId = ?""",
         (self.ownId,))
      return DBTetris.cursor.fetchone()[0]

   ###################################################################
   def getHighScore(self):
      """ """
      ## Get the all-time high score
      DBTetris.cursor.execute("""SELECT MAX(score) FROM Games;""")
      return DBTetris.cursor.fetchone()[0]
   
   ###################################################################
   def getHighScoreDate(self):
      """ """
      DBTetris.cursor.execute("""SELECT date FROM Games 
            WHERE score = (SELECT MAX(score) FROM Games);""")
      return DBTetris.cursor.fetchone()[0]
   
   ###################################################################
   def getScore(self):
      """ """
      DBTetris.cursor.execute("""SELECT score FROM Games WHERE gameId = ?""",
            (self.ownId,))
      score = DBTetris.cursor.fetchone()
      return score[0]
   
   ###################################################################
   def incrementScore(self):
      """ """
      DBTetris.cursor.execute("""UPDATE Games SET score = score + 1
            WHERE gameId = ?; """, (self.ownId,))

   ###################################################################
   def getFallingBlock(self):
      """ """
      if None != self._fallingBlock and None == self._fallingBlock.ownId:
         self._fallingBlock = None
      return self._fallingBlock
   
   ###################################################################
   def getTransformedBlockPositions(self, offsetX, offsetY, rotation, blocks):
      """ """
      result = []
      
      ## Normalize rotation to positive angles < 360
      rotation = rotation % 360
      if 0 > rotation:
          rotation += 360
      
      if rotation >= 270:
         for block in blocks:
            blockAsList = list(block)
            x = blockAsList[1]
            y = blockAsList[2]
            blockAsList[1] = x *  0 + y * 1 + offsetX
            blockAsList[2] = x * -1 + y * 0 + offsetY
            result.append(blockAsList)
      elif rotation >= 180:
         for block in blocks:
            blockAsList = list(block)
            x = blockAsList[1]
            y = blockAsList[2]
            blockAsList[1] = x * -1 + y * 0 + offsetX
            blockAsList[2] = x * 0 + y * -1 + offsetY
            result.append(blockAsList)
      elif rotation >= 90:
         for block in blocks:
            blockAsList = list(block)
            x = blockAsList[1]
            y = blockAsList[2]
            blockAsList[1] = x * 0 + y * -1 + offsetX
            blockAsList[2] = x * 1 + y *  0 + offsetY
            result.append(blockAsList)
      else:
         for block in blocks:
            blockAsList = list(block)
            blockAsList[1] = blockAsList[1] + offsetX
            blockAsList[2] = blockAsList[2] + offsetY
            result.append(blockAsList)

      return result

   ###################################################################
   def doesFallingBlockCollide(self):
      DBTetris.cursor.execute("""SELECT * FROM Blocks 
         WHERE groupId = ? """, (self.boardId,))
      boardTuples = DBTetris.cursor.fetchall()
      maxY = 0
      DBTetris.cursor.execute("""SELECT * FROM Blocks
         WHERE groupId = ? """, (self._fallingBlock.contentsId,))
      fallingTuples = DBTetris.cursor.fetchall()
      x, y, r = self.getFallingBlockPosistionAndRotation()
      fallingTuples = self.getTransformedBlockPositions(x, y, r, fallingTuples)
      
      for fallingTuple in fallingTuples:
         fx = fallingTuple[1]
         fy = fallingTuple[2]
         maxY = max(maxY, fy)
         if 0 > fy:
            ## Collided with bottom of board
            return True

         for boardTuple in boardTuples:
            if fx == boardTuple[1] and fy == boardTuple[2]:
               ## Collided with block already in board
               ## If falling block is above top of board, the game is over
               if maxY >= GAME_BOARD_HEIGHT:
                  self.setGameOver()
               
               return True
      return False
   
   ###################################################################
   def doesFallingBlockFit(self):
      """ """
      x, y, r = self.getFallingBlockPosistionAndRotation()
      DBTetris.cursor.execute("""SELECT * FROM Blocks WHERE groupId = ?""",
            (self._fallingBlock.contentsId,))
      blocks = DBTetris.cursor.fetchall()
      blocks = self.getTransformedBlockPositions(x, y, r, blocks)
      for block in blocks:
         if block[1] < 0 or block[1] >= GAME_BOARD_WIDTH:
            ## Block is off left or right of game board
            return False
   
      return True

   ###################################################################
   def getBoardBlocks(self):
      """ """
      DBTetris.cursor.execute("""SELECT * FROM Blocks
            WHERE groupId = ? """, (self.boardId,))
      return DBTetris.cursor.fetchall()

   ###################################################################
   def getFallingBlocks(self):
      """ """
      DBTetris.cursor.execute("""SELECT * FROM Blocks
            WHERE groupId = ? """, (self._fallingBlock.contentsId,))
      return DBTetris.cursor.fetchall()

   ###################################################################
   def getFallingBlockPosistionAndRotation(self):
      DBTetris.cursor.execute("""SELECT posX, posY, angleDeg
            FROM FallingBlocks
            WHERE fallingBlockId = ? """, (self._fallingBlock.ownId,))
      return DBTetris.cursor.fetchone()

   ###################################################################
   def moveFallingBlockLeft(self):
      """ """
      if None != self._fallingBlock:
         DBTetris.cursor.execute("""BEGIN EXCLUSIVE TRANSACTION""")
         DBTetris.cursor.execute("""UPDATE FallingBlocks SET
               posX = posX - 1 
               WHERE fallingBlockId = ?""", (self._fallingBlock.ownId,))
         if (not self.doesFallingBlockFit() or\
               self.doesFallingBlockCollide()) and\
               not self.getIsOver():
            ## Lateral movement and rotation are not allowed to
            ## cause collisions or cause blocks to leave the
            ## board/play area, so rollback the change
            DBTetris.connection.rollback()             ## <-- Rollback
         else:
            DBTetris.connection.commit()               ## <-- Commit

   ###################################################################
   def moveFallingBlockRight(self):
      """ """
      if None != self._fallingBlock:
         DBTetris.cursor.execute("""BEGIN EXCLUSIVE TRANSACTION""")
         DBTetris.cursor.execute("""UPDATE FallingBlocks SET
               posX = posX + 1
               WHERE fallingBlockId = ?""", (self._fallingBlock.ownId,))
         if (not self.doesFallingBlockFit() or\
               self.doesFallingBlockCollide()) and\
               not self.getIsOver():
            ## Lateral movement and rotation are not allowed to
            ## cause collisions or cause blocks to leave the
            ## board/play area, so rollback the change
            DBTetris.connection.rollback()             ## <-- Rollback
         else:
            DBTetris.connection.commit()               ## <-- Commit

   ###################################################################
   def rotateFallingBlockCounterclockwise(self):
      """ """
      if None != self._fallingBlock:
         DBTetris.cursor.execute("""BEGIN EXCLUSIVE TRANSACTION""")
         DBTetris.cursor.execute("""UPDATE FallingBlocks SET
               angleDeg = angleDeg + 90
               WHERE fallingBlockId = ?""", (self._fallingBlock.ownId,))
         if (not self.doesFallingBlockFit() or\
               self.doesFallingBlockCollide()) and\
               not self.getIsOver():
            ## Lateral movement and rotation are not allowed to
            ## cause collisions or cause blocks to leave the
            ## board/play area, so rollback the change
            DBTetris.connection.rollback()             ## <-- Rollback
         else:
            DBTetris.connection.commit()               ## <-- Commit

   ###################################################################
   def rotateFallingBlockClockwise(self):
      """ """
      if None != self._fallingBlock:
         DBTetris.cursor.execute("""BEGIN EXCLUSIVE TRANSACTION""")
         DBTetris.cursor.execute("""UPDATE FallingBlocks SET
               angleDeg = angleDeg - 90
               WHERE fallingBlockId = ?""", (self._fallingBlock.ownId,))
         if (not self.doesFallingBlockFit() or\
               self.doesFallingBlockCollide()) and\
               not self.getIsOver():
            ## Lateral movement and rotation are not allowed to
            ## cause collisions or cause blocks to leave the
            ## board/play area, so rollback the change
            DBTetris.connection.rollback()             ## <-- Rollback
         else:
            DBTetris.connection.commit()               ## <-- Commit

   ###################################################################
   def moveBlocksAboveRowDown(self, rowNumber):
      """ """
      for i in xrange(rowNumber + 1, GAME_BOARD_HEIGHT):
         DBTetris.cursor.execute("""BEGIN EXCLUSIVE TRANSACTION""")
         DBTetris.cursor.execute("""UPDATE Blocks SET posY = posY - 1
               WHERE groupId = ? AND posY = ?;""", (self.boardId, i))
         DBTetris.connection.commit()                  ## <-- Commit

   ###################################################################
   def moveFallingBlockContentToBoard(self):
      """ """
      
      DBTetris.cursor.execute("""BEGIN EXCLUSIVE TRANSACTION""")
      x, y, r = self.getFallingBlockPosistionAndRotation()
      DBTetris.cursor.execute("""SELECT * FROM Blocks WHERE groupId = ? """,
            (self._fallingBlock.contentsId,))
      blocks = DBTetris.cursor.fetchall()
      blocks = self.getTransformedBlockPositions(x, y, r, blocks)
      
      for block in blocks:
         boardX = block[1]
         boardY = block[2]
         DBTetris.cursor.execute("""UPDATE Blocks SET groupId = ?,
            posX = ?, posY = ?
            WHERE blockId = ?;""",
         (self.boardId, boardX, boardY, block[0],))
      
      DBTetris.connection.commit()                     ## <-- Commit

   ###################################################################
   def clearCompleteRowsAndUpdateScore(self):
      """ """
      DBTetris.cursor.execute("""BEGIN EXCLUSIVE TRANSACTION""")
      for i in xrange(GAME_BOARD_HEIGHT-1, 0-1, -1):
         DBTetris.cursor.execute("""SELECT count(*) FROM Blocks
               WHERE groupId = ? AND posY = ? """,
               (self.boardId, i))
         count = DBTetris.cursor.fetchone()
         if GAME_BOARD_WIDTH <= count[0]:
            ## Remove row
            DBTetris.cursor.execute("""DELETE FROM Blocks
                  WHERE groupId = ? AND posY = ? """,
                  (self.boardId, i))
            self.moveBlocksAboveRowDown(i)
            self.incrementScore()
            DBTetris.connection.commit()               ## <-- Commit
            return True  ## Tell caller that a row was removed
      
      DBTetris.connection.commit()                     ## <-- Commit
      return False   ## Tell caller that no rows were removed
   
   ###################################################################
   def updateFallingBlock(self):
      """ """
      if None != self.getFallingBlock():
         DBTetris.cursor.execute("""BEGIN EXCLUSIVE TRANSACTION""")
         ## The changes made by moveDown() may be rolled back
         DBTetris.cursor.execute("""UPDATE FallingBlocks 
               SET posY = posY - 1 WHERE fallingBlockId = ?""",
               (self._fallingBlock.ownId,))
         
         ## Rollback if transaction produces collision with board sides
         if not self.doesFallingBlockFit():
         
            DBTetris.connection.rollback() ## <--- Rollback
            
         ## Rollback if transaction produces a collision
         elif self.doesFallingBlockCollide() and\
               not self.getIsOver():
         
            DBTetris.connection.rollback() ## <--- Rollback
            
            DBTetris.cursor.execute("""BEGIN EXCLUSIVE TRANSACTION""")
            ## Move falling block's content blocks to board
            self.moveFallingBlockContentToBoard()
            
            # Remove relation to current falling block
            DBTetris.cursor.execute("""UPDATE Games
                  SET fallingBlockId = NULL
                  WHERE gameId = ? """, (self.ownId,))
            
            ## Delete the current falling block
            DBTetris.cursor.execute("""DELETE FROM FallingBlocks 
                  WHERE fallingBlockId = ? """,
               (self._fallingBlock.ownId,))

            ## There is no falling block anymore
            self._fallingBlock = None
            
            DBTetris.connection.commit()              ## <-- Commit
         
         else:
            ## Continue falling
            DBTetris.connection.commit()              ## <-- Commit


DBTetris.create_tables(DBTetris.cursor)

######################################################################
######################################################################
if __name__ == "__main__":
   print 'Please start the game from Game.py'
