import os
import random
from fnmatch import fnmatch
import time

import pygame as pg
from pygame.locals import *
from worldSaver import loadWorld
from utils import *


# globals - world (extracted from the world file)
BLOCKS_NAME_TO_ID = {} # text-id-mapping (!blocks from world file)
BLOCKS_ID_TO_NAME = {} # inversion: id-text-mapping
VARIABLES = {} # other variables (!info from world file)
BLOCKGFX = {} # images for tiles (!blockgfx from world file)
WORLD = None # the world as lists of lists of block ids (row-wise / y coordinate first) (!world from world file)
GOALPOS = None # Coordinates of the goal (x coordinate first)
SPAWNPOS = None # spawn position (first player position and respawn position)

# globals - game
SCREEN = None # the screen for pygame
SCREEN_RESOLUTION = (768, 640) # 24x20 blocks (for 32x32 pixel per block)
SCREEN_SIZE_BLOCKS = None # amount of blocks in X and Y direction (tuple, will be computed when a level is loaded)
PLAYERPOS = None # position of the player character
POSITION_X_HISTORY = list() # a history of the player's x positions of the last POSITION_HISTORY_LENGTH frames
POSITION_HISTORY_LENGTH = 10 # length of POSITION_X_HISTORY
SCORE = 0 # the score
FONT = None # the font object for writing the score
MODE = 0 # 0 = automatic, 1 = manual
FPS = 0 if MODE == 0 else 10 # maximum frames per second, 0 to remove limit
FRAME_COUNTER = 0 # counts the number of frames that happened - equivalent to number of actions taken
NUMBERS = None # holds the number graphics for the score
MAX_TRAINED_FRAMES = 1000000 # after how many trained frames (AI mode) the game will terminate (0 for never)
WORLDNAME = None # name (actually the path) of the currently loaded world
WORLDCOUNT = None # how many worlds the network has been trained on (including current world) (only in AI mode)

# globals - constants for action ids
ACTION_NO_ACTION = 0
ACTION_LEFT = 1
ACTION_RIGHT = 2
ACTION_JUMP = 3

# globals - levels
LEVEL_PREFIX = None # path to the level directory
LEVEL_PATTERN = None # pattern for the level (level will be chosen randomly from all matching files)

# globals - statistics (will be reset after a new level is loaded)
STATISTICS_FILE_NAME = None # where the statistics are stored
STATISTICS_FILE = None
FRAME_COUNTER_OLD = 0
SCORE_TOTAL = 0 # sum of all scores when the goal was reached
DEATH_COUNT = 0 # how often the character has died
LEVEL_COUNT = 0 # how many levels have been beaten
COIN_COUNT = 0 # how many coins have been collected
MOVES_COUNT = [0, 0, 0, 0] # counts how often each action is taken

# screenshot behavior (needed for mario-ai project)
SCREENSHOT_DIRECTORY = None # where to store the screenshots
SCREENSHOT_CURRENT_SIZE = (256, 213) # size (in pixels) of current frame screenshot
SCREENSHOT_OLD_SIZE = (128, 128) # size (in pixels) of older frame screenshots
SCREENSHOT_OLD_COUNT = 0 # how many older screenshots to save (including the current screenshot) (0 means only current screenshot)
SCREENSHOT_OLD_PREFIX = "" # prefix for older screenshots, numbers will be appended
SCREENSHOT_CURRENT_NAME = "current" # name (without extension) for bigger resolution current screenshot
SCREENSHOT_EXTENSION = ".png" # file extension for screenshots
SCREENSHOTS_ACTIVE = 1 if MODE == 0 else 0 # 0 = no screenshots, 1 = take screenshots


# reads information about which levels to use and where to put the statistics and the screenshots from the given file.
def loadPaths(path):
	global LEVEL_PREFIX, LEVEL_PATTERN, STATISTICS_FILE_NAME, SCREENSHOT_DIRECTORY
	print("Loading paths ...")
	pf = open(path, 'r')
	paths = [line[:-1] for line in pf]
	LEVEL_PREFIX = paths[0] # default: r"levels/"
	print("LEVEL_PREFIX", LEVEL_PREFIX)
	LEVEL_PATTERN = paths[1] # default: r"training_*.txt"
	print("LEVEL_PATTERN", LEVEL_PATTERN)
	STATISTICS_FILE_NAME = paths[2] # default: r"learned/statistics_test.csv"
	print("STATISTICS_FILE_NAME", STATISTICS_FILE_NAME)
	SCREENSHOT_DIRECTORY = paths[3] # default: r"/media/ramdisk/tmp/"
	print("SCREENSHOT_DIRECTORY", SCREENSHOT_DIRECTORY)
	# create subfolder, if it doesn't exist
	if not os.path.exists(SCREENSHOT_DIRECTORY):
		os.mkdir(SCREENSHOT_DIRECTORY)
		print("Screenshot directory created.")
	print("Loading paths done.")


