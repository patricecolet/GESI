-- get home path
-- Written by patko in 2016, use however you like.

local OM = pd.Class:new():register("home")

function OM:initialize(name)
    -- create environment object
    self.outlets = 1
    self.inlets = 1
    return true
end



function OM:in_1_bang()
        home = os.getenv( "HOME" )
       -- pd.post("home: ")
        self:outlet(1, "list", {home})
end

