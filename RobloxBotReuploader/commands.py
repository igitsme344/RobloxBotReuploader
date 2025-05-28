import discord
from discord.ext import commands
import os
import asyncio
from datetime import datetime
from config import Config
from file_handler import FileHandler
from validators import RobloxFileValidator
from roblox_api import roblox_api
import logging

logger = logging.getLogger(__name__)

def has_required_role():
    """Check if user has the required role to use bot commands"""
    def predicate(ctx):
        if not ctx.guild:  # DM messages
            return False
        
        # Check by role ID first (more reliable), then fall back to role name
        has_access = False
        required_role_display = ""
        
        if Config.ALLOWED_ROLE_ID:
            # Check by role ID
            role_id = int(Config.ALLOWED_ROLE_ID)
            user_role_ids = [role.id for role in ctx.author.roles]
            has_access = role_id in user_role_ids
            # Find role name for display
            role = discord.utils.get(ctx.guild.roles, id=role_id)
            required_role_display = role.name if role else f"Role ID: {role_id}"
        else:
            # Fallback to role name check
            required_role = Config.ALLOWED_ROLE_NAME
            user_roles = [role.name for role in ctx.author.roles]
            has_access = required_role in user_roles
            required_role_display = required_role
        
        if has_access:
            return True
        
        # Send access denied message
        embed = discord.Embed(
            title="❌ Access Denied",
            description=f"You need the `{required_role_display}` role to use this bot.",
            color=Config.COLOR_ERROR
        )
        embed.add_field(
            name="Required Role",
            value=f"`{required_role_display}`",
            inline=False
        )
        asyncio.create_task(ctx.send(embed=embed))
        return False
    
    return commands.check(predicate)

