-- SQL example for pdlua
-- Written by Frank Barknecht in 2007, use however you like.

-- load driver
luasql = require "luasql.sqlite3"

local M = pd.Class:new():register("lsql")

function M:initialize(name)
    -- create environment object
    self.env = assert (luasql.sqlite3())
    self.con = nil
    self.outlets = 2
    self.inlets = 1
    return true
end


function M:in_1_open(atoms)
    -- connect to data source
    self.con = assert (self.env:connect(atoms[1]))
end


function M:in_1_sql(atoms)
    if not self.con then
        self:error("open a database file first")
        return
    end
    local command = table.concat(atoms, " ")
    -- use : instead of ,
    command = command:gsub("`", ",")
    local cur = assert (self.con:execute(command))
    if type(cur) == "number" then
        -- report affected rows to second outlet:
        self:outlet(2, "float", {cur})
    else
        local row = cur:fetch({})
        while row do
            self:outlet(1, "list", row)
            row = cur:fetch(row)
        end
        -- close cursor
        cur:close()
    end
end