# loads tiles as specified in the given dict. defaults to "gfx/<BLOCKNAME>/primitive.png if not specified
def loadTileGraphics(blockgfx):
	global BLOCKGFX
	for k, v in BLOCKS_NAME_TO_ID.items():
		gfxpath = blockgfx[v] if v in blockgfx else r"gfx/{}/primitive.png".format(k.lower())
		BLOCKGFX[v] = pg.image.load(gfxpath)
	BLOCKGFX[-1] = pg.image.load(blockgfx[-1] if -1 in blockgfx else r"gfx/player/primitive.png")


# loads the number graphics, if possible
def loadNumberGraphics():
	global NUMBERS
	numberpath = r"gfx/numbers/"
	if os.path.isdir(numberpath):
		NUMBERS = list()
		for i in range(10):
			NUMBERS.append(pg.image.load(numberpath + str(i) + r".png"))
		print("Number graphics found and loaded.")


# chooses a random worldfile matching the pattern from the given directory
def chooseWorld(worlddir, pattern):
	return worlddir + random.choice([f for f in os.listdir(worlddir) if fnmatch(f, pattern)])


# initialize stuff that has to be initialized once
def init():
	global SCREEN, FONT, NUMBERS

	# init pygame
	pg.init()
	SCREEN = pg.display.set_mode(SCREEN_RESOLUTION, pg.constants.DOUBLEBUF)
	tmp = 1 if FPS == 0 else int(1000/FPS)
	pg.key.set_repeat(1, tmp)

	# init font
	loadNumberGraphics()
	if not NUMBERS:
		FONT = pg.font.SysFont(None, 64)


# initializes/resets statistic variables and logs statistics to the statistics file
def resetStatistics():
	global STATISTICS_FILE, FRAME_COUNTER_OLD, COIN_COUNT, DEATH_COUNT, LEVEL_COUNT, SCORE_TOTAL, MOVES_COUNT
	# initialize/reset statistics
	if STATISTICS_FILE is None: # happens only if this is called for the first time
		if os.path.isfile(STATISTICS_FILE_NAME): # file already exists
			STATISTICS_FILE = open(STATISTICS_FILE_NAME, "a")
		else: # file doesn't exist
			STATISTICS_FILE = open(STATISTICS_FILE_NAME, "w")
			# STATISTICS_FILE.write("sep=;") # setting separator to ;
			STATISTICS_FILE.write(";".join(["frames since last update", "coins collected", "deaths", "levels beaten", "score gathered", "move count (no action, left, right, jump)", "!world name"]) + "\n") # write head
	else: # method is not called for first time - there are statistics available
		frames = FRAME_COUNTER - FRAME_COUNTER_OLD
		if frames > 0:
			statlist = list()
			statlist.append(frames) # number of frames since last time
			statlist.append(COIN_COUNT) # collected coins
			statlist.append(DEATH_COUNT) # deaths
			statlist.append(LEVEL_COUNT) # beaten levels
			statlist.append(SCORE_TOTAL) # score accumulated since last time
			statlist.append(MOVES_COUNT) # moves since last time
			statlist.append(WORLDNAME)
			# reset statistics
			FRAME_COUNTER_OLD = FRAME_COUNTER
			COIN_COUNT = 0
			DEATH_COUNT = 0
			LEVEL_COUNT = 0
			SCORE_TOTAL = 0
			MOVES_COUNT = [0, 0, 0, 0]
			stmp = ";".join(map(str, statlist))
			print(stmp)
			STATISTICS_FILE.write(stmp + "\n")
		else:
			print("No frames happened since last statistics update ...")


