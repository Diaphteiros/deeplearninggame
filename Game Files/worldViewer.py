import pygame as pg
from pygame.locals import *
from worldSaver import loadWorld
import sys



def drawWorld(screen, world, BLOCKS_NAME_TO_ID, gfx, blocksize=32, x_offset=0, y_offset=0):
	screen.fill((0, 0, 0))
	x_max, y_max = screen.get_size()
	# recover number of blocks in both directions
	x_size = int(x_max / blocksize)
	if x_max % blocksize != 0: x_size += 1
	y_size = int(y_max / blocksize)
	if y_max % blocksize != 0: y_size += 1
	# for every block: draw
	for y in range(y_size):
		if (y + y_offset < 0) or (y + y_offset >= len(world)):
			continue
		for x in range(x_size):
			if (x + x_offset < 0) or (x + x_offset >= len(world[y])):
				continue
			xpos = x * blocksize
			ypos = y * blocksize
			block = world[y + y_offset][x + x_offset]
			if (block != BLOCKS_NAME_TO_ID['AIR']) and (block != BLOCKS_NAME_TO_ID['GROUND']):
				screen.blit(gfx[BLOCKS_NAME_TO_ID['AIR']], (xpos, ypos)) # draw air background for anything except GROUND and AIR
			screen.blit(gfx[block], (xpos, ypos))


def showWorld(info, BLOCKS_NAME_TO_ID, blockgfx, world):
	x_offset = 0
	y_offset = 0
	blocksize = int(info['blocksize']) if ('blocksize' in info) else 32
	blocks = set()
	for row in world: # find all different kinds of blocks
		for element in row:
			if element == '': # ... no idea what this is
				continue
			blocks.add(int(element))
	
	# load images
	gfx = {} 
	inverted_blocks = {v: k for k, v in BLOCKS_NAME_TO_ID.items()}
	for b in blocks:
		gfxpath = blockgfx[b] if (b in blockgfx) else ("gfx/{}/primitive.png".format(inverted_blocks[b].lower()))
		gfx[b] = pg.image.load(gfxpath)
	
	# draw part of world
	screen = pg.display.set_mode((30*blocksize, 20*blocksize), pg.constants.DOUBLEBUF)
	drawWorld(screen, world, BLOCKS_NAME_TO_ID, gfx)
	pg.display.flip()
	pg.key.set_repeat(300, 50)
	while True:
		ev = pg.event.wait()
		if ev.type == pg.QUIT:
			exit()
		elif ev.type == pg.KEYDOWN:
			if ev.key == K_RIGHT:
				x_offset += 1
			elif ev.key == K_LEFT:
				x_offset -= 1
			elif ev.key == K_DOWN:
				y_offset += 1
			elif ev.key == K_UP:
				y_offset -= 1
			elif ev.key == K_ESCAPE:
				exit()
			else:
				continue
			drawWorld(screen, world, BLOCKS_NAME_TO_ID, gfx, blocksize, x_offset, y_offset)
			pg.display.flip()




# main
if len(sys.argv) < 2:
	print("No world given!")
	exit()

info, BLOCKS_NAME_TO_ID, blockgfx, world = loadWorld(sys.argv[1])
showWorld(info, BLOCKS_NAME_TO_ID, blockgfx, world)
