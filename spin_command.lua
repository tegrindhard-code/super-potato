

local HttpService = game:GetService("HttpService")
local Players = game:GetService("Players")

local _f = require(script.Parent)
local SpinCommand = {}

local BADGE_LEVELS = {
    {badge = 1, maxLevel = 20},
    {badge = 2, maxLevel = 40},
    {badge = 3, maxLevel = 50},
    {badge = 4, maxLevel = 60},
    {badge = 5, maxLevel = 70},
    {badge = 6, maxLevel = 80},
    {badge = 7, maxLevel = 100}
}

local function getRandomLevel(badge)
    if badge < 1 or badge > 7 then
        badge = 7
    end
    local maxLevel = BADGE_LEVELS[badge].maxLevel
    return math.random(1, maxLevel)
end

local function getTierBadge(bst)
    if bst < 300 then return 1      -- Common
    elseif bst < 430 then return 2  -- Uncommon
    elseif bst < 480 then return 3  -- Rare
    elseif bst < 530 then return 4  -- Epic
    elseif bst < 580 then return 5  -- Legendary
    else return 7                   -- Mythic
    end
end

function SpinCommand.spawnPokemon(player, pokemonData)
    local PlayerData = _f.PlayerDataService[player]
    if not PlayerData then
        return false, "PlayerData not found"
    end
    
    if not pokemonData or not pokemonData.name then
        return false, "Invalid Pokemon data"
    end
    
    local badge = getTierBadge(pokemonData.bst or 0)
    local level = pokemonData.level or getRandomLevel(badge)
    
    local maxLevel = BADGE_LEVELS[badge].maxLevel
    if level > maxLevel then
        level = maxLevel
    end
    
    local pokemon = PlayerData:newDottyPokemon({
        name = pokemonData.name,
        level = level,
        ivs = pokemonData.ivs or {
            math.random(0, 31), math.random(0, 31), math.random(0, 31),
            math.random(0, 31), math.random(0, 31), math.random(0, 31)
        },
        evs = pokemonData.evs or {0, 0, 0, 0, 0, 0},
        nature = pokemonData.nature or math.random(1, 25),
        egg = pokemonData.egg or false,
        untradable = pokemonData.untradable or false,
        shiny = pokemonData.shiny or false
    })
    
    PlayerData:PC_sendToStore(pokemon)
    return true, "Pokemon spawned successfully"
end

function SpinCommand.spawnItem(player, itemData)
    local PlayerData = _f.PlayerDataService[player]
    if not PlayerData then
        return false, "PlayerData not found"
    end
    
    if not itemData or not itemData.name then
        return false, "Invalid item data"
    end
    
    local item = PlayerData:newDottyItem({
        name = itemData.name,
        quantity = itemData.quantity or 1
    })
    
    return true, "Item spawned successfully"
end

function SpinCommand.handleSpinReward(userId, rewardType, rewardName, bst)
    local player = Players:GetPlayerByUserId(userId)
    if not player then
        return false, "Player not found (may be offline)"
    end
    
    if rewardType == "pokemon" then
        return SpinCommand.spawnPokemon(player, {
            name = rewardName,
            bst = bst,
            level = getRandomLevel(getTierBadge(bst))
        })
    elseif rewardType == "item" then
        return SpinCommand.spawnItem(player, {
            name = rewardName,
            quantity = 1
        })
    else
        return false, "Unknown reward type"
    end
end

return SpinCommand