# initialize stuff that has to be initialized per level
def init_world(worldpath):
	# load world
	global BLOCKS_NAME_TO_ID, BLOCKS_ID_TO_NAME, WORLD, SPAWNPOS, GOALPOS, PLAYERPOS, POSITION_X_HISTORY, SCORE, SCREEN_SIZE_BLOCKS, MOVES_COUNT, COIN_COUNT, DEATH_COUNT, LEVEL_COUNT, SCORE_TOTAL, STATISTICS_FILE, FRAME_COUNTER_OLD, WORLDNAME, WORLDCOUNT
	print("Loading world: {}".format(worldpath)) # debug info
	SCORE_TOTAL = SCORE_TOTAL + SCORE # for statistics
	info, BLOCKS_NAME_TO_ID, blockgfx, WORLD = loadWorld(worldpath)
	BLOCKS_ID_TO_NAME = {v: k for k, v in BLOCKS_NAME_TO_ID.items()}
	loadTileGraphics(blockgfx)
	for k, v in info.items():
		VARIABLES[k] = convertToNumberIfPossible(v)

	# default needed variables
	VARIABLES.setdefault('blocksize', 32)
	VARIABLES.setdefault('jump_height', 3) # how many blocks the character will ascend when jumping
	VARIABLES.setdefault('jump_width', 3) # for how many ticks the character will be "hovering" at the highest point of the jump - the maximum distance he can jump is actually higher
	VARIABLES.setdefault('jump', 1) # how often character is able to jump before he has to touch ground again
	SCORE = VARIABLES['starting_score'] if 'starting_score' in VARIABLES else 0 # what the score is at the beginning
	VARIABLES.setdefault('coin_worth', 5) # how many points one coin gives
	VARIABLES.setdefault('death_worth', -10) # how many points the character will lose if he dies
	VARIABLES.setdefault('goal_worth', 100) # how many points the player will get if he reaches the goal

	# compute amount of blocks in both directions
	# behavior in case of not "blocksize divides resolution" not examined
	SCREEN_SIZE_BLOCKS = (int(SCREEN_RESOLUTION[0] / VARIABLES['blocksize']), int(SCREEN_RESOLUTION[1] / VARIABLES['blocksize']))

	# find spawn and goal position
	SPAWNPOS = None
	GOALPOS = None
	for y in range(len(WORLD)):
		for x in range(len(WORLD[y])):
			if WORLD[y][x] == BLOCKS_NAME_TO_ID['SPAWN']:
				SPAWNPOS = (x, y)
			elif WORLD[y][x] == BLOCKS_NAME_TO_ID['GOAL']:
				GOALPOS = (x, y)
		if (SPAWNPOS is not None) and (GOALPOS is not None): break
	PLAYERPOS = SPAWNPOS
	POSITION_X_HISTORY = [PLAYERPOS[0]]

	resetStatistics()

	WORLDNAME = worldpath # set worldname to currently loaded level
	if WORLDCOUNT:
		AIConnector.increaseWorldCount()
		print("World count increased to: ", AIConnector.getWorldCount()) # debug

	# draw world and take screenshot, if activated
	x_offset, y_offset = computeWorldOffset()
	draw(x_offset, y_offset)
	if SCREENSHOTS_ACTIVE:
		takeScreenshot()


# draw the score
def drawScore():
	position = VARIABLES['score_position'] if 'score_position' in VARIABLES else -1 # -1 = left, 0 = center, 1 = right
	if NUMBERS:
		blocksize = VARIABLES['blocksize']
		if position == -1:
			xpos = 0 # beginning of the score in blocks
		elif position == 1:
			xpos = SCREEN_SIZE_BLOCKS[0] - 4
		else:
			xpos = int(SCREEN_SIZE_BLOCKS[0] / 2) - 2
		for i in reversed(range(4)):
			z = int(((SCORE % (10 ** (i + 1))) - (SCORE % (10 ** i))) / (10 ** i)) # extract single digits
			SCREEN.blit(NUMBERS[z], (xpos * blocksize, 0))
			xpos = xpos + 1
	else: # fallback if no number graphics
		f = FONT.render("{:04d}".format(SCORE), False, (0, 0, 0))
		if position == -1:
			xpos = 0
		elif position == 1:
			xpos = SCREEN_RESOLUTION[0] - f.get_size()[0]
		else:
			xpos = int(SCREEN_RESOLUTION[0]/2.0 - f.get_size()[0]/2.0)
		SCREEN.blit(f, (xpos, 0))


