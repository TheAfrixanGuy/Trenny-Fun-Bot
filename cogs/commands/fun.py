import discord
from discord.ext import commands
import random
import asyncio
import aiohttp
import json
import time
from typing import Dict, List, Optional, Union
import re

class Fun(commands.Cog):
    """Fun commands to liven up your server!"""
    
    def __init__(self, bot):
        self.bot = bot
        self.category = "commands"  # For help command
        self.eight_ball_responses = [
            # Positive responses
            "It is certain.",
            "It is decidedly so.",
            "Without a doubt.",
            "Yes, definitely.",
            "You may rely on it.",
            "As I see it, yes.",
            "Most likely.",
            "Outlook good.",
            "Yes.",
            "Signs point to yes.",
            # Neutral responses
            "Reply hazy, try again.",
            "Ask again later.",
            "Better not tell you now.",
            "Cannot predict now.",
            "Concentrate and ask again.",
            # Negative responses
            "Don't count on it.",
            "My reply is no.",
            "My sources say no.",
            "Outlook not so good.",
            "Very doubtful."
        ]
        self.coin_sides = ["Heads", "Tails"]
        self.dice_pattern = re.compile(r'^(\d+)d(\d+)$')
    
    @commands.command(name="8ball", aliases=["eightball"])
    async def eight_ball(self, ctx, *, question: str = None):
        """
        Ask the magic 8-ball a question.
        
        Examples:
        !8ball Will I win the lottery?
        """
        if not question:
            embed = discord.Embed(
                title="❓ Missing Question",
                description="You need to ask the 8-ball a question!",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
            return
        
        # Select a random response
        response = random.choice(self.eight_ball_responses)
        
        # Determine color based on response type
        if response in self.eight_ball_responses[:10]:
            color = discord.Color.green()  # Positive
        elif response in self.eight_ball_responses[10:15]:
            color = discord.Color.gold()  # Neutral
        else:
            color = discord.Color.red()  # Negative
        
        # Create embed
        embed = discord.Embed(
            title="🎱 Magic 8-Ball",
            color=color
        )
        
        embed.add_field(
            name="Question",
            value=question,
            inline=False
        )
        
        embed.add_field(
            name="Answer",
            value=response,
            inline=False
        )
        
        # Dramatic effect with typing indicator
        async with ctx.typing():
            await asyncio.sleep(1.5)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="coinflip", aliases=["flip", "coin"])
    async def coinflip(self, ctx, times: int = 1):
        """
        Flip a coin one or more times.
        
        Examples:
        !coinflip - Flip once
        !coinflip 5 - Flip 5 times
        """
        # Validate input
        if times <= 0:
            embed = discord.Embed(
                title="❌ Invalid Input",
                description="Please enter a positive number.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        if times > 100:
            embed = discord.Embed(
                title="❌ Too Many Flips",
                description="You can only flip up to 100 coins at once.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Flip coins
        results = [random.choice(self.coin_sides) for _ in range(times)]
        
        # Count results
        heads = results.count("Heads")
        tails = results.count("Tails")
        
        # Create embed
        embed = discord.Embed(
            title="🪙 Coin Flip",
            description=f"Flipped {times} coin{'s' if times > 1 else ''}",
            color=discord.Color.gold()
        )
        
        # Display results
        if times == 1:
            embed.add_field(
                name="Result",
                value=f"**{results[0]}**!",
                inline=False
            )
        else:
            embed.add_field(
                name="Results",
                value=f"**Heads:** {heads} ({heads/times*100:.1f}%)\n**Tails:** {tails} ({tails/times*100:.1f}%)",
                inline=False
            )
            
            # Show all flips if there aren't too many
            if times <= 20:
                flip_text = ", ".join(results)
                embed.add_field(
                    name="All Flips",
                    value=flip_text,
                    inline=False
                )
        
        # Dramatic effect with typing indicator
        if times > 5:
            async with ctx.typing():
                await asyncio.sleep(1)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="dice", aliases=["roll"])
    async def dice(self, ctx, dice_notation: str = "1d6"):
        """
        Roll dice using standard dice notation.
        
        Examples:
        !dice - Roll 1d6 (one six-sided die)
        !dice 2d20 - Roll two twenty-sided dice
        !dice 3d4 - Roll three four-sided dice
        """
        # Parse dice notation
        match = self.dice_pattern.match(dice_notation.lower())
        
        if not match:
            embed = discord.Embed(
                title="❌ Invalid Dice Notation",
                description="Please use the format `NdM` where N is the number of dice and M is the number of sides.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        num_dice = int(match.group(1))
        sides = int(match.group(2))
        
        # Validate input
        if num_dice <= 0 or sides <= 0:
            embed = discord.Embed(
                title="❌ Invalid Input",
                description="Both the number of dice and sides must be positive numbers.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        if num_dice > 100:
            embed = discord.Embed(
                title="❌ Too Many Dice",
                description="You can only roll up to 100 dice at once.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        if sides > 1000:
            embed = discord.Embed(
                title="❌ Too Many Sides",
                description="Dice can have at most 1000 sides.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Roll dice
        rolls = [random.randint(1, sides) for _ in range(num_dice)]
        total = sum(rolls)
        
        # Create embed
        embed = discord.Embed(
            title="🎲 Dice Roll",
            description=f"Rolling **{dice_notation}**",
            color=discord.Color.blue()
        )
        
        # Display results
        if num_dice == 1:
            embed.add_field(
                name="Result",
                value=f"**{rolls[0]}**",
                inline=False
            )
        else:
            embed.add_field(
                name="Total",
                value=f"**{total}**",
                inline=False
            )
            
            # Show individual rolls if there aren't too many
            if num_dice <= 30:
                roll_text = ", ".join(map(str, rolls))
                embed.add_field(
                    name="Individual Rolls",
                    value=roll_text,
                    inline=False
                )
        
        # Dramatic effect with typing indicator
        if num_dice > 5:
            async with ctx.typing():
                await asyncio.sleep(1)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="rps_duel", aliases=["rpsduel"])
    async def rps_duel(self, ctx, member: discord.Member, bet: int = 0):
        """
        Challenge another user to Rock, Paper, Scissors with an optional bet.
        
        Examples:
        !rps_duel @user - Challenge without a bet
        !rps_duel @user 50 - Challenge with a 50 coin bet
        """
        # Validate target
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
                    description=f"You don't have enough coins for this bet!\nYour balance: **{challenger_balance}** 🪙\nRequired: **{bet}** 🪙",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            # Check target's balance
            target_balance = await economy_cog.get_balance(member.id, ctx.guild.id)
            
            if target_balance < bet:
                embed = discord.Embed(
                    title="❌ Insufficient Funds",
                    description=f"{member.mention} doesn't have enough coins for this bet!\nTheir balance: **{target_balance}** 🪙\nRequired: **{bet}** 🪙",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
        
        # Send challenge
        challenge_text = f"{ctx.author.mention} has challenged {member.mention} to Rock, Paper, Scissors!"
        if bet > 0:
            challenge_text += f"\nBet amount: **{bet}** 🪙"
        
        embed = discord.Embed(
            title="✂️ RPS Challenge",
            description=challenge_text,
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="Instructions",
            value=f"{member.mention}, do you accept this challenge?",
            inline=False
        )
        
        message = await ctx.send(embed=embed)
        await message.add_reaction("✅")  # Accept
        await message.add_reaction("❌")  # Decline
        
        # Wait for response
        def check(reaction, user):
            return (
                user.id == member.id and
                str(reaction.emoji) in ["✅", "❌"] and
                reaction.message.id == message.id
            )
        
        try:
            reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
            
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
            
            # Play the game
            await self.play_rps_duel(ctx, message, ctx.author, member, bet)
            
        except asyncio.TimeoutError:
            # Challenge timed out
            embed.description = f"{member.mention} didn't respond in time. Challenge expired."
            embed.color = discord.Color.orange()
            await message.edit(embed=embed)
            try:
                await message.clear_reactions()
            except:
                pass
    
    async def play_rps_duel(self, ctx, message, player1, player2, bet):
        """Handle RPS duel gameplay."""
        # Send DMs to both players asking for their choice
        choices = {"🪨": "Rock", "📄": "Paper", "✂️": "Scissors"}
        
        # Update message
        embed = discord.Embed(
            title="✂️ RPS Duel",
            description=f"Game between {player1.mention} and {player2.mention} has started!\nCheck your DMs to make your choice.",
            color=discord.Color.blue()
        )
        
        if bet > 0:
            embed.add_field(
                name="Bet",
                value=f"**{bet}** 🪙",
                inline=False
            )
        
        await message.edit(embed=embed)
        await message.clear_reactions()
        
        # Send DMs
        player1_choice = None
        player2_choice = None
        
        # Helper function to get choice via DM
        async def get_player_choice(player):
            try:
                embed = discord.Embed(
                    title="✂️ RPS Duel",
                    description=f"You're in a duel with {player2.name if player == player1 else player1.name}!\nMake your choice by clicking a reaction:",
                    color=discord.Color.blue()
                )
                
                dm = await player.send(embed=embed)
                await dm.add_reaction("🪨")  # Rock
                await dm.add_reaction("📄")  # Paper
                await dm.add_reaction("✂️")  # Scissors
                
                def check(reaction, user):
                    return (
                        user.id == player.id and
                        str(reaction.emoji) in choices and
                        reaction.message.id == dm.id
                    )
                
                reaction, _ = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
                choice = str(reaction.emoji)
                
                # Confirm choice
                confirm_embed = discord.Embed(
                    title="✂️ Choice Confirmed",
                    description=f"You chose **{choices[choice]}**!\nWaiting for your opponent...",
                    color=discord.Color.green()
                )
                await dm.edit(embed=confirm_embed)
                
                return choice
                
            except asyncio.TimeoutError:
                # Player didn't choose in time
                timeout_embed = discord.Embed(
                    title="⏱️ Time's Up",
                    description="You didn't make a choice in time.",
                    color=discord.Color.red()
                )
                await player.send(embed=timeout_embed)
                return None
            except discord.Forbidden:
                # Couldn't DM the player
                forbidden_embed = discord.Embed(
                    title="❌ DM Error",
                    description=f"Couldn't send a DM to {player.mention}. Make sure you have your DMs open for this server.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=forbidden_embed)
                return None
        
        # Get choices concurrently
        tasks = [
            asyncio.create_task(get_player_choice(player1)),
            asyncio.create_task(get_player_choice(player2))
        ]
        
        # Wait for both players to choose or timeout
        done, pending = await asyncio.wait(tasks, timeout=65.0, return_when=asyncio.ALL_COMPLETED)
        
        # Handle any pending tasks
        for task in pending:
            task.cancel()
        
        # Get results if both completed
        if len(done) == 2:
            results = [task.result() for task in done]
            player1_choice, player2_choice = results
        
        # Update the message with the results
        if player1_choice is None or player2_choice is None:
            # Someone timed out
            embed.description = "Game canceled because a player didn't make a choice in time."
            embed.color = discord.Color.red()
            await message.edit(embed=embed)
            return
        
        # Determine winner
        winner = None
        if player1_choice == player2_choice:
            result = "It's a tie!"
        elif (
            (player1_choice == "🪨" and player2_choice == "✂️") or
            (player1_choice == "📄" and player2_choice == "🪨") or
            (player1_choice == "✂️" and player2_choice == "📄")
        ):
            winner = player1
            result = f"{player1.mention} wins!"
        else:
            winner = player2
            result = f"{player2.mention} wins!"
        
        # Create result embed
        embed = discord.Embed(
            title="✂️ RPS Duel Results",
            color=discord.Color.gold() if winner is None else discord.Color.green()
        )
        
        embed.add_field(
            name=player1.display_name,
            value=f"Chose **{choices[player1_choice]}** {player1_choice}",
            inline=True
        )
        
        embed.add_field(
            name=player2.display_name,
            value=f"Chose **{choices[player2_choice]}** {player2_choice}",
            inline=True
        )
        
        embed.add_field(
            name="Result",
            value=result,
            inline=False
        )
        
        # Handle bet if there was one
        if bet > 0:
            economy_cog = self.bot.get_cog("Economy")
            if economy_cog and winner is not None:
                # Remove bet from both players
                await economy_cog.remove_balance(player1.id, ctx.guild.id, bet)
                await economy_cog.remove_balance(player2.id, ctx.guild.id, bet)
                
                # Add winnings to winner
                await economy_cog.add_balance(winner.id, ctx.guild.id, bet * 2)
                
                embed.add_field(
                    name="Bet",
                    value=f"{winner.mention} won **{bet * 2}** 🪙!",
                    inline=False
                )
            elif economy_cog and winner is None:
                # Tie - return bets
                embed.add_field(
                    name="Bet",
                    value="It's a tie! Bets have been returned.",
                    inline=False
                )
        
        await message.edit(embed=embed)
    
    @commands.command(name="choose", aliases=["pick"])
    async def choose(self, ctx, *options):
        """
        Let the bot choose between multiple options.
        
        Examples:
        !choose pizza pasta burger
        !choose "go to the movies" "stay home" "go to the park"
        """
        # Validate input
        if len(options) < 2:
            embed = discord.Embed(
                title="❌ Not Enough Options",
                description="Please provide at least two options to choose from.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Choose a random option
        choice = random.choice(options)
        
        # Create embed
        embed = discord.Embed(
            title="🤔 Let Me Choose",
            description=f"I choose...\n\n**{choice}**",
            color=discord.Color.blue()
        )
        
        # List all options
        options_text = "\n".join([f"- {option}" for option in options])
        embed.add_field(
            name="Options",
            value=options_text,
            inline=False
        )
        
        # Dramatic effect with typing indicator
        async with ctx.typing():
            await asyncio.sleep(1.5)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="joke")
    async def joke(self, ctx):
        """
        Get a random joke.
        
        Examples:
        !joke - Get a random joke
        """
        # API for jokes
        joke_apis = [
            "https://official-joke-api.appspot.com/random_joke",
            "https://icanhazdadjoke.com/"
        ]
        
        api_url = random.choice(joke_apis)
        
        async with aiohttp.ClientSession() as session:
            if "icanhazdadjoke" in api_url:
                headers = {'Accept': 'application/json'}
                async with session.get(api_url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        joke = data.get('joke', "Sorry, I couldn't think of a joke right now.")
                        
                        embed = discord.Embed(
                            title="😄 Dad Joke",
                            description=joke,
                            color=discord.Color.green()
                        )
                    else:
                        embed = discord.Embed(
                            title="❌ Error",
                            description="Failed to fetch a joke. Try again later.",
                            color=discord.Color.red()
                        )
            else:
                async with session.get(api_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        setup = data.get('setup', "")
                        punchline = data.get('punchline', "")
                        
                        if setup and punchline:
                            embed = discord.Embed(
                                title="😄 Joke",
                                description=f"{setup}",
                                color=discord.Color.green()
                            )
                            
                            # Wait for dramatic effect
                            msg = await ctx.send(embed=embed)
                            await asyncio.sleep(2)
                            
                            # Update with punchline
                            embed.description = f"{setup}\n\n{punchline}"
                            await msg.edit(embed=embed)
                            return
                        else:
                            embed = discord.Embed(
                                title="❌ Error",
                                description="Failed to fetch a joke. Try again later.",
                                color=discord.Color.red()
                            )
                    else:
                        embed = discord.Embed(
                            title="❌ Error",
                            description="Failed to fetch a joke. Try again later.",
                            color=discord.Color.red()
                        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name="fact")
    async def fact(self, ctx):
        """
        Get a random fact.
        
        Examples:
        !fact - Get a random fact
        """
        # API for facts
        fact_apis = [
            "https://uselessfacts.jsph.pl/random.json?language=en",
            "https://api.chucknorris.io/jokes/random"
        ]
        
        api_url = random.choice(fact_apis)
        
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if "chucknorris" in api_url:
                        fact = data.get('value', "Sorry, I couldn't think of a fact right now.")
                        title = "💪 Chuck Norris Fact"
                    else:
                        fact = data.get('text', "Sorry, I couldn't think of a fact right now.")
                        title = "🧠 Random Fact"
                    
                    embed = discord.Embed(
                        title=title,
                        description=fact,
                        color=discord.Color.blue()
                    )
                else:
                    embed = discord.Embed(
                        title="❌ Error",
                        description="Failed to fetch a fact. Try again later.",
                        color=discord.Color.red()
                    )
        
        await ctx.send(embed=embed)
    
    @commands.command(name="emojify")
    async def emojify(self, ctx, *, text: str):
        """
        Convert text to emoji letters.
        
        Examples:
        !emojify Hello World
        """
        # Convert each letter to regional indicator emoji
        emoji_mapping = {
            'a': '🇦', 'b': '🇧', 'c': '🇨', 'd': '🇩', 'e': '🇪',
            'f': '🇫', 'g': '🇬', 'h': '🇭', 'i': '🇮', 'j': '🇯',
            'k': '🇰', 'l': '🇱', 'm': '🇲', 'n': '🇳', 'o': '🇴',
            'p': '🇵', 'q': '🇶', 'r': '🇷', 's': '🇸', 't': '🇹',
            'u': '🇺', 'v': '🇻', 'w': '🇼', 'x': '🇽', 'y': '🇾',
            'z': '🇿', '0': '0️⃣', '1': '1️⃣', '2': '2️⃣', '3': '3️⃣',
            '4': '4️⃣', '5': '5️⃣', '6': '6️⃣', '7': '7️⃣', '8': '8️⃣',
            '9': '9️⃣', ' ': '  ', '!': '❗', '?': '❓'
        }
        
        # Convert text to lowercase for mapping
        text = text.lower()
        
        # Build emojified text
        emojified = ""
        for char in text:
            if char in emoji_mapping:
                emojified += emoji_mapping[char] + " "
            else:
                emojified += char + " "
        
        # Check if result is too long
        if len(emojified) > 2000:
            embed = discord.Embed(
                title="❌ Text Too Long",
                description="The emojified text is too long to display. Try a shorter message.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        await ctx.send(emojified)
    
    @commands.command(name="reverse")
    async def reverse(self, ctx, *, text: str):
        """
        Reverse text.
        
        Examples:
        !reverse Hello World
        """
        reversed_text = text[::-1]
        
        embed = discord.Embed(
            title="🔄 Reversed Text",
            description=reversed_text,
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="Original",
            value=text,
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name="countdown")
    async def countdown(self, ctx, seconds: int = 10):
        """
        Start a countdown timer.
        
        Examples:
        !countdown - Start a 10 second countdown
        !countdown 5 - Start a 5 second countdown
        """
        # Validate input
        if seconds <= 0:
            embed = discord.Embed(
                title="❌ Invalid Input",
                description="Please enter a positive number of seconds.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        if seconds > 60:
            embed = discord.Embed(
                title="❌ Time Too Long",
                description="The maximum countdown time is 60 seconds.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Create initial embed
        embed = discord.Embed(
            title="⏱️ Countdown",
            description=f"Time remaining: **{seconds}** seconds",
            color=discord.Color.blue()
        )
        
        message = await ctx.send(embed=embed)
        
        # Update countdown
        remaining = seconds
        while remaining > 0:
            await asyncio.sleep(1)
            remaining -= 1
            
            # Update every second for short countdowns, or every 5 seconds for longer ones
            if remaining <= 10 or remaining % 5 == 0:
                # Update embed
                embed.description = f"Time remaining: **{remaining}** seconds"
                
                # Change color for the last few seconds
                if remaining <= 3:
                    embed.color = discord.Color.red()
                elif remaining <= 5:
                    embed.color = discord.Color.orange()
                
                await message.edit(embed=embed)
        
        # Final message
        embed.title = "⏱️ Time's Up!"
        embed.description = "The countdown has ended!"
        embed.color = discord.Color.green()
        
        await message.edit(embed=embed)
        
        # Ping the user
        await ctx.send(f"{ctx.author.mention} Your countdown has ended!")

async def setup(bot):
    await bot.add_cog(Fun(bot))
