import discord
from discord.ext import commands
import asyncio
from typing import Optional, List, Dict, Union, Any
import emoji
from discord.ui import Button, View, Select, Modal, TextInput
import datetime

class PaginationView(View):
    """A pagination view for navigating through multiple pages of embeds."""
    
    def __init__(self, pages: List[discord.Embed], author_id: int, timeout: int = 60):
        super().__init__(timeout=timeout)
        self.pages = pages
        self.author_id = author_id
        self.current_page = 0
        self.total_pages = len(pages)
        self.update_buttons()
        
    def update_buttons(self):
        # Clear existing items
        self.clear_items()
        
        # Add home button
        home_button = Button(style=discord.ButtonStyle.primary, emoji="🏠", custom_id="home")
        home_button.callback = self.home_callback
        self.add_item(home_button)
        
        # Add navigation buttons if more than one page
        if self.total_pages > 1:
            # First page button
            first_button = Button(style=discord.ButtonStyle.secondary, emoji="⏮️", disabled=self.current_page == 0, custom_id="first")
            first_button.callback = self.first_callback
            self.add_item(first_button)
            
            # Previous page button
            prev_button = Button(style=discord.ButtonStyle.secondary, emoji="◀️", disabled=self.current_page == 0, custom_id="prev")
            prev_button.callback = self.prev_callback
            self.add_item(prev_button)
            
            # Page indicator
            page_indicator = Button(style=discord.ButtonStyle.secondary, 
                              label=f"Page {self.current_page + 1}/{self.total_pages}", 
                              disabled=True, 
                              custom_id="page")
            self.add_item(page_indicator)
            
            # Next page button
            next_button = Button(style=discord.ButtonStyle.secondary, emoji="▶️", disabled=self.current_page == self.total_pages - 1, custom_id="next")
            next_button.callback = self.next_callback
            self.add_item(next_button)
            
            # Last page button
            last_button = Button(style=discord.ButtonStyle.secondary, emoji="⏭️", disabled=self.current_page == self.total_pages - 1, custom_id="last")
            last_button.callback = self.last_callback
            self.add_item(last_button)
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("This menu is not for you!", ephemeral=True)
            return False
        return True
    
    async def home_callback(self, interaction: discord.Interaction):
        # This should be overridden by the help command
        await interaction.response.defer()
    
    async def first_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.current_page = 0
        self.update_buttons()
        await interaction.message.edit(embed=self.pages[self.current_page], view=self)
    
    async def prev_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.current_page = max(0, self.current_page - 1)
        self.update_buttons()
        await interaction.message.edit(embed=self.pages[self.current_page], view=self)
    
    async def next_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.current_page = min(self.total_pages - 1, self.current_page + 1)
        self.update_buttons()
        await interaction.message.edit(embed=self.pages[self.current_page], view=self)
    
    async def last_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.current_page = self.total_pages - 1
        self.update_buttons()
        await interaction.message.edit(embed=self.pages[self.current_page], view=self)
        
    async def on_timeout(self):
        # Disable all buttons when the view times out
        for item in self.children:
            item.disabled = True
        # Try to update the message with disabled buttons
        try:
            message = self.message
            await message.edit(view=self)
        except:
            pass

class CategorySelect(Select):
    """A dropdown select menu for choosing categories."""
    
    def __init__(self, help_cog):
        self.help_cog = help_cog
        options = [
            discord.SelectOption(
                label="Games",
                value="games",
                description="Fun games to play with friends",
                emoji="🎮"
            ),
            discord.SelectOption(
                label="Economy",
                value="economy",
                description="Commands for managing coins",
                emoji="💰"
            ),
            discord.SelectOption(
                label="Commands",
                value="commands",
                description="Utility and basic commands",
                emoji="📜"
            ),
            discord.SelectOption(
                label="Settings",
                value="settings",
                description="Server and user preferences",
                emoji="⚙️"
            ),
            discord.SelectOption(
                label="Misc",
                value="misc",
                description="Other fun and useful commands",
                emoji="🔮"
            )
        ]
        super().__init__(placeholder="Select a category...", options=options, custom_id="category_select")
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self.help_cog.send_category_help(category=self.values[0], interaction=interaction)