async def setup_commands(bot):
    """Setup all bot commands"""
    
    @bot.command(name='help')
    @has_required_role()
    async def help_command(ctx):
        """Display help information"""
        embed = discord.Embed(
            title="🎮 Roblox Game Bot Commands",
            description="Upload and manage your Roblox game files!",
            color=Config.COLOR_INFO
        )
        
        embed.add_field(
            name=f"`{Config.COMMAND_PREFIX}help`",
            value="Show this help message",
            inline=False
        )
        
        embed.add_field(
            name=f"`{Config.COMMAND_PREFIX}upload`",
            value="Upload a Roblox game file (.rbxl or .rbxlx)\nAttach the file to your message!",
            inline=False
        )
        
        embed.add_field(
            name=f"`{Config.COMMAND_PREFIX}publish <file_id> <cookie> [place_id]`",
            value="Publish an uploaded game file to Roblox\n`cookie`: Your .ROBLOSECURITY cookie\n`place_id`: (Optional) Update existing place",
            inline=False
        )
        
        embed.add_field(
            name=f"`{Config.COMMAND_PREFIX}status`",
            value="Check bot status and statistics",
            inline=False
        )
        
        embed.add_field(
            name=f"`{Config.COMMAND_PREFIX}cleanup`",
            value="Clean up old uploaded files (admin only)",
            inline=False
        )
        
        embed.add_field(
            name="📁 Supported Formats",
            value="• `.rbxl` - Roblox binary game files\n• `.rbxlx` - Roblox XML game files",
            inline=False
        )
        
        embed.add_field(
            name="📏 File Limits",
            value=f"Maximum file size: {Config.MAX_FILE_SIZE // (1024*1024)}MB",
            inline=False
        )
        
        embed.add_field(
            name="🔒 Access Control",
            value=f"Only users with the `{Config.ALLOWED_ROLE_NAME}` role can use this bot",
            inline=False
        )
        
        embed.set_footer(text="Made with ❤️ for Roblox developers")
        
        await ctx.send(embed=embed)
    
    @bot.command(name='upload')
    @has_required_role()
    async def upload_game(ctx):
        """Handle Roblox game file uploads"""
        if not ctx.message.attachments:
            embed = discord.Embed(
                title="❌ No File Attached",
                description=f"Please attach a Roblox game file (.rbxl or .rbxlx) to your message.\n\nExample:\n`{Config.COMMAND_PREFIX}upload` (with file attached)",
                color=Config.COLOR_ERROR
            )
            await ctx.send(embed=embed)
            return
        
        attachment = ctx.message.attachments[0]
        
        # Create initial response
        embed = discord.Embed(
            title="📤 Processing Upload...",
            description=f"Uploading and validating `{attachment.filename}`\nPlease wait...",
            color=Config.COLOR_WARNING
        )
        status_msg = await ctx.send(embed=embed)
        
        try:
            # Save the file
            success, message, file_path = await FileHandler.save_attachment(attachment, ctx.author.id)
            
            if not success:
                embed = discord.Embed(
                    title="❌ Upload Failed",
                    description=message,
                    color=Config.COLOR_ERROR
                )
                await status_msg.edit(embed=embed)
                return
            
            # Update status - validating
            embed = discord.Embed(
                title="🔍 Validating File...",
                description=f"File uploaded successfully!\nValidating Roblox game format...",
                color=Config.COLOR_WARNING
            )
            await status_msg.edit(embed=embed)
            
            # Validate the Roblox file
            is_valid, validation_message, file_info = await FileHandler.validate_roblox_file(file_path)
            
            if not is_valid:
                # Clean up invalid file
                try:
                    os.remove(file_path)
                except:
                    pass
                
                embed = discord.Embed(
                    title="❌ Invalid Roblox File",
                    description=f"**Error:** {validation_message}",
                    color=Config.COLOR_ERROR
                )
                embed.add_field(
                    name="Requirements",
                    value="• File must be a valid .rbxl or .rbxlx format\n• File must contain proper Roblox game structure\n• File must not be corrupted",
                    inline=False
                )
                await status_msg.edit(embed=embed)
                return
            
            # Success!
            embed = discord.Embed(
                title="✅ Upload Successful!",
                description=f"Your Roblox game file has been uploaded and validated successfully!",
                color=Config.COLOR_SUCCESS
            )
            
            # Add file information
            file_size_mb = file_info['size'] / (1024 * 1024)
            embed.add_field(
                name="📁 File Information",
                value=f"**Name:** {file_info.get('name', 'Unknown')}\n**Type:** {file_info.get('type', 'Unknown')}\n**Size:** {file_size_mb:.2f} MB",
                inline=False
            )
            
            # Add file ID for publishing
            file_id = os.path.basename(file_path)
            embed.add_field(
                name="🔧 Next Steps",
                value=f"To publish this game, use:\n`{Config.COMMAND_PREFIX}publish {file_id}`",
                inline=False
            )
            
            embed.set_footer(text=f"File ID: {file_id}")
            await status_msg.edit(embed=embed)
            
            logger.info(f"User {ctx.author.id} uploaded file: {file_path}")
            
        except Exception as e:
            logger.error(f"Upload error: {e}")
            embed = discord.Embed(
                title="❌ Upload Error",
                description="An unexpected error occurred during upload. Please try again.",
                color=Config.COLOR_ERROR
            )
            await status_msg.edit(embed=embed)
    
    @bot.command(name='publish')
    @has_required_role()
    async def publish_game(ctx, file_id: str = None, cookie: str = None, place_id: str = None):
        """Publish a Roblox game file to actual Roblox"""
        if not file_id or not cookie:
            embed = discord.Embed(
                title="❌ Missing Parameters",
                description=f"Please provide both file ID and Roblox cookie.\n\nExample:\n`{Config.COMMAND_PREFIX}publish your_file_id_here your_roblox_cookie`\n\nOptional: Add place_id to update existing place:\n`{Config.COMMAND_PREFIX}publish file_id cookie place_id`",
                color=Config.COLOR_ERROR
            )
            embed.add_field(
                name="How to get your Roblox cookie:",
                value="1. Go to roblox.com and log in\n2. Press F12 → Application → Cookies → roblox.com\n3. Find `.ROBLOSECURITY` and copy its value",
                inline=False
            )
            await ctx.send(embed=embed)
            return
        
        # Check if file exists
        file_path = os.path.join(Config.UPLOAD_DIR, file_id)
        if not os.path.exists(file_path):
            embed = discord.Embed(
                title="❌ File Not Found",
                description=f"No file found with ID: `{file_id}`\n\nMake sure you've uploaded the file first using `{Config.COMMAND_PREFIX}upload`",
                color=Config.COLOR_ERROR
            )
            await ctx.send(embed=embed)
            return
        
        # Create publishing status message
        embed = discord.Embed(
            title="🚀 Publishing to Roblox...",
            description="Authenticating with Roblox and uploading your game file.\nThis may take a few moments...",
            color=Config.COLOR_WARNING
        )
        status_msg = await ctx.send(embed=embed)
        
        try:
            # Step 1: Verify Roblox authentication
            embed.description = "🔐 Verifying Roblox authentication..."
            await status_msg.edit(embed=embed)
            
            auth_success, auth_message, user_info = await roblox_api.get_user_info(cookie)
            if not auth_success:
                embed = discord.Embed(
                    title="❌ Authentication Failed",
                    description=f"Could not authenticate with Roblox: {auth_message}",
                    color=Config.COLOR_ERROR
                )
                embed.add_field(
                    name="Check your cookie:",
                    value="Make sure your .ROBLOSECURITY cookie is valid and hasn't expired",
                    inline=False
                )
                await status_msg.edit(embed=embed)
                return
            
            # Step 2: Upload the file
            embed.description = f"📤 Uploading game file to Roblox account: {user_info['name']}..."
            await status_msg.edit(embed=embed)
            
            place_id_int = None
            if place_id and place_id.isdigit():
                place_id_int = int(place_id)
            
            upload_success, upload_message, upload_info = await roblox_api.upload_place_file(
                cookie, file_path, place_id_int
            )
            
            if not upload_success:
                embed = discord.Embed(
                    title="❌ Upload Failed",
                    description=f"Failed to upload to Roblox: {upload_message}",
                    color=Config.COLOR_ERROR
                )
                await status_msg.edit(embed=embed)
                return
            
            # Step 3: Publish the place
            new_place_id = upload_info['place_id']
            embed.description = f"🌟 Publishing place {new_place_id}..."
            await status_msg.edit(embed=embed)
            
            publish_success, publish_message, publish_info = await roblox_api.publish_place(
                cookie, new_place_id, f"Discord Upload - {file_id}"
            )
            
            if not publish_success:
                # Upload succeeded but publish failed - still show success with warning
                embed = discord.Embed(
                    title="⚠️ Partially Successful",
                    description=f"File uploaded successfully but publishing failed: {publish_message}",
                    color=Config.COLOR_WARNING
                )
                embed.add_field(
                    name="🎮 Upload Results",
                    value=f"**Place ID:** {new_place_id}\n**Account:** {user_info['name']}\n**Type:** {upload_info['upload_type']}",
                    inline=False
                )
            else:
                # Complete success!
                embed = discord.Embed(
                    title="🎉 Game Published Successfully!",
                    description=f"Your Roblox game has been uploaded and published to {user_info['name']}'s account!",
                    color=Config.COLOR_SUCCESS
                )
                
                embed.add_field(
                    name="🎮 Game Details",
                    value=f"**Place ID:** {new_place_id}\n**Account:** {user_info['name']}\n**Type:** {upload_info['upload_type'].title()}",
                    inline=False
                )
                
                embed.add_field(
                    name="🔗 Links",
                    value=f"[Play Game](https://www.roblox.com/games/{new_place_id})\n[Edit Place](https://www.roblox.com/develop/places/{new_place_id}/overview)",
                    inline=False
                )
            
            await status_msg.edit(embed=embed)
            
        except Exception as e:
            logger.error(f"Publish error: {e}")
            embed = discord.Embed(
                title="❌ Publishing Error",
                description=f"An unexpected error occurred: {str(e)}",
                color=Config.COLOR_ERROR
            )
            await status_msg.edit(embed=embed)
    
    @bot.command(name='status')
    @has_required_role()
    async def bot_status(ctx):
        """Display bot status and statistics"""
        try:
            # Count uploaded files
            upload_count = len([f for f in os.listdir(Config.UPLOAD_DIR) if f != '.gitkeep'])
            
            # Calculate total storage used
            total_size = 0
            for filename in os.listdir(Config.UPLOAD_DIR):
                if filename != '.gitkeep':
                    file_path = os.path.join(Config.UPLOAD_DIR, filename)
                    total_size += os.path.getsize(file_path)
            
            total_size_mb = total_size / (1024 * 1024)
            
            embed = discord.Embed(
                title="🤖 Bot Status",
                description="Current bot status and statistics",
                color=Config.COLOR_INFO
            )
            
            embed.add_field(
                name="📊 Statistics",
                value=f"**Uploaded Files:** {upload_count}\n**Storage Used:** {total_size_mb:.2f} MB\n**Guilds:** {len(bot.guilds)}",
                inline=False
            )
            
            embed.add_field(
                name="⚙️ Configuration",
                value=f"**Max File Size:** {Config.MAX_FILE_SIZE // (1024*1024)} MB\n**Supported Formats:** {', '.join(Config.ALLOWED_EXTENSIONS)}\n**Command Prefix:** `{Config.COMMAND_PREFIX}`",
                inline=False
            )
            
            embed.add_field(
                name="🔧 Commands Available",
                value=f"`{Config.COMMAND_PREFIX}help`, `{Config.COMMAND_PREFIX}upload`, `{Config.COMMAND_PREFIX}publish`, `{Config.COMMAND_PREFIX}status`",
                inline=False
            )
            
            embed.set_footer(text=f"Bot ready since startup")
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Status command error: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Failed to retrieve bot status.",
                color=Config.COLOR_ERROR
            )
            await ctx.send(embed=embed)
    
    @bot.command(name='cleanup')
    @commands.has_permissions(administrator=True)
    async def cleanup_files(ctx, max_age_hours: int = 24):
        """Clean up old uploaded files (admin only)"""
        embed = discord.Embed(
            title="🧹 Cleaning Up Files...",
            description=f"Removing files older than {max_age_hours} hours...",
            color=Config.COLOR_WARNING
        )
        status_msg = await ctx.send(embed=embed)
        
        try:
            await FileHandler.cleanup_old_files(max_age_hours)
            
            embed = discord.Embed(
                title="✅ Cleanup Complete",
                description=f"Successfully cleaned up files older than {max_age_hours} hours.",
                color=Config.COLOR_SUCCESS
            )
            await status_msg.edit(embed=embed)
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
            embed = discord.Embed(
                title="❌ Cleanup Failed",
                description="An error occurred during cleanup.",
                color=Config.COLOR_ERROR
            )
            await status_msg.edit(embed=embed)
    
    @cleanup_files.error
    async def cleanup_error(ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="You need administrator permissions to use this command.",
                color=Config.COLOR_ERROR
            )
            await ctx.send(embed=embed)
