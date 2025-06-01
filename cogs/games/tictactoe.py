import discord
from discord.ext import commands
import asyncio
from typing import Dict, List, Optional, Union
import random
import time

class TicTacToeGame:
    """Represents a game of Tic Tac Toe."""
    
    def __init__(self, player1, player2, bet=0):
        self.player1 = player1  # X player
        self.player2 = player2  # O player
        self.bet = bet
        self.board = [None] * 9  # 3x3 board as a flat list
        self.current_turn = player1  # X goes first
        self.winner = None
        self.game_over = False
        self.message = None
        self.start_time = time.time()
        self.end_time = None
    
    def make_move(self, position, player):
        """Make a move on the board."""
        # Check if the game is over
        if self.game_over:
            return False
        
        # Check if it's the player's turn
        if player.id != self.current_turn.id:
            return False
        
        # Check if the position is valid
        if position < 0 or position > 8:
            return False
        
        # Check if the position is already taken
        if self.board[position] is not None:
            return False
        
        # Make the move
        self.board[position] = "X" if player.id == self.player1.id else "O"
        
        # Switch turns
        self.current_turn = self.player2 if player.id == self.player1.id else self.player1
        
        # Check for win or draw
        self.check_game_over()
        
        return True
    
    def check_game_over(self):
        """Check if the game is over (win or draw)."""
        # Check rows
        for i in range(0, 9, 3):
            if self.board[i] is not None and self.board[i] == self.board[i+1] == self.board[i+2]:
                self.winner = self.player1 if self.board[i] == "X" else self.player2
                self.game_over = True
                self.end_time = time.time()
                return
        
        # Check columns
        for i in range(3):
            if self.board[i] is not None and self.board[i] == self.board[i+3] == self.board[i+6]:
                self.winner = self.player1 if self.board[i] == "X" else self.player2
                self.game_over = True
                self.end_time = time.time()
                return
        
        # Check diagonals
        if self.board[0] is not None and self.board[0] == self.board[4] == self.board[8]:
            self.winner = self.player1 if self.board[0] == "X" else self.player2
            self.game_over = True
            self.end_time = time.time()
            return
        
        if self.board[2] is not None and self.board[2] == self.board[4] == self.board[6]:
            self.winner = self.player1 if self.board[2] == "X" else self.player2
            self.game_over = True
            self.end_time = time.time()
            return
        
        # Check for draw
        if None not in self.board:
            self.game_over = True
            self.end_time = time.time()
            return
    
    def get_board_display(self):
        """Get the current state of the board for display."""
        # Symbol mapping
        symbols = {
            None: "⬜",
            "X": "❌",
            "O": "⭕"
        }
        
        # Create the board string
        rows = []
        for i in range(0, 9, 3):
            row = [symbols[self.board[i]], symbols[self.board[i+1]], symbols[self.board[i+2]]]
            rows.append("".join(row))
        
        return "\n".join(rows)
    
    def get_elapsed_time(self):
        """Get the elapsed time for the game in seconds."""
        end = self.end_time if self.end_time else time.time()
        return end - self.start_time
    
    def format_time(self, seconds):
        """Format time in seconds to mm:ss format."""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"

