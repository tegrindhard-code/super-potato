import discord
import requests
import json
from datetime import datetime, timedelta
from config import SPIN_FIREBASE_URL, SPIN_FIREBASE_AUTH_TOKEN, BOOSTER_ROLE_ID

WINGS_PER_SPIN = 1
DAILY_SPINS_NORMAL = 2
DAILY_SPINS_BOOSTER = 4
DAILY_WINGS_NORMAL = DAILY_SPINS_NORMAL * WINGS_PER_SPIN
DAILY_WINGS_BOOSTER = DAILY_SPINS_BOOSTER * WINGS_PER_SPIN

class SpinManager:
    def __init__(self):
        self.firebase_url = SPIN_FIREBASE_URL
        self.auth_token = SPIN_FIREBASE_AUTH_TOKEN
    
    def _get_user_path(self, user_id):
        """Get Firebase path for user spin data"""
        return f"/spindata/{user_id}"
    
    def _get_url(self, path):
        """Build Firebase URL"""
        return f"{self.firebase_url}{path}.json?auth={self.auth_token}"
    
    def _reset_daily_limit(self, today_str):
        """Create new daily reset structure"""
        return {
            "date": today_str,
            "wings": 0,
            "spins_used": 0,
            "last_updated": datetime.utcnow().isoformat()
        }
    
    def get_user_data(self, user_id):
        """Get user's spin data from Firebase"""
        try:
            response = requests.get(self._get_url(self._get_user_path(user_id)), timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data if data else {}
            return {}
        except:
            return {}
    
    def set_user_data(self, user_id, data):
        """Save user's spin data to Firebase"""
        try:
            response = requests.put(
                self._get_url(self._get_user_path(user_id)),
                data=json.dumps(data),
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            return response.status_code == 200
        except:
            return False
    
    def get_daily_data(self, user_id, today_str=None):
        """Get today's spin/wing data"""
        if today_str is None:
            today_str = datetime.utcnow().strftime("%Y-%m-%d")
        
        user_data = self.get_user_data(user_id)
        daily = user_data.get("daily", {})
        
        if daily.get("date") != today_str:
            return self._reset_daily_limit(today_str)
        
        return daily
    
    def add_wings(self, user_id, amount, reason=""):
        """Add wings to user's balance"""
        user_data = self.get_user_data(user_id)
        current_wings = user_data.get("total_wings", 0)
        user_data["total_wings"] = current_wings + amount
        
        if reason:
            history = user_data.get("history", [])
            history.append({
                "action": "add_wings",
                "amount": amount,
                "reason": reason,
                "timestamp": datetime.utcnow().isoformat()
            })
            user_data["history"] = history
        
        return self.set_user_data(user_id, user_data)
    
    def can_spin(self, member):
        """Check if user has enough wings to spin (no daily limits)"""
        user_data = self.get_user_data(member.id)
        total_wings = user_data.get("total_wings", 0)
        has_wings = total_wings >= WINGS_PER_SPIN
        return has_wings, total_wings
    
    def use_spin(self, member, pokemon_name):
        """Consume a spin (deduct wings only, no daily limits)"""
        user_data = self.get_user_data(member.id)
        
        user_data["total_wings"] = user_data.get("total_wings", 0) - WINGS_PER_SPIN
        
        pokemon_list = user_data.get("pokemon", [])
        pokemon_list.append({
            "name": pokemon_name,
            "timestamp": datetime.utcnow().isoformat()
        })
        user_data["pokemon"] = pokemon_list
        
        return self.set_user_data(member.id, user_data)
    
    def get_user_stats(self, user_id):
        """Get user's spin statistics"""
        user_data = self.get_user_data(user_id)
        return {
            "total_wings": user_data.get("total_wings", 0),
            "total_pokemon_spun": len(user_data.get("pokemon", [])),
            "daily": user_data.get("daily", {}),
            "recent_pokemon": user_data.get("pokemon", [])[-5:]
        }

spin_manager = SpinManager()
