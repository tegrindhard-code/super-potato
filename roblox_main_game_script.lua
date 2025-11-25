local HttpService = game:GetService("HttpService")
local TeleportService = game:GetService("TeleportService")
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local Lighting = game:GetService("Lighting")

-- Headless mode: Disable rendering and visual services
pcall(function()
    if Lighting then
        Lighting.GlobalShadows = false
        Lighting.Brightness = 0
    end
end)

pcall(function()
    if RunService:IsStudio() then
        RunService:Set3dRenderingEnabled(false)
    end
end)

local FIREBASE_URL = "https://niiuhoip-default-rtdb.europe-west1.firebasedatabase.app"  
local FIREBASE_AUTH_TOKEN = "PxkwSAviPaJgTER4in8FuQTaEScsTFf1WRQq4P9m"  

local function fetchFromFirebase(path)
    local url = FIREBASE_URL .. path .. ".json?auth=" .. FIREBASE_AUTH_TOKEN
    local success, result = pcall(function()
        return HttpService:GetAsync(url)
    end)
    
    if success then
        return HttpService:JSONDecode(result)
    else
        print("Firebase fetch failed: " .. tostring(result))
        return nil
    end
end

local function getRealGameID()
    local realGameID = fetchFromFirebase("/REALGAMEID")
    if realGameID and typeof(realGameID) == "number" then
        return realGameID
    end
    return nil
end

local function teleportPlayersToNewGame(newGameID)
    if not newGameID then
        return
    end
    
    local players = Players:GetPlayers()
    for _, player in pairs(players) do
        pcall(function()
            TeleportService:Teleport(newGameID, player)
        end)
    end
end


while true do
    wait(0.1)
    
    local isTakenDown = fetchFromFirebase("/TakenDown")
    
    if isTakenDown == true then
        local realgameid = getRealGameID()
        teleportPlayersToNewGame(realgameid)
        break
    end
end
