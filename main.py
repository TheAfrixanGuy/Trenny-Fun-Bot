import os
import discord
from discord.ext import commands
import asyncio
from dotenv import load_dotenv
import logging
import colorama
from colorama import Fore, Style

# Initialize colorama for cross-platform colored terminal output
colorama.init()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("trenny_fun")

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Define intents (permissions)
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.typing = True
intents.presences = True

# Initialize bot with prefix and intents
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# Bot startup event
@bot.event
async def on_ready():
    """Called when the bot is ready and connected to Discord."""
    print(f'{Fore.GREEN}+---------------------------------------------------------------+')
    print(f'| {Fore.CYAN}Bot is connected to Discord!{Fore.GREEN}                                 |')
    print(f'| {Fore.CYAN}Logged in as: {Fore.YELLOW}{bot.user.name}#{bot.user.discriminator}{Fore.GREEN}                        |')
    print(f'| {Fore.CYAN}Bot ID: {Fore.YELLOW}{bot.user.id}{Fore.GREEN}                                          |')
    print(f'| {Fore.CYAN}Connected to {Fore.YELLOW}{len(bot.guilds)}{Fore.CYAN} servers{Fore.GREEN}                                  |')
    print(f'+---------------------------------------------------------------+{Style.RESET_ALL}')
    
    # Set bot status
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.playing,
            name="!help | Fun Games"
        )
    )
    
    # Load all cogs
    await load_extensions()

async def load_extensions():
    """Load all extension cogs."""
    for folder in ['commands', 'games', 'economy', 'utils']:
        folder_path = f'./cogs/{folder}'
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            for filename in os.listdir(folder_path):
                if filename.endswith('.py'):
                    try:
                        await bot.load_extension(f'cogs.{folder}.{filename[:-3]}')
                        logger.info(f"Loaded extension: cogs.{folder}.{filename[:-3]}")
                    except Exception as e:
                        logger.error(f"Failed to load extension cogs.{folder}.{filename[:-3]}: {e}")
        else:
            logger.warning(f"Folder {folder_path} does not exist, skipping...")

@bot.event
async def on_command_error(ctx, error):
    """Global error handler for command errors."""
    if isinstance(error, commands.CommandNotFound):
        embed = discord.Embed(
            title="❌ Command Not Found",
            description="That command doesn't exist! Type `!help` to see all available commands.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
    elif isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(
            title="❌ Missing Argument",
            description=f"You're missing a required argument: `{error.param.name}`\nUse `!help {ctx.command.name}` for proper usage.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
    elif isinstance(error, commands.CommandOnCooldown):
        embed = discord.Embed(
            title="⏱️ Command On Cooldown",
            description=f"This command is on cooldown. Try again in {error.retry_after:.2f} seconds.",
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed)
    else:
        logger.error(f"Command error in {ctx.command}: {error}")
        embed = discord.Embed(
            title="❌ Error",
            description="An unexpected error occurred while running the command.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

# Run the bot
if __name__ == "__main__":
    if not TOKEN:
        print(f"{Fore.RED}Error: No Discord token found. Please create a .env file with your DISCORD_TOKEN.{Style.RESET_ALL}")
        exit(1)
    
    try:
        asyncio.run(bot.start(TOKEN))
    except KeyboardInterrupt:
        print(f"{Fore.YELLOW}Bot shutdown initiated by user.{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