# draw the world
def draw(x_offset=0, y_offset=0):
	SCREEN.fill((0, 0, 0))
	blocksize = VARIABLES['blocksize']
	for y in range(SCREEN_SIZE_BLOCKS[1]):
		if (y + y_offset < 0) or (y + y_offset >= len(WORLD)):
			continue
		for x in range(SCREEN_SIZE_BLOCKS[0]):
			if (x + x_offset < 0) or (x + x_offset >= len(WORLD[y])):
				continue
			xpos = x * blocksize
			ypos = y * blocksize
			block = WORLD[y + y_offset][x + x_offset]
			if (block != BLOCKS_NAME_TO_ID['AIR']) and (block != BLOCKS_NAME_TO_ID['GROUND']):
				SCREEN.blit(BLOCKGFX[BLOCKS_NAME_TO_ID['AIR']], (xpos, ypos)) # draw air background for anything except GROUND and AIR
			SCREEN.blit(BLOCKGFX[block], (xpos, ypos))
	SCREEN.blit(BLOCKGFX[-1], ((PLAYERPOS[0] - x_offset) * blocksize, (PLAYERPOS[1] - y_offset) * blocksize))
	drawScore()
	pg.display.flip()


# auxiliary method - returns block at given position or None if outside of world
def getBlockAt(coord):
	x, y = coord
	if (y < 0) or (y >= len(WORLD)):
		return None
	if (x < 0) or (x >= len(WORLD[y])):
		return None
	return WORLD[y][x]


# computes the next position of the player
# also handles gravity and collision detection
# returns a list of flags (events triggered by the movement, e.g. contact with an enemy)
def movePlayer(direction, jumpingPhase):
	global PLAYERPOS
	movementFlags = set()
	# move player up/down
	if jumpingPhase == 0: # apply gravity
		block = getBlockAt((PLAYERPOS[0], PLAYERPOS[1] + 1)) # get block below player
		if block == None:
			movementFlags.add('fall')
			return movementFlags # player fell off the world
		elif block != BLOCKS_NAME_TO_ID['GROUND']: # player will fall
			PLAYERPOS = (PLAYERPOS[0], PLAYERPOS[1] + 1)
	elif jumpingPhase > 0: # player is ascending
		block = getBlockAt((PLAYERPOS[0], PLAYERPOS[1] - 1)) # get block above player
		if (block != None) and (block != BLOCKS_NAME_TO_ID['GROUND']): # no obstacle above
			PLAYERPOS = (PLAYERPOS[0], PLAYERPOS[1] - 1)
	# elif jumpingPhase < 0: nothing to do here, player is "hovering" and will move neither up nor down

	# move player left/right
	block = getBlockAt((PLAYERPOS[0] + direction, PLAYERPOS[1]))
	if (block == None) or (block == BLOCKS_NAME_TO_ID['GROUND']): # collision detection
		movementFlags.add('not_moved')
	else:
		PLAYERPOS = (PLAYERPOS[0] + direction, PLAYERPOS[1])

	# add new position to history
	POSITION_X_HISTORY.append(PLAYERPOS[0])
	if len(POSITION_X_HISTORY) > POSITION_HISTORY_LENGTH:
		POSITION_X_HISTORY.pop(0) # this is slow on lists, but deques wouldn't be faster in this case

	# check current block / fill flaglist
	if getBlockAt((PLAYERPOS[0], PLAYERPOS[1] + 1)) == BLOCKS_NAME_TO_ID['GROUND']:
		movementFlags.add('on_ground') # player is on ground
	block = getBlockAt(PLAYERPOS) # block where player is
	if block == BLOCKS_NAME_TO_ID['ENEMY']:
		movementFlags.add('hit_enemy')
	elif block == BLOCKS_NAME_TO_ID['COIN']:
		movementFlags.add('hit_coin')
	elif block == BLOCKS_NAME_TO_ID['GOAL']:
		movementFlags.add('hit_goal')

	return movementFlags


# freezes the screen for some time. optionally clears it before
def freeze(sec, clear=False):
	if clear:
		SCREEN.fill((0, 0, 0))
		pg.display.flip()
	time.sleep(sec)


# sets the parameters to give to the AI
def generateAIParams():
	params = dict()
	params["score"] = SCORE
	params["x"] = PLAYERPOS[0]
	params["xDistanceToGoal"] = GOALPOS[0] - PLAYERPOS[0]
	params["deathCount"] = DEATH_COUNT
	params["levelBeatenCount"] = LEVEL_COUNT
	params["worldname"] = WORLDNAME  # currently not used
	# this sums up the moves of the player for the last frames (-1 for left, 1 for right)
	# then divides it by the amount of actions used
	# will be None for less than 5 values
	# currently not used
	params["historyMoveSum"] = (sum(map(lambda x, y: x - y, POSITION_X_HISTORY[1:], POSITION_X_HISTORY[:-1])))/float(len(POSITION_X_HISTORY)) if len(POSITION_X_HISTORY) >= 5 else None
	return params


