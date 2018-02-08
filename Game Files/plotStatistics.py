import matplotlib.pyplot as plt
from utils import convertToNumberIfPossible
import sys
from os.path import isfile
from cycler import cycler


# STRUCTURE
# dict
#   frames
#       list
#           1000
#           1000
#   deaths
#       list
#           0
#           3
#   moves
#       dict
#           left
#               list
#                   248
#                   105
#           right
#               list
#                   310
#                   528


# loads the data into python
def loadData(directory):
	# read losses
	loss_data = list()
	losspath = directory + r"losses.txt"
	if isfile(losspath):
		f = open(losspath)
		for line in f:
			loss_data.append(convertToNumberIfPossible(line[:-1]))
		f.close()

	# read statistics data
	stat_data = dict()
	heads = None # contains the headlines
	heads_nested = dict() # contains nested headlines, e.g. for move: move -> [no action, left, right, jump]
	f = open(directory + r"statistics.csv")
	for line in f:
		if not stat_data: # dict is empty -> first line
			heads = line.split(";") # read headlines
			for s in heads:
				if "," in s:
					stat_data[s] = dict() # create dict for nested lists (currently only for move count)
					heads_nested[s] = s[s.find("(") + 1:s.find(")")].split(", ") # extract nested heads
					for h in heads_nested[s]:
						stat_data[s][h] = list() # create nested lists
				elif s.lstrip().startswith('!'): # marks a non-number column - ATTENTION: There can't be number columns after a non-number one!
					heads.remove(s) # the following code can't handle non-number values
				else:
					stat_data[s] = list() # create lists for statistics entries
		else:
			tmp = line.split(";")
			for i in range(len(heads)):
				if str(tmp[i]).startswith(r"["):
					# currently only the case for movement - there are lists with 4 values each in here
					# split values
					nested_tmp = tmp[i][1:-1].split(", ") # extract values
					j = 0
					for nh in heads_nested[heads[i]]: # iterate nested heads
						stat_data[heads[i]][nh].append(convertToNumberIfPossible(nested_tmp[j])) # append next value to corresponding list
						j = j + 1
				else:
					stat_data[heads[i]].append(convertToNumberIfPossible(tmp[i]))
	f.close()
	return loss_data, stat_data


# unifies the stat_data
# assumes the key unifyOn to be some kind of "frames since last line" counter and adds lines up until
# this value reaches (or exceeds) a unifyTo
# ATTENTION: wrongly accumulates "per frame" data
def unifyData(stat_data, unifyOn, unifyTo):
	i = 0 # index
	l = len(stat_data[unifyOn]) # amount of entries
	adds = 0 # amount of added up lines (for debugging)
	while i < l:
		while stat_data[unifyOn][i] < unifyTo and i < l-1: # sum up lines
			for _, value in stat_data.items(): # iterate over all columns
				if isinstance(value, dict): # check for nested lists
					for _, v in value.items(): # iterate over nested lists
						v[i] = v[i] + v[i+1]
						del v[i+1]
				else: # no nested lists
					value[i] = value[i] + value[i+1]
					del value[i+1]
			l = l - 1 # decrement amount of entries due to deletions
			adds = adds + 1
		if stat_data[unifyOn][i] > unifyTo:
			print(stat_data[unifyOn][i], i + adds)
		i = i + 1 # increment index
	return stat_data


# iteratively computes the mean of the data
# ignores nested lists
def computeMeanData(stat_data):
	mean_data = dict()
	for key, value in stat_data.items():
		if not isinstance(value, dict): # ignore nested lists
			mean = 0
			t = 0
			l = list()
			for z in value:
				t = t + 1
				mean = mean + (1.0 / t) * (z - mean)
				l.append(mean)
			mean_data[key] = l
	return mean_data