class TicTacToe(commands.Cog):
    """Play Tic Tac Toe against other players with optional betting."""
    
    def __init__(self, bot):
        self.bot = bot
        self.category = "games"  # For help command
        self.games = {}  # Channel ID: game
        self.pending_challenges = {}  # User ID: (challenger, bet, message)
        self.currency_emoji = "🪙"
    
    @commands.command(name="tictactoe", aliases=["ttt"])
    async def tictactoe(self, ctx, member: discord.Member = None, bet: int = 0):
        """
        Challenge another player to a game of Tic Tac Toe with an optional bet.
        
        Examples:
        !tictactoe @user - Challenge with no bet
        !tictactoe @user 50 - Challenge with a 50 coin bet
        """
        # Check if there's already a game in this channel
        if ctx.channel.id in self.games:
            embed = discord.Embed(
                title="❌ Game Already In Progress",
                description="There's already a Tic Tac Toe game in progress in this channel.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Validate the target
        if member is None:
            embed = discord.Embed(
                title="❓ Who to Challenge?",
                description="You need to mention a user to challenge them to Tic Tac Toe.",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
            return
        
        if member.id == ctx.author.id:
            embed = discord.Embed(
                title="❌ Invalid Target",
                description="You can't challenge yourself!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        if member.bot:
            embed = discord.Embed(
                title="❌ Invalid Target",
                description="You can't challenge a bot!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Validate bet
        if bet < 0:
            embed = discord.Embed(
                title="❌ Invalid Bet",
                description="The bet amount cannot be negative.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Check if the member already has a pending challenge
        if member.id in self.pending_challenges:
            challenger, _, _ = self.pending_challenges[member.id]
            embed = discord.Embed(
                title="❌ Pending Challenge",
                description=f"{member.mention} already has a pending challenge from {challenger.mention}.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Check balances if there's a bet
        if bet > 0:
            economy_cog = self.bot.get_cog("Economy")
            if not economy_cog:
                embed = discord.Embed(
                    title="❌ Economy System Error",
                    description="Could not access the economy system.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            # Check challenger's balance
            challenger_balance = await economy_cog.get_balance(ctx.author.id, ctx.guild.id)
            
            if challenger_balance < bet:
                embed = discord.Embed(
                    title="❌ Insufficient Funds",
                    description=f"You don't have enough coins for this bet!\nYour balance: **{challenger_balance}** {self.currency_emoji}\nRequired: **{bet}** {self.currency_emoji}",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            # Check target's balance
            target_balance = await economy_cog.get_balance(member.id, ctx.guild.id)
            
            if target_balance < bet:
                embed = discord.Embed(
                    title="❌ Insufficient Funds",
                    description=f"{member.mention} doesn't have enough coins for this bet!\nTheir balance: **{target_balance}** {self.currency_emoji}\nRequired: **{bet}** {self.currency_emoji}",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
        
        # Create and send challenge
        embed = discord.Embed(
            title="🎮 Tic Tac Toe Challenge",
            description=f"{ctx.author.mention} has challenged {member.mention} to a game of Tic Tac Toe!",
            color=discord.Color.blue()
        )
        
        if bet > 0:
            embed.add_field(
                name="Bet",
                value=f"**{bet}** {self.currency_emoji}",
                inline=False
            )
        
        embed.add_field(
            name="Instructions",
            value=f"{member.mention}, do you accept this challenge?",
            inline=False
        )
        
        message = await ctx.send(embed=embed)
        await message.add_reaction("✅")  # Accept
        await message.add_reaction("❌")  # Decline
        
        # Store the challenge
        self.pending_challenges[member.id] = (ctx.author, bet, message)
        
        # Wait for response
        def check(reaction, user):
            return (
                user.id == member.id and
                str(reaction.emoji) in ["✅", "❌"] and
                reaction.message.id == message.id
            )
        
        try:
            reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
            
            # Remove the pending challenge
            del self.pending_challenges[member.id]
            
            if str(reaction.emoji) == "❌":
                # Challenge declined
                embed.description = f"{member.mention} declined the challenge."
                embed.color = discord.Color.red()
                await message.edit(embed=embed)
                try:
                    await message.clear_reactions()
                except:
                    pass
                return
            
            # Challenge accepted
            embed.description = f"{member.mention} accepted the challenge!"
            await message.edit(embed=embed)
            
            # Start the game
            await self.start_game(ctx, ctx.author, member, bet)
            
        except asyncio.TimeoutError:
            # Challenge timed out
            if member.id in self.pending_challenges:
                del self.pending_challenges[member.id]
            
            embed.description = f"{member.mention} didn't respond in time. Challenge expired."
            embed.color = discord.Color.orange()
            await message.edit(embed=embed)
            try:
                await message.clear_reactions()
            except:
                pass
    
    async def start_game(self, ctx, player1, player2, bet):
        """Start a new Tic Tac Toe game."""
        # Create new game
        game = TicTacToeGame(player1, player2, bet)
        self.games[ctx.channel.id] = game
        
        # Create initial embed
        embed = await self.create_game_embed(game)
        
        # Deduct bets if necessary
        if bet > 0:
            economy_cog = self.bot.get_cog("Economy")
            if economy_cog:
                await economy_cog.remove_balance(player1.id, ctx.guild.id, bet)
                await economy_cog.remove_balance(player2.id, ctx.guild.id, bet)
        
        # Send game board
        game.message = await ctx.send(embed=embed)
        
        # Add reaction controls
        for i in range(9):
            await game.message.add_reaction(f"{i+1}\u20e3")  # Keycap digit
        
        # Start game loop
        await self.game_loop(ctx, game)
    
    async def create_game_embed(self, game):
        """Create an embed for the Tic Tac Toe game."""
        # Determine color based on current turn or game state
        if game.game_over:
            if game.winner:
                color = discord.Color.green()
            else:
                color = discord.Color.gold()  # Draw
        else:
            color = discord.Color.blue()
        
        # Create embed
        embed = discord.Embed(
            title="🎮 Tic Tac Toe",
            description=game.get_board_display(),
            color=color
        )
        
        # Add player info
        embed.add_field(
            name="Players",
            value=(
                f"❌: {game.player1.mention}\n"
                f"⭕: {game.player2.mention}"
            ),
            inline=True
        )
        
        # Add bet info if applicable
        if game.bet > 0:
            embed.add_field(
                name="Bet",
                value=f"**{game.bet}** {self.currency_emoji}",
                inline=True
            )
        
        # Add time info
        embed.add_field(
            name="Time",
            value=game.format_time(game.get_elapsed_time()),
            inline=True
        )
        
        # Add status
        if game.game_over:
            if game.winner:
                status = f"🎉 {game.winner.mention} wins!"
            else:
                status = "🤝 It's a draw!"
        else:
            status = f"Current turn: {game.current_turn.mention} ({'❌' if game.current_turn.id == game.player1.id else '⭕'})"
        
        embed.add_field(
            name="Status",
            value=status,
            inline=False
        )
        
        # Add instructions
        if not game.game_over:
            embed.add_field(
                name="Instructions",
                value="Click a number to place your mark in that position.",
                inline=False
            )
            
            # Add position guide
            position_guide = (
                "Positions:\n"
                "1️⃣2️⃣3️⃣\n"
                "4️⃣5️⃣6️⃣\n"
                "7️⃣8️⃣9️⃣"
            )
            embed.add_field(
                name="Position Guide",
                value=position_guide,
                inline=False
            )
        
        return embed
    
    async def game_loop(self, ctx, game):
        """Main game loop for Tic Tac Toe."""
        while not game.game_over:
            # Wait for a move
            def check(reaction, user):
                return (
                    user.id == game.current_turn.id and
                    reaction.message.id == game.message.id and
                    str(reaction.emoji)[0] in "123456789" and
                    str(reaction.emoji)[1] == "\u20e3"  # Keycap
                )
            
            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=120.0, check=check)
                
                # Convert reaction to position (0-8)
                position = int(str(reaction.emoji)[0]) - 1
                
                # Make the move
                if game.make_move(position, user):
                    # Update the game board
                    embed = await self.create_game_embed(game)
                    await game.message.edit(embed=embed)
                
                # Remove the reaction
                try:
                    await game.message.remove_reaction(reaction.emoji, user)
                except:
                    pass
                
            except asyncio.TimeoutError:
                # Game timed out
                game.game_over = True
                game.end_time = time.time()
                
                embed = discord.Embed(
                    title="⏱️ Game Timeout",
                    description=f"Tic Tac Toe game has ended due to inactivity.",
                    color=discord.Color.orange()
                )
                await ctx.send(embed=embed)
                
                # Return bets if applicable
                if game.bet > 0:
                    economy_cog = self.bot.get_cog("Economy")
                    if economy_cog:
                        await economy_cog.add_balance(game.player1.id, ctx.guild.id, game.bet)
                        await economy_cog.add_balance(game.player2.id, ctx.guild.id, game.bet)
                        
                        embed.add_field(
                            name="Bets Returned",
                            value=f"The bet of **{game.bet}** {self.currency_emoji} has been returned to both players.",
                            inline=False
                        )
                
                # Clean up
                if ctx.channel.id in self.games:
                    del self.games[ctx.channel.id]
                
                try:
                    await game.message.clear_reactions()
                except:
                    pass
                
                return
        
        # Game is over, handle results
        await self.end_game(ctx, game)
    
    async def end_game(self, ctx, game):
        """Handle the end of a Tic Tac Toe game."""
        # Update final state
        embed = await self.create_game_embed(game)
        await game.message.edit(embed=embed)
        
        # Handle bets
        if game.bet > 0:
            economy_cog = self.bot.get_cog("Economy")
            if economy_cog:
                if game.winner:
                    # Winner gets double the bet
                    await economy_cog.add_balance(game.winner.id, ctx.guild.id, game.bet * 2)
                    
                    reward_embed = discord.Embed(
                        title="💰 Bet Result",
                        description=f"{game.winner.mention} won **{game.bet * 2}** {self.currency_emoji}!",
                        color=discord.Color.green()
                    )
                    await ctx.send(embed=reward_embed)
                else:
                    # Draw - return bets
                    await economy_cog.add_balance(game.player1.id, ctx.guild.id, game.bet)
                    await economy_cog.add_balance(game.player2.id, ctx.guild.id, game.bet)
                    
                    reward_embed = discord.Embed(
                        title="💰 Bet Result",
                        description=f"It's a draw! Both players get their **{game.bet}** {self.currency_emoji} back.",
                        color=discord.Color.gold()
                    )
                    await ctx.send(embed=reward_embed)
        
        # Update player stats
        await self.update_stats(game.player1.id, game.player2.id, ctx.guild.id, game)
        
        # Clean up
        try:
            await game.message.clear_reactions()
        except:
            pass
        
        if ctx.channel.id in self.games:
            del self.games[ctx.channel.id]
    
    async def update_stats(self, player1_id, player2_id, guild_id, game):
        """Update player stats in the database."""
        # Get database manager
        db_manager = self.bot.get_cog("Utils").db_manager if hasattr(self.bot.get_cog("Utils"), "db_manager") else None
        
        if not db_manager:
            return
        
        try:
            # Get game data
            game_data = await db_manager.get_game_data("tictactoe", guild_id=guild_id)
            
            # Initialize if doesn't exist
            if not game_data:
                game_data = {"players": {}}
            
            if "players" not in game_data:
                game_data["players"] = {}
            
            # Update stats for both players
            for player_id in [str(player1_id), str(player2_id)]:
                # Get or create player stats
                if player_id not in game_data["players"]:
                    game_data["players"][player_id] = {
                        "games": 0,
                        "wins": 0,
                        "losses": 0,
                        "draws": 0
                    }
                
                player_stats = game_data["players"][player_id]
                player_stats["games"] = player_stats.get("games", 0) + 1
                
                # Update result
                if game.winner:
                    if str(game.winner.id) == player_id:
                        player_stats["wins"] = player_stats.get("wins", 0) + 1
                    else:
                        player_stats["losses"] = player_stats.get("losses", 0) + 1
                else:
                    player_stats["draws"] = player_stats.get("draws", 0) + 1
            
            # Save game data
            await db_manager.update_game_data("tictactoe", game_data, guild_id=guild_id)
            
        except Exception as e:
            print(f"Error updating Tic Tac Toe stats: {e}")
    
    @commands.command(name="ttt_stats", aliases=["tttstat", "tttlb"])
    async def ttt_stats(self, ctx, member: discord.Member = None):
        """
        View Tic Tac Toe stats for yourself or another player.
        
        Examples:
        !ttt_stats - View your own stats
        !ttt_stats @user - View another user's stats
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
            game_data = await db_manager.get_game_data("tictactoe", guild_id=ctx.guild.id)
            
            if not game_data or "players" not in game_data or str(member.id) not in game_data["players"]:
                embed = discord.Embed(
                    title=f"📊 Tic Tac Toe Stats for {member.display_name}",
                    description="This player hasn't played any Tic Tac Toe games yet!",
                    color=discord.Color.blue()
                )
                embed.set_thumbnail(url=member.display_avatar.url)
                await ctx.send(embed=embed)
                return
            
            # Get player stats
            stats = game_data["players"][str(member.id)]
            games = stats.get("games", 0)
            wins = stats.get("wins", 0)
            losses = stats.get("losses", 0)
            draws = stats.get("draws", 0)
            
            # Calculate win rate
            win_rate = (wins / games * 100) if games > 0 else 0
            
            # Create stats embed
            embed = discord.Embed(
                title=f"📊 Tic Tac Toe Stats for {member.display_name}",
                color=discord.Color.blue()
            )
            
            embed.add_field(name="Games Played", value=str(games), inline=True)
            embed.add_field(name="Wins", value=str(wins), inline=True)
            embed.add_field(name="Losses", value=str(losses), inline=True)
            embed.add_field(name="Draws", value=str(draws), inline=True)
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
    
    @commands.command(name="ttt_leaderboard", aliases=["ttt_lb"])
    async def ttt_leaderboard(self, ctx):
        """Display the Tic Tac Toe leaderboard for this server."""
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
            game_data = await db_manager.get_game_data("tictactoe", guild_id=ctx.guild.id)
            
            if not game_data or "players" not in game_data or not game_data["players"]:
                embed = discord.Embed(
                    title="📊 Tic Tac Toe Leaderboard",
                    description="No games have been played yet!",
                    color=discord.Color.blue()
                )
                await ctx.send(embed=embed)
                return
            
            # Sort players by wins
            players = game_data["players"]
            sorted_players = sorted(players.items(), key=lambda x: (x[1].get("wins", 0), -x[1].get("losses", 0)), reverse=True)
            
            # Create leaderboard embed
            embed = discord.Embed(
                title="📊 Tic Tac Toe Leaderboard",
                description="Top Tic Tac Toe players in this server:",
                color=discord.Color.gold()
            )
            
            # Add top players
            for i, (player_id, stats) in enumerate(sorted_players[:10], 1):
                try:
                    member = await ctx.guild.fetch_member(int(player_id))
                    name = member.display_name
                except:
                    name = f"User {player_id}"
                
                games = stats.get("games", 0)
                wins = stats.get("wins", 0)
                losses = stats.get("losses", 0)
                draws = stats.get("draws", 0)
                win_rate = (wins / games * 100) if games > 0 else 0
                
                embed.add_field(
                    name=f"{i}. {name}",
                    value=f"**Wins:** {wins}\n**Games:** {games}\n**Win Rate:** {win_rate:.1f}%",
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
    await bot.add_cog(TicTacToe(bot))
