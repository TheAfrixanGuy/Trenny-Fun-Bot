import discord
from discord.ext import commands
import random
import asyncio
from typing import Dict, List, Optional, Union

class Card:
    """Represents a playing card."""
    def __init__(self, suit, value):
        self.suit = suit
        self.value = value
    
    @property
    def display_name(self):
        """Get the display name of the card."""
        suit_symbols = {
            "hearts": "♥️",
            "diamonds": "♦️",
            "clubs": "♣️",
            "spades": "♠️"
        }
        
        value_names = {
            1: "A",
            11: "J",
            12: "Q",
            13: "K"
        }
        
        value_str = value_names.get(self.value, str(self.value))
        return f"{value_str}{suit_symbols[self.suit]}"
    
    @property
    def blackjack_value(self):
        """Get the value of the card in Blackjack."""
        if self.value == 1:
            return 11  # Ace is initially worth 11
        elif self.value >= 10:
            return 10  # Face cards are worth 10
        else:
            return self.value

class Deck:
    """Represents a deck of cards."""
    def __init__(self):
        self.cards = []
        self.build()
    
    def build(self):
        """Build a new deck of cards."""
        suits = ["hearts", "diamonds", "clubs", "spades"]
        values = range(1, 14)  # 1 = Ace, 11 = Jack, 12 = Queen, 13 = King
        
        self.cards = [Card(suit, value) for suit in suits for value in values]
    
    def shuffle(self):
        """Shuffle the deck."""
        random.shuffle(self.cards)
    
    def deal(self):
        """Deal a card from the deck."""
        if not self.cards:
            self.build()
            self.shuffle()
        
        return self.cards.pop()

class BlackjackGame:
    """Represents a game of Blackjack."""
    def __init__(self, player, bet):
        self.player = player
        self.bet = bet
        self.deck = Deck()
        self.deck.shuffle()
        
        self.player_hand = []
        self.dealer_hand = []
        
        # Deal initial cards
        self.player_hand.append(self.deck.deal())
        self.dealer_hand.append(self.deck.deal())
        self.player_hand.append(self.deck.deal())
        self.dealer_hand.append(self.deck.deal())
        
        self.player_stood = False
        self.game_over = False
        self.result = None
        self.message = None
    
    def get_hand_value(self, hand):
        """Calculate the value of a hand in Blackjack."""
        value = sum(card.blackjack_value for card in hand)
        
        # Adjust for Aces
        aces = sum(1 for card in hand if card.value == 1)
        while value > 21 and aces > 0:
            value -= 10  # Convert an Ace from 11 to 1
            aces -= 1
        
        return value
    
    def is_blackjack(self, hand):
        """Check if a hand is a natural Blackjack (Ace + 10-value card)."""
        if len(hand) != 2:
            return False
        
        return (
            (hand[0].value == 1 and hand[1].blackjack_value >= 10) or
            (hand[1].value == 1 and hand[0].blackjack_value >= 10)
        )
    
    def check_game_over(self):
        """Check if the game is over and determine the result."""
        player_value = self.get_hand_value(self.player_hand)
        dealer_value = self.get_hand_value(self.dealer_hand)
        
        # Check for blackjack
        player_blackjack = self.is_blackjack(self.player_hand)
        dealer_blackjack = self.is_blackjack(self.dealer_hand)
        
        if player_blackjack and dealer_blackjack:
            self.result = "push"  # Both have blackjack, it's a tie
            self.game_over = True
        elif player_blackjack:
            self.result = "blackjack"  # Player has blackjack, pays 3:2
            self.game_over = True
        elif dealer_blackjack:
            self.result = "dealer_blackjack"  # Dealer has blackjack, player loses
            self.game_over = True
        elif player_value > 21:
            self.result = "bust"  # Player busts
            self.game_over = True
        elif self.player_stood:
            # Player stands, now dealer plays
            if dealer_value > 21:
                self.result = "dealer_bust"  # Dealer busts
            elif dealer_value > player_value:
                self.result = "dealer_wins"  # Dealer has higher value
            elif dealer_value < player_value:
                self.result = "player_wins"  # Player has higher value
            else:
                self.result = "push"  # It's a tie
            
            self.game_over = True
        
        return self.game_over
    
    def player_hit(self):
        """Player takes another card."""
        if self.game_over or self.player_stood:
            return False
        
        self.player_hand.append(self.deck.deal())
        return True
    
    def player_stand(self):
        """Player stands (stops taking cards)."""
        if self.game_over or self.player_stood:
            return False
        
        self.player_stood = True
        
        # Dealer plays
        dealer_value = self.get_hand_value(self.dealer_hand)
        
        # Dealer must hit until they have at least 17
        while dealer_value < 17:
            self.dealer_hand.append(self.deck.deal())
            dealer_value = self.get_hand_value(self.dealer_hand)
        
        return True
    
    def calculate_reward(self):
        """Calculate the reward based on the game result."""
        if self.result == "blackjack":
            return int(self.bet * 2.5)  # Blackjack pays 3:2 (bet + 1.5x bet)
        elif self.result in ["player_wins", "dealer_bust"]:
            return self.bet * 2  # Regular win pays 1:1 (bet + bet)
        elif self.result == "push":
            return self.bet  # Push returns the original bet
        else:
            return 0  # Player loses their bet
    
    def get_player_display(self, hide_dealer_card=True):
        """Get a string representation of the player's hand."""
        cards = [card.display_name for card in self.player_hand]
        value = self.get_hand_value(self.player_hand)
        
        # Check for blackjack
        blackjack_text = " (Blackjack!)" if self.is_blackjack(self.player_hand) else ""
        
        return f"Cards: {' '.join(cards)}\nValue: {value}{blackjack_text}"
    
    def get_dealer_display(self, hide_dealer_card=True):
        """Get a string representation of the dealer's hand."""
        if hide_dealer_card and not self.game_over and not self.player_stood:
            # Show only the first card
            cards = [self.dealer_hand[0].display_name, "🂠"]
            value = "?"
        else:
            # Show all cards
            cards = [card.display_name for card in self.dealer_hand]
            value = self.get_hand_value(self.dealer_hand)
            
            # Check for blackjack
            blackjack_text = " (Blackjack!)" if self.is_blackjack(self.dealer_hand) else ""
            value = f"{value}{blackjack_text}"
        
        return f"Cards: {' '.join(cards)}\nValue: {value}"

