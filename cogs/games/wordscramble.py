import discord
from discord.ext import commands
import random
import asyncio
import time
from typing import Dict, List, Optional, Union

class WordScramble(commands.Cog):
    """Word Scramble game for Discord."""
    
    def __init__(self, bot):
        self.bot = bot
        self.category = "games"  # For help command
        self.active_games = {}  # Channel ID: game_data
        self.currency_emoji = "🪙"
        
        # Word categories
        self.word_lists = {
            "easy": [
                "cat", "dog", "run", "jump", "play", "book", "fish", "swim", "cake",
                "game", "sing", "moon", "star", "tree", "bird", "card", "hand", "ball",
                "hat", "pen", "car", "rain", "sun", "door", "rock", "baby", "love"
            ],
            "medium": [
                "music", "water", "earth", "apple", "bread", "dance", "pizza", "river",
                "beach", "light", "clock", "paper", "happy", "table", "sheep", "mouse",
                "house", "money", "phone", "space", "dream", "queen", "wagon", "cloud",
                "plant", "fruit", "smile", "snake", "tiger", "ghost", "story"
            ],
            "hard": [
                "puzzle", "morning", "language", "mountain", "rainbow", "holiday",
                "library", "elephant", "chocolate", "hospital", "butterfly", "universe",
                "adventure", "treasure", "dinosaur", "keyboard", "computer", "calendar",
                "firework", "festival", "symphony", "umbrella", "sandwich", "building",
                "question", "painting", "whisper", "crystal", "triangle", "airplane"
            ],
            "expert": [
                "government", "algorithm", "philosophy", "revolution", "technology",
                "imagination", "celebration", "university", "confidence", "dictionary",
                "development", "enthusiastic", "significance", "achievement", "mysterious",
                "conversation", "photography", "temperature", "environment", "innovation",
                "opportunity", "experience", "community", "inspiration", "vocabulary",
                "impossible", "perspective", "knowledge", "challenge", "atmosphere"
            ]
        }
    
    @commands.command(name="wordscramble", aliases=["ws", "scramble"])
    async def wordscramble(self, ctx, difficulty: str = "medium"):
        """
        Start a word scramble game.
        
        Examples:
        !wordscramble - Start a medium difficulty game
        !wordscramble easy - Start an easy game
        !wordscramble hard - Start a hard game
        !wordscramble expert - Start an expert game
        """
        # Check if there's already a game in this channel
        if ctx.channel.id in self.active_games:
            embed = discord.Embed(
                title="❌ Game Already In Progress",
                description="There's already a Word Scramble game in this channel!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Validate difficulty
        difficulty = difficulty.lower()
        if difficulty not in self.word_lists:
            valid_difficulties = ", ".join([f"`{d}`" for d in self.word_lists.keys()])
            embed = discord.Embed(
                title="❌ Invalid Difficulty",
                description=f"Choose from: {valid_difficulties}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Set up reward based on difficulty
        base_rewards = {
            "easy": 30,
            "medium": 60,
            "hard": 100,
            "expert": 200
        }
        
        # Select a random word
        word = random.choice(self.word_lists[difficulty])
        
        # Scramble the word
        scrambled = self.scramble_word(word)
        
        # Calculate base reward
        base_reward = base_rewards[difficulty]
        
        # Set up game data
        game_data = {
            "word": word,
            "scrambled": scrambled,
            "difficulty": difficulty,
            "base_reward": base_reward,
            "time_bonus": base_reward,  # Start with full time bonus
            "start_time": time.time(),
            "max_time": 60,  # 60 seconds to solve for full time bonus
            "solved": False,
            "solver": None,
            "timeout_task": None
        }
        
        # Store game
        self.active_games[ctx.channel.id] = game_data
        
        # Create and send game embed
        embed = self.create_game_embed(game_data)
        message = await ctx.send(embed=embed)
        
        # Set up timeout task
        timeout_task = asyncio.create_task(self.game_timeout(ctx.channel.id, message))
        game_data["timeout_task"] = timeout_task
        
        # Wait for answers
        def check(m):
            # Valid answer: in the same channel, not from a bot, and correct word
            return (
                m.channel.id == ctx.channel.id and
                not m.author.bot and
                m.content.lower() == word.lower()
            )
        
        try:
            answer_msg = await self.bot.wait_for("message", check=check, timeout=120.0)
            
            # Someone got it right
            game_data["solved"] = True
            game_data["solver"] = answer_msg.author
            
            # Cancel timeout task
            if game_data["timeout_task"] and not game_data["timeout_task"].done():
                game_data["timeout_task"].cancel()
            
            # Calculate final reward with time bonus
            await self.end_game(ctx.channel.id, message, "solved")
            
        except asyncio.TimeoutError:
            # No one got it right in time (this shouldn't trigger if the timeout_task works)
            if ctx.channel.id in self.active_games:
                await self.end_game(ctx.channel.id, message, "timeout")
    
    def scramble_word(self, word):
        """Scramble a word so it's not the same as the original."""
        if len(word) <= 3:
            # For very short words, just reverse them
            return word[::-1]
        
        # Convert to list for shuffling
        word_list = list(word)
        
        # Keep shuffling until we get a different arrangement
        scrambled = "".join(word_list)
        attempts = 0
        
        while scrambled == word and attempts < 10:
            random.shuffle(word_list)
            scrambled = "".join(word_list)
            attempts += 1
        
        return scrambled
    
    def create_game_embed(self, game_data):
        """Create an embed for the word scramble game."""
        difficulty = game_data["difficulty"]
        scrambled = game_data["scrambled"]
        base_reward = game_data["base_reward"]
        time_bonus = game_data["time_bonus"]
        
        # Difficulty color
        colors = {
            "easy": discord.Color.green(),
            "medium": discord.Color.blue(),
            "hard": discord.Color.orange(),
            "expert": discord.Color.purple()
        }
        
        embed = discord.Embed(
            title="🔤 Word Scramble",
            description=f"Unscramble this word: **{scrambled.upper()}**",
            color=colors.get(difficulty, discord.Color.blue())
        )
        
        # Add game info
        embed.add_field(
            name="Difficulty",
            value=difficulty.title(),
            inline=True
        )
        
        embed.add_field(
            name="Letters",
            value=len(scrambled),
            inline=True
        )
        
        embed.add_field(
            name="Reward",
            value=f"Base: {base_reward} {self.currency_emoji}\nTime Bonus: {time_bonus} {self.currency_emoji}\nTotal: {base_reward + time_bonus} {self.currency_emoji}",
            inline=False
        )
        
        embed.set_footer(text="Type your answer in the chat • First correct answer wins!")
        
        return embed
    
    async def game_timeout(self, channel_id, message):
        """Handle game timeout and hint system."""
        try:
            # Wait 30 seconds
            await asyncio.sleep(30)
            
            # Check if game still active
            if channel_id in self.active_games and not self.active_games[channel_id]["solved"]:
                game_data = self.active_games[channel_id]
                
                # Give a hint (first letter)
                word = game_data["word"]
                hint = f"**Hint:** The word starts with **{word[0].upper()}**"
                
                # Update embed with hint
                embed = message.embeds[0]
                
                # Check if there's already a hint field
                hint_field_index = None
                for i, field in enumerate(embed.fields):
                    if field.name == "Hint":
                        hint_field_index = i
                        break
                
                if hint_field_index is not None:
                    embed.set_field_at(hint_field_index, name="Hint", value=hint, inline=False)
                else:
                    embed.add_field(name="Hint", value=hint, inline=False)
                
                # Update time bonus (half it after hint)
                game_data["time_bonus"] = max(0, game_data["time_bonus"] // 2)
                
                # Update reward field
                base_reward = game_data["base_reward"]
                time_bonus = game_data["time_bonus"]
                
                for i, field in enumerate(embed.fields):
                    if field.name == "Reward":
                        embed.set_field_at(
                            i,
                            name="Reward",
                            value=f"Base: {base_reward} {self.currency_emoji}\nTime Bonus: {time_bonus} {self.currency_emoji}\nTotal: {base_reward + time_bonus} {self.currency_emoji}",
                            inline=False
                        )
                        break
                
                await message.edit(embed=embed)
                
                # Wait another 30 seconds
                await asyncio.sleep(30)
                
                # Check if game still active
                if channel_id in self.active_games and not self.active_games[channel_id]["solved"]:
                    # Give another hint (first and last letter)
                    word = game_data["word"]
                    if len(word) > 1:
                        hint = f"**Hint:** The word starts with **{word[0].upper()}** and ends with **{word[-1].upper()}**"
                    else:
                        hint = f"**Hint:** The word is **{word[0].upper()}**"
                    
                    # Update embed with hint
                    embed = message.embeds[0]
                    
                    # Update hint field
                    for i, field in enumerate(embed.fields):
                        if field.name == "Hint":
                            embed.set_field_at(i, name="Hint", value=hint, inline=False)
                            break
                    
                    # Update time bonus (remove it after second hint)
                    game_data["time_bonus"] = 0
                    
                    # Update reward field
                    base_reward = game_data["base_reward"]
                    time_bonus = game_data["time_bonus"]
                    
                    for i, field in enumerate(embed.fields):
                        if field.name == "Reward":
                            embed.set_field_at(
                                i,
                                name="Reward",
                                value=f"Base: {base_reward} {self.currency_emoji}\nTime Bonus: {time_bonus} {self.currency_emoji}\nTotal: {base_reward + time_bonus} {self.currency_emoji}",
                                inline=False
                            )
                            break
                    
                    await message.edit(embed=embed)
                    
                    # Wait final 60 seconds
                    await asyncio.sleep(60)
                    
                    # End game if still active
                    if channel_id in self.active_games and not self.active_games[channel_id]["solved"]:
                        await self.end_game(channel_id, message, "timeout")
        
        except asyncio.CancelledError:
            # Task was cancelled (someone solved it)
            pass
        except Exception as e:
            print(f"Error in wordscramble timeout task: {e}")
    
    async def end_game(self, channel_id, message, end_type):
        """End the word scramble game."""
        if channel_id not in self.active_games:
            return
        
        game_data = self.active_games[channel_id]
        
        # Get channel
        channel = self.bot.get_channel(channel_id)
        if not channel:
            # Channel not found, just clean up
            del self.active_games[channel_id]
            return
        
        # Calculate final reward and create result embed
        if end_type == "solved":
            # Someone solved it
            solver = game_data["solver"]
            word = game_data["word"]
            
            # Calculate time bonus based on how quickly they solved it
            elapsed_time = time.time() - game_data["start_time"]
            max_time = game_data["max_time"]
            
            if elapsed_time < max_time:
                # Full time bonus if solved quickly
                time_factor = 1.0 - (elapsed_time / max_time)
            else:
                # No time bonus if took too long
                time_factor = 0
            
            time_bonus = int(game_data["base_reward"] * time_factor)
            game_data["time_bonus"] = time_bonus
            
            total_reward = game_data["base_reward"] + time_bonus
            
            # Create success embed
            embed = discord.Embed(
                title="🎉 Word Solved!",
                description=f"{solver.mention} correctly unscrambled the word **{word.upper()}**!",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="Reward Breakdown",
                value=f"Base Reward: **{game_data['base_reward']}** {self.currency_emoji}\nTime Bonus: **{time_bonus}** {self.currency_emoji}\nTotal: **{total_reward}** {self.currency_emoji}",
                inline=False
            )
            
            embed.add_field(
                name="Solved In",
                value=f"**{elapsed_time:.1f}** seconds",
                inline=True
            )
            
            embed.add_field(
                name="Difficulty",
                value=game_data["difficulty"].title(),
                inline=True
            )
            
            # Award coins
            economy_cog = self.bot.get_cog("Economy")
            if economy_cog:
                await economy_cog.add_balance(solver.id, channel.guild.id, total_reward)
            
            # Update stats
            await self.update_stats(solver.id, channel.guild.id, True, game_data["difficulty"])
            
        else:
            # Timeout - no one solved it
            word = game_data["word"]
            
            # Create timeout embed
            embed = discord.Embed(
                title="⏱️ Time's Up!",
                description=f"No one unscrambled the word in time.\nThe word was **{word.upper()}**.",
                color=discord.Color.red()
            )
            
            embed.add_field(
                name="Difficulty",
                value=game_data["difficulty"].title(),
                inline=True
            )
        
        # Send result
        await channel.send(embed=embed)
        
        # Clean up
        del self.active_games[channel_id]
    
    async def update_stats(self, user_id, guild_id, won, difficulty):
        """Update player stats in the database."""
        # Get database manager
        db_manager = self.bot.get_cog("Utils").db_manager if hasattr(self.bot.get_cog("Utils"), "db_manager") else None
        
        if not db_manager:
            return
        
        try:
            # Get game data
            game_data = await db_manager.get_game_data("wordscramble", guild_id=guild_id)
            
            # Initialize if doesn't exist
            if not game_data:
                game_data = {"players": {}}
            
            if "players" not in game_data:
                game_data["players"] = {}
            
            # Get or create player stats
            player_id = str(user_id)
            if player_id not in game_data["players"]:
                game_data["players"][player_id] = {"wins": 0, "games": 0, "difficulties": {}}
            
            player_stats = game_data["players"][player_id]
            
            # Update overall stats
            player_stats["games"] = player_stats.get("games", 0) + 1
            
            if won:
                player_stats["wins"] = player_stats.get("wins", 0) + 1
            
            # Update difficulty stats
            if "difficulties" not in player_stats:
                player_stats["difficulties"] = {}
            
            if difficulty not in player_stats["difficulties"]:
                player_stats["difficulties"][difficulty] = {"wins": 0, "games": 0}
            
            player_stats["difficulties"][difficulty]["games"] = player_stats["difficulties"][difficulty].get("games", 0) + 1
            
            if won:
                player_stats["difficulties"][difficulty]["wins"] = player_stats["difficulties"][difficulty].get("wins", 0) + 1
            
            # Save game data
            await db_manager.update_game_data("wordscramble", game_data, guild_id=guild_id)
            
        except Exception as e:
            print(f"Error updating wordscramble stats: {e}")
    
    @commands.command(name="wordscramble_stats", aliases=["wsstats"])
    async def wordscramble_stats(self, ctx, member: discord.Member = None):
        """
        View Word Scramble stats for yourself or another player.
        
        Examples:
        !wordscramble_stats - View your own stats
        !wordscramble_stats @user - View another user's stats
        """
        if not member:
            member = ctx.author
        
        # Get database manager
        db_manager = self.bot.get_cog("Utils").db_manager if hasattr(self.bot.get_cog("Utils"), "db_manager") else None
        
        if not db_manager:
            embed = discord.Embed(
                title="❌ Database Error",
                description="Could not access the database.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        try:
            # Get game data
            game_data = await db_manager.get_game_data("wordscramble", guild_id=ctx.guild.id)
            
            if not game_data or "players" not in game_data or str(member.id) not in game_data["players"]:
                embed = discord.Embed(
                    title=f"📊 Word Scramble Stats for {member.display_name}",
                    description="This player hasn't played any Word Scramble games yet!",
                    color=discord.Color.blue()
                )
                embed.set_thumbnail(url=member.display_avatar.url)
                await ctx.send(embed=embed)
                return
            
            # Get player stats
            stats = game_data["players"][str(member.id)]
            wins = stats.get("wins", 0)
            total_games = stats.get("games", 0)
            win_rate = (wins / total_games * 100) if total_games > 0 else 0
            
            # Create stats embed
            embed = discord.Embed(
                title=f"📊 Word Scramble Stats for {member.display_name}",
                color=discord.Color.blue()
            )
            
            embed.add_field(name="Games Played", value=str(total_games), inline=True)
            embed.add_field(name="Words Solved", value=str(wins), inline=True)
            embed.add_field(name="Success Rate", value=f"{win_rate:.1f}%", inline=True)
            
            # Add difficulty breakdown if available
            if "difficulties" in stats and stats["difficulties"]:
                difficulties = stats["difficulties"]
                difficulty_text = ""
                
                for diff, diff_stats in difficulties.items():
                    diff_wins = diff_stats.get("wins", 0)
                    diff_games = diff_stats.get("games", 0)
                    diff_rate = (diff_wins / diff_games * 100) if diff_games > 0 else 0
                    
                    difficulty_text += f"**{diff.title()}**: {diff_wins}/{diff_games} ({diff_rate:.1f}%)\n"
                
                embed.add_field(
                    name="Difficulty Breakdown",
                    value=difficulty_text,
                    inline=False
                )
            
            embed.set_thumbnail(url=member.display_avatar.url)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"An error occurred: {e}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @commands.command(name="wordscramble_leaderboard", aliases=["wslb"])
    async def wordscramble_leaderboard(self, ctx):
        """Display the Word Scramble leaderboard for this server."""
        # Get database manager
        db_manager = self.bot.get_cog("Utils").db_manager if hasattr(self.bot.get_cog("Utils"), "db_manager") else None
        
        if not db_manager:
            embed = discord.Embed(
                title="❌ Database Error",
                description="Could not access the database.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        try:
            # Get game data
            game_data = await db_manager.get_game_data("wordscramble", guild_id=ctx.guild.id)
            
            if not game_data or "players" not in game_data or not game_data["players"]:
                embed = discord.Embed(
                    title="📊 Word Scramble Leaderboard",
                    description="No games have been played yet!",
                    color=discord.Color.blue()
                )
                await ctx.send(embed=embed)
                return
            
            # Sort players by wins
            players = game_data["players"]
            sorted_players = sorted(players.items(), key=lambda x: x[1]["wins"], reverse=True)
            
            # Create leaderboard embed
            embed = discord.Embed(
                title="📊 Word Scramble Leaderboard",
                description="Top Word Scramble players in this server:",
                color=discord.Color.gold()
            )
            
            # Add top players
            for i, (player_id, stats) in enumerate(sorted_players[:10], 1):
                try:
                    member = await ctx.guild.fetch_member(int(player_id))
                    name = member.display_name
                except:
                    name = f"User {player_id}"
                
                wins = stats.get("wins", 0)
                total_games = stats.get("games", 0)
                win_rate = (wins / total_games * 100) if total_games > 0 else 0
                
                embed.add_field(
                    name=f"{i}. {name}",
                    value=f"**Words Solved:** {wins}\n**Games:** {total_games}\n**Success Rate:** {win_rate:.1f}%",
                    inline=(i % 2 != 0)  # Alternating inline
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"An error occurred: {e}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(WordScramble(bot))
