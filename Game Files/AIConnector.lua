local aiconnector = {}

-- parameters
aiconnector.PARAMS = {}

-- files that have been opened
aiconnector.OPEN_FILES = {}


-- functions

-- main function which returns the action id
function aiconnector.getAction()
    -- call primary function
    on_frame_emulated()
    return actions.NEXT_ACTION
end


-- if the AI wants a new level, it will set PARAMS.reload to true, which is forwarded to python by this method
function aiconnector.getReload()
    return aiconnector.PARAMS.reload == true -- comparison will turn nil into false for python
end


-- returns the action counter from lua (total number of taken actions)
function aiconnector.getActionCount()
	return STATS.ACTION_COUNTER
end


-- returns the world count
function aiconnector.getWorldCount()
	return STATS.WORLD_COUNT
end


-- increases world count by one
function aiconnector.increaseWorldCount(amount)
	amount = amount or 1 -- defaulting to 1
	STATS.WORLD_COUNT = STATS.WORLD_COUNT + 1
end


-- sets PARAMS (only needed because a return value with LUA_PREFIX is necessary
function aiconnector.setParams(par)
    aiconnector.PARAMS = par
end


function aiconnector.cleanup()
    for _, value in ipairs(aiconnector.OPEN_FILES) do
		value:close()
	end

end

return aiconnector