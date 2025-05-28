# Discord Roblox Game Bot

A Discord bot that allows users with a specific role to upload and publish Roblox game files.

## Features

- **Role-Based Access Control**: Only users with the specified role can use the bot
- **File Upload**: Upload Roblox game files (.rbxl and .rbxlx formats)
- **File Validation**: Automatically validates uploaded files to ensure they're legitimate Roblox games
- **Mock Publishing**: Simulate publishing games with generated IDs and URLs
- **File Management**: Automatic cleanup of old files
- **Comprehensive Error Handling**: User-friendly error messages and validation

## Setup Instructions

### 1. Discord Developer Portal Setup

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application and bot
3. Copy your bot token
4. Enable "Message Content Intent" in Bot settings (required for the bot to work)

### 2. Bot Configuration

1. Set your Discord bot token as `DISCORD_TOKEN` environment variable
2. Change the allowed role name in `config.py` by modifying `ALLOWED_ROLE_NAME` (default: "RobloxDev")

### 3. Add Bot to Server

1. In Discord Developer Portal, go to OAuth2 → URL Generator
2. Select "bot" scope and required permissions
3. Use the generated URL to add the bot to your server
4. Create a role with the name specified in `ALLOWED_ROLE_NAME` and assign it to users who should access the bot

## Commands

- `!help` - Display help information and available commands
- `!upload` - Upload a Roblox game file (attach .rbxl or .rbxlx file to the message)
- `!publish <file_id>` - Publish an uploaded game file (mock functionality)
- `!status` - Check bot status and statistics
- `!cleanup <hours>` - Clean up old uploaded files (admin only)

## Access Control

Only users with the specified role (default: "RobloxDev") can use any bot commands. Users without the role will receive an access denied message.

## File Requirements

- **Supported formats**: .rbxl (binary) and .rbxlx (XML) Roblox game files
- **Maximum file size**: 100MB
- **Validation**: Files are automatically validated for proper Roblox game structure

## Running the Bot

```bash
python bot.py
```

The bot will automatically:
- Create necessary storage directories
- Load all commands and validation systems
- Connect to Discord using the provided token
- Start listening for commands from authorized users