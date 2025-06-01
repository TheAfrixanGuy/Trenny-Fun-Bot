import discord
from discord.ext import commands
import random
import asyncio
from typing import Dict, List, Optional, Union

class NumberGuess(commands.Cog):
    """Guess the number game for Discord."""
    
    def __init__(self, bot):
        self.bot = bot
        self.category = "games"  # For help command
        self.games = {}  # Active games
        self.currency_emoji = "🪙"
        self.default_range = (1, 100)
        self.default_attempts = 7
        self.default_reward = 100
    
    @commands.command(name="numguess", aliases=["ng", "guess"])
    async def numguess(self, ctx, difficulty: str = "normal"):
        """
        Start a number guessing game.
        
        Examples:
        !numguess - Start a normal difficulty game (1-100)
        !numguess easy - Start an easy game (1-50)
        !numguess hard - Start a hard game (1-200)
        !numguess expert - Start an expert game (1-500)
        """
        # Check if user already has an active game
        if ctx.author.id in self.games:
            embed = discord.Embed(
                title="❌ Game Already In Progress",
                description="You already have an active Number Guess game! Finish that one first.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Set difficulty
        difficulty = difficulty.lower()
        if difficulty == "easy":
            number_range = (1, 50)
            max_attempts = 6
            reward = 50
        elif difficulty == "normal":
            number_range = (1, 100)
            max_attempts = 7
            reward = 100
        elif difficulty == "hard":
            number_range = (1, 200)
            max_attempts = 8
            reward = 200
        elif difficulty == "expert":
            number_range = (1, 500)
            max_attempts = 9
            reward = 500
        else:
            # Invalid difficulty
            embed = discord.Embed(
                title="❌ Invalid Difficulty",
                description="Choose from: `easy`, `normal`, `hard`, or `expert`",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Create game
        secret_number = random.randint(number_range[0], number_range[1])
        
        # Initialize game state
        game_state = {
            "secret_number": secret_number,
            "range": number_range,
            "attempts": 0,
            "max_attempts": max_attempts,
            "guesses": [],
            "status": "active",
            "message": None,
            "reward": reward,
            "difficulty": difficulty
        }
        
        self.games[ctx.author.id] = game_state
        
        # Create and send initial game state
        embed = self.create_game_embed(ctx.author, game_state)
        game_state["message"] = await ctx.send(embed=embed)
        
        # Game loop
        while game_state["status"] == "active":
            try:
                # Wait for a message from the player
                def check(m):
                    # Check if message is from the player and in the same channel
                    if m.author.id != ctx.author.id or m.channel.id != ctx.channel.id:
                        return False
                    
                    # Check if it's a valid guess (number)
                    try:
                        guess = int(m.content)
                        return True
                    except ValueError:
                        return False
                
                msg = await self.bot.wait_for("message", check=check, timeout=60.0)
                
                try:
                    guess = int(msg.content)
                    await self.process_guess(ctx, game_state, guess)
                except ValueError:
                    continue
                
            except asyncio.TimeoutError:
                # Game timed out
                game_state["status"] = "timeout"
                await self.end_game(ctx, game_state)
                break
    
    async def process_guess(self, ctx, game_state, guess):
        """Process a guess in the Number Guess game."""
        # Increment attempts
        game_state["attempts"] += 1
        
        # Add to guesses list
        game_state["guesses"].append(guess)
        
        # Check guess against secret number
        secret_number = game_state["secret_number"]
        
        if guess == secret_number:
            # Correct guess - win
            game_state["status"] = "won"
            await self.end_game(ctx, game_state)
        elif game_state["attempts"] >= game_state["max_attempts"]:
            # Out of attempts - lose
            game_state["status"] = "lost"
            await self.end_game(ctx, game_state)
        else:
            # Incorrect guess - continue
            # Update game display
            embed = self.create_game_embed(ctx.author, game_state, guess)
            await game_state["message"].edit(embed=embed)
    
    def create_game_embed(self, player, game_state, last_guess=None):
        """Create an embed displaying the current game state."""
        number_range = game_state["range"]
        attempts = game_state["attempts"]
        max_attempts = game_state["max_attempts"]
        guesses = game_state["guesses"]
        secret_number = game_state["secret_number"]
        
        # Create hint based on the last guess
        hint = ""
        if last_guess is not None:
            if last_guess < secret_number:
                hint = f"📈 **{last_guess}** is too low! Go higher."
            else:
                hint = f"📉 **{last_guess}** is too high! Go lower."
        
        # Create embed
        embed = discord.Embed(
            title="🔢 Number Guessing Game",
            description=f"I'm thinking of a number between **{number_range[0]}** and **{number_range[1]}**.\nCan you guess it?",
            color=discord.Color.blue()
        )
        
        # Add game info
        embed.add_field(
            name="Game Info",
            value=f"**Difficulty:** {game_state['difficulty'].title()}\n**Range:** {number_range[0]}-{number_range[1]}\n**Reward:** {game_state['reward']} {self.currency_emoji}",
            inline=True
        )
        
        # Add attempts
        embed.add_field(
            name="Attempts",
            value=f"**Used:** {attempts}/{max_attempts}\n**Remaining:** {max_attempts - attempts}",
            inline=True
        )
        
        # Add previous guesses if any
        if guesses:
            embed.add_field(
                name="Previous Guesses",
                value=", ".join([str(g) for g in guesses]),
                inline=False
            )
        
        # Add hint if available
        if hint:
            embed.add_field(
                name="Hint",
                value=hint,
                inline=False
            )
        
        embed.set_footer(text=f"Playing as {player.name} • Type a number to guess")
        
        return embed
    
    async def end_game(self, ctx, game_state):
        """End the Number Guess game and award prizes if won."""
        secret_number = game_state["secret_number"]
        status = game_state["status"]
        attempts = game_state["attempts"]
        max_attempts = game_state["max_attempts"]
        
        # Create result embed
        if status == "won":
            embed = discord.Embed(
                title="🎉 You Won!",
                description=f"Congratulations! You correctly guessed the number: **{secret_number}**",
                color=discord.Color.green()
            )
            
            # Calculate bonus based on remaining attempts
            remaining_attempts = max_attempts - attempts
            bonus = int(game_state["reward"] * (remaining_attempts * 0.1))  # 10% bonus per remaining attempt
            total_reward = game_state["reward"] + bonus
            
            # Award coins if won
            economy_cog = self.bot.get_cog("Economy")
            if economy_cog:
                await economy_cog.add_balance(ctx.author.id, ctx.guild.id, total_reward)
                
                # Reward details
                reward_text = f"Base Reward: **{game_state['reward']}** {self.currency_emoji}\n"
                if bonus > 0:
                    reward_text += f"Speed Bonus: **{bonus}** {self.currency_emoji}\n"
                reward_text += f"Total: **{total_reward}** {self.currency_emoji}"
                
                embed.add_field(
                    name="Reward",
                    value=reward_text,
                    inline=False
                )
            
        elif status == "lost":
            embed = discord.Embed(
                title="❌ You Lost!",
                description=f"You ran out of attempts! The number was: **{secret_number}**",
                color=discord.Color.red()
            )
            
        else:  # timeout
            embed = discord.Embed(
                title="⏱️ Game Timed Out",
                description=f"You took too long to respond! The number was: **{secret_number}**",
                color=discord.Color.orange()
            )
        
        # Add game stats
        embed.add_field(
            name="Game Stats",
            value=f"**Attempts Used:** {attempts}/{max_attempts}\n**Difficulty:** {game_state['difficulty'].title()}",
            inline=False
        )
        
        # Send result
        await ctx.send(embed=embed)
        
        # Update database stats
        await self.update_stats(ctx.author.id, ctx.guild.id, status == "won")
        
        # Cleanup
        del self.games[ctx.author.id]
    
    async def update_stats(self, user_id, guild_id, won):
        """Update player stats in the database."""
        # Get database manager
        db_manager = self.bot.get_cog("Utils").db_manager if hasattr(self.bot.get_cog("Utils"), "db_manager") else None
        
        if not db_manager:
            return
        
        try:
            # Get game data
            game_data = await db_manager.get_game_data("numguess", guild_id=guild_id)
            
            # Initialize if doesn't exist
            if not game_data:
                game_data = {"players": {}}
            
            if "players" not in game_data:
                game_data["players"] = {}
            
            # Get or create player stats
            player_id = str(user_id)
            if player_id not in game_data["players"]:
                game_data["players"][player_id] = {"wins": 0, "losses": 0, "games": 0}
            
            # Update stats
            game_data["players"][player_id]["games"] = game_data["players"][player_id].get("games", 0) + 1
            
            if won:
                game_data["players"][player_id]["wins"] = game_data["players"][player_id].get("wins", 0) + 1
            else:
                game_data["players"][player_id]["losses"] = game_data["players"][player_id].get("losses", 0) + 1
            
            # Save game data
            await db_manager.update_game_data("numguess", game_data, guild_id=guild_id)
            
        except Exception as e:
            print(f"Error updating numguess stats: {e}")
    
    @commands.command(name="numguess_leaderboard", aliases=["nglb"])
    async def numguess_leaderboard(self, ctx):
        """Display the Number Guess leaderboard for this server."""
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
            game_data = await db_manager.get_game_data("numguess", guild_id=ctx.guild.id)
            
            if not game_data or "players" not in game_data or not game_data["players"]:
                embed = discord.Embed(
                    title="📊 Number Guess Leaderboard",
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
                title="📊 Number Guess Leaderboard",
                description="Top Number Guess players in this server:",
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
                losses = stats.get("losses", 0)
                total_games = stats.get("games", wins + losses)
                win_rate = (wins / total_games * 100) if total_games > 0 else 0
                
                embed.add_field(
                    name=f"{i}. {name}",
                    value=f"**Wins:** {wins}\n**Games:** {total_games}\n**Win Rate:** {win_rate:.1f}%",
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
    
    @commands.command(name="numguess_stats", aliases=["ngstats"])
    async def numguess_stats(self, ctx, member: discord.Member = None):
        """
        View Number Guess stats for yourself or another player.
        
        Examples:
        !numguess_stats - View your own stats
        !numguess_stats @user - View another user's stats
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
            game_data = await db_manager.get_game_data("numguess", guild_id=ctx.guild.id)
            
            if not game_data or "players" not in game_data or str(member.id) not in game_data["players"]:
                embed = discord.Embed(
                    title=f"📊 Number Guess Stats for {member.display_name}",
                    description="This player hasn't played any Number Guess games yet!",
                    color=discord.Color.blue()
                )
                embed.set_thumbnail(url=member.display_avatar.url)
                await ctx.send(embed=embed)
                return
            
            # Get player stats
            stats = game_data["players"][str(member.id)]
            wins = stats.get("wins", 0)
            losses = stats.get("losses", 0)
            total_games = stats.get("games", wins + losses)
            win_rate = (wins / total_games * 100) if total_games > 0 else 0
            
            # Create stats embed
            embed = discord.Embed(
                title=f"📊 Number Guess Stats for {member.display_name}",
                color=discord.Color.blue()
            )
            
            embed.add_field(name="Games Played", value=str(total_games), inline=True)
            embed.add_field(name="Wins", value=str(wins), inline=True)
            embed.add_field(name="Losses", value=str(losses), inline=True)
            embed.add_field(name="Win Rate", value=f"{win_rate:.1f}%", inline=True)
            
            embed.set_thumbnail(url=member.display_avatar.url)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"An error occurred: {e}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(NumberGuess(bot))
