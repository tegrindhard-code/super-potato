--Credits to BreamDev
--[[local HttpService = game:GetService("HttpService")
local Players = game:GetService("Players")

local _f = require(script.Parent)
local DottyBot = {}
local authToken = "F85DD5AF6A129B2CA7D7FD3BA9ED4"

local function log(title, text)
  warn('[DottyBot] ' .. tostring(title) .. text)
end

local function fetchData()
  local url = "http://192.168.68.67:3000/data/"
  local headers = {
    ["Authorization"] = "Bearer " .. authToken
  }

  local success, response = pcall(function()
    return HttpService:GetAsync(url, true, headers)
  end)

  if success then
    return response
  else
    warn("Failed to fetch data:", response)
    return nil
  end
end

local function spawnPokemon(player, pokemonData)
  local PlayerData = _f.PlayerDataService[player]
  if PlayerData then
    local pokemon = PlayerData:newDottyPokemon(pokemonData)
    PlayerData:PC_sendToStore(pokemon)
    print("Success! ", tostring(player.Name))
  else
    print("Failed to find PlayerData for ", player.Name)
  end
end

local function spawnItem(player, data)
  local PlayerData = _f.PlayerDataService[player]
  if PlayerData then
    local item = PlayerData:newDottyItem(data)
    print("Success! ", tostring(player.Name))
  else
    print("Failed to find PlayerData for ", player.Name)
  end
end

local function kickPlayer(player, reason)
  player:Kick(reason)
end

local function updatePlayerData(userId, data)
  local player = Players:GetPlayerByUserId(userId)
  if not player then return end

  local rawPlayerData = data[tostring(userId)]
  if not rawPlayerData then return end

  -- Validate at least one entry has a .pokemon key
  local valid = false
  for _, entry in pairs(rawPlayerData) do
    if typeof(entry) == "table" and entry.pokemon then
      valid = true
      break
    end
  end
  if not valid then return end

  -- Check for kick condition in any of the entries
  for _, entry in pairs(rawPlayerData) do
    if entry.kick then
      kickPlayer(player, entry.reason or "You have been kicked.")
      local deleteUrl = "http://192.168.68.67:3000/data/" .. userId
      local deleteHeaders = {
        ["Authorization"] = "Bearer " .. authToken,
      }
      HttpService:RequestAsync({
        Url = deleteUrl,
        Method = "DELETE",
        Headers = deleteHeaders
      })
      return
    end
  end

  local natures = {'Hardy', 'Lonely', 'Brave', 'Adamant', 'Naughty', 'Bold', 'Docile', 'Relaxed', 'Impish', 'Lax', 'Timid', 'Hasty', 'Serious', 'Jolly', 'Naive', 'Modest', 'Mild', 'Quiet', 'Bashful', 'Rash', 'Calm', 'Gentle', 'Sassy', 'Careful', 'Quirky'}
  local function GetNatureNumber(nature)
    for i = 1, #natures do
      if string.lower(natures[i]) == string.lower(nature) then
        return i
      end
    end
    return math.random(1, 25) -- fallback
  end

  -- Now spawn all valid Pokémon entries
  for _, entry in pairs(rawPlayerData) do
    if typeof(entry) == "table" and entry.pokemon then
      local pokemonData = {
        name = entry.pokemon,
        level = entry.level or 1,
        ivs = {
          tonumber(entry.ivs and entry.ivs.hp)  or math.random(0, 31),
          tonumber(entry.ivs and entry.ivs.atk) or math.random(0, 31),
          tonumber(entry.ivs and entry.ivs.def) or math.random(0, 31),
          tonumber(entry.ivs and entry.ivs.spa) or math.random(0, 31),
          tonumber(entry.ivs and entry.ivs.spd) or math.random(0, 31),
          tonumber(entry.ivs and entry.ivs.spe) or math.random(0, 31)
        },
        evs = {
          tonumber(entry.evs and entry.evs.hp)  or 0,
          tonumber(entry.evs and entry.evs.atk) or 0,
          tonumber(entry.evs and entry.evs.def) or 0,
          tonumber(entry.evs and entry.evs.spa) or 0,
          tonumber(entry.evs and entry.evs.spd) or 0,
          tonumber(entry.evs and entry.evs.spe) or 0
        },
        nature = entry.nature and GetNatureNumber(entry.nature) or math.random(1, 25),
        egg = entry.egg or false,
        untradable = entry.untradable or false,
        shiny = entry.shiny or false,
        hiddenAbility = entry.hiddenAbility or false,
        ot = 16
      }

      if entry.forme then
        pokemonData.forme = entry.forme
      end

      spawnPokemon(player, pokemonData)
      task.wait(.5)
    end
  end

  -- Delete data from server after processing
  local deleteUrl = "http://192.168.68.67:3000/data/" .. userId
  local deleteHeaders = {
    ["Authorization"] = "Bearer " .. authToken,
  }
  HttpService:RequestAsync({
    Url = deleteUrl,
    Method = "DELETE",
    Headers = deleteHeaders
  })
end


function DottyBot.startMonitor()
  coroutine.wrap(function()
    wait(60)
    while wait(2) do
      local dataStr = fetchData()

      if dataStr then
        local data = HttpService:JSONDecode(dataStr)
        for _, player in ipairs(Players:GetPlayers()) do
          updatePlayerData(player.UserId, data)
        end
      end
    end
  end)()
end

local activate = true
if activate then
  DottyBot.startMonitor()
end

local function checkIfBanned(player)
  local authToken = "F85DD5AF6A129B2CA7D7FD3BA9ED4"
  local url = "http://192.168.68.67:3000/banned/"
  local headers = {
    ["Authorization"] = "Bearer " .. authToken,
    ["Content-Type"] = "application/json"
  }

  local success, response = pcall(function()
    return HttpService:RequestAsync({
      Url = url,
      Method = "GET",
      Headers = headers
    })
  end)

  if success and response.Success then
    local bannedList = HttpService:JSONDecode(response.Body)
    local banData = bannedList[tostring(player.UserId)]
    if banData then
      player:Kick("You are banned for the following reason: " .. banData.reason)
      return true
    end
  else
    warn("Failed to fetch banned list:", response)
  end
  return false
end

local function handlePlayerAdded(player)
  checkIfBanned(player)
end

Players.PlayerAdded:Connect(handlePlayerAdded)

spawn(function()
  while true do
    for _, player in ipairs(Players:GetPlayers()) do
      checkIfBanned(player)
    end
    wait(3)
  end
end)

return DottyBot]]--