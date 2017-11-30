import cocos
import pyglet
import DBTetrisGame

BLOCK_WIDTH = 40

######################################################################
######################################################################
class GameBaseAction(cocos.actions.Action):
   """ Asynchronously ask the model to both clear a complete rows
       blocks in the game board and update. The operations are 
       performed together as a single transaction.
   """

   def start(self):
      """ """
      self.current_update_number = 0

   def step(self, dt):
      """ """
      if not self.target.game_model.getIsOver():
         self.current_update_number += 1

######################################################################
######################################################################
class GameFallingBlockAction(GameBaseAction):
   """ Asynchronously ask the model to both clear a complete rows
       blocks in the game board and update. The operations are 
       performed together as a single transaction.
   """

   def step(self, dt):
      """ """
      super( GameFallingBlockAction, self ).step(dt)
      if not self.target.game_model.getIsOver():
         self.current_update_number += 1
         time_divisor = self.target.getTimeDivisor()
         
         if 0 == (self.current_update_number % time_divisor):
            self.target.game_model.updateFallingBlock()

######################################################################
######################################################################
class GameCompleteRowsAction(GameBaseAction):
   """ Asynchronously ask the model to both clear a complete rows
       blocks in the game board and update. The operations are 
       performed together as a single transaction.
   """

   def step(self, dt):
      """ """
      super( GameCompleteRowsAction, self ).step(dt)
      if not self.target.game_model.getIsOver():
         self.current_update_number += 1
         if 0 == self.current_update_number % 30:
            if None == self.target.game_model.getFallingBlock():
               ## Clear any complete rows
               if not self.target.game_model.clearCompleteRowsAndUpdateScore():
                  ## All complete rows have been removed so start new falling block
                  self.target.game_model.addFallingBlock()

######################################################################
######################################################################
class GameScoreAction(GameBaseAction):
   """ Asynchronously ask the model for the current score and current
       high score. Then update the display to match.
   """

   def step(self, dt):
      """ """
      self.target.updateScoreDisplay()

######################################################################
######################################################################
class GameAction(GameBaseAction):
   """
   """

   def step(self, dt):
      """ """
      super( GameAction, self ).step(dt)
      if self.target.game_model.getIsOver():
         self.target.presentGameOverNotice()
         return

      time_divisor = self.target.getTimeDivisor()
      if 0 == (self.current_update_number % time_divisor):
         self.target.synchronizeDisplayWithModel(time_divisor)

