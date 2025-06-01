import discord
from discord.ext import commands
import asyncio
import random
from typing import Dict, Optional, Union, List

class RockPaperScissors(commands.Cog):
    """Advanced Rock Paper Scissors game with beautiful interfaces and multiplayer support."""
    
    def __init__(self, bot):
        self.bot = bot
        self.category = "games"  # For help command
        self.games = {}  # Active games
        self.choices = {
            "rock": "🪨",
            "paper": "📄",
            "scissors": "✂️"
        }
        self.win_messages = [
            "dominates",
            "crushes",
            "demolishes",
            "obliterates",
            "defeats",
            "overpowers"
        ]
    
    @commands.group(name="rps", aliases=["rockpaperscissors"], invoke_without_command=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def rps(self, ctx, member: Optional[discord.Member] = None):
        """
        Play Rock Paper Scissors!
        
        Play against the bot or challenge another member.
        
        Examples:
        !rps - Play against the bot
        !rps @user - Challenge another user
        """
        # Check if user is already in a game
        if ctx.author.id in self.games:
            embed = discord.Embed(
                title="❌ Game Already in Progress",
                description="You're already in a Rock Paper Scissors game! Finish that one first.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # If no member specified, play against bot
        if member is None:
            await self.play_against_bot(ctx)
        else:
            # Can't play against yourself
            if member.id == ctx.author.id:
                embed = discord.Embed(
                    title="❌ Invalid Opponent",
                    description="You can't play against yourself! Choose another opponent or leave blank to play against me.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
                
            # Can't play against bots
            if member.bot:
                embed = discord.Embed(
                    title="❌ Invalid Opponent",
                    description=f"{member.mention} is a bot! You can play against me by just using `!rps` without mentioning anyone.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
                
            # Check if opponent is already in a game
            if member.id in self.games:
                embed = discord.Embed(
                    title="❌ Opponent Busy",
                    description=f"{member.mention} is already in a game! Try again later or choose another opponent.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
                
            # Start multiplayer game
            await self.play_multiplayer(ctx, member)
    
    @rps.command(name="leaderboard", aliases=["lb", "top"])
    async def rps_leaderboard(self, ctx):
        """Show the Rock Paper Scissors leaderboard for this server."""
        # Get database manager
        db_manager = self.bot.get_cog("Utils").db_manager if hasattr(self.bot.get_cog("Utils"), "db_manager") else None
        
        if not db_manager:
            embed = discord.Embed(
                title="❌ Database Error",
                description="Could not access the leaderboard database.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Get leaderboard data
        try:
            # Get game data for this guild
            game_data = await db_manager.get_game_data("rps", guild_id=ctx.guild.id)
            
            if not game_data or "leaderboard" not in game_data:
                embed = discord.Embed(
                    title="📊 Rock Paper Scissors Leaderboard",
                    description="No Rock Paper Scissors games have been played yet!",
                    color=discord.Color.blue()
                )
                await ctx.send(embed=embed)
                return
            
            # Process leaderboard data
            leaderboard = []
            for user_id, stats in game_data["leaderboard"].items():
                wins = stats.get("wins", 0)
                losses = stats.get("losses", 0)
                ties = stats.get("ties", 0)
                total_games = wins + losses + ties
                win_rate = (wins / total_games * 100) if total_games > 0 else 0
                
                leaderboard.append({
                    "user_id": int(user_id),
                    "wins": wins,
                    "losses": losses,
                    "ties": ties,
                    "total_games": total_games,
                    "win_rate": win_rate
                })
            
            # Sort by wins, then by win rate
            leaderboard.sort(key=lambda x: (x["wins"], x["win_rate"]), reverse=True)
            
            # Create embed
            embed = discord.Embed(
                title="📊 Rock Paper Scissors Leaderboard",
                description="Top Rock Paper Scissors players in this server:",
                color=discord.Color.gold()
            )
            
            # Add leaderboard entries
            for i, entry in enumerate(leaderboard[:10], 1):
                user = ctx.guild.get_member(entry["user_id"])
                username = user.name if user else "Unknown User"
                
                if i == 1:
                    medal = "🥇"
                elif i == 2:
                    medal = "🥈"
                elif i == 3:
                    medal = "🥉"
                else:
                    medal = f"{i}."
                
                stats_text = (
                    f"**{entry['wins']}** wins, **{entry['losses']}** losses, **{entry['ties']}** ties\n"
                    f"Win rate: **{entry['win_rate']:.1f}%**"
                )
                
                embed.add_field(
                    name=f"{medal} {username}",
                    value=stats_text,
                    inline=False
                )
            
            if not leaderboard:
                embed.description = "No Rock Paper Scissors games have been played yet!"
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"An error occurred while fetching the leaderboard: {e}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    async def play_against_bot(self, ctx):
        """Play Rock Paper Scissors against the bot."""
        # Mark user as in game
        self.games[ctx.author.id] = {"active": True, "opponent": "bot"}
        
        # Create the game embed
        embed = discord.Embed(
            title="🎮 Rock Paper Scissors",
            description=(
                f"{ctx.author.mention}, choose your move!\n\n"
                f"🪨 - Rock\n"
                f"📄 - Paper\n"
                f"✂️ - Scissors"
            ),
            color=discord.Color.blue()
        )
        embed.set_footer(text="You have 30 seconds to make your choice.")
        
        # Send embed and add reactions
        message = await ctx.send(embed=embed)
        for emoji in self.choices.values():
            await message.add_reaction(emoji)
        
        # Wait for user's choice
        try:
            def check(reaction, user):
                return (
                    user.id == ctx.author.id and
                    reaction.message.id == message.id and
                    str(reaction.emoji) in self.choices.values()
                )
            
            reaction, user = await self.bot.wait_for("reaction_add", check=check, timeout=30.0)
            
            # Get user's choice
            user_choice = None
            for choice, emoji in self.choices.items():
                if str(reaction.emoji) == emoji:
                    user_choice = choice
                    break
            
            # Bot makes a choice
            bot_choice = random.choice(list(self.choices.keys()))
            
            # Determine winner
            result = self.determine_winner(user_choice, bot_choice)
            
            # Create result embed
            await self.show_bot_game_result(ctx, message, user_choice, bot_choice, result)
            
            # Update stats
            await self.update_stats(ctx.author.id, ctx.guild.id, result)
            
        except asyncio.TimeoutError:
            # User didn't make a choice in time
            embed.color = discord.Color.orange()
            embed.title = "⏱️ Time's Up!"
            embed.description = "You took too long to make a choice. Game cancelled."
            
            await message.edit(embed=embed)
            await message.clear_reactions()
        finally:
            # Clean up
            if ctx.author.id in self.games:
                del self.games[ctx.author.id]
    
    async def play_multiplayer(self, ctx, opponent):
        """Play Rock Paper Scissors against another user."""
        # Mark both users as in game
        game_id = f"{ctx.author.id}_{opponent.id}"
        self.games[ctx.author.id] = {"active": True, "opponent": opponent.id, "game_id": game_id}
        self.games[opponent.id] = {"active": True, "opponent": ctx.author.id, "game_id": game_id}
        
        # Create invitation embed
        embed = discord.Embed(
            title="🎮 Rock Paper Scissors Challenge!",
            description=(
                f"{opponent.mention}, you've been challenged to a game of Rock Paper Scissors by {ctx.author.mention}!\n\n"
                f"Do you accept this challenge?"
            ),
            color=discord.Color.blue()
        )
        embed.set_footer(text="You have 30 seconds to accept or decline.")
        
        # Send invitation and add reactions
        message = await ctx.send(embed=embed)
        await message.add_reaction("✅")  # Accept
        await message.add_reaction("❌")  # Decline
        
        # Wait for opponent's response
        try:
            def check(reaction, user):
                return (
                    user.id == opponent.id and
                    reaction.message.id == message.id and
                    str(reaction.emoji) in ["✅", "❌"]
                )
            
            reaction, user = await self.bot.wait_for("reaction_add", check=check, timeout=30.0)
            
            if str(reaction.emoji) == "❌":
                # Opponent declined
                embed.color = discord.Color.red()
                embed.title = "❌ Challenge Declined"
                embed.description = f"{opponent.mention} declined the Rock Paper Scissors challenge."
                
                await message.edit(embed=embed)
                await message.clear_reactions()
                
                # Clean up
                del self.games[ctx.author.id]
                del self.games[opponent.id]
                return
            
            # Opponent accepted, start the game
            embed.color = discord.Color.green()
            embed.title = "✅ Challenge Accepted!"
            embed.description = "Game starting! Both players will receive a DM to make their choice."
            
            await message.edit(embed=embed)
            
            # Get choices from both players via DM
            tasks = [
                self.get_player_choice(ctx.author),
                self.get_player_choice(opponent)
            ]
            
            choices = await asyncio.gather(*tasks)
            player1_choice, player2_choice = choices
            
            # If either player didn't respond, cancel the game
            if player1_choice is None or player2_choice is None:
                embed.color = discord.Color.orange()
                embed.title = "⏱️ Game Cancelled"
                
                if player1_choice is None and player2_choice is None:
                    embed.description = "Both players took too long to make a choice. Game cancelled."
                elif player1_choice is None:
                    embed.description = f"{ctx.author.mention} took too long to make a choice. Game cancelled."
                else:
                    embed.description = f"{opponent.mention} took too long to make a choice. Game cancelled."
                
                await message.edit(embed=embed)
            else:
                # Determine winner
                result = self.determine_winner(player1_choice, player2_choice)
                
                # Show result
                await self.show_multiplayer_result(ctx, message, ctx.author, opponent, player1_choice, player2_choice, result)
                
                # Update stats for both players
                if result == "win":
                    await self.update_stats(ctx.author.id, ctx.guild.id, "win")
                    await self.update_stats(opponent.id, ctx.guild.id, "loss")
                elif result == "loss":
                    await self.update_stats(ctx.author.id, ctx.guild.id, "loss")
                    await self.update_stats(opponent.id, ctx.guild.id, "win")
                else:
                    await self.update_stats(ctx.author.id, ctx.guild.id, "tie")
                    await self.update_stats(opponent.id, ctx.guild.id, "tie")
        
        except asyncio.TimeoutError:
            # Opponent didn't respond in time
            embed.color = discord.Color.orange()
            embed.title = "⏱️ Time's Up!"
            embed.description = f"{opponent.mention} didn't respond to the challenge in time. Game cancelled."
            
            await message.edit(embed=embed)
        finally:
            # Clean up
            await message.clear_reactions()
            if ctx.author.id in self.games:
                del self.games[ctx.author.id]
            if opponent.id in self.games:
                del self.games[opponent.id]
    
    async def get_player_choice(self, player):
        """Get a player's choice via DM."""
        try:
            # Create DM embed
            embed = discord.Embed(
                title="🎮 Rock Paper Scissors",
                description=(
                    "Choose your move!\n\n"
                    f"🪨 - Rock\n"
                    f"📄 - Paper\n"
                    f"✂️ - Scissors"
                ),
                color=discord.Color.blue()
            )
            embed.set_footer(text="You have 30 seconds to make your choice.")
            
            # Send DM
            dm_channel = await player.create_dm()
            message = await dm_channel.send(embed=embed)
            
            # Add reactions
            for emoji in self.choices.values():
                await message.add_reaction(emoji)
            
            # Wait for choice
            def check(reaction, user):
                return (
                    user.id == player.id and
                    reaction.message.id == message.id and
                    str(reaction.emoji) in self.choices.values()
                )
            
            reaction, user = await self.bot.wait_for("reaction_add", check=check, timeout=30.0)
            
            # Get choice
            for choice, emoji in self.choices.items():
                if str(reaction.emoji) == emoji:
                    # Confirm choice
                    embed.color = discord.Color.green()
                    embed.title = "✅ Choice Confirmed"
                    embed.description = f"You chose **{choice.title()}** {emoji}!"
                    
                    await message.edit(embed=embed)
                    return choice
        
        except asyncio.TimeoutError:
            # Player didn't make a choice in time
            try:
                embed = discord.Embed(
                    title="⏱️ Time's Up!",
                    description="You took too long to make a choice. Game cancelled.",
                    color=discord.Color.orange()
                )
                await dm_channel.send(embed=embed)
            except:
                pass
            return None
        except discord.Forbidden:
            # Could not DM player
            return random.choice(list(self.choices.keys()))
    
    def determine_winner(self, choice1, choice2):
        """Determine the winner based on choices."""
        if choice1 == choice2:
            return "tie"
        elif (
            (choice1 == "rock" and choice2 == "scissors") or
            (choice1 == "paper" and choice2 == "rock") or
            (choice1 == "scissors" and choice2 == "paper")
        ):
            return "win"
        else:
            return "loss"
    
    async def show_bot_game_result(self, ctx, message, user_choice, bot_choice, result):
        """Show the result of a game against the bot."""
        # Create result embed
        embed = discord.Embed(
            title="🎮 Rock Paper Scissors Results",
            color=discord.Color.blue()
        )
        
        # User and bot choices
        user_emoji = self.choices[user_choice]
        bot_emoji = self.choices[bot_choice]
        
        # Result description
        if result == "win":
            embed.color = discord.Color.green()
            win_message = random.choice(self.win_messages)
            embed.description = f"**{ctx.author.name}** {win_message} **Bot**!"
            embed.add_field(name=f"{ctx.author.name}'s choice", value=f"{user_emoji} **{user_choice.title()}**", inline=True)
            embed.add_field(name="Bot's choice", value=f"{bot_emoji} **{bot_choice.title()}**", inline=True)
            embed.add_field(name="Result", value="🏆 You win! 🏆", inline=False)
            
            # Award coins if economy system is enabled
            economy_cog = self.bot.get_cog("Economy")
            if economy_cog:
                coins = 20
                await economy_cog.add_balance(ctx.author.id, ctx.guild.id, coins)
                embed.add_field(name="Reward", value=f"You earned **{coins}** coins!", inline=False)
                
        elif result == "loss":
            embed.color = discord.Color.red()
            win_message = random.choice(self.win_messages)
            embed.description = f"**Bot** {win_message} **{ctx.author.name}**!"
            embed.add_field(name=f"{ctx.author.name}'s choice", value=f"{user_emoji} **{user_choice.title()}**", inline=True)
            embed.add_field(name="Bot's choice", value=f"{bot_emoji} **{bot_choice.title()}**", inline=True)
            embed.add_field(name="Result", value="❌ You lose! ❌", inline=False)
        else:
            embed.color = discord.Color.gold()
            embed.description = f"**{ctx.author.name}** and **Bot** tied!"
            embed.add_field(name=f"{ctx.author.name}'s choice", value=f"{user_emoji} **{user_choice.title()}**", inline=True)
            embed.add_field(name="Bot's choice", value=f"{bot_emoji} **{bot_choice.title()}**", inline=True)
            embed.add_field(name="Result", value="🤝 It's a tie! 🤝", inline=False)
            
            # Award smaller amount of coins for a tie
            economy_cog = self.bot.get_cog("Economy")
            if economy_cog:
                coins = 5
                await economy_cog.add_balance(ctx.author.id, ctx.guild.id, coins)
                embed.add_field(name="Reward", value=f"You earned **{coins}** coins!", inline=False)
        
        # Update message
        await message.edit(embed=embed)
        await message.clear_reactions()
    
    async def show_multiplayer_result(self, ctx, message, player1, player2, player1_choice, player2_choice, result):
        """Show the result of a multiplayer game."""
        # Create result embed
        embed = discord.Embed(
            title="🎮 Rock Paper Scissors Results",
            color=discord.Color.blue()
        )
        
        # Player choices
        player1_emoji = self.choices[player1_choice]
        player2_emoji = self.choices[player2_choice]
        
        # Result description
        if result == "win":
            embed.color = discord.Color.green()
            win_message = random.choice(self.win_messages)
            embed.description = f"**{player1.name}** {win_message} **{player2.name}**!"
            
            # Award coins if economy system is enabled
            economy_cog = self.bot.get_cog("Economy")
            if economy_cog:
                coins = 30
                await economy_cog.add_balance(player1.id, ctx.guild.id, coins)
                embed.add_field(name="Reward", value=f"{player1.mention} earned **{coins}** coins!", inline=False)
                
        elif result == "loss":
            embed.color = discord.Color.green()  # Still green because player2 won
            win_message = random.choice(self.win_messages)
            embed.description = f"**{player2.name}** {win_message} **{player1.name}**!"
            
            # Award coins if economy system is enabled
            economy_cog = self.bot.get_cog("Economy")
            if economy_cog:
                coins = 30
                await economy_cog.add_balance(player2.id, ctx.guild.id, coins)
                embed.add_field(name="Reward", value=f"{player2.mention} earned **{coins}** coins!", inline=False)
                
        else:
            embed.color = discord.Color.gold()
            embed.description = f"**{player1.name}** and **{player2.name}** tied!"
            
            # Award smaller amount of coins for a tie
            economy_cog = self.bot.get_cog("Economy")
            if economy_cog:
                coins = 10
                await economy_cog.add_balance(player1.id, ctx.guild.id, coins)
                await economy_cog.add_balance(player2.id, ctx.guild.id, coins)
                embed.add_field(name="Reward", value=f"Both players earned **{coins}** coins!", inline=False)
        
        # Add player choices
        embed.add_field(name=f"{player1.name}'s choice", value=f"{player1_emoji} **{player1_choice.title()}**", inline=True)
        embed.add_field(name=f"{player2.name}'s choice", value=f"{player2_emoji} **{player2_choice.title()}**", inline=True)
        
        # Update message
        await message.edit(embed=embed)
    
    async def update_stats(self, user_id, guild_id, result):
        """Update player stats in the database."""
        # Get database manager
        db_manager = self.bot.get_cog("Utils").db_manager if hasattr(self.bot.get_cog("Utils"), "db_manager") else None
        
        if not db_manager:
            return
        
        try:
            # Get game data for this guild
            game_data = await db_manager.get_game_data("rps", guild_id=guild_id)
            
            if not game_data:
                game_data = {"leaderboard": {}}
            
            if "leaderboard" not in game_data:
                game_data["leaderboard"] = {}
            
            # Update user's stats
            user_id_str = str(user_id)
            if user_id_str not in game_data["leaderboard"]:
                game_data["leaderboard"][user_id_str] = {
                    "wins": 0,
                    "losses": 0,
                    "ties": 0
                }
            
            # Increment appropriate stat
            game_data["leaderboard"][user_id_str][f"{result}s"] += 1
            
            # Save updated data
            await db_manager.update_game_data("rps", game_data, guild_id=guild_id)
                
        except Exception as e:
            print(f"Error updating RPS stats: {e}")

async def setup(bot):
    await bot.add_cog(RockPaperScissors(bot))