# modifies the score by the given amount
# lower bound: 0
def modifyScore(amount):
	global SCORE
	SCORE = max(0, SCORE + amount)


# Computes the world offset.
# Tries to keep the player in the center of the screen, but without moving outside the level.
# minimum offset = 0
# maximum offset = world size - screen size (in blocks)
def computeWorldOffset():
	x_offset = PLAYERPOS[0] - int(SCREEN_SIZE_BLOCKS[0] / 2)
	x_offset = int(max(0, min(len(WORLD[0]) - SCREEN_SIZE_BLOCKS[0], x_offset)))
	y_offset = PLAYERPOS[1] - int(SCREEN_SIZE_BLOCKS[1] / 2)
	y_offset = int(max(0, min(len(WORLD) - SCREEN_SIZE_BLOCKS[1], y_offset)))
	return x_offset, y_offset



def takeScreenshot():
	# rename old screenshots, if any
	for sfile in sorted(os.listdir(SCREENSHOT_DIRECTORY), reverse=True):
		if (not sfile.startswith(SCREENSHOT_CURRENT_NAME)) and sfile.startswith(SCREENSHOT_OLD_PREFIX):
			sfcomp = os.path.splitext(sfile)  # split into name and extension
			sfprefix = sfcomp[0][:len(SCREENSHOT_OLD_PREFIX)]
			sfnumber = int(sfcomp[0][len(SCREENSHOT_OLD_PREFIX):])
			if sfnumber >= SCREENSHOT_OLD_COUNT - 1:
				os.remove(SCREENSHOT_DIRECTORY + sfile)
			else:
				os.rename(SCREENSHOT_DIRECTORY + sfile, "{}{}{:02d}{}".format(SCREENSHOT_DIRECTORY, sfprefix, sfnumber + 1, sfcomp[1]))
	# create new screenshot
	pg.image.save(pg.transform.scale(SCREEN, SCREENSHOT_CURRENT_SIZE), SCREENSHOT_DIRECTORY + SCREENSHOT_CURRENT_NAME + SCREENSHOT_EXTENSION)
	if SCREENSHOT_OLD_COUNT > 0:
		pg.image.save(pg.transform.scale(SCREEN, SCREENSHOT_OLD_SIZE), SCREENSHOT_DIRECTORY + SCREENSHOT_OLD_PREFIX + "00" + SCREENSHOT_EXTENSION)


# main
loadPaths(r"paths.txt")
init()
init_world(chooseWorld(LEVEL_PREFIX, LEVEL_PATTERN))

# start AI
if MODE == 0:
	print("Initializing AI ...")
	import AIConnector
	print("Setting AI screenshot folder to: ", 	AIConnector.setScreenshotPath(SCREENSHOT_DIRECTORY + SCREENSHOT_CURRENT_NAME + SCREENSHOT_EXTENSION))
	print("AI Initialization complete.")
	print("AI Action Count: ", AIConnector.getActionCount())
	AIConnector.increaseWorldCount() # compensate for missed call in init_world
	WORLDCOUNT = AIConnector.getWorldCount()
	print("AI World Count: ", WORLDCOUNT)

