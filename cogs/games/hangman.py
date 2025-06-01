import discord
from discord.ext import commands
import asyncio
import random
import re
import string
from typing import Dict, List, Optional, Union

class Hangman(commands.Cog):
    """Play Hangman with the bot and earn coins!"""
    
    def __init__(self, bot):
        self.bot = bot
        self.category = "games"  # For help command
        self.games = {}  # Store active games
        self.currency_emoji = "🪙"
        
        # Word categories and lists
        self.word_categories = {
            "animals": ["elephant", "giraffe", "penguin", "dolphin", "kangaroo", "alligator", "rhinoceros", 
                        "squirrel", "hedgehog", "flamingo", "butterfly", "cheetah", "octopus", "panther"],
            "food": ["hamburger", "spaghetti", "chocolate", "pancakes", "sandwich", "quesadilla", "blueberry", 
                     "pineapple", "strawberry", "watermelon", "avocado", "cucumber", "broccoli"],
            "countries": ["australia", "canada", "germany", "brazil", "thailand", "egypt", "mexico", 
                          "netherlands", "switzerland", "singapore", "portugal", "argentina"],
            "sports": ["basketball", "volleyball", "swimming", "gymnastics", "skateboarding", "snowboarding", 
                       "surfing", "baseball", "football", "tennis", "hockey", "soccer", "cricket"],
            "movies": ["titanic", "avengers", "inception", "avatar", "frozen", "jaws", "ghostbusters", 
                       "matrix", "jumanji", "batman", "superman", "spiderman"]
        }
        
        # Hangman stages
        self.stages = [
            "```\n   _____ \n  |     | \n  |       \n  |       \n  |       \n__|__\n```",
            "```\n   _____ \n  |     | \n  |     O \n  |       \n  |       \n__|__\n```",
            "```\n   _____ \n  |     | \n  |     O \n  |     | \n  |       \n__|__\n```",
            "```\n   _____ \n  |     | \n  |     O \n  |    /| \n  |       \n__|__\n```",
            "```\n   _____ \n  |     | \n  |     O \n  |    /|\\ \n  |       \n__|__\n```",
            "```\n   _____ \n  |     | \n  |     O \n  |    /|\\ \n  |    /  \n__|__\n```",
            "```\n   _____ \n  |     | \n  |     O \n  |    /|\\ \n  |    / \\ \n__|__\n```"
        ]
    
    @commands.command(name="hangman", aliases=["hm"])
    async def hangman(self, ctx, category=None):
        """
        Play a game of Hangman.
        
        Examples:
        !hangman - Play with a random category
        !hangman animals - Play with animal words
        """
        # Check if user already has an active game
        if ctx.author.id in self.games:
            embed = discord.Embed(
                title="❌ Game Already In Progress",
                description="You already have an active Hangman game! Finish that one first.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Show categories if none specified
        if category is None:
            categories = list(self.word_categories.keys())
            category = random.choice(categories)
            category_message = f"Playing with a random category: **{category.title()}**"
        elif category.lower() in self.word_categories:
            category = category.lower()
            category_message = f"Playing with category: **{category.title()}**"
        else:
            # Invalid category
            categories = ", ".join([f"`{cat}`" for cat in self.word_categories.keys()])
            embed = discord.Embed(
                title="❌ Invalid Category",
                description=f"Choose from: {categories}, or leave blank for random",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Select a random word from the category
        word = random.choice(self.word_categories[category])
        
        # Initialize game state
        game_state = {
            "word": word,
            "guessed_letters": set(),
            "incorrect_guesses": 0,
            "message": None,
            "status": "active",
            "reward": len(set(word)) * 10  # Reward based on unique letters
        }
        
        self.games[ctx.author.id] = game_state
        
        # Create and send initial game state
        embed = self.create_game_embed(ctx.author, game_state, category_message)
        game_state["message"] = await ctx.send(embed=embed)
        
        # Game loop
        while game_state["status"] == "active":
            try:
                # Wait for a message from the player
                def check(m):
                    # Check if message is from the player and in the same channel
                    if m.author.id != ctx.author.id or m.channel.id != ctx.channel.id:
                        return False
                    
                    # Check if it's a valid guess (single letter or whole word)
                    content = m.content.lower()
                    return (
                        len(content) == 1 and content.isalpha() or
                        len(content) == len(game_state["word"])
                    )
                
                msg = await self.bot.wait_for("message", check=check, timeout=60.0)
                guess = msg.content.lower()
                
                # Process the guess
                await self.process_guess(ctx, game_state, guess)
                
                # Check game end conditions
                word_progress = "".join([letter if letter in game_state["guessed_letters"] else "_" for letter in game_state["word"]])
                
                if "_" not in word_progress:
                    # Player won
                    game_state["status"] = "won"
                    await self.end_game(ctx, game_state)
                elif game_state["incorrect_guesses"] >= len(self.stages) - 1:
                    # Player lost
                    game_state["status"] = "lost"
                    await self.end_game(ctx, game_state)
                
            except asyncio.TimeoutError:
                # Game timed out
                game_state["status"] = "timeout"
                await self.end_game(ctx, game_state)
                break
    
    async def process_guess(self, ctx, game_state, guess):
        """Process a guess in the Hangman game."""
        # Handle whole word guess
        if len(guess) > 1:
            if guess == game_state["word"]:
                # Correct word guess - reveal all letters
                for letter in game_state["word"]:
                    game_state["guessed_letters"].add(letter)
            else:
                # Incorrect word guess - counts as 2 strikes
                game_state["incorrect_guesses"] += 2
                
                # Prevent overflow
                if game_state["incorrect_guesses"] >= len(self.stages) - 1:
                    game_state["incorrect_guesses"] = len(self.stages) - 1
        
        # Handle single letter guess
        else:
            # Check if letter already guessed
            if guess in game_state["guessed_letters"]:
                embed = discord.Embed(
                    title="❌ Letter Already Guessed",
                    description=f"You already guessed the letter '{guess}'!",
                    color=discord.Color.orange()
                )
                await ctx.send(embed=embed, delete_after=3.0)
                return
            
            # Add to guessed letters
            game_state["guessed_letters"].add(guess)
            
            # Check if guess is correct
            if guess not in game_state["word"]:
                game_state["incorrect_guesses"] += 1
        
        # Update game display
        embed = self.create_game_embed(ctx.author, game_state)
        await game_state["message"].edit(embed=embed)
    
    def create_game_embed(self, player, game_state, category_message=None):
        """Create an embed displaying the current game state."""
        word = game_state["word"]
        guessed_letters = game_state["guessed_letters"]
        incorrect_guesses = game_state["incorrect_guesses"]
        
        # Create word display with guessed letters
        word_display = " ".join([letter if letter in guessed_letters else "_" for letter in word])
        
        # Create alphabet display
        alphabet = string.ascii_lowercase
        alphabet_display = ""
        for letter in alphabet:
            if letter in guessed_letters:
                if letter in word:
                    alphabet_display += f"🟢{letter} "  # Green for correct
                else:
                    alphabet_display += f"🔴{letter} "  # Red for incorrect
            else:
                alphabet_display += f"⚪{letter} "  # White for not guessed
        
        # Create embed
        embed = discord.Embed(
            title="🎮 Hangman Game",
            description=category_message if category_message else "Guess the word one letter at a time!",
            color=discord.Color.blue()
        )
        
        # Add current hangman stage
        embed.add_field(
            name="Hangman",
            value=self.stages[incorrect_guesses],
            inline=False
        )
        
        # Add word progress
        embed.add_field(
            name="Word",
            value=f"```{word_display}```",
            inline=False
        )
        
        # Add available letters
        embed.add_field(
            name="Letters",
            value=alphabet_display,
            inline=False
        )
        
        # Add game info
        embed.add_field(
            name="Status",
            value=f"**Incorrect Guesses:** {incorrect_guesses}/{len(self.stages)-1}\n**Reward:** {game_state['reward']} {self.currency_emoji}",
            inline=False
        )
        
        embed.set_footer(text=f"Playing as {player.name} • Type a letter to guess")
        
        return embed
    
    async def end_game(self, ctx, game_state):
        """End the Hangman game and award prizes if won."""
        word = game_state["word"]
        status = game_state["status"]
        
        # Create result embed
        if status == "won":
            embed = discord.Embed(
                title="🎉 You Won!",
                description=f"Congratulations! You correctly guessed the word: **{word}**",
                color=discord.Color.green()
            )
            
            # Award coins if won
            economy_cog = self.bot.get_cog("Economy")
            if economy_cog:
                reward = game_state["reward"]
                await economy_cog.add_balance(ctx.author.id, ctx.guild.id, reward)
                embed.add_field(
                    name="Reward",
                    value=f"You earned **{reward}** {self.currency_emoji} coins!",
                    inline=False
                )
            
        elif status == "lost":
            embed = discord.Embed(
                title="💀 You Lost!",
                description=f"You ran out of guesses! The word was: **{word}**",
                color=discord.Color.red()
            )
            
        else:  # timeout
            embed = discord.Embed(
                title="⏱️ Game Timed Out",
                description=f"You took too long to respond! The word was: **{word}**",
                color=discord.Color.orange()
            )
        
        # Add game stats
        incorrect = game_state["incorrect_guesses"]
        total_guesses = len(game_state["guessed_letters"])
        correct = total_guesses - incorrect
        
        embed.add_field(
            name="Game Stats",
            value=f"**Total Guesses:** {total_guesses}\n**Correct:** {correct}\n**Incorrect:** {incorrect}",
            inline=False
        )
        
        # Send result and update original message
        await ctx.send(embed=embed)
        
        # Cleanup
        del self.games[ctx.author.id]
    
    @commands.command(name="hangman_leaderboard", aliases=["hmlb"])
    async def hangman_leaderboard(self, ctx):
        """Display the Hangman leaderboard for this server."""
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
            game_data = await db_manager.get_game_data("hangman", guild_id=ctx.guild.id)
            
            if not game_data or "players" not in game_data or not game_data["players"]:
                embed = discord.Embed(
                    title="📊 Hangman Leaderboard",
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
                title="📊 Hangman Leaderboard",
                description="Top Hangman players in this server:",
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
                total_games = wins + losses
                win_rate = (wins / total_games * 100) if total_games > 0 else 0
                
                embed.add_field(
                    name=f"{i}. {name}",
                    value=f"**Wins:** {wins}\n**Losses:** {losses}\n**Win Rate:** {win_rate:.1f}%",
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
    
    @commands.command(name="hangman_stats", aliases=["hmstats"])
    async def hangman_stats(self, ctx, member: discord.Member = None):
        """
        View Hangman stats for yourself or another player.
        
        Examples:
        !hangman_stats - View your own stats
        !hangman_stats @user - View another user's stats
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
            game_data = await db_manager.get_game_data("hangman", guild_id=ctx.guild.id)
            
            if not game_data or "players" not in game_data or str(member.id) not in game_data["players"]:
                embed = discord.Embed(
                    title=f"📊 Hangman Stats for {member.display_name}",
                    description="This player hasn't played any Hangman games yet!",
                    color=discord.Color.blue()
                )
                embed.set_thumbnail(url=member.display_avatar.url)
                await ctx.send(embed=embed)
                return
            
            # Get player stats
            stats = game_data["players"][str(member.id)]
            wins = stats.get("wins", 0)
            losses = stats.get("losses", 0)
            total_games = wins + losses
            win_rate = (wins / total_games * 100) if total_games > 0 else 0
            
            # Create stats embed
            embed = discord.Embed(
                title=f"📊 Hangman Stats for {member.display_name}",
                color=discord.Color.blue()
            )
            
            embed.add_field(name="Games Played", value=str(total_games), inline=True)
            embed.add_field(name="Wins", value=str(wins), inline=True)
            embed.add_field(name="Losses", value=str(losses), inline=True)
            embed.add_field(name="Win Rate", value=f"{win_rate:.1f}%", inline=True)
            
            # Add favorite category if available
            if "categories" in stats:
                categories = stats["categories"]
                favorite = max(categories.items(), key=lambda x: x[1])
                embed.add_field(
                    name="Favorite Category",
                    value=f"{favorite[0].title()} ({favorite[1]} games)",
                    inline=True
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

async def setup(bot):
    await bot.add_cog(Hangman(bot))
