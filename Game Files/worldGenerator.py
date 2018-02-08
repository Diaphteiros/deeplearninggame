import random
from worldSaver import getWorldAsString, saveWorld
import os


# constants - graphics
BLOCK_SIZE = 32 # 32x32 pixel per tile
GFX_DIRECTORY = r"gfx/"
GFX = dict()
for directory in filter(lambda x: os.path.isdir(os.path.join(GFX_DIRECTORY, x)), os.listdir(GFX_DIRECTORY)):
	dir_c = os.path.join(GFX_DIRECTORY, directory)
	GFX[directory] = list(filter(lambda x: os.path.isfile(x) and x.endswith(r".png"), [os.path.join(dir_c, f) for f in os.listdir(dir_c)]))


# constants - blocks
BLOCKS_NAME_TO_ID = dict()
BLOCKS_NAME_TO_ID['PLAYER'] = -1
BLOCKS_NAME_TO_ID['AIR'] = 0
BLOCKS_NAME_TO_ID['GROUND'] = 1
BLOCKS_NAME_TO_ID['ENEMY'] = 2
BLOCKS_NAME_TO_ID['COIN'] = 3
BLOCKS_NAME_TO_ID['SPAWN'] = 4
BLOCKS_NAME_TO_ID['GOAL'] = 5


# constants - game
JUMP = 0
JUMP_HEIGHT = 0
JUMP_WIDTH = 0
SCORE_POSITION = 0


# constants - world generation
WORLD_SIZE_X = 0
WORLD_SIZE_Y = 0
MAX_HEIGHT_DIFF = 0
MAX_HEIGHT_TERRAIN = 0
HEIGHT_CHANGE_PROBABILITY = 0
HEIGHT_UP_PROBABILITY = 0
HEIGHT_DOWN_FACTOR = 0
ENEMY_SPAWN_PROBABILITY = 0
ENEMY_MAX_WIDTH = 0
ENEMY_MAX_HEIGHT = 0
ENEMY_GROW_PROBABILITY = 0
SPAWN_AREA_PERCENTAGE = 0
SPAWN_LEFT_PROBABILITY = 0
COIN_SPAWN_PROBABILITY = 0


# sets constants (game and world generation section) to default values
def resetVariables():
	global JUMP, JUMP_HEIGHT, JUMP_WIDTH, SCORE_POSITION, WORLD_SIZE_X, WORLD_SIZE_Y, MAX_HEIGHT_DIFF, MAX_HEIGHT_TERRAIN, HEIGHT_CHANGE_PROBABILITY, HEIGHT_UP_PROBABILITY, HEIGHT_DOWN_FACTOR, ENEMY_SPAWN_PROBABILITY, ENEMY_MAX_WIDTH, ENEMY_MAX_HEIGHT, ENEMY_GROW_PROBABILITY, SPAWN_AREA_PERCENTAGE, SPAWN_LEFT_PROBABILITY, COIN_SPAWN_PROBABILITY
	JUMP = 1  # how often player can jump before it has to touch ground again
	JUMP_HEIGHT = 3  # jump height
	JUMP_WIDTH = 3  # jump width
	SCORE_POSITION = -1  # -1 = left, 0 = center, 1 = right

	WORLD_SIZE_X = 75  # width of the world to be generated (in blocks)
	WORLD_SIZE_Y = 20  # height of the world to be generated (in blocks)
	MAX_HEIGHT_DIFF = JUMP_HEIGHT * JUMP  # maximum height change of ground terrain
	MAX_HEIGHT_TERRAIN = int(round((1.0 / 2.0) * WORLD_SIZE_Y))  # maximum height of ground terrain (in array positions, so terrain can be 1 higher than this value)
	HEIGHT_CHANGE_PROBABILITY = 0.2  # probability that the terrain height changes
	HEIGHT_UP_PROBABILITY = 0.5  # probability that in case of a height change, the height will go up (as opposed to down)
	HEIGHT_DOWN_FACTOR = 0.01  # will be multiplied with the current height level and subtracted from HEIGHT_UP_PROBABILITY (will prevent increasing ground height levels)
	ENEMY_SPAWN_PROBABILITY = 0.15  # on what percentage of possible positions enemies should spawn
	ENEMY_MAX_WIDTH = 1  # after how many enemy blocks next to each other there needs to be a free space (lowest value: 1)
	ENEMY_MAX_HEIGHT = JUMP_HEIGHT  # maximum enemy height
	ENEMY_GROW_PROBABILITY = 0.25  # probability at which an enemy will grow (if possible)
	SPAWN_AREA_PERCENTAGE = 0.2  # spawn and goal will be placed somewhere in the first and last part of the world as specified by this constant.
	SPAWN_LEFT_PROBABILITY = 1.0  # probability of having spawn left and goal right (opposed to the other way around)
	COIN_SPAWN_PROBABILITY = 0.05  # on what percentage of possible positions coins should spawn


