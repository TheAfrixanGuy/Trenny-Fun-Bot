import os
import json
import asyncio
from typing import Dict, Any, List, Optional, Union
import logging
from discord.ext import commands

# Configure logger
logger = logging.getLogger("trenny_fun.db")

class DatabaseManager:
    """
    Handles all database operations for the bot.
    Can use either JSON files or MongoDB depending on configuration.
    """
    
    def __init__(self, bot, use_mongodb=False):
        self.bot = bot
        self.use_mongodb = use_mongodb
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
        self.cache = {}
        self.locks = {}
        
        # Create data directory if it doesn't exist
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
        # Initialize MongoDB if enabled
        if self.use_mongodb:
            try:
                import pymongo
                from pymongo import MongoClient
                
                # Get MongoDB URI from environment
                mongodb_uri = os.getenv('MONGODB_URI')
                if not mongodb_uri:
                    logger.warning("MongoDB enabled but no URI provided. Falling back to JSON storage.")
                    self.use_mongodb = False
                else:
                    self.client = MongoClient(mongodb_uri)
                    self.db = self.client.trenny_fun
                    logger.info("Connected to MongoDB successfully")
            except ImportError:
                logger.warning("pymongo not installed. Falling back to JSON storage.")
                self.use_mongodb = False
                
    async def get_user_data(self, user_id: int) -> Dict[str, Any]:
        """Get user data from database."""
        return await self._get_data('users', str(user_id))
        
    async def update_user_data(self, user_id: int, data: Dict[str, Any]) -> None:
        """Update user data in database."""
        await self._update_data('users', str(user_id), data)
        
    async def get_guild_data(self, guild_id: int) -> Dict[str, Any]:
        """Get guild data from database."""
        return await self._get_data('guilds', str(guild_id))
        
    async def update_guild_data(self, guild_id: int, data: Dict[str, Any]) -> None:
        """Update guild data in database."""
        await self._update_data('guilds', str(guild_id), data)
        
    async def get_game_data(self, game_name: str, user_id: Optional[int] = None, guild_id: Optional[int] = None) -> Dict[str, Any]:
        """Get game data from database."""
        if user_id and guild_id:
            key = f"{game_name}_{guild_id}_{user_id}"
        elif user_id:
            key = f"{game_name}_{user_id}"
        elif guild_id:
            key = f"{game_name}_{guild_id}"
        else:
            key = game_name
            
        return await self._get_data('games', key)
        
    async def update_game_data(self, game_name: str, data: Dict[str, Any], user_id: Optional[int] = None, guild_id: Optional[int] = None) -> None:
        """Update game data in database."""
        if user_id and guild_id:
            key = f"{game_name}_{guild_id}_{user_id}"
        elif user_id:
            key = f"{game_name}_{user_id}"
        elif guild_id:
            key = f"{game_name}_{guild_id}"
        else:
            key = game_name
            
        await self._update_data('games', key, data)
        
    async def get_economy_data(self, user_id: int, guild_id: int) -> Dict[str, Any]:
        """Get economy data for a user in a guild."""
        key = f"{guild_id}_{user_id}"
        return await self._get_data('economy', key)
        
    async def update_economy_data(self, user_id: int, guild_id: int, data: Dict[str, Any]) -> None:
        """Update economy data for a user in a guild."""
        key = f"{guild_id}_{user_id}"
        await self._update_data('economy', key, data)
        
    async def add_currency(self, user_id: int, guild_id: int, amount: int) -> int:
        """Add currency to a user and return new balance."""
        data = await self.get_economy_data(user_id, guild_id)
        
        # Initialize if user doesn't exist
        if not data:
            data = {"balance": 0, "inventory": [], "last_daily": 0}
            
        # Add currency
        data["balance"] += amount
        
        # Update database
        await self.update_economy_data(user_id, guild_id, data)
        
        return data["balance"]
        
    async def remove_currency(self, user_id: int, guild_id: int, amount: int) -> int:
        """Remove currency from a user and return new balance."""
        data = await self.get_economy_data(user_id, guild_id)
        
        # Initialize if user doesn't exist
        if not data:
            data = {"balance": 0, "inventory": [], "last_daily": 0}
            
        # Remove currency (don't go below 0)
        data["balance"] = max(0, data["balance"] - amount)
        
        # Update database
        await self.update_economy_data(user_id, guild_id, data)
        
        return data["balance"]
        
    async def get_leaderboard(self, guild_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get economy leaderboard for a guild."""
        if self.use_mongodb:
            collection = self.db.economy
            cursor = collection.find({"_id": {"$regex": f"^{guild_id}_"}}).sort("balance", -1).limit(limit)
            leaderboard = []
            
            async for doc in cursor:
                user_id = int(doc["_id"].split("_")[1])
                leaderboard.append({
                    "user_id": user_id,
                    "balance": doc["balance"]
                })
                
            return leaderboard
        else:
            # For JSON storage, load all economy data and filter
            economy_dir = os.path.join(self.data_dir, 'economy')
            if not os.path.exists(economy_dir):
                return []
                
            leaderboard = []
            for filename in os.listdir(economy_dir):
                if filename.startswith(f"{guild_id}_") and filename.endswith('.json'):
                    user_id = int(filename.split('_')[1].split('.')[0])
                    data = await self._get_data('economy', f"{guild_id}_{user_id}")
                    
                    if data:
                        leaderboard.append({
                            "user_id": user_id,
                            "balance": data.get("balance", 0)
                        })
            
            # Sort and limit
            leaderboard.sort(key=lambda x: x["balance"], reverse=True)
            return leaderboard[:limit]
        
    async def _get_data(self, collection: str, key: str) -> Dict[str, Any]:
        """Get data from database (either MongoDB or JSON)."""
        if self.use_mongodb:
            # Get data from MongoDB
            doc = await self.db[collection].find_one({"_id": key})
            return doc if doc else {}
        else:
            # Get data from JSON file
            cache_key = f"{collection}_{key}"
            
            # Check cache first
            if cache_key in self.cache:
                return self.cache[cache_key]
                
            # Get lock for this file
            if cache_key not in self.locks:
                self.locks[cache_key] = asyncio.Lock()
                
            async with self.locks[cache_key]:
                # Ensure collection directory exists
                collection_dir = os.path.join(self.data_dir, collection)
                if not os.path.exists(collection_dir):
                    os.makedirs(collection_dir)
                    
                # Get file path
                file_path = os.path.join(collection_dir, f"{key}.json")
                
                # Read file if it exists
                if os.path.exists(file_path):
                    try:
                        with open(file_path, 'r') as f:
                            data = json.load(f)
                            self.cache[cache_key] = data
                            return data
                    except json.JSONDecodeError:
                        logger.error(f"Error decoding JSON file: {file_path}")
                        return {}
                else:
                    return {}
        
    async def _update_data(self, collection: str, key: str, data: Dict[str, Any]) -> None:
        """Update data in database (either MongoDB or JSON)."""
        if self.use_mongodb:
            # Update data in MongoDB
            await self.db[collection].update_one(
                {"_id": key},
                {"$set": data},
                upsert=True
            )
        else:
            # Update data in JSON file
            cache_key = f"{collection}_{key}"
            
            # Update cache
            self.cache[cache_key] = data
            
            # Get lock for this file
            if cache_key not in self.locks:
                self.locks[cache_key] = asyncio.Lock()
                
            async with self.locks[cache_key]:
                # Ensure collection directory exists
                collection_dir = os.path.join(self.data_dir, collection)
                if not os.path.exists(collection_dir):
                    os.makedirs(collection_dir)
                    
                # Get file path
                file_path = os.path.join(collection_dir, f"{key}.json")
                
                # Write to file
                try:
                    with open(file_path, 'w') as f:
                        json.dump(data, f, indent=2)
                except Exception as e:
                    logger.error(f"Error writing to JSON file: {file_path} - {e}")
                    
    async def _delete_data(self, collection: str, key: str) -> None:
        """Delete data from database (either MongoDB or JSON)."""
        if self.use_mongodb:
            # Delete data from MongoDB
            await self.db[collection].delete_one({"_id": key})
        else:
            # Delete data from JSON file
            cache_key = f"{collection}_{key}"
            
            # Remove from cache
            if cache_key in self.cache:
                del self.cache[cache_key]
                
            # Get lock for this file
            if cache_key not in self.locks:
                self.locks[cache_key] = asyncio.Lock()
                
            async with self.locks[cache_key]:
                # Get file path
                file_path = os.path.join(self.data_dir, collection, f"{key}.json")
                
                # Delete file if it exists
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        logger.error(f"Error deleting JSON file: {file_path} - {e}")


class DatabaseCog(commands.Cog):
    """Database management utility for the bot."""
    
    def __init__(self, bot):
        self.bot = bot
        self.category = "utils"  # For help command
        self.db_manager = DatabaseManager(bot, use_mongodb='MONGODB_URI' in os.environ)


async def setup(bot):
    """Setup function for the database cog."""
    await bot.add_cog(DatabaseCog(bot))
