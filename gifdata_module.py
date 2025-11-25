import os
import math
import time
import json
import requests
import xmltodict
import re
import ast
from PIL import Image, ImageSequence

# Variables
MAX_DIMENSION = 1024
UPLOAD_URL = "https://apis.roblox.com/assets/user-auth/v1/assets"
USER_INFO_URL = "https://users.roblox.com/v1/users/authenticated"
OPERATION_URL_BASE = "https://apis.roblox.com/assets/user-auth/v1/operations/"
TEMP_DIR = "temp_gifdata"
COOKIE_FILE = "roblox_cookie.txt"

# Roblox api stuff
def get_csrf_token(auth_cookie):
    response = requests.post(UPLOAD_URL, headers={"Cookie": f".ROBLOSECURITY={auth_cookie}"})
    if response.status_code == 403:
        return response.headers.get("x-csrf-token")
    raise Exception("Failed to get CSRF token")

def get_user_id(auth_cookie):
    response = requests.get(USER_INFO_URL, headers={"Cookie": f".ROBLOSECURITY={auth_cookie}"})
    if response.status_code == 200:
        return response.json()["id"]
    raise Exception("Failed to get authenticated user")

def poll_operation(operation_id, auth_cookie):
    for _ in range(10):
        time.sleep(2)
        url = OPERATION_URL_BASE + operation_id
        response = requests.get(url, headers={"Cookie": f".ROBLOSECURITY={auth_cookie}"})
        if response.status_code == 200:
            data = response.json()
            if data.get("done") and data.get("response", {}).get("assetId"):
                return data["response"]["assetId"]
    raise Exception("Asset processing timed out")

def upload_asset(file_path, auth_cookie, user_id, csrf_token):
    with open(file_path, "rb") as f:
        files = {
            "fileContent": (os.path.basename(file_path), f, "image/png")
        }
        payload = {
            "request": json.dumps({
                "displayName": os.path.basename(file_path),
                "description": "Bream so cool",
                "assetType": "Decal",
                "creationContext": {
                    "creator": { "userId": user_id },
                    "expectedPrice": 0
                }
            })
        }
        headers = {
            "x-csrf-token": csrf_token,
            "Cookie": f".ROBLOSECURITY={auth_cookie}"
        }
        response = requests.post(UPLOAD_URL, data=payload, files=files, headers=headers)
        if response.status_code == 200:
            operation_id = response.json().get("operationId")
            if not operation_id:
                raise Exception("Missing operation ID")
            return poll_operation(operation_id, auth_cookie)
        raise Exception(f"Upload failed: {response.status_code} - {response.text}")

