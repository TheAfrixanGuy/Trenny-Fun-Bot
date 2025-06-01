import discord
from discord.ext import commands
import random
import asyncio
from typing import Dict, List, Optional, Union
import time

class MemoryGame:
    """Represents a memory card matching game."""
    
    def __init__(self, player, difficulty="normal"):
        self.player = player
        self.difficulty = difficulty.lower()
        self.grid_size = self._get_grid_size()
        self.emoji_pairs = self._get_emoji_pairs()
        self.board = self._create_board()
        self.revealed = [[False for _ in range(self.grid_size[1])] for _ in range(self.grid_size[0])]
        self.first_pick = None
        self.moves = 0
        self.matches = 0
        self.start_time = None
        self.end_time = None
        self.message = None
    
    def _get_grid_size(self):
        """Get grid size based on difficulty."""
        sizes = {
            "easy": (4, 4),  # 16 cards (8 pairs)
            "normal": (4, 6),  # 24 cards (12 pairs)
            "hard": (6, 6),  # 36 cards (18 pairs)
            "expert": (6, 8)   # 48 cards (24 pairs)
        }
        return sizes.get(self.difficulty, (4, 6))  # Default to normal
    
    def _get_emoji_pairs(self):
        """Get emoji pairs for the game based on difficulty."""
        # Pool of emojis to use for the game
        emoji_pool = [
            "🍎", "🍌", "🍒", "🍓", "🍊", "🍉", "🍇", "🍍",
            "🥭", "🍋", "🥝", "🍅", "🥑", "🥔", "🥕", "🌽",
            "🥦", "🥬", "🥒", "🍆", "🧀", "🍞", "🥐", "🥯",
            "🥨", "🥞", "🧇", "🧁", "🍰", "🍦", "🍩", "🍪",
            "🍫", "🍬", "🍭", "🍿", "🧂", "☕", "🍵", "🥤",
            "🧊", "🧃", "🍷", "🍹", "🍺", "🥂", "🥃", "🧉"
        ]
        
        # Calculate number of pairs needed based on grid size
        num_pairs = (self.grid_size[0] * self.grid_size[1]) // 2
        
        # Ensure we don't request more pairs than available
        if num_pairs > len(emoji_pool):
            num_pairs = len(emoji_pool)
        
        # Select random emojis for the pairs
        selected_emojis = random.sample(emoji_pool, num_pairs)
        
        # Create pairs
        return selected_emojis * 2
    
    def _create_board(self):
        """Create and shuffle the game board."""
        # Shuffle the emoji pairs
        random.shuffle(self.emoji_pairs)
        
        # Create the board as a 2D grid
        board = []
        emoji_index = 0
        
        for row in range(self.grid_size[0]):
            board_row = []
            for col in range(self.grid_size[1]):
                if emoji_index < len(self.emoji_pairs):
                    board_row.append(self.emoji_pairs[emoji_index])
                    emoji_index += 1
                else:
                    # In case we somehow run out of emojis
                    board_row.append("❓")
            board.append(board_row)
        
        return board
    
    def get_display_board(self):
        """Get the current state of the board for display."""
        display = []
        
        for row in range(self.grid_size[0]):
            display_row = []
            for col in range(self.grid_size[1]):
                if self.revealed[row][col]:
                    # Card is revealed
                    display_row.append(self.board[row][col])
                else:
                    # Card is hidden
                    display_row.append("🎴")
            display.append(display_row)
        
        return display
    
    def is_valid_pick(self, row, col):
        """Check if the selected card is a valid pick."""
        # Check if indices are within bounds
        if row < 0 or row >= self.grid_size[0] or col < 0 or col >= self.grid_size[1]:
            return False
        
        # Check if card is already revealed
        if self.revealed[row][col]:
            return False
        
        return True
    
    def make_pick(self, row, col):
        """Make a card selection."""
        if not self.is_valid_pick(row, col):
            return False
        
        # Start the timer on first move
        if self.moves == 0:
            self.start_time = time.time()
        
        # Increment moves
        self.moves += 1
        
        # Reveal the card
        self.revealed[row][col] = True
        
        # Handle first or second pick
        if self.first_pick is None:
            # This is the first pick
            self.first_pick = (row, col)
            return True
        else:
            # This is the second pick
            first_row, first_col = self.first_pick
            
            # Check if it's a match
            if self.board[first_row][first_col] == self.board[row][col]:
                # It's a match!
                self.matches += 1
                self.first_pick = None
                
                # Check if game is over
                if self.matches == (self.grid_size[0] * self.grid_size[1]) // 2:
                    self.end_time = time.time()
                
                return True
            else:
                # Not a match, will need to hide both cards after a delay
                return False
    
    def hide_picks(self):
        """Hide the two picked cards that didn't match."""
        if self.first_pick:
            row, col = self.first_pick
            self.revealed[row][col] = False
            self.first_pick = None
    
    def get_elapsed_time(self):
        """Get the elapsed time for the game."""
        if self.start_time is None:
            return 0
        
        end = self.end_time if self.end_time else time.time()
        return end - self.start_time
    
    def get_score(self):
        """Calculate score based on performance."""
        if not self.end_time:
            return 0
        
        # Base scores for each difficulty
        difficulty_base = {
            "easy": 100,
            "normal": 200,
            "hard": 300,
            "expert": 400
        }
        
        # Get base score
        base_score = difficulty_base.get(self.difficulty, 200)
        
        # Calculate time bonus - faster is better
        time_taken = self.get_elapsed_time()
        time_factor = max(0.5, min(2.0, 120 / max(1, time_taken)))
        
        # Calculate move efficiency bonus
        min_possible_moves = (self.grid_size[0] * self.grid_size[1]) // 2  # Perfect memory
        move_efficiency = min_possible_moves / max(1, self.moves / 2)  # Divide moves by 2 since each match requires 2 moves
        move_factor = max(0.5, min(1.5, move_efficiency))
        
        # Calculate final score
        score = int(base_score * time_factor * move_factor)
        
        return score
    
    def get_reward(self):
        """Calculate coin reward based on score."""
        score = self.get_score()
        
        # Base reward is proportional to score but capped
        base_reward = min(500, score // 4)
        
        # Difficulty bonus
        difficulty_bonus = {
            "easy": 1.0,
            "normal": 1.2,
            "hard": 1.5,
            "expert": 2.0
        }
        
        multiplier = difficulty_bonus.get(self.difficulty, 1.0)
        
        return int(base_reward * multiplier)
    
    def format_time(self, seconds):
        """Format time in seconds to mm:ss format."""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"

class Memory(commands.Cog):
    """Memory card matching game. Match pairs of cards to win!"""
    
    def __init__(self, bot):
        self.bot = bot
        self.category = "games"  # For help command
        self.games = {}  # User ID: game
        self.currency_emoji = "🪙"
        self.reaction_controls = [
            "1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣",
            "🇦", "🇧", "🇨", "🇩", "🇪", "🇫", "🇬", "🇭"
        ]
    
    @commands.command(name="memory", aliases=["memo", "match"])
    async def memory(self, ctx, difficulty: str = "normal"):
        """
        Play a memory card matching game.
        
        Examples:
        !memory - Play with normal difficulty
        !memory easy - Play on easy difficulty
        !memory hard - Play on hard difficulty
        !memory expert - Play on expert difficulty
        """
        # Check if user already has an active game
        if ctx.author.id in self.games:
            embed = discord.Embed(
                title="❌ Game Already In Progress",
                description="You already have an active Memory game! Finish that one first.",
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
        game = MemoryGame(ctx.author, difficulty)
        self.games[ctx.author.id] = game
        
        # Create initial embed
        embed = await self.create_game_embed(game)
        
        # Send embed with instructions
        instructions = discord.Embed(
            title="🎮 Memory Game Instructions",
            description=(
                "Match pairs of cards by selecting two cards at a time.\n"
                "Use the row letter and column number reactions to select a card.\n"
                "For example, to select the card at row B, column 3, click 🇧 then 3️⃣.\n\n"
                "Game will start in 5 seconds..."
            ),
            color=discord.Color.blue()
        )
        await ctx.send(embed=instructions)
        await asyncio.sleep(5)
        
        # Send game board
        game.message = await ctx.send(embed=embed)
        
        # Add row selection reactions
        for i in range(game.grid_size[0]):
            await game.message.add_reaction(self.reaction_controls[i + 8])  # Row letters start at index 8
        
        # Start game loop
        await self.game_loop(ctx, game)
    
    async def create_game_embed(self, game):
        """Create an embed for the Memory game."""
        # Get current board state
        display_board = game.get_display_board()
        
        # Create board display
        board_text = ""
        
        # Add column headers (numbers)
        board_text += "   "
        for col in range(game.grid_size[1]):
            board_text += f"{col+1}️⃣ "
        board_text += "\n"
        
        # Add rows with row headers (letters)
        for row in range(game.grid_size[0]):
            board_text += f"{self.reaction_controls[row+8]} "  # Row letters start at index 8
            for col in range(game.grid_size[1]):
                board_text += f"{display_board[row][col]} "
            board_text += "\n"
        
        # Create embed
        embed = discord.Embed(
            title=f"🧠 Memory Game - {game.difficulty.capitalize()}",
            description=board_text,
            color=discord.Color.blue()
        )
        
        # Add game stats
        embed.add_field(
            name="Stats",
            value=(
                f"**Moves:** {game.moves}\n"
                f"**Matches:** {game.matches}/{(game.grid_size[0] * game.grid_size[1]) // 2}\n"
                f"**Time:** {game.format_time(game.get_elapsed_time())}"
            ),
            inline=True
        )
        
        # Add selection status
        if game.first_pick is None:
            status = "Select your first card (row → column)"
        else:
            first_row, first_col = game.first_pick
            row_letter = self.reaction_controls[first_row + 8]
            status = f"First card: {row_letter}{first_col+1} ({game.board[first_row][first_col]})\nSelect your second card"
        
        embed.add_field(
            name="Selection",
            value=status,
            inline=True
        )
        
        return embed
    
    async def game_loop(self, ctx, game):
        """Handle the memory game loop."""
        current_stage = "row"  # Start by selecting a row
        selected_row = None
        
        while ctx.author.id in self.games and not game.end_time:
            # Wait for player's action
            def check(reaction, user):
                # Check if it's the player reacting
                if user.id != ctx.author.id or reaction.message.id != game.message.id:
                    return False
                
                # Check reaction based on current selection stage
                if current_stage == "row":
                    # Check if it's a valid row selection
                    row_index = self.reaction_controls.index(str(reaction.emoji)) - 8 if str(reaction.emoji) in self.reaction_controls[8:] else -1
                    return 0 <= row_index < game.grid_size[0]
                else:  # column stage
                    # Check if it's a valid column selection
                    col_index = self.reaction_controls.index(str(reaction.emoji)) if str(reaction.emoji) in self.reaction_controls[:8] else -1
                    return 0 <= col_index < game.grid_size[1]
            
            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=120.0, check=check)
                
                # Process the selection
                if current_stage == "row":
                    # Handle row selection
                    selected_row = self.reaction_controls.index(str(reaction.emoji)) - 8
                    
                    # Move to column selection
                    current_stage = "column"
                    
                    # Add column selection reactions
                    for i in range(game.grid_size[1]):
                        await game.message.add_reaction(self.reaction_controls[i])
                    
                    # Remove row reactions to avoid confusion
                    try:
                        for i in range(game.grid_size[0]):
                            await game.message.remove_reaction(self.reaction_controls[i + 8], self.bot.user)
                    except:
                        pass
                    
                else:  # column stage
                    # Handle column selection
                    selected_col = self.reaction_controls.index(str(reaction.emoji))
                    
                    # Make the pick
                    if game.is_valid_pick(selected_row, selected_col):
                        match_result = game.make_pick(selected_row, selected_col)
                        
                        # Update the board
                        embed = await self.create_game_embed(game)
                        await game.message.edit(embed=embed)
                        
                        if not match_result and game.first_pick is None:
                            # Not a match, wait then hide the cards
                            await asyncio.sleep(1.5)
                            game.hide_picks()
                            
                            # Update the board again
                            embed = await self.create_game_embed(game)
                            await game.message.edit(embed=embed)
                    
                    # Reset to row selection
                    current_stage = "row"
                    
                    # Clean up reactions
                    try:
                        await game.message.clear_reactions()
                        # Add row selection reactions again
                        for i in range(game.grid_size[0]):
                            await game.message.add_reaction(self.reaction_controls[i + 8])
                    except:
                        pass
                
                # Remove the player's reaction
                try:
                    await game.message.remove_reaction(reaction.emoji, ctx.author)
                except:
                    pass
                
                # Check if game is over
                if game.end_time:
                    await self.end_game(ctx, game)
                    break
                
            except asyncio.TimeoutError:
                # Player took too long
                embed = discord.Embed(
                    title="⏱️ Game Timeout",
                    description="Memory game has ended due to inactivity.",
                    color=discord.Color.orange()
                )
                await ctx.send(embed=embed)
                
                # Clean up
                if ctx.author.id in self.games:
                    del self.games[ctx.author.id]
                
                try:
                    await game.message.clear_reactions()
                except:
                    pass
                
                break
    
    async def end_game(self, ctx, game):
        """Handle the end of a Memory game."""
        # Calculate final stats
        score = game.get_score()
        reward = game.get_reward()
        time_taken = game.format_time(game.get_elapsed_time())
        
        # Award coins
        economy_cog = self.bot.get_cog("Economy")
        if economy_cog:
            await economy_cog.add_balance(ctx.author.id, ctx.guild.id, reward)
        
        # Create result embed
        embed = discord.Embed(
            title="🎮 Memory Game Complete!",
            description=f"Congratulations {ctx.author.mention}! You've completed the Memory game!",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="Final Stats",
            value=(
                f"**Difficulty:** {game.difficulty.capitalize()}\n"
                f"**Moves:** {game.moves}\n"
                f"**Time:** {time_taken}\n"
                f"**Score:** {score}"
            ),
            inline=True
        )
        
        embed.add_field(
            name="Reward",
            value=f"You earned **{reward}** {self.currency_emoji}!",
            inline=True
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
            game_data = await db_manager.get_game_data("memory", guild_id=guild_id)
            
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
                    "best_score": 0,
                    "fastest_time": float('inf'),
                    "total_score": 0,
                    "total_moves": 0,
                    "difficulty_counts": {"easy": 0, "normal": 0, "hard": 0, "expert": 0}
                }
            
            # Update stats
            player_stats = game_data["players"][player_id]
            player_stats["games_played"] = player_stats.get("games_played", 0) + 1
            player_stats["best_score"] = max(player_stats.get("best_score", 0), game.get_score())
            
            # Update fastest time if this game was completed
            if game.end_time:
                time_taken = game.get_elapsed_time()
                if time_taken < player_stats.get("fastest_time", float('inf')):
                    player_stats["fastest_time"] = time_taken
            
            player_stats["total_score"] = player_stats.get("total_score", 0) + game.get_score()
            player_stats["total_moves"] = player_stats.get("total_moves", 0) + game.moves
            
            # Initialize difficulty counts if not present
            if "difficulty_counts" not in player_stats:
                player_stats["difficulty_counts"] = {"easy": 0, "normal": 0, "hard": 0, "expert": 0}
            
            # Update difficulty count
            player_stats["difficulty_counts"][game.difficulty] = player_stats["difficulty_counts"].get(game.difficulty, 0) + 1
            
            # Save game data
            await db_manager.update_game_data("memory", game_data, guild_id=guild_id)
            
        except Exception as e:
            print(f"Error updating memory stats: {e}")
    
    @commands.command(name="memory_stats", aliases=["memostats"])
    async def memory_stats(self, ctx, member: discord.Member = None):
        """
        View Memory game stats for yourself or another player.
        
        Examples:
        !memory_stats - View your own stats
        !memory_stats @user - View another user's stats
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
            game_data = await db_manager.get_game_data("memory", guild_id=ctx.guild.id)
            
            if not game_data or "players" not in game_data or str(member.id) not in game_data["players"]:
                embed = discord.Embed(
                    title=f"📊 Memory Stats for {member.display_name}",
                    description="This player hasn't played any Memory games yet!",
                    color=discord.Color.blue()
                )
                embed.set_thumbnail(url=member.display_avatar.url)
                await ctx.send(embed=embed)
                return
            
            # Get player stats
            stats = game_data["players"][str(member.id)]
            games_played = stats.get("games_played", 0)
            best_score = stats.get("best_score", 0)
            
            # Format fastest time
            fastest_time = stats.get("fastest_time", float('inf'))
            if fastest_time == float('inf'):
                fastest_time_str = "N/A"
            else:
                minutes = int(fastest_time // 60)
                seconds = int(fastest_time % 60)
                fastest_time_str = f"{minutes:02d}:{seconds:02d}"
            
            avg_score = stats.get("total_score", 0) / max(1, games_played)
            avg_moves = stats.get("total_moves", 0) / max(1, games_played)
            
            # Get difficulty breakdown
            difficulty_counts = stats.get("difficulty_counts", {"easy": 0, "normal": 0, "hard": 0, "expert": 0})
            
            # Create stats embed
            embed = discord.Embed(
                title=f"📊 Memory Stats for {member.display_name}",
                color=discord.Color.blue()
            )
            
            embed.add_field(name="Games Played", value=str(games_played), inline=True)
            embed.add_field(name="Best Score", value=str(best_score), inline=True)
            embed.add_field(name="Fastest Time", value=fastest_time_str, inline=True)
            embed.add_field(name="Avg. Score", value=f"{avg_score:.1f}", inline=True)
            embed.add_field(name="Avg. Moves", value=f"{avg_moves:.1f}", inline=True)
            
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
    
    @commands.command(name="memory_leaderboard", aliases=["memolb"])
    async def memory_leaderboard(self, ctx):
        """Display the Memory game leaderboard for this server."""
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
            game_data = await db_manager.get_game_data("memory", guild_id=ctx.guild.id)
            
            if not game_data or "players" not in game_data or not game_data["players"]:
                embed = discord.Embed(
                    title="📊 Memory Leaderboard",
                    description="No games have been played yet!",
                    color=discord.Color.blue()
                )
                await ctx.send(embed=embed)
                return
            
            # Sort players by best score
            players = game_data["players"]
            sorted_players = sorted(players.items(), key=lambda x: x[1]["best_score"], reverse=True)
            
            # Create leaderboard embed
            embed = discord.Embed(
                title="📊 Memory Leaderboard",
                description="Top Memory game players in this server:",
                color=discord.Color.gold()
            )
            
            # Add top players
            for i, (player_id, stats) in enumerate(sorted_players[:10], 1):
                try:
                    member = await ctx.guild.fetch_member(int(player_id))
                    name = member.display_name
                except:
                    name = f"User {player_id}"
                
                games_played = stats.get("games_played", 0)
                best_score = stats.get("best_score", 0)
                
                # Format fastest time
                fastest_time = stats.get("fastest_time", float('inf'))
                if fastest_time == float('inf'):
                    fastest_time_str = "N/A"
                else:
                    minutes = int(fastest_time // 60)
                    seconds = int(fastest_time % 60)
                    fastest_time_str = f"{minutes:02d}:{seconds:02d}"
                
                embed.add_field(
                    name=f"{i}. {name}",
                    value=f"**Best Score:** {best_score}\n**Games:** {games_played}\n**Fastest Time:** {fastest_time_str}",
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
    await bot.add_cog(Memory(bot))
