-- This object represents a state.
local State = {}
State.__index = State

-- @param id The id number of the state.
-- @param screen The screenshot of the game, expected to be jpg-compressed.
-- @param new: deathCount
-- @param new: levelBeatenCount how many levels have been beaten
-- @param playerX X-coordinate of Mario.
-- @param action The action chosen at this state.
-- @param reward The reward received at this state.
function State.new(id, screen, score, deathCount, levelBeatenCount, playerX, worldCount, action, reward)
	local self = setmetatable({}, State)
	if id == nil then
		id = STATS.STATE_ID
		STATS.STATE_ID = STATS.STATE_ID + 1
	end
	self.id = id
	self.screen = screen
	self.score = score
	self.deathCount = deathCount
	self.levelBeatenCount = levelBeatenCount
	self.playerX = playerX
	self.worldCount = worldCount
	self.action = action
	self.reward = reward
	self.isDummy = false
	return self
end
	
-- Objects here have no members functions, because those seemed to be gone
-- after torch.save() and then torch.load().

return State
