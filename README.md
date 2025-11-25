# Roblox Automatic Reupload System

An automated Discord bot system for managing Roblox game backups and publishing.

## Features

- **Automatic Game Monitoring**: Monitors your main Roblox game and automatically restores it if it goes down
- **Firebase Integration**: Uses Firebase Realtime Database to communicate between Discord bot and Roblox Lua script
- **Place Backup System**: Creates backup copies of your Roblox places using AssetService
- **Publish Game Files**: Upload .rbxl/.rbxlx files directly to Roblox places via Discord
- **Audio Upload**: Upload audio files (MP3, OGG, WAV, FLAC) to Roblox with automatic conversion
- **API Key Management**: Automatically generate Roblox Open Cloud API keys via Selenium

## Setup Instructions

### 1. Roblox Setup

**IMPORTANT: Prerequisites for CreatePlaceAsync to Work**

1. **Create a Roblox Group** (if you don't have one):
   - Go to https://www.roblox.com/groups/create
   - CreatePlaceAsync requires group ownership (doesn't work reliably with personal accounts)

2. Create two Roblox games **owned by your GROUP**:
   - **Template Game**: This is where the Lua script will run
   - **Main Game**: This is the game you want to monitor and backup
   - Transfer ownership: Game Settings → Configure → Configure Place → Transfer to Group

3. **Enable Required Permissions** for your **Template Game**:
   
   **In Roblox Studio:**
   - File → Game Settings → Security tab:
     - ✅ Enable "Enable Studio Access to API Services"
     - ✅ Enable "Allow HTTP Requests"
   
   **On Roblox Website (create.roblox.com):**
   - Go to your Template Game → ⚙ Settings → Configure Start Place
   - Click **Permissions** tab:
     - ✅ Enable "Allow Copying"
   
   **Important:** After changing settings in Studio, you must **publish the game** and then verify settings on the website

4. **Verify Your Group Role**:
   - You must be **Owner** or **Admin** in the group (not just a member)

5. Add the Lua script to your **Template Game**:
   - Copy the content from `roblox_backup_script.lua`
   - In Roblox Studio, open your Template Game
   - Create a **Script** (not ModuleScript) in **ServerScriptService**
   - Paste the Lua code into the script
   - Replace `YOUR_FIREBASE_URL_HERE` with your Firebase URL
   - Replace `YOUR_FIREBASE_AUTH_TOKEN_HERE` with your Firebase auth token
   - **Publish to Roblox** (File → Publish to Roblox)

6. **Test in a Live Server** (Not Studio):
   - CreatePlaceAsync often fails in Studio even with permissions enabled
   - Click "Play" on your game in Roblox website to test in a live server
   - Check the Output logs in the Developer Console (F9)

### 2. Discord Bot Setup
1. Create a Discord bot at https://discord.com/developers/applications
2. Enable Message Content Intent in the bot settings
3. Invite the bot to your server with proper permissions

### 3. Configuration

**Important:** The bot requires the following environment variables to be set:

Required:
- `FIREBASE_URL` - Your Firebase Realtime Database URL
- `FIREBASE_AUTH_TOKEN` - Your Firebase authentication token
- `DISCORD_BOT_TOKEN` - Your Discord bot token
- `TEMPLATE_PLACE_ID` - The Roblox place ID where your Lua script runs
- `UNIVERSE_ID` - Your Roblox universe (game) ID

Optional:
- `REALGAMEID` - Your main game place ID for automatic monitoring and auto-restore
- `ROBLOX_API_KEY` - Roblox Open Cloud API key (required for publishing)
- `ROBLOX_COOKIE` - Your .ROBLOSECURITY cookie (required for setupapikey command and REALGAMEID auto-restore)

The environment variables are already configured in this Repl. To modify them, use the Replit Secrets tab.

**Lua Script Configuration:**
1. Open `roblox_backup_script.lua`
2. Replace `YOUR_FIREBASE_URL_HERE` with your Firebase URL
3. Replace `YOUR_FIREBASE_AUTH_TOKEN_HERE` with your Firebase auth token

### 4. Running the Bot
The bot runs automatically. You can also start it manually with:
```bash
python bot.py
```

## Discord Commands

### Game Management
- `!setmaingame <place_id>` - Set main game to monitor (auto-restores when down)
- `!backup` - Create a new backup of the Roblox place
- `!checkbackup` - Check the current backup place ID
- `!settemplate <place_id>` - Set the template place ID (Admin only)

### Publishing
- `!publish <place_id>` - Publish a .rbxl file to a Roblox place (attach file)
- `!uploadgamefile` - Upload game file when auto-restore is triggered (attach .rbxl file)

### Audio Management
- `!upload <creator_id> "Name" [Description]` - Upload audio file (attach file)
  - Example: `!upload 123456 "My Song"`
  - For groups: `!upload g:789012 "Group Song"`

### Setup
- `!setupapikey <universe_id> <place_id>` - Setup API key automatically (Bot will DM you)
- `!help` - Show help message

## Automatic Game Monitoring (REALGAMEID)

For **automatic** monitoring without manual Discord commands, set the `REALGAMEID` environment variable:

1. Set `REALGAMEID` to your main game's place ID in the Secrets tab
2. Pre-populate `temp_places/` with your game's .rbxl file
3. The bot will automatically:
   - Monitor the game every 3 seconds
   - Detect when it goes down (404 error)
   - Get the backup place from Firebase
   - Generate an API key using your Roblox cookie
   - Auto-publish the .rbxl file to the backup place

**Note**: REALGAMEID monitoring runs independently from manual monitoring (!setmaingame). You can use both together for redundancy.

## How It Works

### Backup System
1. Discord bot sends a "clone" command to Firebase
2. Lua script (running in Template Game) polls Firebase for commands
3. When it sees a clone command, it creates a new place using AssetService:CreatePlaceAsync()
4. The new place ID is sent back to Firebase
5. Discord bot reads the response and stores the backup place ID

### Auto-Restore System
1. Bot monitors your main game every 3 seconds
2. If the game goes down (404 error), it triggers auto-restore
3. Waits 30 seconds for you to upload a game file via `!uploadgamefile`
4. Alternatively, looks for a .rbxl file in `directory/game-file/`
5. Creates a new backup place using the Lua script
6. Publishes the game file to the new backup place
7. Provides the new game link

## File Structure

- `bot.py` - Main Discord bot code
- `config.py` - Configuration with credentials
- `roblox_backup_script.lua` - Lua script for Roblox Studio
- `directory/game-file/` - Place .rbxl files here for auto-restore
- `temp_audio/` - Temporary storage for audio uploads
- `temp_places/` - Temporary storage for place uploads

## Important Notes

- The Lua script must be running in your Template Game for backups to work
- You need to be in the Template Game for the bot to trigger the join command
- Make sure to set up a valid Roblox Open Cloud API key for publishing to work
- Never share your credentials or Roblox cookie publicly

## Troubleshooting

### "HTTP 403 (Forbidden)" Error in Lua Script
This is the most common error with CreatePlaceAsync. It means permissions aren't configured correctly:

**Required Fixes:**
1. ✅ **Transfer game to GROUP ownership** (most important!)
   - Personal accounts have strict limitations
   - Go to Game Settings → Configure → Transfer to Group
   - You must be Owner/Admin in the group

2. ✅ **Enable all required permissions:**
   
   **In Roblox Studio** (File → Game Settings → Security):
   - "Allow HTTP Requests" = ON
   - "Enable Studio Access to API Services" = ON
   
   **On Roblox Website** (create.roblox.com → your game → Configure Start Place):
   - Permissions tab: "Allow Copying" = ON

3. ✅ **Test in a LIVE SERVER, not Studio:**
   - CreatePlaceAsync often fails in Studio even with correct permissions
   - Publish your game and play it from the Roblox website
   - Check Output logs in Developer Console (F9)

4. ✅ **Verify template place ID:**
   - Must be a valid place you own/control
   - Should belong to the same group
   - Must have copying enabled

### "No response from Lua script"
- Make sure you're testing in a **live server** (not Studio)
- Check that HttpService is enabled in the game settings
- Verify the Lua script is running in ServerScriptService as a **Script** (not ModuleScript)
- Check Firebase URL and auth token are correctly configured in the Lua script
- Look at the Output logs in Roblox (press F9) for detailed error messages

### "Publishing failed"
- Verify your Roblox API key is valid
- Check that the API key has permissions for the universe
- Ensure the place ID belongs to the correct universe
- Make sure you used `!setupapikey` or manually created an API key with proper permissions

### "Upload failed"
- Check file size limits (20MB for audio, 100MB for places)
- Verify file format is supported (.rbxl, .rbxlx for games; MP3, OGG, WAV, FLAC for audio)
- Make sure your API key has asset upload permissions
