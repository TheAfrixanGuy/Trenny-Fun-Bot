import discord
from discord.ext import commands
import asyncio
from typing import Dict, List, Optional, Union
import time

class Inventory(commands.Cog):
    """Advanced inventory system for managing purchased items."""
    
    def __init__(self, bot):
        self.bot = bot
        self.category = "economy"  # For help command
        self.currency_name = "coins"
        self.currency_emoji = "🪙"
        self.items_per_page = 5
    
    @commands.group(name="inventory", aliases=["inv", "items"], invoke_without_command=True)
    async def inventory(self, ctx, page: int = 1):
        """
        View your inventory of purchased items.
        
        Examples:
        !inventory - View your inventory
        !inventory 2 - View the second page of your inventory
        """
        # Get database manager
        db_manager = self.bot.get_cog("Utils").db_manager if hasattr(self.bot.get_cog("Utils"), "db_manager") else None
        
        if not db_manager:
            embed = discord.Embed(
                title="❌ Database Error",
                description="Could not access the inventory database.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        try:
            # Get user data
            data = await db_manager.get_economy_data(ctx.author.id, ctx.guild.id)
            
            if not data or "inventory" not in data or not data["inventory"]:
                embed = discord.Embed(
                    title="🎒 Your Inventory",
                    description="Your inventory is empty! Buy items from the shop with `!shop`.",
                    color=discord.Color.blue()
                )
                await ctx.send(embed=embed)
                return
            
            inventory = data["inventory"]
            
            # Calculate total pages
            total_pages = max(1, (len(inventory) + self.items_per_page - 1) // self.items_per_page)
            
            # Validate page number
            if page < 1:
                page = 1
            elif page > total_pages:
                page = total_pages
            
            # Get items for this page
            start_idx = (page - 1) * self.items_per_page
            end_idx = start_idx + self.items_per_page
            page_items = inventory[start_idx:end_idx]
            
            # Create embed
            embed = discord.Embed(
                title="🎒 Your Inventory",
                description=f"You have {len(inventory)} items in your inventory.\nUse `!inventory use <item_id>` to use an item.",
                color=discord.Color.blue()
            )
            
            # Add active boosters section if any
            if "boosters" in data and data["boosters"]:
                active_boosters = [b for b in data["boosters"] if b.get("active", False)]
                if active_boosters:
                    booster_text = ""
                    for booster in active_boosters:
                        expires_at = booster.get("expires_at", 0)
                        expires_in = expires_at - int(time.time())
                        
                        if expires_in <= 0:
                            time_left = "Expired"
                        else:
                            days = expires_in // 86400
                            hours = (expires_in % 86400) // 3600
                            time_left = f"{days}d {hours}h"
                        
                        booster_text += f"{booster['emoji']} **{booster['name']}** - Expires in: {time_left}\n"
                    
                    embed.add_field(
                        name="🚀 Active Boosters",
                        value=booster_text,
                        inline=False
                    )
            
            # Group items by type
            grouped_items = {}
            for item in page_items:
                item_type = item.get("type", "item")
                if item_type not in grouped_items:
                    grouped_items[item_type] = []
                grouped_items[item_type].append(item)
            
            # Add grouped items to embed
            for item_type, items in grouped_items.items():
                # Format the item type
                type_name = item_type.replace("_", " ").title()
                
                items_text = ""
                for item in items:
                    acquired_at = item.get("acquired_at", 0)
                    acquired_date = f"<t:{acquired_at}:R>" if acquired_at else "Unknown"
                    
                    items_text += f"{item['emoji']} **{item['name']}**\n"
                    items_text += f"ID: `{item['id']}`\n"
                    items_text += f"Acquired: {acquired_date}\n\n"
                
                embed.add_field(
                    name=f"📦 {type_name}s",
                    value=items_text,
                    inline=False
                )
            
            # Add pagination footer
            embed.set_footer(text=f"Page {page}/{total_pages} • Use !inventory <page> to view more items")
            
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
                        await self.inventory(ctx, page - 1)
                    elif str(reaction.emoji) == "▶️" and page < total_pages:
                        await message.delete()
                        await self.inventory(ctx, page + 1)
                    
                except asyncio.TimeoutError:
                    try:
                        await message.clear_reactions()
                    except:
                        pass
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"An error occurred: {e}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @inventory.command(name="use")
    async def inventory_use(self, ctx, item_id: str):
        """
        Use an item from your inventory.
        
        Examples:
        !inventory use lootbox_common - Open a common lootbox
        !inventory use daily_booster - Activate a daily reward booster
        """
        # Get database manager
        db_manager = self.bot.get_cog("Utils").db_manager if hasattr(self.bot.get_cog("Utils"), "db_manager") else None
        
        if not db_manager:
            embed = discord.Embed(
                title="❌ Database Error",
                description="Could not access the inventory database.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        try:
            # Get user data
            data = await db_manager.get_economy_data(ctx.author.id, ctx.guild.id)
            
            if not data or "inventory" not in data or not data["inventory"]:
                embed = discord.Embed(
                    title="❌ Item Not Found",
                    description="Your inventory is empty! Buy items from the shop with `!shop`.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            # Find the item in inventory
            inventory = data["inventory"]
            item = None
            item_index = -1
            
            for i, inv_item in enumerate(inventory):
                if inv_item["id"].lower() == item_id.lower():
                    item = inv_item
                    item_index = i
                    break
            
            if not item:
                embed = discord.Embed(
                    title="❌ Item Not Found",
                    description=f"You don't have an item with ID `{item_id}` in your inventory.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            # Process item usage based on type
            if item["type"] == "lootbox":
                success = await self.use_lootbox(ctx, item, data)
            elif item["type"] == "booster":
                success = await self.use_booster(ctx, item, data)
            else:
                # Generic item
                embed = discord.Embed(
                    title="❓ Unknown Item Type",
                    description=f"This item can't be used directly.",
                    color=discord.Color.orange()
                )
                await ctx.send(embed=embed)
                return
            
            if success:
                # Remove item from inventory
                inventory.pop(item_index)
                
                # Save user data
                await db_manager.update_economy_data(ctx.author.id, ctx.guild.id, data)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"An error occurred: {e}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @inventory.command(name="gift")
    async def inventory_gift(self, ctx, member: discord.Member, item_id: str):
        """
        Gift an item from your inventory to another user.
        
        Examples:
        !inventory gift @user lootbox_common - Gift a common lootbox to a user
        """
        # Validate recipient
        if member.id == ctx.author.id:
            embed = discord.Embed(
                title="❌ Invalid Recipient",
                description="You can't gift items to yourself!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        if member.bot:
            embed = discord.Embed(
                title="❌ Invalid Recipient",
                description="You can't gift items to bots!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Get database manager
        db_manager = self.bot.get_cog("Utils").db_manager if hasattr(self.bot.get_cog("Utils"), "db_manager") else None
        
        if not db_manager:
            embed = discord.Embed(
                title="❌ Database Error",
                description="Could not access the inventory database.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        try:
            # Get sender's data
            sender_data = await db_manager.get_economy_data(ctx.author.id, ctx.guild.id)
            
            if not sender_data or "inventory" not in sender_data or not sender_data["inventory"]:
                embed = discord.Embed(
                    title="❌ Item Not Found",
                    description="Your inventory is empty! Buy items from the shop with `!shop`.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            # Find the item in inventory
            inventory = sender_data["inventory"]
            item = None
            item_index = -1
            
            for i, inv_item in enumerate(inventory):
                if inv_item["id"].lower() == item_id.lower():
                    item = inv_item
                    item_index = i
                    break
            
            if not item:
                embed = discord.Embed(
                    title="❌ Item Not Found",
                    description=f"You don't have an item with ID `{item_id}` in your inventory.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            # Get recipient's data
            recipient_data = await db_manager.get_economy_data(member.id, ctx.guild.id)
            
            if not recipient_data:
                # Initialize if recipient doesn't exist
                recipient_data = {"balance": 0, "inventory": [], "last_daily": 0, "daily_streak": 0}
            
            if "inventory" not in recipient_data:
                recipient_data["inventory"] = []
            
            # Remove item from sender's inventory
            sender_data["inventory"].pop(item_index)
            
            # Add item to recipient's inventory
            item["acquired_at"] = int(time.time())  # Update acquisition time
            recipient_data["inventory"].append(item)
            
            # Save data for both users
            await db_manager.update_economy_data(ctx.author.id, ctx.guild.id, sender_data)
            await db_manager.update_economy_data(member.id, ctx.guild.id, recipient_data)
            
            # Success message
            embed = discord.Embed(
                title="🎁 Gift Sent",
                description=f"You gifted **{item['emoji']} {item['name']}** to {member.mention}!",
                color=discord.Color.green()
            )
            
            await ctx.send(embed=embed)
            
            # Notify recipient
            try:
                recipient_embed = discord.Embed(
                    title="🎁 Gift Received",
                    description=f"You received **{item['emoji']} {item['name']}** from {ctx.author.mention}!",
                    color=discord.Color.green()
                )
                
                await member.send(embed=recipient_embed)
            except:
                # Couldn't DM user, but gift still processed
                pass
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"An error occurred: {e}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    async def use_lootbox(self, ctx, lootbox, user_data):
        """Use a lootbox item from inventory."""
        # Get Shop cog to use its lootbox opening function
        shop_cog = self.bot.get_cog("Shop")
        if not shop_cog:
            embed = discord.Embed(
                title="❌ Error",
                description="Could not access the shop system.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return False
        
        return await shop_cog.open_lootbox(ctx, lootbox, user_data)
    
    async def use_booster(self, ctx, booster, user_data):
        """Activate a booster item from inventory."""
        # Initialize boosters if not present
        if "boosters" not in user_data:
            user_data["boosters"] = []
        
        # Check if a similar booster is already active
        for existing_booster in user_data["boosters"]:
            if (
                existing_booster.get("effect") == booster.get("effect") and
                existing_booster.get("active", False)
            ):
                # Ask for confirmation to replace
                embed = discord.Embed(
                    title="⚠️ Booster Already Active",
                    description=(
                        f"You already have an active **{existing_booster['name']}**.\n"
                        f"Do you want to replace it with your new **{booster['name']}**?"
                    ),
                    color=discord.Color.orange()
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
                    
                    if str(reaction.emoji) == "❌":
                        # User declined
                        embed = discord.Embed(
                            title="❌ Activation Cancelled",
                            description="Booster activation cancelled. Your item remains in your inventory.",
                            color=discord.Color.red()
                        )
                        await message.edit(embed=embed)
                        await message.clear_reactions()
                        return False
                    
                    # User confirmed, deactivate existing booster
                    existing_booster["active"] = False
                    
                except asyncio.TimeoutError:
                    # No response
                    embed = discord.Embed(
                        title="⏱️ Time's Up",
                        description="You took too long to respond. Booster activation cancelled.",
                        color=discord.Color.orange()
                    )
                    await message.edit(embed=embed)
                    try:
                        await message.clear_reactions()
                    except:
                        pass
                    return False
        
        # Calculate expiration time
        duration_days = booster.get("duration", 7)
        expires_at = int(time.time()) + (duration_days * 86400)  # seconds in a day
        
        # Create active booster entry
        active_booster = {
            "id": booster["id"],
            "name": booster["name"],
            "emoji": booster["emoji"],
            "effect": booster.get("effect", ""),
            "multiplier": booster.get("multiplier", 1),
            "expires_at": expires_at,
            "active": True
        }
        
        # Add to boosters
        user_data["boosters"].append(active_booster)
        
        # Success message
        embed = discord.Embed(
            title="🚀 Booster Activated",
            description=f"You activated **{booster['emoji']} {booster['name']}**!",
            color=discord.Color.purple()
        )
        
        embed.add_field(
            name="Effect",
            value=f"{booster.get('effect', 'Unknown').replace('_', ' ').title()}: x{booster.get('multiplier', 1)}",
            inline=True
        )
        
        embed.add_field(
            name="Duration",
            value=f"{duration_days} days",
            inline=True
        )
        
        await ctx.send(embed=embed)
        return True
    
    @commands.command(name="boosters", aliases=["buffs"])
    async def boosters(self, ctx):
        """
        View your active boosters and their effects.
        
        Examples:
        !boosters - View all your active boosters
        """
        # Get database manager
        db_manager = self.bot.get_cog("Utils").db_manager if hasattr(self.bot.get_cog("Utils"), "db_manager") else None
        
        if not db_manager:
            embed = discord.Embed(
                title="❌ Database Error",
                description="Could not access the boosters database.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        try:
            # Get user data
            data = await db_manager.get_economy_data(ctx.author.id, ctx.guild.id)
            
            if not data or "boosters" not in data or not data["boosters"]:
                embed = discord.Embed(
                    title="🚀 Your Boosters",
                    description="You don't have any active boosters! Buy some from the shop with `!shop`.",
                    color=discord.Color.blue()
                )
                await ctx.send(embed=embed)
                return
            
            # Filter active boosters
            active_boosters = [b for b in data["boosters"] if b.get("active", False)]
            expired_boosters = []
            current_time = int(time.time())
            
            # Check for expired boosters
            for booster in active_boosters:
                if booster.get("expires_at", 0) <= current_time:
                    booster["active"] = False
                    expired_boosters.append(booster)
            
            # Remove expired boosters from active list
            for expired in expired_boosters:
                active_boosters.remove(expired)
            
            # Save if any boosters expired
            if expired_boosters:
                await db_manager.update_economy_data(ctx.author.id, ctx.guild.id, data)
            
            if not active_boosters:
                embed = discord.Embed(
                    title="🚀 Your Boosters",
                    description="You don't have any active boosters! Buy some from the shop with `!shop`.",
                    color=discord.Color.blue()
                )
                await ctx.send(embed=embed)
                return
            
            # Create embed
            embed = discord.Embed(
                title="🚀 Your Active Boosters",
                description=f"You have {len(active_boosters)} active boosters:",
                color=discord.Color.purple()
            )
            
            # Add boosters to embed
            for booster in active_boosters:
                expires_at = booster.get("expires_at", 0)
                expires_in = expires_at - current_time
                
                days = expires_in // 86400
                hours = (expires_in % 86400) // 3600
                time_left = f"{days}d {hours}h"
                
                effect = booster.get("effect", "unknown").replace("_", " ").title()
                multiplier = booster.get("multiplier", 1)
                
                name = f"{booster['emoji']} {booster['name']}"
                value = (
                    f"**Effect**: {effect} x{multiplier}\n"
                    f"**Expires**: In {time_left}"
                )
                
                embed.add_field(name=name, value=value, inline=False)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"An error occurred: {e}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Inventory(bot))
