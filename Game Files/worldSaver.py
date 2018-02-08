from os.path import isfile, isdir


def getWorldAsString(world):
	return '\n'.join([' '.join([str(x) for x in y]) for y in world])



def saveWorld(world, w_name, BLOCKS_NAME_TO_ID={'AIR':0, 'GROUND':1, 'ENEMY':2, 'COIN':3, 'SPAWN':4, 'GOAL':5}, w_overwrite=False, info={}, w_tiles={}):
	if (not w_overwrite) and (isfile(w_name) or isdir(w_name)):
		raise IOError("File {} already exists!".format(w_name))
	
	f = open(w_name, 'w')
	f.write("!info\n")
	for k, v in info.items():
		f.write("{0}={1}\n".format(k, v))
	f.write("!blocks\n")
	for k, v in BLOCKS_NAME_TO_ID.items():
		f.write("{0}={1}\n".format(k, v))
	f.write("!blockgfx\n")
	for k, v in w_tiles.items():
		f.write("{0}={1}\n".format(k, v))
	f.write("!world\n")
	f.write(getWorldAsString(world))
	f.write("\n")
	f.close()



def loadWorld(fileName):
	wf = open(fileName, 'r')
	mode = "null"
	info = {}
	BLOCKS_NAME_TO_ID = {}
	blockgfx = {}
	world = []
	for raw_line in wf:
		line = raw_line[:-1]
		if (len(line) == 0) or (line[0] == "#") or (mode == "null" and line[0] != "!"):
			continue # ignore things after # and before any category specifier
		
		if line[0] == "!":
			mode = line[1:] # set mode
			continue
		
		# differentiate modes
		if mode == "info": # mode == info - general variables
			tmp = line.split("=")
			info[tmp[0]] = tmp[1]
		elif mode == "blocks": # mode == blocks - dictionary with mappings from words to numbers
			tmp = line.split("=")
			BLOCKS_NAME_TO_ID[tmp[0].upper()] = int(tmp[1])
		elif mode == "blockgfx": # mode == blockgfx - graphic files for tiles
			tmp = line.split("=")
			blockgfx[int(tmp[0])] = tmp[1]
		elif mode == "world":
			world.append([int(z) for z in line.split(" ")])
		else:
			print("Could not interprete: mode={}, line={}\n".format(mode, line))
		
	return (info, BLOCKS_NAME_TO_ID, blockgfx, world)

