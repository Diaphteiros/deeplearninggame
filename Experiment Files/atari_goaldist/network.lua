-- Network functions.
-- E.g.:
--   - Creating the model
--   - Converting chains of states to training batches
--   - Forward/backward of batches
--   - Using the model to approximate good actions for a chain of states
require 'torch'
require 'paths'
require 'nn'
require 'layers.Rectifier'
require 'stn'


local network = {}

-- Load a saved model or return nil.
function network.load(fp)
	fp = fp or "learned/network.th7"
	if paths.filep(fp) then
		local savedData = torch.load(fp)
		return savedData
	else
		print("[INFO] Could not load previously saved network, file does not exist.")
		return nil
	end
end

-- Save the model to the save file.
function network.save(fp)
	fp = fp or "learned/network.th7"
	network.prepareNetworkForSave(Q)
	torch.save(fp, Q)
end

-- Tries to load the network from the save file. If that fails, it creates a new network.
function network.createOrLoadQ()
	local loaded = network.load()
	if loaded == nil then
		return network.createAtari()
	else
		return loaded
	end
end

function network.createAtari()
	-- set params to default values
	local args = {}
	-- from convnet_atari3
	args.n_units = {32, 64, 64}
	args.filter_size = {8, 4, 3}
	args.filter_stride = {4, 2, 1}
	args.n_hid = {512}
	args.nl = nn.Rectifier
	-- the rest
	args.hist_len = STATES_PER_EXAMPLE -- length of the history, hopefully
	args.ncols = 1 -- amount of color channels in the input
	args.input_dims = {args.hist_len * args.ncols, IMG_DIMENSIONS_Q_LAST[2], IMG_DIMENSIONS_Q_LAST[3]}
	args.gpu = 1 -- to use gpu
	args.verbose = 2 -- more debug output
	args.n_actions = #actions.ACTIONS_NETWORK -- size of output layer / number of available actions


	local net = nn.Sequential()
	net:add(nn.Reshape(unpack(args.input_dims)))

	--- first convolutional layer
	local convLayer = nn.SpatialConvolution

	net:add(convLayer(args.hist_len*args.ncols, args.n_units[1],
						args.filter_size[1], args.filter_size[1],
						args.filter_stride[1], args.filter_stride[1],1))
	net:add(args.nl())

	-- Add convolutional layers
	for i=1,(#args.n_units-1) do
		-- second convolutional layer
		net:add(convLayer(args.n_units[i], args.n_units[i+1],
							args.filter_size[i+1], args.filter_size[i+1],
							args.filter_stride[i+1], args.filter_stride[i+1]))
		net:add(args.nl())
	end

	local nel
	if args.gpu >= 0 then
		nel = net:cuda():forward(torch.zeros(1,unpack(args.input_dims))
				:cuda()):nElement()
	else
		nel = net:forward(torch.zeros(1,unpack(args.input_dims))):nElement()
	end

	-- reshape all feature planes into a vector per example
	net:add(nn.Reshape(nel))

	-- fully connected layer
	net:add(nn.Linear(nel, args.n_hid[1]))
	net:add(args.nl())
	local last_layer_size = args.n_hid[1]

	for i=1,(#args.n_hid-1) do
		-- add Linear layer
		last_layer_size = args.n_hid[i+1]
		net:add(nn.Linear(args.n_hid[i], last_layer_size))
		net:add(args.nl())
	end

	-- add the last fully connected layer (to actions)
	net:add(nn.Linear(last_layer_size, args.n_actions))

	if args.gpu >=0 then
		net:cuda()
	end
	if args.verbose >= 2 then
		print(net)
		print('Convolutional layers flattened output size:', nel)
	end
	return net
end


-- Perform a forward/backward training pass for a given batch.
function network.forwardBackwardBatch(batchInput, batchTarget)
	local loss
	batchTarget = batchTarget:cuda()
	Q:training()
	local feval = function(x)
		local input = batchInput
		local target = batchTarget

		GRAD_PARAMETERS:zero() -- reset gradients
		-- forward pass
		local batchOutput = Q:forward(input)
		local err = CRITERION:forward(batchOutput, target)
		--  backward pass
		local df_do = CRITERION:backward(batchOutput, target)
		Q:backward(input, df_do)
		--errG = network.l1(PARAMETERS, GRAD_PARAMETERS, err, 1e-6)
		err = network.l2(PARAMETERS, GRAD_PARAMETERS, err, Q_L2_NORM)
		network.clamp(GRAD_PARAMETERS, Q_CLAMP)

		loss = err
		return err, GRAD_PARAMETERS
	end
	optim.adam(feval, PARAMETERS, OPTCONFIG, OPTSTATE)
	--optim.adagrad(feval, PARAMETERS, {}, OPTSTATE)
	--optim.sgd(feval, PARAMETERS, {learningRate=0.00001}, OPTSTATE)
	--optim.sgd(feval, PARAMETERS, OPTCONFIG, OPTSTATE)
	--optim.rmsprop(feval, PARAMETERS, {}, OPTSTATE)
	Q:evaluate()
	return loss
end

-- Compute the loss of a given batch without training on it.
function network.batchToLoss(batchInput, batchTarget)
	Q:evaluate()
	batchTarget = batchTarget:cuda()
	local batchOutput = Q:forward(batchInput)
	local err = CRITERION:forward(batchOutput, batchTarget)
	err = network.l2(PARAMETERS, nil, err, Q_L2_NORM)
	return err
end

-- Approximate the Q-value of a specific action for a given state chain.
function network.approximateActionValue(stateChain, action)
	assert(action ~= nil)
	local values = network.approximateActionValues(stateChain)
	--return {arrows = values[action.arrows], buttons = values[action.buttons]}
	return (values[action.arrow])
end

-- Approximate the Q-values of all actions for a list of state chains.
-- TODO fully replace this function with approximateActionValuesBatch().
function network.approximateActionValues(stateChain)
	assert(#stateChain == STATES_PER_EXAMPLE)

	local out = network.approximateActionValuesBatch({stateChain})
	out = out[1]

	return out
end

-- Approximate Q-values (for all actions) for many chains of states.
function network.approximateActionValuesBatch(stateChains, net)
	net = net or Q
	net:evaluate()
	local batchInput = network.stateChainsToBatchInput(stateChains)
	local result = net:forward(batchInput):float()
	local out = {}
	for i=1,result:size(1) do
		out[i] = network.networkVectorToActionValues(result[i])
	end

	--[[ -- no idea if this still works, but it isn't needed
	local plotPoints = {}
	for i=1,result[1]:size(1) do
		table.insert(plotPoints, {i, result[1][i]})
	end
	display.plot(plotPoints, {win=41, labels={'Action', 'Q(s,a)'}, title='Q(s,a) using network output action positions'})
	--]]

	return out
end

-- Predict the best action (maximal reward) for a chain of states.
-- @returns tuple (Action, action value)
function network.approximateBestAction(stateChain)
	local values = network.approximateActionValues(stateChain)

	local bestArrowIdx = nil
	local bestArrowValue = nil
	for key, value in pairs(values) do
		if actions.isArrowsActionIdx(key) then
			if bestArrowIdx == nil or value > bestArrowValue then
				bestArrowIdx = key
				bestArrowValue = value
			end
		end
	end
--[[
	local bestButtonIdx = nil
	local bestButtonValue = nil
	for key, value in pairs(values) do
		if actions.isButtonsActionIdx(key) then
			if bestButtonIdx == nil or value > bestButtonValue then
				bestButtonIdx = key
				bestButtonValue = value
			end
		end
	end
--]]
	-- dont use pairs() here for iteration, because order of items is important for display.plot()
	local plotPointsArrows = {}
	for i=1,#actions.ACTIONS_ARROWS do
		local key = actions.ACTIONS_ARROWS[i]
		table.insert(plotPointsArrows, {key, values[key]})
	end
	display.plot(plotPointsArrows, {win=39, labels={'Action', 'Q(s,a)'}, title='Q(s,a) using emulator action IDs (Arrows)'})
--[[
	local plotPointsButtons = {}
	for i=1,#actions.ACTIONS_BUTTONS do
		local key = actions.ACTIONS_BUTTONS[i]
		table.insert(plotPointsButtons, {key, values[key]})
	end
	display.plot(plotPointsButtons, {win=40, labels={'Action', 'Q(s,a)'}, title='Q(s,a) using emulator action IDs (Buttons)'})
--]]
	return Action.new(bestArrowIdx), (bestArrowValue)
end

-- Predicts the best actions (maximal reward) for many chains of states.
-- @returns List of (Action, action value)
function network.approximateBestActionsBatch(stateChains, net)
	net = net or Q
	local result = {}
	local valuesBatch = network.approximateActionValuesBatch(stateChains, net)
	for i=1,#valuesBatch do
		local values = valuesBatch[i]

		local bestArrowIdx = nil
		local bestArrowValue = nil
		for key, value in pairs(values) do
			if actions.isArrowsActionIdx(key) then
				if bestArrowIdx == nil or value > bestArrowValue then
					bestArrowIdx = key
					bestArrowValue = value
				end
			end
		end
--[[
		local bestButtonIdx = nil
		local bestButtonValue = nil
		for key, value in pairs(values) do
			if actions.isButtonsActionIdx(key) then
				if bestButtonIdx == nil or value > bestButtonValue then
					bestButtonIdx = key
					bestButtonValue = value
				end
			end
		end
--]]
		local oneResult = {action = Action.new(bestArrowIdx), value = (bestArrowValue)}
		table.insert(result, oneResult)
	end
	return result
end

-- Converts many chains of states to a batch for training/validation.
-- @returns tuple (input/X, target/Y)
function network.stateChainsToBatch(stateChains)
	local batchInput = network.stateChainsToBatchInput(stateChains)
	local batchTarget = network.stateChainsToBatchTarget(stateChains)
	return batchInput, batchTarget
end

-- Converts many chains of states to the input/x of a batch.
-- @returns Table {action history tensor, state history tensor, last state tensor}
-- CHANGED: only history tensor
function network.stateChainsToBatchInput(stateChains)
	local batchSize = #stateChains
	local batchInput = torch.zeros(#stateChains, STATES_PER_EXAMPLE, IMG_DIMENSIONS_Q_HISTORY[2], IMG_DIMENSIONS_Q_HISTORY[3])
		--[[ {
		--torch.zeros(#stateChains, STATES_PER_EXAMPLE, #actions.ACTIONS_NETWORK),
		torch.zeros(#stateChains, STATES_PER_EXAMPLE, IMG_DIMENSIONS_Q_HISTORY[2], IMG_DIMENSIONS_Q_HISTORY[3]),
		--torch.zeros(#stateChains, IMG_DIMENSIONS_Q_LAST[1], IMG_DIMENSIONS_Q_LAST[2], IMG_DIMENSIONS_Q_LAST[3])
	} --]]
	for i=1,#stateChains do
		local stateChain = stateChains[i]
		local example = network.stateChainToInput(stateChain)
		batchInput[i] = example[1]
		--batchInput[2][i] = example[2]
		--batchInput[3][i] = example[3]
	end

	return batchInput:cuda()
end

-- Converts many chains of states to their batch targets (Y).
-- @returns Tensor
function network.stateChainsToBatchTarget(stateChains)
	local batchSize = #stateChains
	local batchTarget = torch.zeros(batchSize, #actions.ACTIONS_NETWORK)
	for i=1,#stateChains do
		local stateChain = stateChains[i]
		batchTarget[i] = network.stateChainToTarget(stateChain)
	end

	return batchTarget
end

-- Converts a single state chain to a batch input.
-- @returns {action history tensor, image history tensor, last image tensor}
-- CHANGED: only image history tensor
function network.stateChainToInput(stateChain)
	assert(#stateChain == STATES_PER_EXAMPLE)
	--[[
	local actionChain = torch.zeros(#stateChain, #actions.ACTIONS_NETWORK)
	for i=1,#stateChain do
		if stateChain[i].action ~= nil then
			actionChain[i] = network.actionToNetworkVector(stateChain[i].action)
		end
	end
	--]]

	local imageHistory = torch.zeros(#stateChain, IMG_DIMENSIONS_Q_HISTORY[2], IMG_DIMENSIONS_Q_HISTORY[3])
	for i=1,#stateChain do
		local screenDec = states.decompressScreen(stateChain[i].screen)
		screenDec = util.toImageDimensions(screenDec, IMG_DIMENSIONS_Q_HISTORY)
		imageHistory[i] = screenDec
	end

	-- local lastImage = util.toImageDimensions(states.decompressScreen(stateChain[#stateChain].screen), IMG_DIMENSIONS_Q_LAST)

	-- to not change the type ...
	local example = {imageHistory}

	return example
end

-- Converts a single state chain to a batch target.
-- @returns Tensor
function network.stateChainToTarget(stateChain)
	local lastState = stateChain[#stateChain]
	local action = lastState.action
	local vec = network.actionToNetworkVector(action)
	vec:mul(rewards.getSumForTraining(lastState.reward))
	return vec
end

-- Converts an Action object to a two-hot-vector that can be used as target for a batch.
-- (Two, because there are two choices: Arrow and other button.)
-- @returns Tensor
function network.actionToNetworkVector(action)
	local vec = torch.zeros(#actions.ACTIONS_NETWORK)
	vec[network.getNetworkPositionOfActionIdx(action.arrow)] = 1
	return vec
end

-- Converts a network output to a table [action index => reward].
-- @returns Table
function network.networkVectorToActionValues(vec)
	local out = {}
	for i=1,vec:size(1) do
		out[actions.ACTIONS_NETWORK[i]] = vec[i]
	end
	return out
end

-- Returns the position (1..N) of an action (specified by its index) among the output neurons of the network.
-- @returns integer
function network.getNetworkPositionOfActionIdx(actionIdx)
	assert(actionIdx ~= nil)
	for i=1,#actions.ACTIONS_NETWORK do
		if actions.ACTIONS_NETWORK[i] == actionIdx then
			return i
		end
	end
	error("action not found: " .. actionIdx)
end

-- Clamps/truncates gradient values.
function network.clamp(gradParameters, clampValue)
	if clampValue ~= 0 then
		gradParameters:clamp((-1)*clampValue, clampValue)
	end
end

-- Applies a L1 norm to the parameters of the network.
function network.l1(parameters, gradParameters, lossValue, l1weight)
	if l1weight ~= 0 then
		lossValue = lossValue + l1weight * torch.norm(parameters, 1)
		if gradParameters ~= nil then
			gradParameters:add(torch.sign(parameters):mul(l1Weight))
		end
	end
	return lossValue
end

-- Applies a L2 norm to the parameters of the network.
function network.l2(parameters, gradParameters, lossValue, l2weight)
	if l2weight ~= 0 then
		lossValue = lossValue + l2weight * torch.norm(parameters, 2)^2/2
		if gradParameters ~= nil then
			gradParameters:add(parameters:clone():mul(l2weight))
		end
	end
	return lossValue
end

-- Returns the number of parameters/weights in a network.
function network.getNumberOfParameters(net)
	local nparams = 0
	local dModules = net:listModules()
	for i=1,#dModules do
		if dModules[i].weight ~= nil then
			nparams = nparams + dModules[i].weight:nElement()
		end
	end
	return nparams
end

-- Displays a batch of images.
-- TODO does this still work? is this still used?
function network.displayBatch(images, windowId, title, width)
	--print("network.displayBatch start")
	local nExamples, nStates, h, w = images:size(1), images:size(2), images:size(3), images:size(4)
	local imgsDisp = torch.zeros(nExamples*nStates, 1, h, w)
	local counter = 1
	for i=1,nExamples do
		for j=1,nStates do
			imgsDisp[counter] = images[i][j]
			counter = counter + 1
		end
	end

	local out = image.toDisplayTensor{input=imgsDisp, nrow=STATES_PER_EXAMPLE, padding=1}

	title = title or string.format("Images")
	if width then
		display.image(out, {win=windowId, width=width, title=title})
	else
		display.image(out, {win=windowId, title=title})
	end
	--print("network.displayBatch end")
end

-- Plot measured losses per N batches
function network.plotAverageLoss(lossData, clampTo)
	clampTo = clampTo or 10
	local losses = {}
	for i=1,#lossData do
		local entry = lossData[i]
		table.insert(losses, {entry[1], math.min(entry[2], clampTo), math.min(entry[3], clampTo)})
	end
	display.plot(losses, {win=4, labels={'batch group', 'training', 'validation'}, title='Average loss per batch'})
end


-- Prepares a network for saving to file by shrinking/removing unnecessary data.
-- Works in-place, i.e. does not return anything.
-- from https://github.com/torch/DEPRECEATED-torch7-distro/issues/47
-- Resize the output, gradInput, etc temporary tensors to zero (so that the on disk size is smaller)
function network.prepareNetworkForSave(node)
	-- from https://github.com/torch/DEPRECEATED-torch7-distro/issues/47
	function zeroDataSize(data)
		if type(data) == 'table' then
			for i = 1, #data do
				data[i] = zeroDataSize(data[i])
			end
		elseif type(data) == 'userdata' then
			data = torch.Tensor():typeAs(data)
		end
		return data
	end

	if node.output ~= nil then
		node.output = zeroDataSize(node.output)
	end
	if node.gradInput ~= nil then
		node.gradInput = zeroDataSize(node.gradInput)
	end
	if node.finput ~= nil then
		node.finput = zeroDataSize(node.finput)
	end
	-- Recurse on nodes with 'modules'
	if (node.modules ~= nil) then
		if (type(node.modules) == 'table') then
			for i = 1, #node.modules do
				local child = node.modules[i]
				network.prepareNetworkForSave(child)
			end
		end
	end
	collectgarbage()
end



return network