# iteratively computes mean of loss data
def computeLossMeanData(loss_data):
	lm_data = list()
	mean = 0
	t = 0
	for z in loss_data:
		t = t + 1
		mean = mean + (1.0 / t) * (z - mean)
		lm_data.append(mean)
	return lm_data


# plots the loaded data
def plotData(loss_data, stat_data, mean_data=None, lossmean_data=None):
	plot_index = 1

	# plot losses
	plt.figure(plot_index)
	plt.plot(loss_data, color="r", marker=r".", markersize="1.0", linestyle="None")
	if lossmean_data:
		plt.plot(lm_data)
	plt.title("Loss")
	# plt.xlabel("time (frames)")
	plt.ylabel("loss")

	# plot statistics
	for key, value in stat_data.items():
		plot_index = plot_index + 1
		plt.figure(plot_index)
		if isinstance(value, dict): # we have nested lists here
			# plot values
			legend_list = list()
			for k, v in sorted(value.items()): # sort for comparability to other plots
				legend_list.append(k)
				plt.plot(v, marker=r".", linestyle="None")
			plt.legend(legend_list)
		else:
			# should be a list of numbers, just plot it
			plt.plot(value, linewidth=0.5)
			if mean_data and mean_data[key]:
				plt.plot(mean_data[key])
		plt.title(key)
		plt.xlabel("1000 frames")  # DEBUG

	# print averages, if known
	if mean_data or lossmean_data:
		print("----- Averages -----")
	if mean_data:
		for k, v in mean_data.items():
			print(k, v[-1])
	if lossmean_data:
		print("loss", lossmean_data[-1])

	# show plots
	plt.show()


# takes a dict containing (mean loss data, mean stat data) as value
# plots same data to the same graph using the keys as legend
# won't plot nested lists
def plotManyData(data):
	max_plot_index = 1 # maximum used plot index

	headToPlotIndex = dict() # maps stat data heads to fitting plot indices
	legend_list = list()

	# plot data
	for key, (loss_data, stat_data) in sorted(data.items()):
		legend_list.append(key) # add current stat file to legend

		# plot losses
		plt.figure(1) # loss figure
		plt.plot(loss_data)

		# plot statistics
		for k, v in stat_data.items():
			if k not in headToPlotIndex:
				max_plot_index = max_plot_index + 1
				headToPlotIndex[k] = max_plot_index

			plt.figure(headToPlotIndex[k])
			plt.plot(v)

	# add legend and title
	plt.figure(1)
	plt.legend(legend_list, loc=2)
	plt.title("loss")
	plt.ylabel("loss")
	for k, v in headToPlotIndex.items():
		plt.figure(v)
		plt.legend(legend_list, loc=2)
		plt.title(k)
		plt.xlabel("1000 frames")  # DEBUG

	# show plots
	plt.show()







###### main ######
# check command line arguments
if len(sys.argv) > 2:
	# multiple file mode
	# extend pyplot color cycle to use other line types when it runs out of colors
	plt.rc('axes', prop_cycle=cycler('linestyle', ['-', '--', ':', '-.']) * plt.rcParams['axes.prop_cycle'])
	# print only mean data
	data = dict()
	for path in sys.argv[1:]: # load all given data files
		if path[-1] != r"/":
			path = path + r"/"
		data[path[:-1]] = loadData(path)
	for key, (l_data, s_data) in data.items(): # enhance data
		data[key] = (computeLossMeanData(l_data), computeMeanData(unifyData(s_data, "frames since last update", 1000))) # changing entries while iterating should be fine
	plotManyData(data) # plot data
else:
	# single file mode
	if len(sys.argv) > 1:
		path = sys.argv[1]
		if path[-1] != r"/":
			path = path + r"/"
	else:
		path = r"learned/"
	l_data, s_data = loadData(path)
	unifyData(s_data, "frames since last update", 1000)
	m_data = computeMeanData(s_data)
	lm_data = computeLossMeanData(l_data)
	plotData(l_data, s_data, m_data, lm_data)
