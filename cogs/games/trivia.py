import discord
from discord.ext import commands
import asyncio
import random
import json
import os
from typing import Dict, List, Optional
import html
import aiohttp

class TriviaGame(commands.Cog):
    """Advanced trivia game with categories, difficulty levels, and leaderboards."""
    
    def __init__(self, bot):
        self.bot = bot
        self.games = {}  # Store active games
        self.category = "games"  # For help command
        self.trivia_api_url = "https://opentdb.com/api.php"
        self.categories = {
            "general": 9,
            "books": 10,
            "film": 11,
            "music": 12,
            "tv": 14,
            "videogames": 15,
            "science": 17,
            "computers": 18,
            "math": 19,
            "sports": 21,
            "geography": 22,
            "history": 23,
            "animals": 27
        }
        self.difficulties = ["easy", "medium", "hard"]
        self.difficulty_emojis = {
            "easy": "🟢",
            "medium": "🟡",
            "hard": "🔴"
        }
        self.difficulty_points = {
            "easy": 10,
            "medium": 20,
            "hard": 30
        }
        self.session = aiohttp.ClientSession()
    
    def cog_unload(self):
        """Clean up when cog is unloaded."""
        asyncio.create_task(self.session.close())
    
    @commands.group(name="trivia", aliases=["t", "quiz"], invoke_without_command=True)
    async def trivia(self, ctx, difficulty: Optional[str] = "medium", category: Optional[str] = None):
        """
        Play a round of trivia with various categories and difficulties.
        
        Difficulty can be: easy, medium, or hard
        Category can be one of: general, books, film, music, tv, videogames, science, computers, math, sports, geography, history, animals
        
        Examples:
        !trivia - Plays a medium difficulty question from a random category
        !trivia easy - Plays an easy difficulty question from a random category
        !trivia hard geography - Plays a hard geography question
        """
        # Check if user is already in a game
        if ctx.author.id in self.games:
            embed = discord.Embed(
                title="❌ Game Already in Progress",
                description="You're already playing a trivia game! Finish that one first.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Validate difficulty
        if difficulty not in self.difficulties and difficulty in self.categories:
            # User probably put category first
            category, difficulty = difficulty, "medium"
        
        if difficulty not in self.difficulties:
            embed = discord.Embed(
                title="❌ Invalid Difficulty",
                description=f"Please choose a valid difficulty: {', '.join(self.difficulties)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Validate category if provided
        category_id = None
        if category:
            if category.lower() not in self.categories:
                embed = discord.Embed(
                    title="❌ Invalid Category",
                    description=f"Please choose a valid category: {', '.join(self.categories.keys())}",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            category_id = self.categories[category.lower()]
        
        # Start the game
        await self.start_trivia_game(ctx, difficulty, category_id, category)
    
    @trivia.command(name="categories", aliases=["cats", "list"])
    async def trivia_categories(self, ctx):
        """Show all available trivia categories."""
        embed = discord.Embed(
            title="🎮 Trivia Categories",
            description="Here are all available trivia categories:",
            color=discord.Color.blue()
        )
        
        categories_text = "\n".join([f"• **{cat.title()}**" for cat in self.categories.keys()])
        embed.add_field(name="Categories", value=categories_text, inline=False)
        
        embed.add_field(
            name="How to Play",
            value="Use `!trivia [difficulty] [category]` to start a game.\nExample: `!trivia hard geography`",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @trivia.command(name="leaderboard", aliases=["lb", "top"])
    async def trivia_leaderboard(self, ctx):
        """Show the trivia leaderboard for this server."""
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
        leaderboard_data = []
        try:
            # Get game data for this guild
            game_data = await db_manager.get_game_data("trivia", guild_id=ctx.guild.id)
            
            if not game_data or "leaderboard" not in game_data:
                embed = discord.Embed(
                    title="📊 Trivia Leaderboard",
                    description="No trivia games have been played yet!",
                    color=discord.Color.blue()
                )
                await ctx.send(embed=embed)
                return
            
            # Sort leaderboard by points
            leaderboard_data = sorted(
                game_data["leaderboard"].items(),
                key=lambda x: x[1],
                reverse=True
            )
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"An error occurred while fetching the leaderboard: {e}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Create embed
        embed = discord.Embed(
            title="📊 Trivia Leaderboard",
            description="Top trivia players in this server:",
            color=discord.Color.gold()
        )
        
        # Add leaderboard entries
        for i, (user_id, points) in enumerate(leaderboard_data[:10], 1):
            user = ctx.guild.get_member(int(user_id))
            username = user.name if user else "Unknown User"
            
            if i == 1:
                medal = "🥇"
            elif i == 2:
                medal = "🥈"
            elif i == 3:
                medal = "🥉"
            else:
                medal = f"{i}."
            
            embed.add_field(
                name=f"{medal} {username}",
                value=f"**{points}** points",
                inline=False
            )
        
        if not leaderboard_data:
            embed.description = "No trivia games have been played yet!"
        
        await ctx.send(embed=embed)
    
    async def start_trivia_game(self, ctx, difficulty, category_id=None, category_name=None):
        """Start a trivia game for a user."""
        # Create loading message
        embed = discord.Embed(
            title="🎮 Trivia Game",
            description="Fetching your question...",
            color=discord.Color.blue()
        )
        message = await ctx.send(embed=embed)
        
        # Mark user as in game
        self.games[ctx.author.id] = {"active": True}
        
        # Fetch question from API
        try:
            question_data = await self.get_trivia_question(difficulty, category_id)
            
            if not question_data:
                embed.title = "❌ Error"
                embed.description = "Failed to fetch a trivia question. Please try again later."
                embed.color = discord.Color.red()
                await message.edit(embed=embed)
                del self.games[ctx.author.id]
                return
        except Exception as e:
            embed.title = "❌ Error"
            embed.description = f"An error occurred: {e}"
            embed.color = discord.Color.red()
            await message.edit(embed=embed)
            del self.games[ctx.author.id]
            return
        
        # Extract question data
        question = html.unescape(question_data["question"])
        correct_answer = html.unescape(question_data["correct_answer"])
        incorrect_answers = [html.unescape(ans) for ans in question_data["incorrect_answers"]]
        
        # Format the question
        category_display = category_name.title() if category_name else question_data["category"]
        embed = discord.Embed(
            title=f"🎮 Trivia: {category_display}",
            description=f"{self.difficulty_emojis[difficulty]} **Difficulty:** {difficulty.title()}\n\n**Question:**\n{question}",
            color=discord.Color.blue()
        )
        
        # Add all answers in random order
        all_answers = incorrect_answers + [correct_answer]
        random.shuffle(all_answers)
        
        # Create answer mapping
        answer_letters = ["🇦", "🇧", "🇨", "🇩"]
        answer_mapping = {}
        answer_text = ""
        
        for i, answer in enumerate(all_answers):
            letter = answer_letters[i]
            answer_mapping[letter] = answer
            answer_text += f"{letter} {answer}\n"
        
        embed.add_field(name="Answers", value=answer_text, inline=False)
        embed.set_footer(text=f"You have 20 seconds to answer | Points: {self.difficulty_points[difficulty]}")
        
        # Update message
        await message.edit(embed=embed)
        
        # Add reactions for answers
        for letter in answer_letters[:len(all_answers)]:
            await message.add_reaction(letter)
        
        # Wait for answer
        try:
            def check(reaction, user):
                return (
                    user.id == ctx.author.id and
                    reaction.message.id == message.id and
                    str(reaction.emoji) in answer_mapping.keys()
                )
            
            reaction, user = await self.bot.wait_for("reaction_add", check=check, timeout=20.0)
            selected_answer = answer_mapping[str(reaction.emoji)]
            is_correct = selected_answer == correct_answer
            
            # Update game state
            self.games[ctx.author.id]["completed"] = True
            self.games[ctx.author.id]["correct"] = is_correct
            
            # Create result embed
            if is_correct:
                embed.color = discord.Color.green()
                embed.title = "✅ Correct Answer!"
                result_text = f"You got it right! The answer was **{correct_answer}**."
                
                # Award points
                points = self.difficulty_points[difficulty]
                await self.award_points(ctx.author.id, ctx.guild.id, points)
                result_text += f"\nYou earned **{points}** points!"
            else:
                embed.color = discord.Color.red()
                embed.title = "❌ Incorrect Answer!"
                result_text = f"Sorry, that's wrong. The correct answer was **{correct_answer}**."
            
            embed.description = result_text
            embed.remove_field(0)  # Remove answers field
            
            await message.edit(embed=embed)
            
        except asyncio.TimeoutError:
            # User didn't answer in time
            embed.color = discord.Color.orange()
            embed.title = "⏱️ Time's Up!"
            embed.description = f"You ran out of time! The correct answer was **{correct_answer}**."
            embed.remove_field(0)  # Remove answers field
            
            await message.edit(embed=embed)
        finally:
            # Clean up
            del self.games[ctx.author.id]
            try:
                await message.clear_reactions()
            except:
                pass
    
    async def get_trivia_question(self, difficulty, category_id=None):
        """Fetch a trivia question from the Open Trivia DB API."""
        params = {
            "amount": 1,
            "difficulty": difficulty,
            "type": "multiple"
        }
        
        if category_id:
            params["category"] = category_id
        
        try:
            async with self.session.get(self.trivia_api_url, params=params) as response:
                if response.status != 200:
                    return None
                
                data = await response.json()
                
                if data["response_code"] != 0 or not data["results"]:
                    return None
                
                return data["results"][0]
        except Exception as e:
            print(f"Error fetching trivia question: {e}")
            return None
    
    async def award_points(self, user_id, guild_id, points):
        """Award trivia points to a user."""
        # Get database manager
        db_manager = self.bot.get_cog("Utils").db_manager if hasattr(self.bot.get_cog("Utils"), "db_manager") else None
        
        if not db_manager:
            return
        
        try:
            # Get game data for this guild
            game_data = await db_manager.get_game_data("trivia", guild_id=guild_id)
            
            if not game_data:
                game_data = {"leaderboard": {}}
            
            if "leaderboard" not in game_data:
                game_data["leaderboard"] = {}
            
            # Update user's points
            user_id_str = str(user_id)
            if user_id_str in game_data["leaderboard"]:
                game_data["leaderboard"][user_id_str] += points
            else:
                game_data["leaderboard"][user_id_str] = points
            
            # Save updated data
            await db_manager.update_game_data("trivia", game_data, guild_id=guild_id)
            
            # Also award economy currency if economy system is enabled
            economy_cog = self.bot.get_cog("Economy")
            if economy_cog:
                await economy_cog.add_balance(user_id, guild_id, points // 2)
                
        except Exception as e:
            print(f"Error awarding trivia points: {e}")

async def setup(bot):
    await bot.add_cog(TriviaGame(bot))
