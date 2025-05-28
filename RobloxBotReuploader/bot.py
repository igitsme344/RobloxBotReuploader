import discord
from discord.ext import commands
import asyncio
import logging
import os
from config import Config
from commands import setup_commands

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RobloxGameBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        # Only enable message content if it's available, otherwise use default permissions
        try:
            intents.message_content = True
        except:
            pass
        
        super().__init__(
            command_prefix=Config.COMMAND_PREFIX,
            intents=intents,
            help_command=None
        )
        
    async def on_ready(self):
        logger.info(f'{self.user} has connected to Discord!')
        logger.info(f'Bot is in {len(self.guilds)} guilds')
        
        # Set bot status
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="for Roblox game files | !help"
        )
        await self.change_presence(activity=activity)
        
    async def on_command_error(self, ctx, error):
        """Global error handler for commands"""
        if isinstance(error, commands.CommandNotFound):
            embed = discord.Embed(
                title="❌ Command Not Found",
                description=f"Unknown command. Use `{Config.COMMAND_PREFIX}help` to see available commands.",
                color=0xff0000
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="❌ Missing Argument",
                description=f"Missing required argument: `{error.param.name}`",
                color=0xff0000
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.BadArgument):
            embed = discord.Embed(
                title="❌ Invalid Argument",
                description=str(error),
                color=0xff0000
            )
            await ctx.send(embed=embed)
        else:
            logger.error(f"Unexpected error: {error}")
            embed = discord.Embed(
                title="❌ Unexpected Error",
                description="An unexpected error occurred. Please try again later.",
                color=0xff0000
            )
            await ctx.send(embed=embed)

async def main():
    """Main function to run the bot"""
    # Create storage directory if it doesn't exist
    os.makedirs('storage/uploads', exist_ok=True)
    
    # Initialize bot
    bot = RobloxGameBot()
    
    # Setup commands
    await setup_commands(bot)
    
    # Get token from environment
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logger.error("DISCORD_TOKEN environment variable not set!")
        return
    
    try:
        await bot.start(token)
    except discord.LoginFailure:
        logger.error("Invalid Discord token provided!")
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")

if __name__ == "__main__":
    asyncio.run(main())