'''
Takes a column and checks this column from bottom to top. Has two modes: 
groundOnly (default): The number of ground blocks before the first block of anything else is returned. Only counts GROUND blocks.
not groundOnly: Gives the number of blocks between the bottom and the first block of AIR. Should always be equal to or greater than the groundOnly option. Counts any block until AIR is found.
'''
def getHeightLevel(world, col, groundOnly = True):
	for y in range(WORLD_SIZE_Y - 1, -1, -1):
		if world[y][col] == BLOCKS_NAME_TO_ID['GROUND']: # GROUND is found: continue
			continue
		elif groundOnly or world[y][col] == BLOCKS_NAME_TO_ID['AIR']: # groundOnly is active and something else was found or AIR was found: return number of GROUND blocks
			return WORLD_SIZE_Y - y - 1
	return -2


def generateWorld(defaultValues=False):
	# ATTENTION: since the world is saved row-wise, the first coordinate is Y, not X!
	if defaultValues:
		resetVariables()
	world = [[0 for _ in range(WORLD_SIZE_X)] for _ in range(WORLD_SIZE_Y)]
	generateGround(world)
	generateSpawnAndGoal(world)
	generateEnemies(world)
	generateCoins(world)
	return world


def generateGround(world):
	heightLevel = random.randint(0, MAX_HEIGHT_TERRAIN) # how high the ground is at the moment (0 means one block of GROUND here!)
	for x in range(WORLD_SIZE_X):
		if random.random() < HEIGHT_CHANGE_PROBABILITY:
			# height changes
			heightLevel = heightLevel + random.randint(1, MAX_HEIGHT_DIFF) * (1 if random.random() < (HEIGHT_UP_PROBABILITY - heightLevel * HEIGHT_DOWN_FACTOR) else (-1))
			heightLevel = max(0, min(MAX_HEIGHT_TERRAIN, heightLevel)) # cut to allowed ranges
		for y in range(heightLevel + 1): # slice assigning is difficult in a two-dimensional list ...
			world[-(y+1)][x] = BLOCKS_NAME_TO_ID['GROUND']
			

def generateSpawnAndGoal(world):
	firstPart = [x for x in range(0, max(1, int(WORLD_SIZE_X * SPAWN_AREA_PERCENTAGE)), 1)]
	lastPart = [x for x in range(WORLD_SIZE_X - len(firstPart), WORLD_SIZE_X, 1)]
	spawn = -1
	goal = -1
	if random.random() < SPAWN_LEFT_PROBABILITY:
		spawn = random.choice(firstPart)
		try:
			lastPart.remove(spawn) # enforce different positions for spawn and goal
		except ValueError:
			pass
		goal = random.choice(lastPart)
	else:
		spawn = random.choice(lastPart)
		try:
			lastPart.remove(spawn) # enforce different positions for spawn and goal
		except ValueError:
			pass
		goal = random.choice(firstPart)
	world[WORLD_SIZE_Y - getHeightLevel(world, spawn) - 1][spawn] = BLOCKS_NAME_TO_ID['SPAWN']
	world[WORLD_SIZE_Y - getHeightLevel(world, goal) - 1][goal] = BLOCKS_NAME_TO_ID['GOAL']


def generateEnemies(world):
	# restriction: terrain + enemy height must not exceed maximum height difference to either side
	# in addition, at least one space between enemies
	# enemies are only placed on the ground at the moment
	# TODO: check that there is at least one free space between an enemy and the upper end of the world
	hl_prev = -1 # height level of last column
	hl_curr = -1 # height level of current column
	hl_next = getHeightLevel(world, 0) if getHeightLevel(world, 0, True) == getHeightLevel(world, 0, False) else -1 # height level of next column
	consecutiveEnemies = 0 # whether an enemy was placed
	for x in range(WORLD_SIZE_X):
		# update height levels
		hl_prev = hl_curr
		hl_curr = hl_next
		hl_next = getHeightLevel(world, x + 1) if x < WORLD_SIZE_X - 1 and getHeightLevel(world, x + 1, True) == getHeightLevel(world, x + 1, False) else -1
		# check whether enemy placement is possible
		if (hl_curr < 0 or hl_prev < 0 or hl_next < 0) or (consecutiveEnemies >= ENEMY_MAX_WIDTH): # something is between GROUND and AIR here / to many enemies placed next to each other
			consecutiveEnemies = 0
			continue
		
		heightDiff = max(abs(hl_curr - hl_prev), abs(hl_curr - hl_next))
		if heightDiff < MAX_HEIGHT_DIFF: # enemy placing is possible
			if random.random() < ENEMY_SPAWN_PROBABILITY: # spawn enemy here
				enemySize = 1
				while (enemySize < MAX_HEIGHT_DIFF - heightDiff) and (random.random() < ENEMY_GROW_PROBABILITY): # create higher enemies
					enemySize += 1
				enemySize = min(enemySize, MAX_HEIGHT_DIFF - heightDiff)
				for i in range(enemySize):
					world[WORLD_SIZE_Y - hl_curr - 1 - i][x] = BLOCKS_NAME_TO_ID['ENEMY']
				consecutiveEnemies += 1
			else:
				consecutiveEnemies = 0


