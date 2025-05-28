import os

class Config:
    """Configuration settings for the Discord bot"""
    
    # Bot settings
    COMMAND_PREFIX = os.getenv('COMMAND_PREFIX', '!')
    
    # File settings
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB in bytes
    ALLOWED_EXTENSIONS = ['.rbxl', '.rbxlx']
    UPLOAD_DIR = 'storage/uploads'
    
    # Discord settings
    MAX_MESSAGE_LENGTH = 2000
    
    # Roblox file validation
    RBXLX_REQUIRED_TAGS = ['roblox']
    RBXL_MAGIC_BYTES = b'<roblox'
    
    # Colors for embeds
    COLOR_SUCCESS = 0x00ff00
    COLOR_ERROR = 0xff0000
    COLOR_WARNING = 0xffaa00
    COLOR_INFO = 0x0099ff
    
    # Roblox publishing settings
    PUBLISH_DELAY = 3  # seconds to simulate publishing process
    ROBLOX_API_BASE = "https://apis.roblox.com"
    ROBLOX_UPLOAD_API = "https://data.roblox.com"
    
    # Access control settings
    ALLOWED_ROLE_ID = os.getenv('ALLOWED_ROLE_ID', '1376841148336836608')  # Your specific role ID
    ALLOWED_ROLE_NAME = os.getenv('ALLOWED_ROLE_NAME', 'RobloxDev')  # Fallback to role name if ID not set
