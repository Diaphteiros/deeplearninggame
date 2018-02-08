-- Functions and constants dealing with the choice and application of actions,
-- i.e. pressing buttons on the controller.
-- Functions to find optimal actions are in network.lua .

local actions = {}

-- action ids for game
actions.NO_ACTION = 0
actions.LEFT_ACTION = 1
actions.RIGHT_ACTION = 2
actions.JUMP_ACTION = 3
-- next action to be chosen
actions.NEXT_ACTION = actions.NO_ACTION 

-- List of all action ids.
actions.ACTIONS_ALL = {
    actions.ACTION_BUTTON_B, actions.ACTION_BUTTON_Y,
    actions.ACTION_BUTTON_SELECT, actions.ACTION_BUTTON_START,
    actions.ACTION_BUTTON_UP, actions.ACTION_BUTTON_DOWN,
    actions.ACTION_BUTTON_LEFT, actions.ACTION_BUTTON_RIGHT,
    actions.ACTION_BUTTON_A, actions.ACTION_BUTTON_X,
    actions.ACTION_BUTTON_L, actions.ACTION_BUTTON_R
}

-- List of action ids that the network can use (i.e. for which it predicts rewards).
-- Note that the order is important, the first action id is the action that is
-- represented by the first output neuron of the network.
actions.ACTIONS_NETWORK = {
    actions.NO_ACTION, actions.LEFT_ACTION, actions.RIGHT_ACTION, actions.JUMP_ACTION
}

-- List of arrow actions (up, left, right).
actions.ACTIONS_ARROWS = {
    actions.NO_ACTION, actions.LEFT_ACTION, actions.RIGHT_ACTION, actions.JUMP_ACTION
}

-- List of "other" button actions (A, B, X, Y).
--[[ 
actions.ACTIONS_BUTTONS = {
    actions.ACTION_BUTTON_B, actions.ACTION_BUTTON_Y,
    --actions.ACTION_BUTTON_SELECT, actions.ACTION_BUTTON_START,
    actions.ACTION_BUTTON_A, actions.ACTION_BUTTON_X,
    --actions.ACTION_BUTTON_L, actions.ACTION_BUTTON_R
}
--]]

-- Short string names for each action, used for string conversions.
actions.ACTION_TO_SHORT_NAME = {}
actions.ACTION_TO_SHORT_NAME[0] = "-"
actions.ACTION_TO_SHORT_NAME[1] = "L"
actions.ACTION_TO_SHORT_NAME[2] = "R"
actions.ACTION_TO_SHORT_NAME[3] = "J"

-- Returns whether a certain action index represents an arrow action (up, down, left, right).
function actions.isArrowsActionIdx(actionIdx)
    for i=1,#actions.ACTIONS_ARROWS do
        if actionIdx == actions.ACTIONS_ARROWS[i] then
            return true
        end
    end
    return false
end

-- Returns whether a certain action index represents a button action (A, B, X, Y).
--[[function actions.isButtonsActionIdx(actionIdx)
    for i=1,#actions.ACTIONS_BUTTONS do
        if actionIdx == actions.ACTIONS_BUTTONS[i] then
            return true
        end
    end
    return false
end--]]

-- Transforms an action (arrow action index + button action index) to a short, readable string.
function actions.actionToString(action)
    if action == nil then
        return "nil"
    else
        return actions.ACTION_TO_SHORT_NAME[action.arrow]-- .. "+" .. actions.ACTION_TO_SHORT_NAME[action.button]
    end
end

-- Returns a new, random Action object.
function actions.createRandomAction()
    local arrow = actions.ACTIONS_ARROWS[math.random(#actions.ACTIONS_ARROWS)]
    return Action.new(arrow)
end

-- Resets all buttons (to "not pressed").
function actions.endAllActions()
    --for i=1,#actions.ACTIONS_ALL do
    --    local newstate = 0 -- 1 = pressed, 0 = released
    --    local mode = 3 -- 1 = autohold, 2 = framehold, others = press/release
    --    input.do_button_action(actions.ACTION_TO_BUTTON_NAME[actions.ACTIONS_ALL[i]], newstate, mode)
	--end
	actions.NEXT_ACTION = actions.NO_ACTION
end

-- Starts an action.
-- @param action An Action object.
function actions.startAction(action)
    assert(action ~= nil)
    --local newstate = 1 -- 1 = pressed, 0 = released
    --local mode = 3 -- 1 = autohold, 2 = framehold, others = press/release
    --local arrowAction = actions.ACTION_TO_BUTTON_NAME[action.arrow]
    --assert(arrowAction ~= nil)
    --input.do_button_action(arrowAction, newstate, mode)
	actions.NEXT_ACTION = action.arrow
end

-- Chooses an action based on a chain of states.
-- @param lastStates List of State objects.
-- @param perfect Boolean, sets exploration prob. to 0.0 (not really necessary anymore with pExplore).
-- @param bestAction Optionally an Action object for epsilon-greedy policy, otherwise the best action will be approximated.
-- @param pExplore Exploration probability for epsilon-greedy policy.
function actions.chooseAction(lastStates, perfect, bestAction, pExplore)
    perfect = perfect or false
    pExplore = pExplore or STATS.P_EXPLORE_CURRENT
    local _action, _actionValue
    if not perfect and math.random() < pExplore then
        -- randomize
        _action = Action.new(util.getRandomEntry(actions.ACTIONS_ARROWS))
        --print("Choosing action randomly: ", actions.ACTION_TO_SHORT_NAME[_action.arrow])
    else
        if bestAction ~= nil then
            _action = bestAction
            --print("Best action already set: ", actions.ACTION_TO_SHORT_NAME[_action.arrow])
        else
            -- Use network to approximate action with maximal value
            _action, _actionValue = network.approximateBestAction(lastStates)
            --print("Q approximated action: ", actions.ACTION_TO_SHORT_NAME[_action.arrow])
        end
    end

    return _action
end

return actions