def generateCoins(world):
	hl_prev = -1 # height level of last column
	hl_curr = -1 # height level of current column
	hl_next = getHeightLevel(world, 0) if getHeightLevel(world, 0, True) == getHeightLevel(world, 0, False) else -1 # height level of next column
	for x in range(WORLD_SIZE_X):
		hl_prev = hl_curr
		hl_curr = hl_next
		hl_next = getHeightLevel(world, x + 1) if x < WORLD_SIZE_X - 1 and getHeightLevel(world, x + 1, True) == getHeightLevel(world, x + 1, False) else -1
		maxh = WORLD_SIZE_Y - max(hl_prev, hl_curr, hl_next) - MAX_HEIGHT_DIFF - 2
		if maxh == -1: # something in between ground and air on this and on the neighboring columns
			continue # don't place coins here
		for y in range(WORLD_SIZE_Y - getHeightLevel(world, x, False) - 1, max(0, maxh), -1):
			if random.random() < COIN_SPAWN_PROBABILITY:
				world[y][x] = BLOCKS_NAME_TO_ID['COIN']


# change this method to change the randomization of parameters
def randomizeParameters():
	global JUMP, JUMP_HEIGHT, JUMP_WIDTH, WORLD_SIZE_X, WORLD_SIZE_Y, MAX_HEIGHT_DIFF, MAX_HEIGHT_TERRAIN, HEIGHT_CHANGE_PROBABILITY, HEIGHT_DOWN_FACTOR, ENEMY_SPAWN_PROBABILITY, ENEMY_MAX_WIDTH, ENEMY_MAX_HEIGHT, ENEMY_GROW_PROBABILITY, SCORE_POSITION
	WORLD_SIZE_X = random.randint(50, 75) # tendency towards shorter levels
	MAX_HEIGHT_DIFF = random.randint(2, 3) # more flat levels
	HEIGHT_CHANGE_PROBABILITY = 0.2 - (0.1 * random.random()) # more flat levels
	HEIGHT_DOWN_FACTOR = 0.01 + random.random() * 0.09 # more flat levels
	ENEMY_SPAWN_PROBABILITY = 0.1 + random.random() * 0.05 # tendency towards fewer enemies
	ENEMY_GROW_PROBABILITY = 0.1 + random.random() * 0.15
	#SCORE_POSITION = random.choice([-1, 0, 1])


# change this method to change the randomization of the block graphics
def randomizeBlockGFX():
	global SCORE_POSITION
	tiles = dict()
	for k, v in BLOCKS_NAME_TO_ID.items():
		if k.lower() in GFX.keys():
			tiles[v] = random.choice(GFX[k.lower()])
	#SCORE_POSITION = random.choice([-1, 0, 1])
	return tiles


def generateManyWorlds(amount, naming_template, printWorld=False, randomizeParams=False, randomizeGFX=False):
	for i in range(amount):
		resetVariables() # reset variables to default values
		if randomizeParams:
			randomizeParameters()
		tiles = dict()
		if randomizeGFX:
			tiles = randomizeBlockGFX()
		world = generateWorld()
		if printWorld:
			print(getWorldAsString(world))
		variables = {'blocksize': BLOCK_SIZE, 'jump': JUMP, 'jump_height': JUMP_HEIGHT, 'jump_width': JUMP_WIDTH, 'score_position': SCORE_POSITION}
		saveWorld(world, naming_template.format(i), BLOCKS_NAME_TO_ID, True, variables, tiles)




# main

resetVariables()

generateManyWorlds(1000, r"levels/training_{}.txt", printWorld=False, randomizeParams=True, randomizeGFX=False)
