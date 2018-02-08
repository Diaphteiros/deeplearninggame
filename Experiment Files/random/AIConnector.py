# DUMMY IMPLEMENTATION FOR RANDOM ACTIONS

import random

ACTION_COUNT = 0
WORLD_COUNT = 0


# calls setParams in AIConnector.lua
# giving the dict as argument is possible, but it won't be a lua table then, which could cause trouble
#   therefore a serialized version is given and reconstructed in lua
# returns the set dict (serialized in lua style) (for debugging purposes mainly)
def setParams(params):
	return "set params call"


# calls the getAction() method from AIConnector.lua and forwards its return value
def getAction():
	global ACTION_COUNT
	ACTION_COUNT = ACTION_COUNT + 1
	return random.randint(0, 3)


# sets the global SCREENSHOT_FILEPATH in lua
def setScreenshotPath(path):
	return path # for debugging


# returns wether the AI requested a new level to be loaded (boolean)
def getReload():
	return ACTION_COUNT % 1000 == 0


# returns the action counter
def getActionCount():
	return ACTION_COUNT


# returns world count
def getWorldCount():
	return WORLD_COUNT


# increases world count by given amount
def increaseWorldCount(amount=1):
	global WORLD_COUNT
	WORLD_COUNT = WORLD_COUNT + amount
	return WORLD_COUNT


# cleanup at program end (close open files etc)
def cleanup():
	pass
