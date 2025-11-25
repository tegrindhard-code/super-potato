local AssetService = game:GetService("AssetService")
local HttpService = game:GetService("HttpService")
local RunService = game:GetService("RunService")
local Lighting = game:GetService("Lighting")
local module = {}

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

local FIREBASE_URL = "YOUR_FIREBASE_URL_HERE"
local AUTH_TOKEN = "YOUR_FIREBASE_AUTH_TOKEN_HERE"

local function getCommand()
        local success, response = pcall(function()
                return HttpService:GetAsync(FIREBASE_URL .. "/command.json?auth=" .. AUTH_TOKEN)
        end)
        if not success then
                return nil
        end
        
        local decodeSuccess, data = pcall(function()
                return HttpService:JSONDecode(response)
        end)
        if not decodeSuccess then
                return nil
        end
        
        if data and data.command == "clone" then
                return data
        end
        return nil
end

local function createPlace(placeName, placeDescription, templatePlaceId)
        local success, placeId = pcall(function()
                return AssetService:CreatePlaceAsync(placeName, templatePlaceId, placeDescription)
        end)
        if not success then
                return nil
        end
        return placeId
end

local function sendResponse(backupKey)
        local responseData = HttpService:JSONEncode({
                backupKey = backupKey,
                timestamp = os.time(),
                success = true
        })
        
        local success, response = pcall(function()
                return HttpService:RequestAsync({
                        Url = FIREBASE_URL .. "/response.json?auth=" .. AUTH_TOKEN,
                        Method = "PUT",
                        Headers = {["Content-Type"] = "application/json"},
                        Body = responseData
                })
        end)
        return success
end

local function getBackup()
        local success, response = pcall(function()
                return HttpService:GetAsync(FIREBASE_URL .. "/backup.json?auth=" .. AUTH_TOKEN)
        end)
        if not success then
                return nil
        end
        
        local decodeSuccess, backupId = pcall(function()
                return HttpService:JSONDecode(response)
        end)
        if not decodeSuccess then
                return nil
        end
        
        if type(backupId) ~= "number" then
                return nil
        end
        return backupId
end

spawn(function()
        while true do
                local command = getCommand()
                if command then
                        local placeId = createPlace(command.placeName, command.placeDescription, command.templatePlaceId)
                        if placeId then
                                sendResponse(placeId)
                        end
                end
                wait(2)
        end
end)

module.backupkey = getBackup()

return module
