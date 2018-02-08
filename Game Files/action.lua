-- Object that represents an action.
-- Every action consists of two sub-actions:
--  arrowAction: The pressed arrow button (up, down, left, right).
--  buttonAction: The pressed "other" button (A, B, X, Y).
-- Both sub-actions are given by their action id (see actions.lua).
--CHANGED: only one arrow action at a time
local Action = {}
Action.__index = Action

function Action.new(arrowAction)
    local self = setmetatable({}, Action)
    self.arrow = arrowAction
    return self
end

-- Objects here have no members functions, because those seemed to be gone
-- after torch.save() and then torch.load().

return Action
