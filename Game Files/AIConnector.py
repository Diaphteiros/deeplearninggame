import DLFCN
import sys
sys.setdlopenflags(DLFCN.RTLD_NOW | DLFCN.RTLD_GLOBAL)
import lua
from utils import isNumber

# path to the main lua file
PATH_TO_LUA_MAIN = "train.lua"

# for lua interface
LG = lua.globals()

# loads the AI
LG.dofile(PATH_TO_LUA_MAIN)


# calls setParams in AIConnector.lua
# giving the dict as argument is possible, but it won't be a lua table then, which could cause trouble
#   therefore a serialized version is given and reconstructed in lua
# returns the set dict (serialized in lua style) (for debugging purposes mainly)
def setParams(params):
	cmd = "{"
	for key, value in params.items():
		if value is None:
			cmd += "{}=nil, ".format(key)
		elif isNumber(value):
			cmd += "{}={}, ".format(key, value) # no quotes needed for numbers
		else:
			cmd += "{}=\"{}\", ".format(key, value) # lua table constructor ignores trailing commas, so this is fine
	cmd += "}"
	LG.aiconnector.setParams(lua.eval(cmd))
	return cmd


# calls the getAction() method from AIConnector.lua and forwards its return value
def getAction():
	return LG.aiconnector.getAction()


# sets the global SCREENSHOT_FILEPATH in lua
def setScreenshotPath(path):
	LG.SCREENSHOT_FILEPATH = path
	return path # for debugging


# returns wether the AI requested a new level to be loaded (boolean)
def getReload():
	return LG.aiconnector.getReload()


# returns the action counter
def getActionCount():
	return LG.aiconnector.getActionCount()


# returns world count
def getWorldCount():
	return LG.aiconnector.getWorldCount()


# increases world count by given amount
def increaseWorldCount(amount=1):
	return LG.aiconnector.increaseWorldCount(amount)


# cleanup at program end (close open files etc)
def cleanup():
	LG.aiconnector.cleanup()