class CommandSearchModal(Modal, title="Search Commands"):
    """Modal for searching commands by name or description."""
    
    def __init__(self, help_cog):
        super().__init__(timeout=300)
        self.help_cog = help_cog
        
        self.search_input = TextInput(
            label="Enter command name or keywords",
            placeholder="e.g., balance, blackjack, daily",
            style=discord.TextStyle.short,
            min_length=1,
            max_length=100,
            required=True
        )
        
        self.add_item(self.search_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        search_term = self.search_input.value.lower()
        matching_commands = []
        
        for command in self.help_cog.bot.commands:
            # Skip hidden commands
            if command.hidden:
                continue
                
            # Check command name
            if search_term in command.name.lower():
                matching_commands.append(command)
                continue
                
            # Check aliases
            if command.aliases and any(search_term in alias.lower() for alias in command.aliases):
                matching_commands.append(command)
                continue
                
            # Check description/help text
            if command.help and search_term in command.help.lower():
                matching_commands.append(command)
                continue
                
            # Check brief description
            if command.brief and search_term in command.brief.lower():
                matching_commands.append(command)
                continue
        
        if not matching_commands:
            embed = discord.Embed(
                title="Search Results",
                description=f"No commands found matching `{search_term}`. Try a different search term.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Create result pages
        pages = []
        items_per_page = 6
        
        for i in range(0, len(matching_commands), items_per_page):
            page_commands = matching_commands[i:i+items_per_page]
            
            embed = discord.Embed(
                title=f"Search Results for '{search_term}'",
                description=f"Found {len(matching_commands)} command(s) matching your search.",
                color=discord.Color.green()
            )
            
            for cmd in page_commands:
                name = f"!{cmd.name}"
                if cmd.aliases:
                    aliases = ", ".join([f"!{alias}" for alias in cmd.aliases])
                    name += f" (Aliases: {aliases})"
                    
                brief = cmd.brief or "No description"
                embed.add_field(name=name, value=brief, inline=False)
            
            page_num = i // items_per_page + 1
            total_pages = (len(matching_commands) + items_per_page - 1) // items_per_page
            embed.set_footer(text=f"Page {page_num}/{total_pages} • Click on a button below to view details")
            pages.append(embed)
        
        # Create view for navigation and command selection
        view = discord.ui.View(timeout=60)
        
        # Home button
        home_button = Button(style=discord.ButtonStyle.primary, emoji="🏠", label="Main Menu", custom_id="home")
        
        async def home_button_callback(interaction):
            await interaction.response.defer()
            await self.help_cog.send_help_menu(interaction=interaction)
            
        home_button.callback = home_button_callback
        view.add_item(home_button)
        
        # Add command buttons for the first page
        for i, cmd in enumerate(matching_commands[:min(5, len(matching_commands))]):  # Max 5 buttons per row
            cmd_button = Button(
                style=discord.ButtonStyle.success, 
                label=cmd.name, 
                custom_id=f"cmd_{cmd.name}",
                row=1
            )
            
            async def command_button_callback(interaction, command=cmd):
                await interaction.response.defer()
                await self.help_cog.send_command_help(command=command, interaction=interaction)
                
            cmd_button.callback = command_button_callback
            view.add_item(cmd_button)
        
        await interaction.response.send_message(embed=pages[0], view=view)

class CommandSelect(Select):
    """A dropdown select menu for choosing commands within a category."""
    
    def __init__(self, help_cog, commands_list, category):
        self.help_cog = help_cog
        self.category = category
        options = []
        
        for cmd in commands_list[:25]:  # Discord limit of 25 options
            desc = cmd.brief or "No description"
            # Truncate description if too long
            if len(desc) > 50:
                desc = desc[:47] + "..."
                
            options.append(discord.SelectOption(
                label=cmd.name,
                description=desc,
                value=cmd.name
            ))
            
        super().__init__(placeholder="Select a command...", options=options, custom_id="command_select")
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        command = self.help_cog.bot.get_command(self.values[0])
        if command:
            await self.help_cog.send_command_help(command=command, interaction=interaction)

class HelpCommand(commands.Cog):
    """Advanced help command system with interactive buttons and select menus."""
    
    def __init__(self, bot):
        self.bot = bot
        self.emoji_map = {
            "commands": "📜",
            "games": "🎮",
            "economy": "💰",
            "settings": "⚙️",
            "misc": "🔮",
            "home": "🏠",
            "back": "◀️",
            "next": "▶️",
            "info": "ℹ️"
        }
        self.color_map = {
            "commands": discord.Color.blue(),
            "games": discord.Color.purple(),
            "economy": discord.Color.gold(),
            "settings": discord.Color.dark_gray(),
            "misc": discord.Color.teal(),
            "default": discord.Color.blurple()
        }
        
    @commands.command(name="help", aliases=["h", "commands", "cmds"])
    async def help_command(self, ctx, *, command_name: Optional[str] = None):
        """
        Advanced help command with beautiful interactive interface.
        
        Usage:
        !help - Shows all command categories
        !help [category] - Shows all commands in a category
        !help [command] - Shows detailed help for a specific command
        """
        if command_name is None:
            await self.send_help_menu(ctx)
        else:
            # Check if it's a category
            if command_name.lower() in ["games", "economy", "commands", "settings", "misc"]:
                await self.send_category_help(ctx, command_name.lower())
            else:
                # Check if it's a command
                command = self.bot.get_command(command_name)
                if command is not None:
                    await self.send_command_help(ctx, command)
                else:
                    embed = discord.Embed(
                        title="❌ Command Not Found",
                        description=f"The command `{command_name}` doesn't exist! Type `!help` to see all available commands.",
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=embed)
    
    async def send_help_menu(self, ctx=None, interaction: discord.Interaction = None):
        """Sends the main help menu with categories using buttons and select menu."""
        embed = discord.Embed(
            title="🌟 Trenny Fun - Advanced Gaming Bot",
            description=(
                "Welcome to Trenny Fun! Below are the command categories.\n\n"
                "**Select a category** from the dropdown menu below to explore commands.\n"
                "For specific command help, type `!help [command_name]`.\n\n"
                "This bot features various games, economy, and utility commands to enhance your Discord experience!"
            ),
            color=self.color_map["default"]
        )
        
        # Add category fields with emoji and better descriptions
        categories = [
            ("games", "Fun games to play alone or with friends! Challenge others, earn rewards, and climb leaderboards."),
            ("economy", "Manage your virtual coins, shop for items, check your balance, and more!"),
            ("commands", "Essential commands for information, utilities, and basic bot features."),
            ("settings", "Customize the bot to suit your server's needs with these configuration commands."),
            ("misc", "Fun and miscellaneous commands that don't fit in other categories!")
        ]
        
        for category, description in categories:
            embed.add_field(
                name=f"{self.emoji_map[category]} {category.title()}",
                value=description,
                inline=False
            )
        
        # Add visual enhancements
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        
        # Add timestamp and footer
        embed.timestamp = datetime.datetime.now()
        embed.set_footer(text=f"Type !help [command] for specific help | Bot Version 1.0.0")
        
        # Create view with components
        view = discord.ui.View(timeout=60)
        
        # Add category select menu
        category_select = CategorySelect(self)
        view.add_item(category_select)
        
        # Add bot info button
        info_button = discord.ui.Button(style=discord.ButtonStyle.secondary, label="Bot Info", emoji="ℹ️", custom_id="info")
        
        async def info_button_callback(interaction):
            await interaction.response.defer()
            await self.send_bot_info(interaction=interaction)
            
        info_button.callback = info_button_callback
        view.add_item(info_button)
        
        # Add search button
        search_button = discord.ui.Button(style=discord.ButtonStyle.primary, label="Search Commands", emoji="🔍", custom_id="search")
        
        async def search_button_callback(interaction):
            modal = CommandSearchModal(self)
            await interaction.response.send_modal(modal)
            
        search_button.callback = search_button_callback
        view.add_item(search_button)
        
        # Add refresh button
        refresh_button = discord.ui.Button(style=discord.ButtonStyle.success, label="Refresh", emoji="🔄", custom_id="refresh")
        
        async def refresh_button_callback(interaction):
            await interaction.response.defer()
            await self.send_help_menu(interaction=interaction)
            
        refresh_button.callback = refresh_button_callback
        view.add_item(refresh_button)
        
        # Send the embed or update existing message
        if interaction:
            if hasattr(interaction, 'response') and not interaction.response.is_done():
                await interaction.response.edit_message(embed=embed, view=view)
            else:
                await interaction.message.edit(embed=embed, view=view)
        else:
            await ctx.send(embed=embed, view=view)
    
    async def send_category_help(self, ctx=None, category: str = None, interaction: discord.Interaction = None):
        """Sends help for a specific category using buttons and select menu."""
        # Get all commands in this category
        commands_list = []
        
        for command in self.bot.commands:
            # Skip hidden commands
            if command.hidden:
                continue
                
            # Check if command belongs to this category (based on cog name or category attribute)
            command_category = getattr(command.cog, "category", None)
            if command_category is None and command.cog:
                command_category = command.cog.__class__.__name__.lower().replace("cog", "")
            
            # Some commands might have explicit category
            explicit_category = getattr(command, "category", None)
            if explicit_category:
                command_category = explicit_category
            
            # Add command to list if it matches category
            if command_category and category.lower() in command_category.lower():
                commands_list.append(command)
        
        # If no commands in category, show message
        if not commands_list:
            embed = discord.Embed(
                title=f"{self.emoji_map[category]} {category.title()} Commands",
                description="No commands found in this category.",
                color=discord.Color.orange()
            )
            if interaction:
                if hasattr(interaction, 'response') and not interaction.response.is_done():
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                else:
                    await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await ctx.send(embed=embed)
            return
        
        # Sort commands alphabetically
        commands_list.sort(key=lambda x: x.name)
        
        # Create pages for pagination
        pages = []
        items_per_page = 5  # Show fewer commands per page but with more details
        
        for i in range(0, len(commands_list), items_per_page):
            page_commands = commands_list[i:i+items_per_page]
            
            embed = discord.Embed(
                title=f"{self.emoji_map[category]} {category.title()} Commands",
                description=f"Select a command from the dropdown menu below or click a button to view details.",
                color=self.color_map.get(category, discord.Color.blue())
            )
            
            # Show category description based on category
            category_descriptions = {
                "games": "Challenge other players, earn rewards, and have fun with these interactive games!",
                "economy": "Manage your virtual coins, shop for items, and participate in the economy system.",
                "commands": "Essential commands for information and utilities.",
                "settings": "Configure the bot and customize your experience.",
                "misc": "Miscellaneous commands that don't fit in other categories."
            }
            
            if category in category_descriptions:
                embed.add_field(
                    name="Category Description",
                    value=category_descriptions[category],
                    inline=False
                )
            
            # Add commands to embed with better formatting
            for cmd in page_commands:
                name = f"`!{cmd.name}`"
                if cmd.aliases:
                    aliases = ", ".join([f"`!{alias}`" for alias in cmd.aliases])
                    name += f" (Aliases: {aliases})"
                
                brief = cmd.brief or cmd.help
                if not brief:
                    brief = "No description available"
                # Truncate if too long
                if len(brief) > 100:
                    brief = brief[:97] + "..."
                
                # Add usage hints
                usage = f"`!{cmd.name}`"
                if cmd.signature:
                    usage += f" `{cmd.signature}`"
                
                value = f"{brief}\n**Usage:** {usage}"
                
                embed.add_field(name=name, value=value, inline=False)
            
            # Add footer with page info
            page_num = i // items_per_page + 1
            total_pages = (len(commands_list) + items_per_page - 1) // items_per_page
            embed.set_footer(text=f"Page {page_num}/{total_pages} • {len(commands_list)} command(s) in {category}")
            
            # Add timestamp
            embed.timestamp = datetime.datetime.now()
            
            pages.append(embed)
        
        # Create pagination view
        class CategoryHelpView(PaginationView):
            def __init__(self, help_command, pages, author_id, category, commands_list):
                super().__init__(pages, author_id)
                self.help_command = help_command
                self.category = category
                self.commands_list = commands_list
                self.message = None
                
                # Add command select menu
                self.add_item(CommandSelect(help_command, commands_list, category))
                
            async def home_callback(self, interaction):
                await interaction.response.defer()
                await self.help_command.send_help_menu(interaction=interaction)
        
        # Get author ID
        author_id = ctx.author.id if ctx else interaction.user.id
        
        # Create and configure view
        view = CategoryHelpView(self, pages, author_id, category, commands_list)
        
        # Send message or update existing message
        if interaction:
            if hasattr(interaction, 'response') and not interaction.response.is_done():
                message = await interaction.response.send_message(embed=pages[0], view=view)
                view.message = message
            else:
                await interaction.message.edit(embed=pages[0], view=view)
                view.message = interaction.message
        else:
            message = await ctx.send(embed=pages[0], view=view)
            view.message = message
    
    async def send_command_help(self, ctx=None, command=None, interaction: discord.Interaction = None):
        """Sends detailed help for a specific command using buttons."""
        # Determine the command category for color coding
        command_category = getattr(command.cog, "category", None)
        if command_category is None and command.cog:
            command_category = command.cog.__class__.__name__.lower().replace("cog", "")
        
        # Get the appropriate color
        category_key = next((cat for cat in self.color_map.keys() if cat in command_category.lower()), "default")
        color = self.color_map.get(category_key, discord.Color.green())
        
        embed = discord.Embed(
            title=f"Command: !{command.name}",
            color=color
        )
        
        # Command description with improved formatting
        description = command.help or "No detailed description available."
        embed.description = description
        
        # Command usage with better formatting
        usage = f"!{command.name}"
        if command.signature:
            usage += f" {command.signature}"
        embed.add_field(name="Usage", value=f"```{usage}```", inline=False)
        
        # Command aliases
        if command.aliases:
            aliases = ", ".join([f"`!{alias}`" for alias in command.aliases])
            embed.add_field(name="Aliases", value=aliases, inline=False)
        
        # Command cooldown with friendly display
        if command._buckets and command._buckets._cooldown:
            cooldown = command._buckets._cooldown
            # Format cooldown in a more readable way
            if cooldown.per < 60:
                time_format = f"{cooldown.per:.0f} seconds"
            elif cooldown.per < 3600:
                time_format = f"{cooldown.per / 60:.1f} minutes"
            else:
                time_format = f"{cooldown.per / 3600:.1f} hours"
                
            embed.add_field(
                name="Cooldown",
                value=f"{cooldown.rate} use{'s' if cooldown.rate > 1 else ''} every {time_format}",
                inline=False
            )
        
        # Required permissions if any
        if command.checks:
            perm_list = []
            for check in command.checks:
                check_name = getattr(check, "__qualname__", str(check))
                if "has_permissions" in check_name or "guild_only" in check_name or "is_owner" in check_name:
                    perm_list.append(f"• {check_name.replace('_', ' ').title()}")
            
            if perm_list:
                embed.add_field(name="Required Permissions", value="\n".join(perm_list), inline=False)
        
        # Command examples if available
        examples = getattr(command, "examples", None)
        if examples:
            embed.add_field(name="Examples", value=examples, inline=False)
        
        # Related commands (commands in the same cog)
        if command.cog:
            related = []
            for cmd in command.cog.get_commands():
                if cmd.name != command.name and not cmd.hidden:
                    related.append(f"`!{cmd.name}`")
            
            if related:
                embed.add_field(
                    name="Related Commands", 
                    value=", ".join(related[:8]) + (" and more..." if len(related) > 8 else ""),
                    inline=False
                )
        
        # Add footer with category info
        cog_name = command.cog.__class__.__name__ if command.cog else "Uncategorized"
        embed.set_footer(text=f"Command from: {cog_name} • Type !help for the main menu")
        
        # Add timestamp
        embed.timestamp = datetime.datetime.now()
        
        # Create view with buttons
        view = discord.ui.View(timeout=60)
        
        # Back button (to category)
        if command_category:
            back_button = discord.ui.Button(
                style=discord.ButtonStyle.secondary, 
                emoji="◀️", 
                label=f"Back to {command_category.title()}", 
                custom_id="back_category"
            )
            
            async def back_button_callback(interaction):
                await interaction.response.defer()
                await self.send_category_help(interaction=interaction, category=command_category)
                
            back_button.callback = back_button_callback
            view.add_item(back_button)
        
        # Home button
        home_button = discord.ui.Button(
            style=discord.ButtonStyle.primary, 
            emoji="🏠", 
            label="Main Menu", 
            custom_id="home"
        )
        
        async def home_button_callback(interaction):
            await interaction.response.defer()
            await self.send_help_menu(interaction=interaction)
            
        home_button.callback = home_button_callback
        view.add_item(home_button)
        
        # Try command button
        try_button = discord.ui.Button(
            style=discord.ButtonStyle.success, 
            emoji="▶️", 
            label="Try Command", 
            custom_id="try"
        )
        
        async def try_button_callback(interaction):
            await interaction.response.send_message(
                f"To use this command, type: `{usage}` in a channel",
                ephemeral=True
            )
            
        try_button.callback = try_button_callback
        view.add_item(try_button)
        
        # Send message or update existing
        if interaction:
            if hasattr(interaction, 'response') and not interaction.response.is_done():
                await interaction.response.send_message(embed=embed, view=view)
            else:
                await interaction.message.edit(embed=embed, view=view)
        else:
            await ctx.send(embed=embed, view=view)
    
    async def send_bot_info(self, ctx=None, interaction: discord.Interaction = None):
        """Sends information about the bot using buttons."""
        # Count commands by category
        category_counts = {}
        for command in self.bot.commands:
            if command.hidden:
                continue
                
            category = getattr(command.cog, "category", None)
            if category is None and command.cog:
                category = command.cog.__class__.__name__.lower().replace("cog", "")
            
            if not category:
                category = "uncategorized"
                
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Create a rich embed with more information and better formatting
        embed = discord.Embed(
            title=f"✨ About {self.bot.user.name}",
            description="An advanced Discord gaming bot with multiple games, economy system, and fun commands!",
            color=discord.Color.purple()
        )
        
        # Bot stats in a cleaner format
        stats_field = (
            f"**Servers:** {len(self.bot.guilds)}\n"
            f"**Total Commands:** {len(self.bot.commands)}\n"
            f"**Users:** {sum(guild.member_count for guild in self.bot.guilds)}\n"
        )
        
        # Add bot uptime if available
        if hasattr(self.bot, "uptime"):
            from datetime import datetime
            delta = datetime.utcnow() - self.bot.uptime
            hours, remainder = divmod(int(delta.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            days, hours = divmod(hours, 24)
            uptime = f"{days}d {hours}h {minutes}m {seconds}s"
            stats_field += f"**Uptime:** {uptime}\n"
        
        embed.add_field(name="Bot Statistics", value=stats_field, inline=False)
        
        # Featured games - pulled from your memory about the bot
        games_field = (
            "• **Blackjack** - Play against the dealer with betting\n"
            "• **Snake** - Control a snake to eat apples\n"
            "• **Tic Tac Toe** - Challenge others to a game\n"
            "• **Rock Paper Scissors** - Play with betting\n"
            "• **Trivia** - Test your knowledge"
        )
        embed.add_field(name="Featured Games", value=games_field, inline=True)
        
        # Fun commands - pulled from your memory about the bot
        fun_field = (
            "• **8-ball** - Fortune telling\n"
            "• **Coin flip** - Flip a coin\n"
            "• **Dice roll** - Roll dice\n"
            "• **Choose** - Pick between options\n"
            "• **Jokes** - Get random jokes"
        )
        embed.add_field(name="Fun Commands", value=fun_field, inline=True)
        
        # Add creator and version info
        embed.add_field(
            name="Bot Info", 
            value=f"**Creator:** Your Discord Username\n**Version:** 1.0.0\n**Framework:** discord.py {discord.__version__}", 
            inline=False
        )
        
        # Add links
        embed.add_field(
            name="Links", 
            value="[GitHub](https://github.com/yourusername/trenny-fun) | [Support Server](https://discord.gg/yourserver) | [Invite Bot](https://discord.com/api/oauth2/authorize)",
            inline=False
        )
        
        # Enhanced visual elements
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(text="Type !help to see all commands | Created with ❤️")
        embed.timestamp = datetime.datetime.now()
        
        # Create view with buttons
        view = discord.ui.View(timeout=60)
        
        # Home button
        home_button = discord.ui.Button(
            style=discord.ButtonStyle.primary, 
            emoji="🏠", 
            label="Main Menu", 
            custom_id="home"
        )
        
        async def home_button_callback(interaction):
            await interaction.response.defer()
            await self.send_help_menu(interaction=interaction)
            
        home_button.callback = home_button_callback
        view.add_item(home_button)
        
        # Support server button
        support_button = discord.ui.Button(
            style=discord.ButtonStyle.link, 
            label="Support Server", 
            url="https://discord.gg/yourserver", 
            emoji="📫"
        )
        view.add_item(support_button)
        
        # GitHub button
        github_button = discord.ui.Button(
            style=discord.ButtonStyle.link, 
            label="GitHub", 
            url="https://github.com/yourusername/trenny-fun", 
            emoji="📑"
        )
        view.add_item(github_button)
        
        # Refresh button
        refresh_button = discord.ui.Button(
            style=discord.ButtonStyle.secondary, 
            emoji="🔄", 
            label="Refresh Stats", 
            custom_id="refresh"
        )
        
        async def refresh_button_callback(interaction):
            await interaction.response.defer()
            await self.send_bot_info(interaction=interaction)
            
        refresh_button.callback = refresh_button_callback
        view.add_item(refresh_button)
        
        # Send message or update existing
        if interaction:
            if hasattr(interaction, 'response') and not interaction.response.is_done():
                await interaction.response.send_message(embed=embed, view=view)
            else:
                await interaction.message.edit(embed=embed, view=view)
        else:
            await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(HelpCommand(bot))
