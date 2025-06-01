import discord
from discord.ext import commands
import asyncio
import random
from datetime import datetime, timedelta
import time
from typing import Dict, List, Optional, Union
import os

class Economy(commands.Cog):
    """Advanced economy system with currency, daily rewards, and more."""
    
    def __init__(self, bot):
        self.bot = bot
        self.category = "economy"  # For help command
        self.currency_name = "coins"
        self.currency_emoji = "🪙"
        
        # Daily reward settings
        self.daily_min = 100
        self.daily_max = 200
        self.daily_streak_bonus = 50  # Bonus per day streak
        self.daily_cooldown = 86400  # 24 hours in seconds
        
        # Work settings
        self.work_min = 10
        self.work_max = 50
        self.work_cooldown = 3600  # 1 hour in seconds
        
        # Work messages
        self.work_messages = [
            "You worked as a Discord moderator and earned **{amount}** {currency}!",
            "You helped someone fix their code and earned **{amount}** {currency}!",
            "You created memes for a social media page and earned **{amount}** {currency}!",
            "You went fishing and sold your catch for **{amount}** {currency}!",
            "You delivered packages for an e-commerce company and earned **{amount}** {currency}!",
            "You walked your neighbor's dog and received **{amount}** {currency}!",
            "You participated in a gaming tournament and won **{amount}** {currency}!",
            "You solved a complicated puzzle and earned **{amount}** {currency}!",
            "You wrote an article for a tech blog and earned **{amount}** {currency}!",
            "You tutored a student and earned **{amount}** {currency}!"
        ]
    
    @commands.command(name="balance", aliases=["bal", "coins", "money"])
    async def balance(self, ctx, member: Optional[discord.Member] = None):
        """
        Check your balance or another user's balance.
        
        Examples:
        !balance - Check your own balance
        !balance @user - Check another user's balance
        """
        target = member or ctx.author
        
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
        
        # Get user's balance
        try:
            data = await db_manager.get_economy_data(target.id, ctx.guild.id)
            
            if not data:
                # Initialize if user doesn't exist
                data = {"balance": 0, "inventory": [], "last_daily": 0, "daily_streak": 0}
                await db_manager.update_economy_data(target.id, ctx.guild.id, data)
            
            # Create embed
            balance = data.get("balance", 0)
            
            if target == ctx.author:
                title = f"Your Balance"
                description = f"You have **{balance}** {self.currency_emoji} {self.currency_name}."
            else:
                title = f"{target.name}'s Balance"
                description = f"{target.mention} has **{balance}** {self.currency_emoji} {self.currency_name}."
            
            embed = discord.Embed(
                title=title,
                description=description,
                color=discord.Color.gold()
            )
            
            # Add daily streak info if it's the user's own balance
            if target == ctx.author and "daily_streak" in data:
                streak = data["daily_streak"]
                if streak > 0:
                    next_daily = data.get("last_daily", 0) + self.daily_cooldown
                    now = int(time.time())
                    
                    if next_daily < now:
                        time_left = "Available now!"
                    else:
                        time_left = self.format_time_difference(next_daily - now)
                    
                    embed.add_field(
                        name="Daily Streak",
                        value=f"🔥 **{streak}** day streak\nNext daily: {time_left}",
                        inline=False
                    )
            
            # Set footer with tip
            embed.set_footer(text=f"Use !daily to claim your daily rewards!")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"An error occurred: {e}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @commands.command(name="daily", aliases=["dailyreward", "claim"])
    async def daily(self, ctx):
        """
        Claim your daily reward of coins.
        Maintains a streak for consecutive days, giving you bonus coins.
        """
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
            
            # Check if daily reward is available
            now = int(time.time())
            last_daily = data.get("last_daily", 0)
            time_since_last = now - last_daily
            
            if time_since_last < self.daily_cooldown:
                # Not enough time has passed
                time_left = self.daily_cooldown - time_since_last
                
                embed = discord.Embed(
                    title="⏱️ Daily Reward Not Available",
                    description=f"You've already claimed your daily reward!\nCome back in {self.format_time_difference(time_left)}.",
                    color=discord.Color.orange()
                )
                
                # Add streak info
                if "daily_streak" in data and data["daily_streak"] > 0:
                    embed.add_field(
                        name="Current Streak",
                        value=f"🔥 **{data['daily_streak']}** day streak",
                        inline=False
                    )
                
                await ctx.send(embed=embed)
                return
            
            # Calculate streak
            streak = data.get("daily_streak", 0)
            streak_bonus = 0
            
            # Check if streak should continue or reset
            if time_since_last < (self.daily_cooldown * 2):  # Within 48 hours
                # Continue streak
                streak += 1
                streak_bonus = streak * self.daily_streak_bonus
            else:
                # Reset streak
                streak = 1
            
            # Calculate reward
            base_reward = random.randint(self.daily_min, self.daily_max)
            total_reward = base_reward + streak_bonus
            
            # Update user data
            data["balance"] = data.get("balance", 0) + total_reward
            data["last_daily"] = now
            data["daily_streak"] = streak
            
            await db_manager.update_economy_data(ctx.author.id, ctx.guild.id, data)
            
            # Create embed
            embed = discord.Embed(
                title="🎁 Daily Reward Claimed!",
                description=f"You claimed your daily reward of **{base_reward}** {self.currency_emoji} {self.currency_name}!",
                color=discord.Color.green()
            )
            
            if streak_bonus > 0:
                embed.add_field(
                    name="Streak Bonus",
                    value=f"🔥 **{streak}** day streak: +**{streak_bonus}** {self.currency_emoji}",
                    inline=False
                )
            
            embed.add_field(
                name="Total Reward",
                value=f"**{total_reward}** {self.currency_emoji} {self.currency_name}",
                inline=False
            )
            
            embed.add_field(
                name="New Balance",
                value=f"**{data['balance']}** {self.currency_emoji} {self.currency_name}",
                inline=False
            )
            
            embed.set_footer(text=f"Come back tomorrow for another reward! Maintain your streak for bigger bonuses!")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"An error occurred: {e}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @commands.command(name="work", aliases=["job", "earn"])
    @commands.cooldown(1, 3600, commands.BucketType.user)  # 1 hour cooldown
    async def work(self, ctx):
        """
        Work to earn some coins. Can be used once per hour.
        """
        # Get database manager
        db_manager = self.bot.get_cog("Utils").db_manager if hasattr(self.bot.get_cog("Utils"), "db_manager") else None
        
        if not db_manager:
            embed = discord.Embed(
                title="❌ Database Error",
                description="Could not access the economy database.",
                color=discord.Color.red()
            )
            ctx.command.reset_cooldown(ctx)
            await ctx.send(embed=embed)
            return
        
        try:
            # Calculate earnings
            earnings = random.randint(self.work_min, self.work_max)
            
            # Get user data
            data = await db_manager.get_economy_data(ctx.author.id, ctx.guild.id)
            
            if not data:
                # Initialize if user doesn't exist
                data = {"balance": 0, "inventory": [], "last_daily": 0, "daily_streak": 0}
            
            # Update balance
            data["balance"] = data.get("balance", 0) + earnings
            
            # Save data
            await db_manager.update_economy_data(ctx.author.id, ctx.guild.id, data)
            
            # Create embed
            work_message = random.choice(self.work_messages)
            work_message = work_message.format(amount=earnings, currency=self.currency_name)
            
            embed = discord.Embed(
                title="💼 Work Completed",
                description=work_message,
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="New Balance",
                value=f"**{data['balance']}** {self.currency_emoji} {self.currency_name}",
                inline=False
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            ctx.command.reset_cooldown(ctx)
            embed = discord.Embed(
                title="❌ Error",
                description=f"An error occurred: {e}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @commands.command(name="pay", aliases=["give", "transfer", "send"])
    async def pay(self, ctx, member: discord.Member, amount: int):
        """
        Transfer coins to another user.
        
        Examples:
        !pay @user 100 - Send 100 coins to the mentioned user
        """
        # Check valid amount
        if amount <= 0:
            embed = discord.Embed(
                title="❌ Invalid Amount",
                description="The amount must be greater than zero.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Can't pay yourself
        if member.id == ctx.author.id:
            embed = discord.Embed(
                title="❌ Invalid Recipient",
                description="You can't pay yourself!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Can't pay bots
        if member.bot:
            embed = discord.Embed(
                title="❌ Invalid Recipient",
                description="You can't pay bots!",
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
            # Get sender data
            sender_data = await db_manager.get_economy_data(ctx.author.id, ctx.guild.id)
            
            if not sender_data:
                # Initialize if user doesn't exist
                sender_data = {"balance": 0, "inventory": [], "last_daily": 0, "daily_streak": 0}
                await db_manager.update_economy_data(ctx.author.id, ctx.guild.id, sender_data)
            
            # Check if sender has enough coins
            sender_balance = sender_data.get("balance", 0)
            if sender_balance < amount:
                embed = discord.Embed(
                    title="❌ Insufficient Funds",
                    description=f"You don't have enough {self.currency_name}!\nYour balance: **{sender_balance}** {self.currency_emoji}",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            # Get recipient data
            recipient_data = await db_manager.get_economy_data(member.id, ctx.guild.id)
            
            if not recipient_data:
                # Initialize if user doesn't exist
                recipient_data = {"balance": 0, "inventory": [], "last_daily": 0, "daily_streak": 0}
            
            # Update balances
            sender_data["balance"] -= amount
            recipient_data["balance"] = recipient_data.get("balance", 0) + amount
            
            # Save data
            await db_manager.update_economy_data(ctx.author.id, ctx.guild.id, sender_data)
            await db_manager.update_economy_data(member.id, ctx.guild.id, recipient_data)
            
            # Create embed
            embed = discord.Embed(
                title="💸 Payment Sent",
                description=f"You sent **{amount}** {self.currency_emoji} {self.currency_name} to {member.mention}!",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="Your New Balance",
                value=f"**{sender_data['balance']}** {self.currency_emoji} {self.currency_name}",
                inline=False
            )
            
            await ctx.send(embed=embed)
            
            # Send notification to recipient
            try:
                recipient_embed = discord.Embed(
                    title="💰 Payment Received",
                    description=f"You received **{amount}** {self.currency_emoji} {self.currency_name} from {ctx.author.mention}!",
                    color=discord.Color.green()
                )
                
                recipient_embed.add_field(
                    name="Your New Balance",
                    value=f"**{recipient_data['balance']}** {self.currency_emoji} {self.currency_name}",
                    inline=False
                )
                
                await member.send(embed=recipient_embed)
            except:
                # Couldn't DM user, but payment still processed
                pass
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"An error occurred: {e}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @commands.command(name="leaderboard", aliases=["lb", "top", "rich"])
    async def leaderboard(self, ctx, limit: int = 10):
        """
        Show the richest users on the server.
        
        Examples:
        !leaderboard - Show top 10 users
        !leaderboard 5 - Show top 5 users
        """
        # Validate limit
        if limit < 1:
            limit = 10
        elif limit > 25:
            limit = 25
        
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
            # Get leaderboard data
            leaderboard_data = await db_manager.get_leaderboard(ctx.guild.id, limit)
            
            # Create embed
            embed = discord.Embed(
                title=f"💰 {ctx.guild.name} Richest Users",
                description=f"The wealthiest users on this server:",
                color=discord.Color.gold()
            )
            
            # Add leaderboard entries
            for i, entry in enumerate(leaderboard_data, 1):
                user_id = entry["user_id"]
                balance = entry["balance"]
                
                member = ctx.guild.get_member(user_id)
                name = member.name if member else f"User {user_id}"
                
                if i == 1:
                    medal = "🥇"
                elif i == 2:
                    medal = "🥈"
                elif i == 3:
                    medal = "🥉"
                else:
                    medal = f"{i}."
                
                embed.add_field(
                    name=f"{medal} {name}",
                    value=f"**{balance}** {self.currency_emoji} {self.currency_name}",
                    inline=False
                )
            
            if not leaderboard_data:
                embed.description = "No users have any coins yet!"
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"An error occurred: {e}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @commands.command(name="gamble", aliases=["bet"])
    async def gamble(self, ctx, amount: str):
        """
        Gamble your coins for a chance to win more.
        
        You can bet a specific amount or "all" for your entire balance.
        Win multipliers:
        - Roll 1-30: Lose your bet
        - Roll 31-50: 1x (get your money back)
        - Roll 51-70: 1.5x
        - Roll 71-90: 2x
        - Roll 91-99: 3x
        - Roll 100: 5x
        
        Examples:
        !gamble 100 - Bet 100 coins
        !gamble all - Bet all your coins
        !gamble half - Bet half your coins
        """
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
            
            balance = data.get("balance", 0)
            
            # Determine bet amount
            bet_amount = 0
            if amount.lower() == "all":
                bet_amount = balance
            elif amount.lower() == "half":
                bet_amount = balance // 2
            else:
                try:
                    bet_amount = int(amount)
                except ValueError:
                    embed = discord.Embed(
                        title="❌ Invalid Amount",
                        description="Please enter a valid number, 'all', or 'half'.",
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=embed)
                    return
            
            # Validate bet amount
            if bet_amount <= 0:
                embed = discord.Embed(
                    title="❌ Invalid Bet",
                    description="Your bet must be greater than zero!",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            if bet_amount > balance:
                embed = discord.Embed(
                    title="❌ Insufficient Funds",
                    description=f"You don't have enough {self.currency_name}!\nYour balance: **{balance}** {self.currency_emoji}",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            # Roll the dice
            roll = random.randint(1, 100)
            
            # Determine multiplier
            multiplier = 0
            if roll <= 30:
                # Loss
                multiplier = 0
                result_text = f"You rolled **{roll}** and lost your bet."
                color = discord.Color.red()
            elif roll <= 50:
                # Money back
                multiplier = 1
                result_text = f"You rolled **{roll}** and got your money back."
                color = discord.Color.gold()
            elif roll <= 70:
                # 1.5x
                multiplier = 1.5
                result_text = f"You rolled **{roll}** and won **1.5x** your bet!"
                color = discord.Color.green()
            elif roll <= 90:
                # 2x
                multiplier = 2
                result_text = f"You rolled **{roll}** and won **2x** your bet!"
                color = discord.Color.green()
            elif roll <= 99:
                # 3x
                multiplier = 3
                result_text = f"You rolled **{roll}** and won **3x** your bet!"
                color = discord.Color.green()
            else:
                # 5x - Jackpot
                multiplier = 5
                result_text = f"🎉 JACKPOT! You rolled **{roll}** and won **5x** your bet!"
                color = discord.Color.green()
            
            # Calculate winnings/losses
            winnings = int(bet_amount * multiplier) - bet_amount
            
            # Update balance
            data["balance"] = balance + winnings
            await db_manager.update_economy_data(ctx.author.id, ctx.guild.id, data)
            
            # Create embed
            embed = discord.Embed(
                title="🎲 Gambling Results",
                description=result_text,
                color=color
            )
            
            embed.add_field(
                name="Bet Amount",
                value=f"**{bet_amount}** {self.currency_emoji} {self.currency_name}",
                inline=True
            )
            
            if winnings >= 0:
                embed.add_field(
                    name="Winnings",
                    value=f"+**{winnings}** {self.currency_emoji} {self.currency_name}",
                    inline=True
                )
            else:
                embed.add_field(
                    name="Loss",
                    value=f"-**{abs(winnings)}** {self.currency_emoji} {self.currency_name}",
                    inline=True
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
    
    # Helper method to format time
    def format_time_difference(self, seconds):
        """Format a time difference in seconds to a human-readable string."""
        if seconds < 60:
            return f"{seconds} seconds"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''}"
        elif seconds < 86400:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours} hour{'s' if hours != 1 else ''} and {minutes} minute{'s' if minutes != 1 else ''}"
        else:
            days = seconds // 86400
            hours = (seconds % 86400) // 3600
            return f"{days} day{'s' if days != 1 else ''} and {hours} hour{'s' if hours != 1 else ''}"
    
    # Method for other cogs to add balance to users
    async def add_balance(self, user_id, guild_id, amount):
        """Add currency to a user's balance. Used by other cogs."""
        # Get database manager
        db_manager = self.bot.get_cog("Utils").db_manager if hasattr(self.bot.get_cog("Utils"), "db_manager") else None
        
        if not db_manager:
            return False
        
        try:
            # Get user data
            data = await db_manager.get_economy_data(user_id, guild_id)
            
            if not data:
                # Initialize if user doesn't exist
                data = {"balance": 0, "inventory": [], "last_daily": 0, "daily_streak": 0}
            
            # Update balance
            data["balance"] = data.get("balance", 0) + amount
            
            # Save data
            await db_manager.update_economy_data(user_id, guild_id, data)
            return True
        except:
            return False
    
    # Method for other cogs to remove balance from users
    async def remove_balance(self, user_id, guild_id, amount):
        """Remove currency from a user's balance. Used by other cogs."""
        # Get database manager
        db_manager = self.bot.get_cog("Utils").db_manager if hasattr(self.bot.get_cog("Utils"), "db_manager") else None
        
        if not db_manager:
            return False
        
        try:
            # Get user data
            data = await db_manager.get_economy_data(user_id, guild_id)
            
            if not data:
                # Initialize if user doesn't exist
                data = {"balance": 0, "inventory": [], "last_daily": 0, "daily_streak": 0}
            
            # Update balance (don't go below 0)
            data["balance"] = max(0, data.get("balance", 0) - amount)
            
            # Save data
            await db_manager.update_economy_data(user_id, guild_id, data)
            return True
        except:
            return False

async def setup(bot):
    await bot.add_cog(Economy(bot))
