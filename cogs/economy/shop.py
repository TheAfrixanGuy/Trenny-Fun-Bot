import discord
from discord.ext import commands
import asyncio
import json
from typing import Dict, List, Optional, Union
import os

class Shop(commands.Cog):
    """Advanced shop system for purchasing items with currency."""
    
    def __init__(self, bot):
        self.bot = bot
        self.category = "economy"  # For help command
        self.currency_name = "coins"
        self.currency_emoji = "🪙"
        self.items_per_page = 5
        
        # Default shop items
        self.default_items = [
            {
                "id": "color_red",
                "name": "Red Color Role",
                "emoji": "🔴",
                "description": "A red color role to stand out in the server.",
                "price": 500,
                "type": "role",
                "role_color": 0xFF0000
            },
            {
                "id": "color_blue",
                "name": "Blue Color Role",
                "emoji": "🔵",
                "description": "A blue color role to stand out in the server.",
                "price": 500,
                "type": "role",
                "role_color": 0x0000FF
            },
            {
                "id": "color_green",
                "name": "Green Color Role",
                "emoji": "🟢",
                "description": "A green color role to stand out in the server.",
                "price": 500,
                "type": "role",
                "role_color": 0x00FF00
            },
            {
                "id": "color_purple",
                "name": "Purple Color Role",
                "emoji": "🟣",
                "description": "A purple color role to stand out in the server.",
                "price": 500,
                "type": "role",
                "role_color": 0x800080
            },
            {
                "id": "color_gold",
                "name": "Gold Color Role",
                "emoji": "🟡",
                "description": "A prestigious gold color role.",
                "price": 1000,
                "type": "role",
                "role_color": 0xFFD700
            },
            {
                "id": "vip",
                "name": "VIP Role",
                "emoji": "👑",
                "description": "A special VIP role with perks.",
                "price": 5000,
                "type": "role",
                "role_color": 0xFFD700
            },
            {
                "id": "lootbox_common",
                "name": "Common Lootbox",
                "emoji": "📦",
                "description": "A common lootbox with random items and coins.",
                "price": 200,
                "type": "lootbox",
                "min_coins": 50,
                "max_coins": 300,
                "rarity": "common"
            },
            {
                "id": "lootbox_rare",
                "name": "Rare Lootbox",
                "emoji": "🎁",
                "description": "A rare lootbox with better items and coins.",
                "price": 500,
                "type": "lootbox",
                "min_coins": 200,
                "max_coins": 800,
                "rarity": "rare"
            },
            {
                "id": "lootbox_epic",
                "name": "Epic Lootbox",
                "emoji": "💎",
                "description": "An epic lootbox with valuable items and coins.",
                "price": 1000,
                "type": "lootbox",
                "min_coins": 500,
                "max_coins": 2000,
                "rarity": "epic"
            },
            {
                "id": "daily_booster",
                "name": "Daily Reward Booster",
                "emoji": "🚀",
                "description": "Doubles your daily reward for 7 days.",
                "price": 2000,
                "type": "booster",
                "duration": 7,
                "effect": "daily_multiplier",
                "multiplier": 2
            }
        ]
    
    @commands.group(name="shop", invoke_without_command=True)
    async def shop(self, ctx, page: int = 1):
        """
        Browse the shop to purchase items with your coins.
        
        Examples:
        !shop - Show the first page of shop items
        !shop 2 - Show the second page of shop items
        """
        # Get shop items for this guild
        items = await self.get_shop_items(ctx.guild.id)
        
        # Calculate total pages
        total_pages = max(1, (len(items) + self.items_per_page - 1) // self.items_per_page)
        
        # Validate page number
        if page < 1:
            page = 1
        elif page > total_pages:
            page = total_pages
        
        # Get items for this page
        start_idx = (page - 1) * self.items_per_page
        end_idx = start_idx + self.items_per_page
        page_items = items[start_idx:end_idx]
        
        # Create embed
        embed = discord.Embed(
            title=f"🛒 {ctx.guild.name} Shop",
            description="Purchase items using your coins!\nUse `!shop buy <item_id>` to buy an item.",
            color=discord.Color.blue()
        )
        
        # Add items to embed
        for item in page_items:
            name = f"{item['emoji']} {item['name']} ({item['price']} {self.currency_emoji})"
            value = f"{item['description']}\nID: `{item['id']}`"
            embed.add_field(name=name, value=value, inline=False)
        
        # Add pagination footer
        embed.set_footer(text=f"Page {page}/{total_pages} • Use !shop <page> to view more items")
        
        # Send embed
        message = await ctx.send(embed=embed)
        
        # Add navigation reactions if multiple pages
        if total_pages > 1:
            await message.add_reaction("◀️")  # Previous page
            await message.add_reaction("▶️")  # Next page
            
            # Wait for reaction
            def check(reaction, user):
                return (
                    user == ctx.author and
                    str(reaction.emoji) in ["◀️", "▶️"] and
                    reaction.message.id == message.id
                )
            
            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=30.0, check=check)
                
                # Handle navigation
                if str(reaction.emoji) == "◀️" and page > 1:
                    await message.delete()
                    await self.shop(ctx, page - 1)
                elif str(reaction.emoji) == "▶️" and page < total_pages:
                    await message.delete()
                    await self.shop(ctx, page + 1)
                
            except asyncio.TimeoutError:
                try:
                    await message.clear_reactions()
                except:
                    pass
    
    @shop.command(name="buy")
    async def shop_buy(self, ctx, item_id: str):
        """
        Purchase an item from the shop.
        
        Examples:
        !shop buy color_red - Buy the red color role
        !shop buy lootbox_common - Buy a common lootbox
        """
        # Get shop items for this guild
        items = await self.get_shop_items(ctx.guild.id)
        
        # Find the item by ID
        item = None
        for shop_item in items:
            if shop_item["id"].lower() == item_id.lower():
                item = shop_item
                break
        
        if not item:
            embed = discord.Embed(
                title="❌ Item Not Found",
                description=f"The item with ID `{item_id}` was not found in the shop.\nUse `!shop` to see available items.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Get database manager
        db_manager = self.bot.get_cog("Utils").db_manager if hasattr(self.bot.get_cog("Utils"), "db_manager") else None
        
        if not db_manager:
            embed = discord.Embed(
                title="❌ Database Error",
                description="Could not access the economy database.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        try:
            # Get user data
            data = await db_manager.get_economy_data(ctx.author.id, ctx.guild.id)
            
            if not data:
                # Initialize if user doesn't exist
                data = {"balance": 0, "inventory": [], "last_daily": 0, "daily_streak": 0}
                await db_manager.update_economy_data(ctx.author.id, ctx.guild.id, data)
            
            # Check if user has enough coins
            balance = data.get("balance", 0)
            price = item["price"]
            
            if balance < price:
                embed = discord.Embed(
                    title="❌ Insufficient Funds",
                    description=f"You don't have enough {self.currency_name}!\nItem price: **{price}** {self.currency_emoji}\nYour balance: **{balance}** {self.currency_emoji}",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            # Process purchase based on item type
            if item["type"] == "role":
                success = await self.process_role_purchase(ctx, item)
            elif item["type"] == "lootbox":
                success = await self.process_lootbox_purchase(ctx, item, data)
            elif item["type"] == "booster":
                success = await self.process_booster_purchase(ctx, item, data)
            else:
                success = await self.process_generic_purchase(ctx, item, data)
            
            if not success:
                # Purchase failed
                return
            
            # Deduct coins and update data
            data["balance"] -= price
            await db_manager.update_economy_data(ctx.author.id, ctx.guild.id, data)
            
            # Success message
            embed = discord.Embed(
                title="✅ Purchase Successful",
                description=f"You purchased **{item['emoji']} {item['name']}** for **{price}** {self.currency_emoji}!",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="New Balance",
                value=f"**{data['balance']}** {self.currency_emoji} {self.currency_name}",
                inline=False
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"An error occurred: {e}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @shop.command(name="add")
    @commands.has_permissions(administrator=True)
    async def shop_add(self, ctx, item_id: str, name: str, price: int, emoji: str, *, description: str):
        """
        [Admin] Add a custom item to the shop.
        
        Examples:
        !shop add custom_role "Special Role" 1000 👑 A custom special role for VIPs
        """
        # Validate inputs
        if price <= 0:
            embed = discord.Embed(
                title="❌ Invalid Price",
                description="The price must be greater than zero.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Get shop items for this guild
        items = await self.get_shop_items(ctx.guild.id)
        
        # Check if item ID already exists
        for item in items:
            if item["id"].lower() == item_id.lower():
                embed = discord.Embed(
                    title="❌ Item ID Already Exists",
                    description=f"An item with ID `{item_id}` already exists in the shop.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
        
        # Create new item
        new_item = {
            "id": item_id,
            "name": name,
            "emoji": emoji,
            "description": description,
            "price": price,
            "type": "custom"
        }
        
        # Add item to shop
        items.append(new_item)
        
        # Save shop items
        await self.save_shop_items(ctx.guild.id, items)
        
        # Success message
        embed = discord.Embed(
            title="✅ Item Added",
            description=f"Added **{emoji} {name}** to the shop for **{price}** {self.currency_emoji}!",
            color=discord.Color.green()
        )
        
        await ctx.send(embed=embed)
    
    @shop.command(name="remove")
    @commands.has_permissions(administrator=True)
    async def shop_remove(self, ctx, item_id: str):
        """
        [Admin] Remove an item from the shop.
        
        Examples:
        !shop remove custom_role - Remove the custom_role item
        """
        # Get shop items for this guild
        items = await self.get_shop_items(ctx.guild.id)
        
        # Find the item by ID
        item = None
        item_index = -1
        for i, shop_item in enumerate(items):
            if shop_item["id"].lower() == item_id.lower():
                item = shop_item
                item_index = i
                break
        
        if not item:
            embed = discord.Embed(
                title="❌ Item Not Found",
                description=f"The item with ID `{item_id}` was not found in the shop.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Remove item from shop
        items.pop(item_index)
        
        # Save shop items
        await self.save_shop_items(ctx.guild.id, items)
        
        # Success message
        embed = discord.Embed(
            title="✅ Item Removed",
            description=f"Removed **{item['emoji']} {item['name']}** from the shop.",
            color=discord.Color.green()
        )
        
        await ctx.send(embed=embed)
    
    async def get_shop_items(self, guild_id):
        """Get shop items for a guild."""
        # Get database manager
        db_manager = self.bot.get_cog("Utils").db_manager if hasattr(self.bot.get_cog("Utils"), "db_manager") else None
        
        if not db_manager:
            return self.default_items
        
        try:
            # Get shop data for this guild
            shop_data = await db_manager.get_game_data("shop", guild_id=guild_id)
            
            if not shop_data or "items" not in shop_data:
                # Initialize with default items
                shop_data = {"items": self.default_items}
                await db_manager.update_game_data("shop", shop_data, guild_id=guild_id)
            
            return shop_data["items"]
        except:
            return self.default_items
    
    async def save_shop_items(self, guild_id, items):
        """Save shop items for a guild."""
        # Get database manager
        db_manager = self.bot.get_cog("Utils").db_manager if hasattr(self.bot.get_cog("Utils"), "db_manager") else None
        
        if not db_manager:
            return False
        
        try:
            # Save shop data
            shop_data = {"items": items}
            await db_manager.update_game_data("shop", shop_data, guild_id=guild_id)
            return True
        except:
            return False
    
    async def process_role_purchase(self, ctx, item):
        """Process the purchase of a role item."""
        # Check if bot has permissions
        if not ctx.guild.me.guild_permissions.manage_roles:
            embed = discord.Embed(
                title="❌ Missing Permissions",
                description="I don't have permission to manage roles!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return False
        
        # Check if user already has the role
        role_name = f"{item['name']} [{ctx.author.name}]"
        existing_role = discord.utils.get(ctx.author.roles, name=role_name)
        
        if existing_role:
            embed = discord.Embed(
                title="❌ Already Owned",
                description=f"You already have the **{item['name']}** role!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return False
        
        try:
            # Create or find role
            role = discord.utils.get(ctx.guild.roles, name=role_name)
            
            if not role:
                # Create new role
                role = await ctx.guild.create_role(
                    name=role_name,
                    color=discord.Color(item.get("role_color", 0x000000)),
                    reason=f"Shop purchase by {ctx.author.name}"
                )
            
            # Add role to user
            await ctx.author.add_roles(role, reason="Shop purchase")
            return True
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Failed to assign role: {e}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return False
    
    async def process_lootbox_purchase(self, ctx, item, user_data):
        """Process the purchase of a lootbox item."""
        # Add lootbox to inventory if not opened immediately
        if "inventory" not in user_data:
            user_data["inventory"] = []
        
        user_data["inventory"].append({
            "id": item["id"],
            "name": item["name"],
            "emoji": item["emoji"],
            "type": "lootbox",
            "rarity": item.get("rarity", "common"),
            "acquired_at": int(ctx.message.created_at.timestamp())
        })
        
        # Ask if user wants to open now
        embed = discord.Embed(
            title="🎁 Lootbox Purchased",
            description=f"You purchased a **{item['emoji']} {item['name']}**!\nDo you want to open it now?",
            color=discord.Color.gold()
        )
        
        message = await ctx.send(embed=embed)
        await message.add_reaction("✅")  # Yes
        await message.add_reaction("❌")  # No
        
        # Wait for reaction
        def check(reaction, user):
            return (
                user == ctx.author and
                str(reaction.emoji) in ["✅", "❌"] and
                reaction.message.id == message.id
            )
        
        try:
            reaction, user = await self.bot.wait_for("reaction_add", timeout=30.0, check=check)
            
            if str(reaction.emoji) == "✅":
                # Open lootbox now
                await self.open_lootbox(ctx, item, user_data)
            
            return True
            
        except asyncio.TimeoutError:
            # No response, keep in inventory
            embed.description = f"You purchased a **{item['emoji']} {item['name']}**!\nIt has been added to your inventory. Use `!inventory use {item['id']}` to open it later."
            await message.edit(embed=embed)
            try:
                await message.clear_reactions()
            except:
                pass
            return True
    
    async def open_lootbox(self, ctx, lootbox, user_data):
        """Open a lootbox and give rewards."""
        import random
        
        # Get economy cog for adding currency
        economy_cog = self.bot.get_cog("Economy")
        if not economy_cog:
            embed = discord.Embed(
                title="❌ Error",
                description="Could not access the economy system.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return False
        
        # Calculate coin reward
        min_coins = lootbox.get("min_coins", 50)
        max_coins = lootbox.get("max_coins", 300)
        coins = random.randint(min_coins, max_coins)
        
        # Add coins to user
        await economy_cog.add_balance(ctx.author.id, ctx.guild.id, coins)
        
        # Create reward embed
        embed = discord.Embed(
            title=f"🎁 {lootbox['name']} Opened!",
            description=f"You opened your {lootbox['emoji']} **{lootbox['name']}** and found:",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="💰 Coins",
            value=f"**{coins}** {self.currency_emoji} {self.currency_name}",
            inline=False
        )
        
        # TODO: Add more potential rewards based on lootbox rarity
        
        await ctx.send(embed=embed)
        return True
    
    async def process_booster_purchase(self, ctx, item, user_data):
        """Process the purchase of a booster item."""
        import time
        
        # Add booster to user data
        if "boosters" not in user_data:
            user_data["boosters"] = []
        
        # Calculate expiration time
        duration_days = item.get("duration", 7)
        expires_at = int(time.time()) + (duration_days * 86400)  # seconds in a day
        
        # Add booster
        user_data["boosters"].append({
            "id": item["id"],
            "name": item["name"],
            "emoji": item["emoji"],
            "effect": item.get("effect", ""),
            "multiplier": item.get("multiplier", 1),
            "expires_at": expires_at,
            "active": True
        })
        
        # Success message
        embed = discord.Embed(
            title="🚀 Booster Activated",
            description=f"You activated **{item['emoji']} {item['name']}**!\nEffect: {item['description']}\nExpires in {duration_days} days.",
            color=discord.Color.purple()
        )
        
        await ctx.send(embed=embed)
        return True
    
    async def process_generic_purchase(self, ctx, item, user_data):
        """Process the purchase of a generic item."""
        # Add item to inventory
        if "inventory" not in user_data:
            user_data["inventory"] = []
        
        user_data["inventory"].append({
            "id": item["id"],
            "name": item["name"],
            "emoji": item["emoji"],
            "type": item.get("type", "item"),
            "acquired_at": int(ctx.message.created_at.timestamp())
        })
        
        return True

async def setup(bot):
    await bot.add_cog(Shop(bot))
