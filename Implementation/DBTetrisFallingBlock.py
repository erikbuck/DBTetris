from datetime import date, datetime
import sqlite3
import random
import DBTetris


standard_block_arrangements = (
   ((-1, 0), (0, 0), (1,  0), ( 2, 0)), ## Horizontal bar
   (( 0, 1), (1, 1), (0,  0), ( 1, 0)), ## Box
   (( 0, 1), (1, 1), (1,  0), ( 2, 0)), ## Z one
   (( 2, 1), (1, 1), (1,  0), ( 0, 0)), ## Z two
   ((-1, 0), (0, 0), (1,  0), ( 0, 1)), ## Tee
   ((-1, 0), (0, 0), (1,  0), ( 1, 1)), ## L one
   ((-1, 0), (0, 0), (1,  0), (-1, 1)), ## L two
)


######################################################################
######################################################################
class DBTetrisFallingBlock(object):
   """ """

   ###################################################################
   def __init__(self, cursor, x, y, ownId = None):
      """ """
      self.cursor = cursor
      
      if None == ownId:
         DBTetris.cursor.execute("""BEGIN EXCLUSIVE TRANSACTION""")
         
         ## Create BlockGroup to store falling block's contents
         self.cursor.execute("""INSERT INTO BlockGroups VALUES(NULL);""")
         self.contentsId = self.cursor.lastrowid         
         
         ## Insert FallingBlock
         self.cursor.execute("""INSERT INTO FallingBlocks(
            posX, posY, angleDeg, contentsId) VALUES(?,?,?,?)""",
            (x, y, 0, self.contentsId))
         self.load(self.cursor.lastrowid)

         ## Populate the content group with Blocks in a randomly selected
         ## arrangement and color
         r = random.randint(128,255)
         g = random.randint(128,255)
         b = random.randint(128,255)
         randomIndex = random.randint(0, len(standard_block_arrangements)-1)
         arrangement = standard_block_arrangements[randomIndex]
         for pos in arrangement:
            self.cursor.execute("""INSERT INTO Blocks(
               posX, posY, groupId, red, green, blue)
               VALUES(?,?,?,?,?,?)""",
               (pos[0], pos[1], self.contentsId, r, g, b))
         
         DBTetris.connection.commit()               ## <-- Commit
   
      else:
         self.load(ownId)

   ###################################################################
   def load(self, ownId):
      """ """
      self.ownId = ownId
      self.cursor.execute("""SELECT contentsId FROM FallingBlocks
         WHERE fallingBlockId = ?""", (self.ownId,))
      self.contentsId = list(self.cursor.fetchone())[0]


######################################################################
######################################################################
if __name__ == "__main__":
   print 'Please start the game from Game.py'
