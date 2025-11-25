# Roblox Automatic Reupload System

## Overview

This project is an automated Discord bot system designed to manage Roblox game backups and publishing workflows. It bridges Discord, Firebase Realtime Database, and Roblox to enable automated game monitoring, backup restoration, and asset management. The system allows communication between a Discord bot (Python) and Roblox game servers (Lua) via Firebase, acting as a message queue and data store. Its purpose is to provide robust game stability by automatically restoring games in case of unexpected takedowns, alongside offering advanced asset management and a unique in-game interactive system.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Core Design Pattern

The system implements a **command-and-response architecture** using Firebase Realtime Database as a communication bridge between Discord Bot (Python), Firebase, and Roblox Game Server (Lua). This decoupled architecture addresses the inability of Roblox game servers to directly communicate with Discord and vice-versa, with Firebase serving as a cloud-based intermediary.

### Frontend Architecture

**Discord Bot Interface**: Built using discord.py with slash commands for all interactions (e.g., `/backup`, `/spin`, `/publish`). It handles game monitoring, file publishing, audio asset uploading, API key management via browser automation, and a Pokemon gacha spin system with a rainbow wings currency. The spin embed displays animated GIF sprites reconstructed from `gifdata.lua` sprite sheet data, downloaded from Roblox, and rebuilt using PIL. Discord was chosen for real-time notifications, file handling, chat history, and accessibility.

### Backend Architecture

**Python Discord Bot (bot.py)**: Utilizes an asynchronous, event-driven architecture. It features background tasks for periodic game monitoring, file system operations for temporary storage, and Selenium WebDriver integration for browser automation. A two-tier monitoring system includes manual (`main_game_id`) and automatic (`REALGAMEID`) game monitoring. Configuration is managed via environment variables (`config.py`) for security and flexibility.

**Data Flow Architecture**:
- **Command Flow**: Discord command -> Bot writes to Firebase (`/command`) -> Lua script polls Firebase -> Lua executes operations -> Lua writes response to Firebase (`/response`) -> Bot reads response -> Discord notification.
- **Backup/Restore Flow**: Bot triggers backup via Firebase -> Lua uses AssetService to clone -> Backup ID stored in Firebase.
- **REALGAMEID Auto-Restore Flow**: Periodically, the bot backs up a template place, storing its ID in Firebase. If the `REALGAMEID` game is detected as down (404), the system automatically retrieves a pre-backed-up `.rbxl` file, generates a temporary API key via Selenium, publishes the file, and notifies Discord.

### Authentication Architecture

**Multi-layer Authentication**: Involves Firebase token-based authentication, Discord bot token authentication, and a dual Roblox authentication system (cookie-based for browser automation via `.ROBLOSECURITY` and API key-based for Open Cloud operations). Selenium automates API key generation and authenticated sessions for operations lacking direct programmatic endpoints.

### File Management

**Local Storage Strategy**: Uses `maingame.json` for configuration, `directory/game-file/` for temporary game file uploads, `temp_places/` for auto-restore `.rbxl` files, and `temp_audio/` for temporary audio files. Supports Roblox game files (.rbxl, .rbxlx), audio files (MP3, OGG, WAV, FLAC with conversion), and Pokemon sprite data. Local storage enables validation, format conversion, and immediate file access for auto-restore.

### Three Separate Reward Systems

**1. SPIN System** - Random Pokemon/Item gacha using "Rainbow Wings" currency
- Users spin for random Pokemon (70% chance) or items (30% chance) - **either one, never both**
- Pokemon level determined by Base Stat Total (BST) tier, not player badges
- Costs 1 rainbow wing per spin
- No daily limits
- Discord command: `/spin`
- **Mega Pokemon Formatting**: Displayed as `BaseName-M` (e.g., `Charizard-M`)
- **GIF Sprite Display**: Reconstructs animated GIF sprites from `gifdata.lua` entries:
  1. Extracting full sprite metadata (sheets, frame dimensions, frame count)
  2. Downloading sprite sheets from Roblox CDN
  3. Slicing frames from sheets using PIL
  4. Rebuilding as animated GIF with original animation speed
  5. Attaching GIF to Discord embed
- **Fuzzy Matching**: If exact Pokemon name not found in gifdata, finds closest match with 66% name similarity threshold

**2. SPAWN System** - Admin command to spawn exact rewards
- Admins use `/spawnpokemon` in Discord to spawn specific Pokemon at specific levels for players
- Can spawn exact items, currency, Battle Points, Tix, TMs, Rare Candies
- No badges-based scaling - exact rewards specified by admin
- Implemented in `spawn_command.lua` with functions for each reward type
- Firebase `/spawn.json` endpoint for communication

**3. CODES System** - Promotional redemption codes
- Mods create codes via `/createcode` command
- Codes work like SPAWN - exact rewards specified by creator
- Supports expiration dates and usage limits
- All code data stored in Firebase `/codes.json`
- Automatically loaded into Roblox via `loadDynamicCodes()` in `checkCode()`

**Available Code Functions (via `/createcode`)**:
- `pokemon` - Award specific Pokemon at specific level
- `item` - Award items with quantity
- `money` - Award in-game currency
- `bp` - Award Battle Points
- `tix` - Award Tickets
- `tm` - Award Technical Machine

## Slash Commands

**User Commands**:
- `/spin` - Spin for a random Pokemon or item (costs 1 rainbow wing)
- `/spinstats` - View spin statistics and total Pokemon won
- `/link_roblox` - Link Discord account to Roblox username
- `/gifinfo <pokemon_name>` - Get sprite animation info
- `/pokemonlist [page]` - Browse Pokemon with pagination

**Mod Commands**:
- `/addwings <user> <amount>` - Award wings to user
- `/addwings_all <amount>` - Award wings to all members
- `/createcode <code_name> <function> <param1> [param2] [level] [expiration_days] [limit]` - Create redemption code
  - Examples: 
    - `/createcode PIKACODE pokemon Pikachu level:25` - Award Pikachu Lv 25
    - `/createcode PROMO item pokeball 50 expiration_days:7 limit:1000` - Award 50 Pokéballs, expires in 7 days, max 1000 uses
    - `/createcode SEASONAL money 5000 expiration_days:30 limit:100` - Award $5000, expires in 30 days, max 100 players

**Admin Commands**:
- `/spawnpokemon <roblox_username> <pokemon_name> [level]` - Spawn Pokemon for a player

## External Dependencies

### Cloud Services

**Firebase Realtime Database**: Used as a message queue and state persistence layer for `/command.json` and `/response.json` endpoints.

### Roblox Platform APIs

**Roblox Open Cloud API**: Utilized for publishing game files and managing assets, requiring API key authentication with specific permissions.
**Roblox AssetService (Lua)**: Used for creating place backups via `CreatePlaceAsync` within the Roblox game environment.
**Roblox Web Platform**: Accessed via Selenium for operations lacking direct API support, such as API key generation and account management, requiring cookie-based authentication.

### Third-Party Libraries

**Python**: `discord.py`, `requests`, `selenium`, `webdriver`.
**Browser**: Chrome/Chromium and ChromeDriver for Selenium automation.

### Platform Requirements

**Deployment Environment**: Replit (Nix-based, secrets management, persistent storage, Python 3.x).
**Roblox Game Requirements**: Template game owned by a Roblox GROUP with the bot user as Owner/Admin. Requires "Allow HTTP Requests" and "Enable Studio Access to API Services" in Studio settings, and "Allow Copying" on the website.