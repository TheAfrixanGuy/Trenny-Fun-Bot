import discord
from discord.ext import commands
import asyncio
import random
from typing import Dict, List, Tuple
import time

class SnakeGame:
    """Represents a game of Snake."""
    
    # Direction constants
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)
    
    # Board characters
    EMPTY = "⬛"
    SNAKE_HEAD = "🟢"
    SNAKE_BODY = "🟩"
    FOOD = "🍎"
    BORDER = "⬜"
    
    def __init__(self, player, difficulty="normal"):
        self.player = player
        self.difficulty = difficulty.lower()
        self.set_difficulty_params()
        self.reset_game()
        self.message = None
    
    def set_difficulty_params(self):
        """Set game parameters based on difficulty."""
        if self.difficulty == "easy":
            self.width = 8
            self.height = 8
            self.move_interval = 1.5  # seconds
        elif self.difficulty == "normal":
            self.width = 10
            self.height = 10
            self.move_interval = 1.0
        elif self.difficulty == "hard":
            self.width = 12
            self.height = 12
            self.move_interval = 0.8
        elif self.difficulty == "expert":
            self.width = 15
            self.height = 15
            self.move_interval = 0.6
        else:  # Default to normal
            self.difficulty = "normal"
            self.width = 10
            self.height = 10
            self.move_interval = 1.0
    
    def reset_game(self):
        """Reset the game state."""
        # Initialize board
        self.board = [[self.EMPTY for _ in range(self.width)] for _ in range(self.height)]
        
        # Place snake at center
        self.snake = [(self.width // 2, self.height // 2)]
        self.direction = self.RIGHT
        self.next_direction = self.RIGHT
        
        # Initialize other variables
        self.score = 0
        self.food = None
        self.game_over = False
        self.start_time = None
        self.end_time = None
        
        # Place food
        self.place_food()
    
    def place_food(self):
        """Place food at a random empty position."""
        empty_positions = []
        for y in range(self.height):
            for x in range(self.width):
                if (x, y) not in self.snake:
                    empty_positions.append((x, y))
        
        if empty_positions:
            self.food = random.choice(empty_positions)
    
    def move(self):
        """Move the snake in the current direction."""
        if self.game_over:
            return False
        
        # Start the timer on first move
        if self.start_time is None:
            self.start_time = time.time()
        
        # Update direction
        self.direction = self.next_direction
        
        # Calculate new head position
        head_x, head_y = self.snake[0]
        dx, dy = self.direction
        new_head = ((head_x + dx) % self.width, (head_y + dy) % self.height)
        
        # Check if snake hit itself
        if new_head in self.snake:
            self.game_over = True
            self.end_time = time.time()
            return False
        
        # Add new head
        self.snake.insert(0, new_head)
        
        # Check if snake ate food
        if new_head == self.food:
            self.score += 1
            self.food = None
            self.place_food()
        else:
            # Remove tail if didn't eat food
            self.snake.pop()
        
        return True
    
    def change_direction(self, new_direction):
        """Change the direction of the snake."""
        # Cannot reverse direction directly
        if (new_direction[0] == -self.direction[0] and new_direction[1] == -self.direction[1]):
            return False
        
        self.next_direction = new_direction
        return True
    
    def get_board_display(self):
        """Get the current state of the board for display."""
        # Create a fresh board
        display_board = [[self.EMPTY for _ in range(self.width)] for _ in range(self.height)]
        
        # Place food
        if self.food:
            x, y = self.food
            display_board[y][x] = self.FOOD
        
        # Place snake
        for i, (x, y) in enumerate(self.snake):
            if i == 0:
                display_board[y][x] = self.SNAKE_HEAD
            else:
                display_board[y][x] = self.SNAKE_BODY
        
        return display_board
    
    def get_display_string(self):
        """Get the board as a string for display in Discord."""
        display_board = self.get_board_display()
        
        # Add top border
        board_str = self.BORDER * (self.width + 2) + "\n"
        
        # Add rows with side borders
        for row in display_board:
            board_str += self.BORDER + "".join(row) + self.BORDER + "\n"
        
        # Add bottom border
        board_str += self.BORDER * (self.width + 2)
        
        return board_str
    
    def get_elapsed_time(self):
        """Get the elapsed time for the game in seconds."""
        if self.start_time is None:
            return 0
        
        end = self.end_time if self.end_time else time.time()
        return end - self.start_time
    
    def get_reward(self):
        """Calculate the coin reward based on score and difficulty."""
        # Base reward is score * 10
        base_reward = self.score * 10
        
        # Apply difficulty multiplier
        difficulty_multiplier = {
            "easy": 1.0,
            "normal": 1.5,
            "hard": 2.0,
            "expert": 3.0
        }.get(self.difficulty, 1.0)
        
        return int(base_reward * difficulty_multiplier)
    
    def format_time(self, seconds):
        """Format time in seconds to mm:ss format."""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"

class Snake(commands.Cog):
    """Play Snake using reaction controls. Eat food to grow longer!"""
    
    def __init__(self, bot):
        self.bot = bot
        self.category = "games"  # For help command
        self.games = {}  # User ID: game
        self.currency_emoji = "🪙"
    
    @commands.command(name="snake", aliases=["snek"])
    async def snake(self, ctx, difficulty: str = "normal"):
        """
        Play a game of Snake using reaction controls.
        
        Examples:
        !snake - Play with normal difficulty
        !snake easy - Play on easy difficulty
        !snake hard - Play on hard difficulty
        !snake expert - Play on expert difficulty
        """
        # Check if user already has an active game
        if ctx.author.id in self.games:
            embed = discord.Embed(
                title="❌ Game Already In Progress",
                description="You already have an active Snake game! Finish that one first.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Validate difficulty
        valid_difficulties = ["easy", "normal", "hard", "expert"]
        difficulty = difficulty.lower()
        
        if difficulty not in valid_difficulties:
            embed = discord.Embed(
                title="❌ Invalid Difficulty",
                description=f"Valid difficulties are: {', '.join(valid_difficulties)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Create new game
        game = SnakeGame(ctx.author, difficulty)
        self.games[ctx.author.id] = game
        
        # Create initial embed
        embed = await self.create_game_embed(game)
        
        # Send embed with instructions
        instructions = discord.Embed(
            title="🐍 Snake Game Instructions",
            description=(
                "Use the reaction controls to move the snake:\n"
                "⬆️ - Move Up\n"
                "⬇️ - Move Down\n"
                "⬅️ - Move Left\n"
                "➡️ - Move Right\n"
                "🛑 - End Game\n\n"
                "Eat the food 🍎 to grow longer and earn points.\n"
                "Don't run into yourself!\n\n"
                "Game will start in 5 seconds..."
            ),
            color=discord.Color.green()
        )
        await ctx.send(embed=instructions)
        await asyncio.sleep(5)
        
        # Send game board
        game.message = await ctx.send(embed=embed)
        
        # Add control reactions
        controls = ["⬆️", "⬇️", "⬅️", "➡️", "🛑"]
        for control in controls:
            await game.message.add_reaction(control)
        
        # Start game loop
        await self.game_loop(ctx, game)
    
    async def create_game_embed(self, game):
        """Create an embed for the Snake game."""
        # Create embed
        embed = discord.Embed(
            title=f"🐍 Snake - {game.difficulty.capitalize()}",
            description=game.get_display_string(),
            color=discord.Color.green()
        )
        
        # Add game stats
        embed.add_field(
            name="Score",
            value=str(game.score),
            inline=True
        )
        
        embed.add_field(
            name="Length",
            value=str(len(game.snake)),
            inline=True
        )
        
        embed.add_field(
            name="Time",
            value=game.format_time(game.get_elapsed_time()),
            inline=True
        )
        
        # Add status
        if game.game_over:
            status = "Game Over! 💀"
        else:
            status = "Use the reactions to control the snake!"
        
        embed.add_field(
            name="Status",
            value=status,
            inline=False
        )
        
        return embed
    
    async def game_loop(self, ctx, game):
        """Main game loop for Snake."""
        # Map reaction emojis to directions
        direction_map = {
            "⬆️": SnakeGame.UP,
            "⬇️": SnakeGame.DOWN,
            "⬅️": SnakeGame.LEFT,
            "➡️": SnakeGame.RIGHT
        }
        
        # Create tasks for handling input and game movement
        input_queue = asyncio.Queue()
        
        # Task to handle user input
        async def handle_input():
            def check(reaction, user):
                return (
                    user.id == ctx.author.id and
                    str(reaction.emoji) in ["⬆️", "⬇️", "⬅️", "➡️", "🛑"] and
                    reaction.message.id == game.message.id
                )
            
            while not game.game_over:
                try:
                    reaction, user = await self.bot.wait_for("reaction_add", timeout=game.move_interval, check=check)
                    
                    # Handle direction change or stop
                    if str(reaction.emoji) in direction_map:
                        await input_queue.put(direction_map[str(reaction.emoji)])
                    elif str(reaction.emoji) == "🛑":
                        game.game_over = True
                    
                    # Remove the reaction
                    try:
                        await game.message.remove_reaction(reaction.emoji, user)
                    except:
                        pass
                except asyncio.TimeoutError:
                    # No input during this interval, continue with current direction
                    pass
        
        # Task to handle game movement
        async def handle_movement():
            while not game.game_over:
                # Check for new direction input
                try:
                    while not input_queue.empty():
                        new_direction = await input_queue.get()
                        game.change_direction(new_direction)
                except:
                    pass
                
                # Move the snake
                game.move()
                
                # Update the game display
                embed = await self.create_game_embed(game)
                await game.message.edit(embed=embed)
                
                # Wait for next move
                await asyncio.sleep(game.move_interval)
        
        # Start the tasks
        input_task = asyncio.create_task(handle_input())
        movement_task = asyncio.create_task(handle_movement())
        
        # Wait for the game to end
        while not game.game_over:
            await asyncio.sleep(0.5)
        
        # Cancel the tasks
        input_task.cancel()
        movement_task.cancel()
        
        # Update the final state
        embed = await self.create_game_embed(game)
        await game.message.edit(embed=embed)
        
        # Handle game end
        await self.end_game(ctx, game)
    
    async def end_game(self, ctx, game):
        """Handle the end of a Snake game."""
        # Calculate reward
        reward = game.get_reward()
        
        # Award coins
        economy_cog = self.bot.get_cog("Economy")
        if economy_cog and reward > 0:
            await economy_cog.add_balance(ctx.author.id, ctx.guild.id, reward)
        
        # Create result embed
        embed = discord.Embed(
            title="🐍 Snake Game Over!",
            description=f"Game ended for {ctx.author.mention}",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="Final Score",
            value=str(game.score),
            inline=True
        )
        
        embed.add_field(
            name="Snake Length",
            value=str(len(game.snake)),
            inline=True
        )
        
        embed.add_field(
            name="Time Played",
            value=game.format_time(game.get_elapsed_time()),
            inline=True
        )
        
        embed.add_field(
            name="Reward",
            value=f"**{reward}** {self.currency_emoji}",
            inline=False
        )
        
        await ctx.send(embed=embed)
        
        # Update player stats
        await self.update_stats(ctx.author.id, ctx.guild.id, game)
        
        # Clean up
        try:
            await game.message.clear_reactions()
        except:
            pass
        
        if ctx.author.id in self.games:
            del self.games[ctx.author.id]
    
    async def update_stats(self, user_id, guild_id, game):
        """Update player stats in the database."""
        # Get database manager
        db_manager = self.bot.get_cog("Utils").db_manager if hasattr(self.bot.get_cog("Utils"), "db_manager") else None
        
        if not db_manager:
            return
        
        try:
            # Get game data
            game_data = await db_manager.get_game_data("snake", guild_id=guild_id)
            
            # Initialize if doesn't exist
            if not game_data:
                game_data = {"players": {}}
            
            if "players" not in game_data:
                game_data["players"] = {}
            
            # Get or create player stats
            player_id = str(user_id)
            if player_id not in game_data["players"]:
                game_data["players"][player_id] = {
                    "games_played": 0,
                    "high_score": 0,
                    "longest_snake": 0,
                    "total_score": 0,
                    "total_time": 0,
                    "difficulty_counts": {"easy": 0, "normal": 0, "hard": 0, "expert": 0}
                }
            
            # Update stats
            player_stats = game_data["players"][player_id]
            player_stats["games_played"] = player_stats.get("games_played", 0) + 1
            player_stats["high_score"] = max(player_stats.get("high_score", 0), game.score)
            player_stats["longest_snake"] = max(player_stats.get("longest_snake", 0), len(game.snake))
            player_stats["total_score"] = player_stats.get("total_score", 0) + game.score
            player_stats["total_time"] = player_stats.get("total_time", 0) + game.get_elapsed_time()
            
            # Initialize difficulty counts if not present
            if "difficulty_counts" not in player_stats:
                player_stats["difficulty_counts"] = {"easy": 0, "normal": 0, "hard": 0, "expert": 0}
            
            # Update difficulty count
            player_stats["difficulty_counts"][game.difficulty] = player_stats["difficulty_counts"].get(game.difficulty, 0) + 1
            
            # Save game data
            await db_manager.update_game_data("snake", game_data, guild_id=guild_id)
            
        except Exception as e:
            print(f"Error updating snake stats: {e}")
    
    @commands.command(name="snake_stats", aliases=["snekstats"])
    async def snake_stats(self, ctx, member: discord.Member = None):
        """
        View Snake game stats for yourself or another player.
        
        Examples:
        !snake_stats - View your own stats
        !snake_stats @user - View another user's stats
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
            game_data = await db_manager.get_game_data("snake", guild_id=ctx.guild.id)
            
            if not game_data or "players" not in game_data or str(member.id) not in game_data["players"]:
                embed = discord.Embed(
                    title=f"📊 Snake Stats for {member.display_name}",
                    description="This player hasn't played any Snake games yet!",
                    color=discord.Color.green()
                )
                embed.set_thumbnail(url=member.display_avatar.url)
                await ctx.send(embed=embed)
                return
            
            # Get player stats
            stats = game_data["players"][str(member.id)]
            games_played = stats.get("games_played", 0)
            high_score = stats.get("high_score", 0)
            longest_snake = stats.get("longest_snake", 0)
            total_score = stats.get("total_score", 0)
            total_time = stats.get("total_time", 0)
            
            # Calculate average score and time
            avg_score = total_score / max(1, games_played)
            avg_time = total_time / max(1, games_played)
            
            # Format time
            total_time_str = self.format_time(total_time)
            avg_time_str = self.format_time(avg_time)
            
            # Get difficulty breakdown
            difficulty_counts = stats.get("difficulty_counts", {"easy": 0, "normal": 0, "hard": 0, "expert": 0})
            
            # Create stats embed
            embed = discord.Embed(
                title=f"📊 Snake Stats for {member.display_name}",
                color=discord.Color.green()
            )
            
            embed.add_field(name="Games Played", value=str(games_played), inline=True)
            embed.add_field(name="High Score", value=str(high_score), inline=True)
            embed.add_field(name="Longest Snake", value=f"{longest_snake} units", inline=True)
            embed.add_field(name="Average Score", value=f"{avg_score:.1f}", inline=True)
            embed.add_field(name="Total Time", value=total_time_str, inline=True)
            embed.add_field(name="Avg. Time per Game", value=avg_time_str, inline=True)
            
            # Format difficulty breakdown
            difficulty_text = "\n".join([
                f"**{diff.capitalize()}:** {count}" 
                for diff, count in difficulty_counts.items() 
                if count > 0
            ])
            
            if not difficulty_text:
                difficulty_text = "No games played"
            
            embed.add_field(name="Difficulty Breakdown", value=difficulty_text, inline=False)
            
            embed.set_thumbnail(url=member.display_avatar.url)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"An error occurred: {e}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @commands.command(name="snake_leaderboard", aliases=["sneklb"])
    async def snake_leaderboard(self, ctx):
        """Display the Snake game leaderboard for this server."""
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
            game_data = await db_manager.get_game_data("snake", guild_id=ctx.guild.id)
            
            if not game_data or "players" not in game_data or not game_data["players"]:
                embed = discord.Embed(
                    title="📊 Snake Leaderboard",
                    description="No games have been played yet!",
                    color=discord.Color.green()
                )
                await ctx.send(embed=embed)
                return
            
            # Sort players by high score
            players = game_data["players"]
            sorted_players = sorted(players.items(), key=lambda x: x[1]["high_score"], reverse=True)
            
            # Create leaderboard embed
            embed = discord.Embed(
                title="📊 Snake Leaderboard",
                description="Top Snake players in this server:",
                color=discord.Color.gold()
            )
            
            # Add top players
            for i, (player_id, stats) in enumerate(sorted_players[:10], 1):
                try:
                    member = await ctx.guild.fetch_member(int(player_id))
                    name = member.display_name
                except:
                    name = f"User {player_id}"
                
                high_score = stats.get("high_score", 0)
                longest_snake = stats.get("longest_snake", 0)
                games_played = stats.get("games_played", 0)
                
                embed.add_field(
                    name=f"{i}. {name}",
                    value=f"**High Score:** {high_score}\n**Longest Snake:** {longest_snake}\n**Games:** {games_played}",
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
    
    def format_time(self, seconds):
        """Format time in seconds to mm:ss format."""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"

async def setup(bot):
    await bot.add_cog(Snake(bot))