gameRunning = True
'''
How jumping works:
jumping saves how often the character has jumped since his last contact with the ground. This is needed for double-jump.
jumpingPhase indicates the current phase of jumping:
	positive number: the character is ascending. He will ascend as many blocks as given here, one per tick.
	negative number: the character finished ascending and is now "hovering" at the highest point of the jump. 
		This counts for how many ticks he is hovering.
	zero: the character is not jumping right now => gravity applies
'''
jumping = 0
jumpingPhase = 0
'''
movementFlags will contain flags that describe the outcome of a movement action. 
Possible flags:
	on_ground
		the character is on the ground
	not_moved
		the character wasn't moved (probably he ran against a wall or something like that)
		doesn't apply to jumping (not set if the character can't move upward because of some obstacle)
	hit_coin
		the character has moved over a coin
	hit_enemy
		the character has moved in an enemy
	hit_goal
		the character has moved to the goal
	fall
		the character fell out of the world
'''
movementFlags = set()
clock = pg.time.Clock()
freezeTime = 0 if FPS == 0 else (1.0/FPS) * 5
while gameRunning:
	if FPS > 0:
		clock.tick(FPS)
	movementFlags.clear()
	move = 0
	action = ACTION_NO_ACTION

	if MODE == 0: # game is played by the AI
		# check wether a new level was requested by the AI
		if AIConnector.getReload():
			freeze(freezeTime)
			freeze(freezeTime, True)
			jumping = 0
			jumpingPhase = 0
			init_world(chooseWorld(LEVEL_PREFIX, LEVEL_PATTERN))
		# check if maximum amount of training frames is reached
		if 0 < MAX_TRAINED_FRAMES < AIConnector.getActionCount():
			print("Set number of frames to train reached ({}). The game will now quit.".format(MAX_TRAINED_FRAMES))
			gameRunning = False
			break
		# set parameters for AI script
		AIConnector.setParams(generateAIParams())
		# run AI script
		action = AIConnector.getAction()
	# elif MODE == 1: # game is played by a human
	events = pg.event.get()
	for ev in events:
		if ev.type == pg.QUIT:
			gameRunning = False
		elif ev.type == pg.KEYDOWN:
			if ev.key == K_ESCAPE:
				gameRunning = False
			elif ev.key == K_RIGHT:
				action = ACTION_RIGHT
			elif ev.key == K_LEFT:
				action = ACTION_LEFT
			elif ev.key == K_UP:
				action = ACTION_JUMP
			else: # some event that is not of interest
				continue
		break # only one event is handled at a time, the rest is discarded

	FRAME_COUNTER = FRAME_COUNTER + 1
	if FRAME_COUNTER % 1000 == 0:
		print("Frame: {}".format(FRAME_COUNTER))

	# progress action
	if action == ACTION_RIGHT:
		move = 1
	elif action == ACTION_LEFT:
		move = -1
	elif action == ACTION_JUMP:
		if jumping < VARIABLES['jump']: # character can still jump
			jumping += 1
			jumpingPhase = VARIABLES['jump_height']

	# update move statistics
	MOVES_COUNT[action] = MOVES_COUNT[action] + 1

	# update player movement
	movementFlags = movePlayer(move, jumpingPhase)

	# update jumping state
	if (jumpingPhase > 1) or (jumpingPhase < 0):
		jumpingPhase -= 1
	elif jumpingPhase == 1:
		jumpingPhase = -1
	if jumpingPhase < (-1) * VARIABLES['jump_width']: # end of hovering
		jumpingPhase = 0

	# compute offset
	x_offset, y_offset = computeWorldOffset()

	# draw world
	draw(x_offset, y_offset)

	# take screenshots (if activated)
	if SCREENSHOTS_ACTIVE:
		takeScreenshot()

	# interprete movementFlags
	for flag in movementFlags:
		if (flag == 'fall') or (flag == 'hit_enemy'): # apply death penalty and respawn player
			modifyScore(VARIABLES['death_worth'])
			DEATH_COUNT = DEATH_COUNT + 1
			PLAYERPOS = SPAWNPOS
			freeze(freezeTime)
			freeze(freezeTime, True)
		elif flag == 'hit_coin': # remove coin and grant points
			if getBlockAt(PLAYERPOS) == BLOCKS_NAME_TO_ID['COIN']: # should always be the case, just to be sure ...
				WORLD[PLAYERPOS[1]][PLAYERPOS[0]] = BLOCKS_NAME_TO_ID['AIR'] # remove coin
				modifyScore(VARIABLES['coin_worth']) # grant points
				COIN_COUNT = COIN_COUNT + 1 # update statistics
		elif flag == 'hit_goal':
			modifyScore(VARIABLES['goal_worth'])
			LEVEL_COUNT = LEVEL_COUNT + 1
			draw(x_offset, y_offset) # draw level to show increased score
			'''
			if MODE == 0:
				# dummy call to the AI to inform about increased score
				if SCREENSHOTS_ACTIVE:
					takeScreenshot()
				AIConnector.setParams(generateAIParams())
				AIConnector.getAction() # dummy AI call, ignore return value
				FRAME_COUNTER = FRAME_COUNTER + 1 # synchronize FRAME_COUNTER with AIConnector.getActionCount()
			'''
			freeze(freezeTime)
			freeze(freezeTime, True)
			jumping = 0
			jumpingPhase = 0
			# load random new level
			init_world(chooseWorld(LEVEL_PREFIX, LEVEL_PATTERN))
		elif flag == 'on_ground': # update jumping
			jumping = 0
			jumpingPhase = 0

# end stuff
STATISTICS_FILE.close()
if MODE == 0:
	AIConnector.cleanup()