class Blackjack(commands.Cog):
    """Play Blackjack and bet your coins!"""
    
    def __init__(self, bot):
        self.bot = bot
        self.category = "games"  # For help command
        self.games = {}  # User ID: game
        self.currency_emoji = "🪙"
    
    @commands.command(name="blackjack", aliases=["bj", "21"])
    async def blackjack(self, ctx, bet: int = None):
        """
        Play a game of Blackjack against the dealer.
        
        Examples:
        !blackjack - Play with the minimum bet
        !blackjack 100 - Play with a bet of 100 coins
        """
        # Check if user already has an active game
        if ctx.author.id in self.games:
            embed = discord.Embed(
                title="❌ Game Already In Progress",
                description="You already have an active Blackjack game! Finish that one first.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Get minimum and maximum bet amounts
        min_bet = 10
        max_bet = 1000
        
        # Use default bet if none specified
        if bet is None:
            bet = min_bet
        
        # Validate bet amount
        if bet < min_bet:
            embed = discord.Embed(
                title="❌ Invalid Bet",
                description=f"The minimum bet is **{min_bet}** {self.currency_emoji}.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        if bet > max_bet:
            embed = discord.Embed(
                title="❌ Invalid Bet",
                description=f"The maximum bet is **{max_bet}** {self.currency_emoji}.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Check if user has enough coins
        economy_cog = self.bot.get_cog("Economy")
        if not economy_cog:
            embed = discord.Embed(
                title="❌ Economy System Error",
                description="Could not access the economy system.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Get user balance
        user_data = await economy_cog.get_balance(ctx.author.id, ctx.guild.id)
        
        if user_data < bet:
            embed = discord.Embed(
                title="❌ Insufficient Funds",
                description=f"You don't have enough coins for this bet!\nYour balance: **{user_data}** {self.currency_emoji}\nRequired: **{bet}** {self.currency_emoji}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Deduct bet from balance
        await economy_cog.remove_balance(ctx.author.id, ctx.guild.id, bet)
        
        # Create new game
        game = BlackjackGame(ctx.author, bet)
        self.games[ctx.author.id] = game
        
        # Create initial embed
        embed = self.create_game_embed(game)
        
        # Send embed with buttons
        game.message = await ctx.send(embed=embed)
        
        # Add reaction buttons
        await game.message.add_reaction("👊")  # Hit
        await game.message.add_reaction("🛑")  # Stand
        
        # Check for immediate blackjack or bust
        game.check_game_over()
        
        if game.game_over:
            # Update embed with final state
            embed = self.create_game_embed(game)
            await game.message.edit(embed=embed)
            
            # Process rewards
            await self.process_game_end(ctx, game)
            return
        
        # Game loop
        while not game.game_over:
            # Wait for player's action
            def check(reaction, user):
                return (
                    user.id == ctx.author.id and
                    str(reaction.emoji) in ["👊", "🛑"] and
                    reaction.message.id == game.message.id
                )
            
            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
                
                if str(reaction.emoji) == "👊":
                    # Hit - take another card
                    if game.player_hit():
                        # Update the game state
                        game.check_game_over()
                        
                        # Update embed
                        embed = self.create_game_embed(game)
                        await game.message.edit(embed=embed)
                        
                        # Remove the reaction
                        try:
                            await game.message.remove_reaction("👊", ctx.author)
                        except:
                            pass
                
                elif str(reaction.emoji) == "🛑":
                    # Stand - dealer plays
                    if game.player_stand():
                        # Update the game state
                        game.check_game_over()
                        
                        # Update embed
                        embed = self.create_game_embed(game)
                        await game.message.edit(embed=embed)
                
                # If game is over, process the results
                if game.game_over:
                    await self.process_game_end(ctx, game)
                    break
            
            except asyncio.TimeoutError:
                # Player took too long, auto-stand
                if not game.game_over and not game.player_stood:
                    game.player_stand()
                    game.check_game_over()
                    
                    # Update embed
                    embed = self.create_game_embed(game)
                    await game.message.edit(embed=embed)
                    
                    # Process results
                    await self.process_game_end(ctx, game)
                    break
    
    def create_game_embed(self, game):
        """Create an embed for the Blackjack game."""
        # Determine color based on game state
        if not game.game_over:
            color = discord.Color.blue()
        elif game.result in ["blackjack", "player_wins", "dealer_bust"]:
            color = discord.Color.green()
        elif game.result in ["dealer_blackjack", "dealer_wins", "bust"]:
            color = discord.Color.red()
        else:  # push
            color = discord.Color.gold()
        
        # Create embed
        embed = discord.Embed(
            title="🃏 Blackjack",
            color=color
        )
        
        # Add player's hand
        embed.add_field(
            name=f"{game.player.display_name}'s Hand",
            value=game.get_player_display(),
            inline=False
        )
        
        # Add dealer's hand
        embed.add_field(
            name="Dealer's Hand",
            value=game.get_dealer_display(not game.game_over),
            inline=False
        )
        
        # Add bet information
        embed.add_field(
            name="Bet",
            value=f"**{game.bet}** {self.currency_emoji}",
            inline=True
        )
        
        # Add game status
        if game.game_over:
            # Show result
            result_messages = {
                "blackjack": f"🎉 **BLACKJACK!** You win **{game.calculate_reward()}** {self.currency_emoji}",
                "player_wins": f"🎉 **You win!** You receive **{game.calculate_reward()}** {self.currency_emoji}",
                "dealer_bust": f"🎉 **Dealer busts!** You win **{game.calculate_reward()}** {self.currency_emoji}",
                "push": f"🤝 **Push!** Your bet of **{game.bet}** {self.currency_emoji} has been returned",
                "bust": "💥 **Bust!** You went over 21 and lost your bet",
                "dealer_blackjack": "💔 **Dealer has Blackjack!** You lost your bet",
                "dealer_wins": "❌ **Dealer wins!** You lost your bet"
            }
            
            status_text = result_messages.get(game.result, "Game over")
        else:
            # Show instructions
            status_text = "👊 Hit (take another card) or 🛑 Stand (keep your current hand)"
        
        embed.add_field(
            name="Status",
            value=status_text,
            inline=False
        )
        
        return embed
    
    async def process_game_end(self, ctx, game):
        """Process the end of a Blackjack game."""
        # Calculate reward
        reward = game.calculate_reward()
        
        # Award coins if player won or pushed
        if reward > 0:
            economy_cog = self.bot.get_cog("Economy")
            if economy_cog:
                await economy_cog.add_balance(ctx.author.id, ctx.guild.id, reward)
        
        # Update player stats
        await self.update_stats(ctx.author.id, ctx.guild.id, game.result)
        
        # Clean up
        del self.games[ctx.author.id]
        
        # Remove reactions
        try:
            await game.message.clear_reactions()
        except:
            pass
    
    async def update_stats(self, user_id, guild_id, result):
        """Update player stats in the database."""
        # Get database manager
        db_manager = self.bot.get_cog("Utils").db_manager if hasattr(self.bot.get_cog("Utils"), "db_manager") else None
        
        if not db_manager:
            return
        
        try:
            # Get game data
            game_data = await db_manager.get_game_data("blackjack", guild_id=guild_id)
            
            # Initialize if doesn't exist
            if not game_data:
                game_data = {"players": {}}
            
            if "players" not in game_data:
                game_data["players"] = {}
            
            # Get or create player stats
            player_id = str(user_id)
            if player_id not in game_data["players"]:
                game_data["players"][player_id] = {
                    "games": 0,
                    "wins": 0,
                    "losses": 0,
                    "pushes": 0,
                    "blackjacks": 0
                }
            
            # Update stats
            player_stats = game_data["players"][player_id]
            player_stats["games"] = player_stats.get("games", 0) + 1
            
            # Categorize result
            if result == "blackjack":
                player_stats["wins"] = player_stats.get("wins", 0) + 1
                player_stats["blackjacks"] = player_stats.get("blackjacks", 0) + 1
            elif result in ["player_wins", "dealer_bust"]:
                player_stats["wins"] = player_stats.get("wins", 0) + 1
            elif result == "push":
                player_stats["pushes"] = player_stats.get("pushes", 0) + 1
            else:  # dealer_blackjack, dealer_wins, bust
                player_stats["losses"] = player_stats.get("losses", 0) + 1
            
            # Save game data
            await db_manager.update_game_data("blackjack", game_data, guild_id=guild_id)
            
        except Exception as e:
            print(f"Error updating blackjack stats: {e}")
    
    @commands.command(name="blackjack_stats", aliases=["bjstats"])
    async def blackjack_stats(self, ctx, member: discord.Member = None):
        """
        View Blackjack stats for yourself or another player.
        
        Examples:
        !blackjack_stats - View your own stats
        !blackjack_stats @user - View another user's stats
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
            game_data = await db_manager.get_game_data("blackjack", guild_id=ctx.guild.id)
            
            if not game_data or "players" not in game_data or str(member.id) not in game_data["players"]:
                embed = discord.Embed(
                    title=f"📊 Blackjack Stats for {member.display_name}",
                    description="This player hasn't played any Blackjack games yet!",
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
            pushes = stats.get("pushes", 0)
            blackjacks = stats.get("blackjacks", 0)
            
            # Calculate rates
            win_rate = (wins / games * 100) if games > 0 else 0
            blackjack_rate = (blackjacks / games * 100) if games > 0 else 0
            
            # Create stats embed
            embed = discord.Embed(
                title=f"📊 Blackjack Stats for {member.display_name}",
                color=discord.Color.blue()
            )
            
            embed.add_field(name="Games Played", value=str(games), inline=True)
            embed.add_field(name="Wins", value=str(wins), inline=True)
            embed.add_field(name="Losses", value=str(losses), inline=True)
            embed.add_field(name="Pushes", value=str(pushes), inline=True)
            embed.add_field(name="Blackjacks", value=str(blackjacks), inline=True)
            embed.add_field(name="Win Rate", value=f"{win_rate:.1f}%", inline=True)
            
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text=f"Blackjack Rate: {blackjack_rate:.1f}%")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"An error occurred: {e}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @commands.command(name="blackjack_leaderboard", aliases=["bjlb"])
    async def blackjack_leaderboard(self, ctx):
        """Display the Blackjack leaderboard for this server."""
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
            game_data = await db_manager.get_game_data("blackjack", guild_id=ctx.guild.id)
            
            if not game_data or "players" not in game_data or not game_data["players"]:
                embed = discord.Embed(
                    title="📊 Blackjack Leaderboard",
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
                title="📊 Blackjack Leaderboard",
                description="Top Blackjack players in this server:",
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
                blackjacks = stats.get("blackjacks", 0)
                win_rate = (wins / games * 100) if games > 0 else 0
                
                embed.add_field(
                    name=f"{i}. {name}",
                    value=f"**Wins:** {wins}\n**Games:** {games}\n**Blackjacks:** {blackjacks}\n**Win Rate:** {win_rate:.1f}%",
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
    await bot.add_cog(Blackjack(bot))