######################################################################
######################################################################
class Game(cocos.layer.ColorLayer):
   """
   """

   # Tell cocos that this layer is for handling input!
   is_event_handler = True

   ###################################################################
   def __init__(self):
      """ """
      self.game_model = DBTetrisGame.DBTetrisGame()
      self.keys_being_pressed = set()
      self.isDropping = False
      self.model_block_to_layer_map = {}
      self.updates_per_move = 25
      self.current_update_number = 0
      self.last_score = 0
      self.last_high_score = 0
      
      self.director_width = DBTetrisGame.GAME_BOARD_WIDTH * BLOCK_WIDTH
      self.director_height = DBTetrisGame.GAME_BOARD_HEIGHT * BLOCK_WIDTH
      cocos.director.director.init(self.director_width, self.director_height,
         caption = "DBTetris", fullscreen=False)

      super( Game, self ).__init__(64, 64, 64, 255)
      
      self.intro_scene = cocos.scene.Scene(self)
      self.score_label = cocos.text.Label(text="Score: 0",
            font_size = 24, position = (10, self.director_height - 40))
      self.add(self.score_label)
      self.high_score_label = cocos.text.Label(text="High: 0", font_size = 24,
            position = (self.director_width-10, self.director_height - 40),
            anchor_x = "right")
      self.add(self.high_score_label)
      self.game_over_label = None
      
      self.do(GameAction())
      self.do(GameScoreAction())
      self.do(GameCompleteRowsAction())
      self.do(GameFallingBlockAction())
      
   ###################################################################
   def on_key_press(self, key, modifiers):
      """ """
      self.keys_being_pressed.add(key)
      if pyglet.window.key.LEFT == key:
         self.game_model.moveFallingBlockLeft()
      elif pyglet.window.key.RIGHT == key:
         self.game_model.moveFallingBlockRight()
      elif pyglet.window.key.SPACE == key:
         self.isDropping = True
      elif pyglet.window.key.A == key:
         self.game_model.rotateFallingBlockCounterclockwise()
      elif pyglet.window.key.D == key:
         self.game_model.rotateFallingBlockClockwise()

   ###################################################################
   def presentGameOverNotice(self):
      """ """
      if None == self.game_over_label:
         self.game_over_label = cocos.layer.Layer()
         label = cocos.text.Label(text="GAME OVER",
            font_size = 54,
            position = (self.director_width//2, self.director_height//2),
            anchor_x = "center")
         self.game_over_label.add(label)
      
         date = self.game_model.getHighScoreDate()
         message = 'High Score Achived ' + date
         message_layer = cocos.text.Label(text=message,
            font_size = 20,
            position = (self.director_width//2, self.director_height//2 - 40),
            anchor_x = "center")
         self.game_over_label.add(message_layer)
         
         self.add(self.game_over_label)
         self.game_over_label.opacity = 0
         self.game_over_label.do(cocos.actions.RotateTo(-30, duration = 1))
         self.game_over_label.do(cocos.actions.FadeIn(1))
   
   ###################################################################
   def updateScoreDisplay(self):
      """ """
      score = self.game_model.getScore()
      if self.last_score != score:
         self.last_score = score
         self.score_label.element.text = "Score: "+str(self.last_score)
      
      high_score = self.game_model.getHighScore()
      if self.last_high_score != high_score:
         self.last_high_score = high_score
         self.high_score_label.element.text = "High: "+str(self.last_high_score)

   ###################################################################
   def getTimeDivisor(self):
      """ """
      time_divisor = max(1, self.updates_per_move)

      if self.isDropping:
         time_divisor = 1 ## Drop as fast as possible
      
      return time_divisor
      
   ###################################################################
   def synchronizeDisplayWithModel(self, time_divisor):
      """ """
      blocks = self.game_model.getBoardBlocks()

      # Build map by adding blocks that are still in the model
      new_model_block_to_layer_map = {}

      ## Update positions of layers to match the blocks on the board
      for block in blocks:
         newX = block[1] * BLOCK_WIDTH
         newY = block[2] * BLOCK_WIDTH
         if not block[0] in self.model_block_to_layer_map:
            ## Create layer to represent block
            newBlockLayer = cocos.layer.ColorLayer(
                  block[4], block[5], block[6], 255, BLOCK_WIDTH, BLOCK_WIDTH)
            newBlockLayer.position = (newX, newY)
            self.add(newBlockLayer)
            self.model_block_to_layer_map[block[0]] = newBlockLayer
         
         layer = self.model_block_to_layer_map[block[0]]
         layer.position = (newX, newY)
         new_model_block_to_layer_map[block[0]] = layer
     
      ## Update positions of layers to match the blocks that are falling
      if None != self.game_model.getFallingBlock():
         x,y, rotation = self.game_model.getFallingBlockPosistionAndRotation()
         fallingBlocks = self.game_model.getTransformedBlockPositions(
            x, y, rotation, self.game_model.getFallingBlocks())

         ## Reposition each layer to match its corresponding block's position
         for block in fallingBlocks:
            newX = block[1] * BLOCK_WIDTH
            newY = block[2] * BLOCK_WIDTH
            if not block[0] in self.model_block_to_layer_map:
               ## Create a layer to represent block
               newBlockLayer = cocos.layer.ColorLayer(
                     block[4], block[5], block[6], 255, BLOCK_WIDTH, BLOCK_WIDTH)
               newBlockLayer.position = (newX, newY)
               self.add(newBlockLayer)
               self.model_block_to_layer_map[block[0]] = newBlockLayer
               self.isDropping = False
            
            layer = self.model_block_to_layer_map[block[0]]
            layer.stop()
            layer.do(cocos.actions.MoveTo((newX, newY),
                  duration=1.0/60.0 * time_divisor))
                  
            new_model_block_to_layer_map[block[0]] = layer

      ## Remove layers that no longer have corresponding blocks in the model
      # for each block in self.model_block_to_layer_map that isn't in
      # new_model_block_to_layer_map, remove the corresponding layer
      for id, layer in self.model_block_to_layer_map.iteritems():
         if not id in new_model_block_to_layer_map:
            layer.do(cocos.actions.FadeOut(0.5)+\
               cocos.actions.CallFuncS(cocos.layer.Layer.kill))

      self.model_block_to_layer_map = new_model_block_to_layer_map
   
   def run(self, host=None, port=None):
      """ """
      cocos.director.director.set_show_FPS(True)
      cocos.director.director.run (self.intro_scene)

######################################################################
######################################################################
if __name__ == "__main__":
   game = Game()
   game.run()
