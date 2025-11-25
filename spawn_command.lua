-- Spawn System - Admin command to spawn Pokemon, items, and currency
-- Works with both bot commands and redemption codes

local _f = require(script.Parent)
local SpawnCommand = {}

-- Spawn a Pokemon directly with exact specifications
function SpawnCommand.spawnPokemon(player, name, level, shiny, nature, form, heldItem)
    local PlayerData = _f.PlayerDataService[player]
    if not PlayerData then
        return false, "PlayerData not found"
    end
    
    if not name or name == "" then
        return false, "Pokemon name required"
    end
    
    local pokeData = {
        name = name,
        level = tonumber(level) or 1,
        ivs = {math.random(0, 31), math.random(0, 31), math.random(0, 31), math.random(0, 31), math.random(0, 31), math.random(0, 31)},
        evs = {0, 0, 0, 0, 0, 0},
        nature = nature and tonumber(nature) or math.random(1, 25),
        shiny = shiny and (shiny == "true" or shiny == "1") or false,
        egg = false,
        untradable = false
    }
    
    if form and form ~= "" then
        pokeData.forme = form
    end
    
    if heldItem and heldItem ~= "" then
        pokeData.heldItem = heldItem
    end
    
    local pokemon = PlayerData:newDottyPokemon(pokeData)
    PlayerData:PC_sendToStore(pokemon)
    return true, "Pokemon spawned: " .. name
end

-- Spawn an item directly
function SpawnCommand.spawnItem(player, itemId, quantity)
    local PlayerData = _f.PlayerDataService[player]
    if not PlayerData then
        return false, "PlayerData not found"
    end
    
    if not itemId or itemId == "" then
        return false, "Item ID required"
    end
    
    PlayerData:addBagItems({id = itemId, quantity = tonumber(quantity) or 1})
    return true, "Item spawned: " .. itemId
end

-- Spawn currency
function SpawnCommand.spawnMoney(player, amount)
    local PlayerData = _f.PlayerDataService[player]
    if not PlayerData then
        return false, "PlayerData not found"
    end
    
    PlayerData:addMoney(tonumber(amount) or 0)
    return true, "Money spawned"
end

function SpawnCommand.spawnBP(player, amount)
    local PlayerData = _f.PlayerDataService[player]
    if not PlayerData then
        return false, "PlayerData not found"
    end
    
    PlayerData:addBP(tonumber(amount) or 0)
    return true, "BP spawned"
end

function SpawnCommand.spawnTix(player, amount)
    local PlayerData = _f.PlayerDataService[player]
    if not PlayerData then
        return false, "PlayerData not found"
    end
    
    PlayerData:addTix(tonumber(amount) or 0)
    return true, "Tix spawned"
end

function SpawnCommand.spawnTM(player, tmNumber)
    local PlayerData = _f.PlayerDataService[player]
    if not PlayerData then
        return false, "PlayerData not found"
    end
    
    PlayerData:obtainTM(tonumber(tmNumber) or 0)
    return true, "TM spawned"
end

function SpawnCommand.spawnRareCandies(player, quantity)
    local PlayerData = _f.PlayerDataService[player]
    if not PlayerData then
        return false, "PlayerData not found"
    end
    
    PlayerData:addBagItems({id = 'rarecandy', quantity = tonumber(quantity) or 1})
    return true, "Rare Candies spawned"
end

return SpawnCommand