# Sprite sheet processing
def create_sprite_sheets(gif_path, gif_name):
    gif = Image.open(gif_path)
    frames = [frame.convert("RGBA") for frame in ImageSequence.Iterator(gif)]
    num_frames = len(frames)
    width, height = frames[0].size
    columns = MAX_DIMENSION // width
    frames_per_sheet = columns * (MAX_DIMENSION // height)
    num_sheets = math.ceil(num_frames / frames_per_sheet)
    os.makedirs(TEMP_DIR, exist_ok=True)

    sheet_paths = []
    rows_per_sheet = []

    for sheet_index in range(num_sheets):
        start = sheet_index * frames_per_sheet
        end = min(start + frames_per_sheet, num_frames)
        frames_in_sheet = end - start
        rows = min(MAX_DIMENSION // height, math.ceil(frames_in_sheet / columns))
        sheet = Image.new('RGBA', (columns * width, rows * height))

        x, y = 0, 0
        for i in range(frames_in_sheet):
            frame = frames[start + i]
            sheet.paste(frame, (x * width, y * height), mask=frame)
            x += 1
            if x == columns:
                x = 0
                y += 1

        path = os.path.join(TEMP_DIR, f"{gif_name}_sheet_{sheet_index + 1}.png")
        sheet.save(path)
        sheet_paths.append(path)
        rows_per_sheet.append(rows)

    return sheet_paths, rows_per_sheet, num_frames, width - 1, height - 1, columns

# super sigma decal to image id converter
def grab_image_id(decal_id, auth_cookie):
    url = f"https://assetdelivery.roblox.com/v1/asset/?id={decal_id}"
    headers = {
        "Cookie": f".ROBLOSECURITY={auth_cookie}"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        data = xmltodict.parse(response.text)
        content_url = data.get("roblox", {}).get("Item", {}).get("Properties", {}).get("Content", {}).get("url")

        if content_url:
            if "rbxassetid://" in content_url:
                return content_url.split("rbxassetid://")[1]
            elif "?id=" in content_url:
                return content_url.split("?id=")[1]
    except Exception as e:
        print(f"Failed to fetch asset ID: {e}")

    return None

def convert_lua_to_python_format(lua_str):
    """Convert Lua table format to Python dict format"""
    # Replace Lua table syntax with Python dict syntax
    result = lua_str
    
    # Convert {{...}} to [{...}] (table of tables)
    result = result.replace("{{", "[{").replace("}}", "}]")
    
    # Convert key=value to "key":value
    result = re.sub(r'(\w+)=', r'"\1":', result)
    
    # Remove trailing commas before closing brackets
    result = re.sub(r',(\s*[}\]])', r'\1', result)
    
    # Wrap in braces if it's not already wrapped
    if not result.strip().startswith('{'):
        result = "{" + result + "}"
    
    return result

# lua to python dictionary
def lua_to_python_dict(gif_str):
    # Convert Lua format to Python format first
    formatted = convert_lua_to_python_format(gif_str)
    try:
        return ast.literal_eval(formatted)
    except Exception as e:
        raise ValueError(f"Failed to parse input: {e}")

def slice_frames(sheet_img, frame_width, frame_height, frames_per_row, total_frames):
    frames = []
    for i in range(total_frames):
        row = i // frames_per_row
        col = i % frames_per_row
        x = col * frame_width
        y = row * frame_height
        frame = sheet_img.crop((x, y, x + frame_width, y + frame_height))
        frames.append(frame)
    return frames

def rebuild_gif_from_gifdata(gif_input, image_paths, output_path="rebuilt.gif", fps=24):
    data = lua_to_python_dict(gif_input)

    fWidth = data["fWidth"] + 1
    fHeight = data["fHeight"] + 1
    total_needed_frames = data["nFrames"]

    all_frames = []

    for i, sheet in enumerate(data["sheets"]):
        image_path = image_paths[i]
        try:
            img = Image.open(image_path).convert("RGBA")
        except Exception as e:
            print(f"Failed to load image at {image_path}: {e}")
            continue

        rows = sheet.get("rows", 1)
        frames_per_sheet = rows * data["framesPerRow"]
        remaining_frames = total_needed_frames - len(all_frames)
        frames_to_extract = min(frames_per_sheet, remaining_frames)

        if frames_to_extract <= 0:
            break

        frames = slice_frames(
            img,
            fWidth,
            fHeight,
            data["framesPerRow"],
            frames_to_extract
        )
        all_frames.extend(frames)

    if all_frames:
        frame_duration = int(1000 / fps)
        all_frames[0].save(
            output_path,
            save_all=True,
            append_images=all_frames[1:],
            duration=frame_duration,
            loop=0,
            disposal=2
        )
        return output_path
    else:
        raise Exception("No frames extracted.")



def ensure_temp_dir():
    os.makedirs(TEMP_DIR, exist_ok=True)

# Global cache for pokedex
_pokedex_cache = None

def load_pokedex():
    """Load Pokemon data from pokedex.lua with full stats (cached)"""
    global _pokedex_cache
    
    # Return cached version if available
    if _pokedex_cache is not None:
        return _pokedex_cache
    
    try:
        pokedex_file = "pokedex.lua"
        if not os.path.exists(pokedex_file):
            print(f"Error: {pokedex_file} not found")
            return {}
        
        with open(pokedex_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        if not content:
            print("Error: pokedex.lua is empty")
            return {}
        
        pokedex = {}
        # Split entries by },\n or },\r\n to process each pokemon separately
        entries = re.split(r'},\s*\n', content)
        
        for entry in entries:
            # Extract pokemon name
            name_match = re.match(r'\s*(\w+)=\{', entry)
            if not name_match:
                continue
            
            key = name_match.group(1)
            
            # Extract species
            species_match = re.search(r'species="([^"]+)"', entry)
            if not species_match:
                continue
            
            species = species_match.group(1)
            
            # Extract baseStats
            stats_match = re.search(r'baseStats=\{(\d+,\d+,\d+,\d+,\d+,\d+)\}', entry)
            if not stats_match:
                continue
            
            try:
                base_stats = [int(x) for x in stats_match.group(1).split(',')]
                bst = sum(base_stats)
                
                pokedex[key] = {
                    "species": species,
                    "baseStats": base_stats,
                    "bst": bst
                }
            except Exception:
                continue
        
        # Cache the result
        _pokedex_cache = pokedex
        return pokedex
    except Exception as e:
        print(f"Error loading pokedex: {e}")
        return {}

# Global cache for items
_items_cache = None

def load_items():
    """Load items from itemmeta.lua with sell prices (cached)"""
    global _items_cache
    
    # Return cached version if available
    if _items_cache is not None:
        return _items_cache
    
    try:
        items_file = "itemmeta.lua"
        if not os.path.exists(items_file):
            print(f"Error: {items_file} not found")
            return {}
        
        with open(items_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        if not content:
            print("Error: itemmeta.lua is empty")
            return {}
        
        items = {}
        # Match CSV lines: id,name,sell_price
        lines = content.split('\n')
        in_csv = False
        for line in lines:
            if '[[item_id,name,sell_price' in line:
                in_csv = True
                continue
            if in_csv and line.strip() and not line.startswith(']]'):
                parts = line.split(',')
                if len(parts) >= 3:
                    try:
                        item_id = int(parts[0].strip())
                        item_name = parts[1].strip().strip('"')
                        sell_price_str = parts[2].strip()
                        sell_price = int(sell_price_str) if sell_price_str and sell_price_str.isdigit() else None
                        
                        if sell_price is not None and sell_price > 0:
                            items[item_name] = {
                                "id": item_id,
                                "sell_price": sell_price
                            }
                    except:
                        pass
        
        # Cache the result
        _items_cache = items
        return items
    except Exception as e:
        print(f"Error loading items: {e}")
        return {}

def get_tier_and_emoji(bst):
    """Get tier name and emoji based on BST"""
    if bst >= 580:
        return "Legendary", "✨"
    elif bst >= 530:
        return "Mythic", "💜"
    elif bst >= 480:
        return "Epic", "💎"
    elif bst >= 430:
        return "Rare", "💙"
    else:
        return "Common", "💛"

def load_gifdata():
    """Load sprite data from gifdata.lua"""
    try:
        with open("gifdata.lua", "r", encoding="utf-8") as f:
            content = f.read()
        
        gifdata = {"_FRONT": {}}
        
        pattern = r"\['([^']+)'\]=\{sheets=\{\{id=(\d+)"
        matches = re.finditer(pattern, content)
        
        for match in matches:
            name = match.group(1)
            sprite_id = int(match.group(2))
            gifdata["_FRONT"][name] = {"sheets": [{"id": sprite_id}]}
        
        return gifdata if gifdata["_FRONT"] else {}
    except Exception as e:
        print(f"Error loading gifdata: {e}")
    return {"_FRONT": {}}

def get_pokemon_sprite(pokemon_name, gifdata=None):
    """Get sprite asset ID for Pokemon"""
    if gifdata is None:
        gifdata = load_gifdata()
    
    front_sprites = gifdata.get("_FRONT", {})
    if pokemon_name in front_sprites:
        sprite_data = front_sprites[pokemon_name]
        if sprite_data and "sheets" in sprite_data and len(sprite_data["sheets"]) > 0:
            return sprite_data["sheets"][0]["id"]
    return None

def get_all_gifdata_names():
    """Get all Pokemon names available in gifdata.lua"""
    try:
        with open("gifdata.lua", "r", encoding="utf-8") as f:
            content = f.read()
        
        names = []
        # Find all entries in the _FRONT table
        pattern = r"\['([^']+)'\]=\{|\"([^\"]+)\"=\{"
        matches = re.finditer(pattern, content)
        
        for match in matches:
            name = match.group(1) or match.group(2)
            if name and name != "_FRONT":
                names.append(name)
        
        return names
    except Exception as e:
        print(f"Error getting gifdata names: {e}")
    return []

def name_similarity(s1, s2):
    """Calculate name similarity (0-1) between two Pokemon names"""
    # Normalize: lowercase, remove spaces and dashes
    s1_norm = s1.lower().replace(" ", "").replace("-", "")
    s2_norm = s2.lower().replace(" ", "").replace("-", "")
    
    if not s1_norm or not s2_norm:
        return 0.0
    
    # Count matching characters
    matches = sum(1 for c in s1_norm if c in s2_norm)
    return matches / max(len(s1_norm), len(s2_norm))

def find_closest_gifdata_match(pokemon_name, min_similarity=0.66):
    """Find closest matching Pokemon name in gifdata (min 66% similarity)"""
    all_names = get_all_gifdata_names()
    if not all_names:
        return None
    
    # Calculate similarity for each name
    similarities = [(name, name_similarity(pokemon_name, name)) for name in all_names]
    
    # Sort by similarity (highest first)
    similarities.sort(key=lambda x: x[1], reverse=True)
    
    # Return the closest match if it meets minimum threshold
    if similarities and similarities[0][1] >= min_similarity:
        return similarities[0][0]
    
    return None

def get_full_gifdata_entry(pokemon_name):
    """Extract full gifdata entry for a Pokemon from gifdata.lua"""
    try:
        with open("gifdata.lua", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Find the entry for this pokemon - match from ={ to },
        pattern = rf"\['{re.escape(pokemon_name)}'\]=\{{(.*?)\}},"
        match = re.search(pattern, content, re.DOTALL)
        
        if match:
            entry_str = match.group(1)
            return entry_str
    except Exception as e:
        print(f"Error extracting gifdata for {pokemon_name}: {e}")
    return None

def download_sprite_sheet(sheet_id):
    """Download sprite sheet image from Roblox"""
    try:
        os.makedirs(TEMP_DIR, exist_ok=True)
        url = f"https://assetdelivery.roblox.com/v1/asset/?id={sheet_id}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        file_path = os.path.join(TEMP_DIR, f"sheet_{sheet_id}.png")
        with open(file_path, "wb") as f:
            f.write(response.content)
        return file_path
    except Exception as e:
        print(f"Error downloading sprite sheet {sheet_id}: {e}")
    return None

def generate_pokemon_gif(pokemon_name, fps=24):
    """Generate a GIF from Pokemon sprite data"""
    try:
        # Try exact match first
        gifdata_name = pokemon_name
        gifdata_str = get_full_gifdata_entry(gifdata_name)
        
        # If not found, try to find closest match
        if not gifdata_str:
            gifdata_name = find_closest_gifdata_match(pokemon_name)
            if gifdata_name:
                print(f"Using closest match: {pokemon_name} -> {gifdata_name}")
                gifdata_str = get_full_gifdata_entry(gifdata_name)
        
        if not gifdata_str:
            print(f"No gifdata found for {pokemon_name}")
            return None
        
        # Convert Lua format to Python dict format, then parse
        data = lua_to_python_dict(gifdata_str)
        
        # Download all sprite sheets
        image_paths = []
        if "sheets" in data:
            for sheet_info in data["sheets"]:
                sheet_id = sheet_info.get("id")
                if sheet_id:
                    sheet_path = download_sprite_sheet(sheet_id)
                    if sheet_path:
                        image_paths.append(sheet_path)
        
        if not image_paths:
            print(f"No sprite sheets could be downloaded for {gifdata_name}")
            return None
        
        # Generate the GIF
        output_path = os.path.join(TEMP_DIR, f"{pokemon_name}.gif")
        gif_path = rebuild_gif_from_gifdata(gifdata_str, image_paths, output_path, fps)
        return gif_path
    except Exception as e:
        print(f"Error generating GIF for {pokemon_name}: {e}")
        import traceback
        traceback.print_exc()
    return None

def get_random_pokemon(pokedex=None):
    """Get random Pokemon"""
    if pokedex is None:
        pokedex = load_pokedex()
    
    if not pokedex:
        return None
    
    import random
    pokemon_list = list(pokedex.keys())
    if not pokemon_list:
        return None
    
    return random.choice(pokemon_list)

def cleanup_temp_dir():
    """Clean up temporary files"""
    try:
        for f in os.listdir(TEMP_DIR):
            try:
                file_path = os.path.join(TEMP_DIR, f)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            except:
                pass
    except:
        pass