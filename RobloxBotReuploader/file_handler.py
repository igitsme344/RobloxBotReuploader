import aiofiles
import asyncio
import os
import uuid
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Optional, Tuple
import logging

from config import Config
from validators import RobloxFileValidator

logger = logging.getLogger(__name__)

class FileHandler:
    """Handles file operations for Roblox game files"""
    
    @staticmethod
    async def save_attachment(attachment, user_id: int) -> Tuple[bool, str, Optional[str]]:
        """
        Save Discord attachment to storage
        Returns: (success, message, file_path)
        """
        try:
            # Validate file extension
            if not any(attachment.filename.lower().endswith(ext) for ext in Config.ALLOWED_EXTENSIONS):
                return False, f"Invalid file type. Allowed extensions: {', '.join(Config.ALLOWED_EXTENSIONS)}", None
            
            # Check file size
            if attachment.size > Config.MAX_FILE_SIZE:
                size_mb = Config.MAX_FILE_SIZE / (1024 * 1024)
                return False, f"File too large. Maximum size: {size_mb}MB", None
            
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            filename = f"{user_id}_{timestamp}_{unique_id}_{attachment.filename}"
            file_path = os.path.join(Config.UPLOAD_DIR, filename)
            
            # Download and save file
            async with aiofiles.open(file_path, 'wb') as f:
                async for chunk in attachment.iter_chunked(1024):
                    await f.write(chunk)
            
            logger.info(f"File saved: {file_path}")
            return True, "File uploaded successfully", file_path
            
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            return False, f"Failed to save file: {str(e)}", None
    
    @staticmethod
    async def validate_roblox_file(file_path: str) -> Tuple[bool, str, dict]:
        """
        Validate if the file is a legitimate Roblox game file
        Returns: (is_valid, message, file_info)
        """
        try:
            file_info = {
                'type': None,
                'size': 0,
                'name': None,
                'description': None,
                'creator': None
            }
            
            # Get file stats
            stat = os.stat(file_path)
            file_info['size'] = stat.st_size
            
            filename = os.path.basename(file_path)
            extension = os.path.splitext(filename)[1].lower()
            
            if extension == '.rbxlx':
                is_valid, message, info = await FileHandler._validate_rbxlx(file_path)
            elif extension == '.rbxl':
                is_valid, message, info = await FileHandler._validate_rbxl(file_path)
            else:
                return False, "Unsupported file format", file_info
            
            file_info.update(info)
            return is_valid, message, file_info
            
        except Exception as e:
            logger.error(f"Error validating file: {e}")
            return False, f"Validation failed: {str(e)}", file_info
    
    @staticmethod
    async def _validate_rbxlx(file_path: str) -> Tuple[bool, str, dict]:
        """Validate RBXLX (XML) file"""
        info = {'type': 'RBXLX (XML)'}
        
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            
            # Parse XML
            root = ET.fromstring(content)
            
            # Check if it's a Roblox file
            if root.tag.lower() != 'roblox':
                return False, "Not a valid Roblox file (missing roblox root tag)", info
            
            # Extract game information
            info['name'] = root.get('name', 'Unknown')
            
            # Look for game metadata
            for item in root.iter('Item'):
                if item.get('class') == 'Workspace':
                    workspace = item
                    for prop in workspace.iter('Properties'):
                        for name_prop in prop.iter('string'):
                            if name_prop.get('name') == 'Name':
                                info['name'] = name_prop.text or 'Untitled Game'
                                break
                    break
            
            # Basic structure validation
            has_workspace = any(item.get('class') == 'Workspace' for item in root.iter('Item'))
            has_services = len(list(root.iter('Item'))) > 0
            
            if not has_workspace:
                return False, "Invalid Roblox file structure (missing Workspace)", info
            
            if not has_services:
                return False, "Invalid Roblox file structure (no services found)", info
            
            return True, "Valid RBXLX file", info
            
        except ET.ParseError as e:
            return False, f"Invalid XML format: {str(e)}", info
        except UnicodeDecodeError:
            return False, "File encoding error (not valid UTF-8)", info
        except Exception as e:
            return False, f"Validation error: {str(e)}", info
    
    @staticmethod
    async def _validate_rbxl(file_path: str) -> Tuple[bool, str, dict]:
        """Validate RBXL (binary) file"""
        info = {'type': 'RBXL (Binary)'}
        
        try:
            async with aiofiles.open(file_path, 'rb') as f:
                header = await f.read(1024)  # Read first 1KB for validation
            
            # Check for Roblox binary signature
            if not header.startswith(b'<roblox'):
                # Try to check if it's a compressed/binary format
                if b'ROBLOX' not in header.upper() and b'workspace' not in header.lower():
                    return False, "Not a valid Roblox binary file", info
            
            # For binary files, we can't easily extract detailed info
            # but we can perform basic structural checks
            info['name'] = 'Binary Roblox Game'
            
            return True, "Valid RBXL file", info
            
        except Exception as e:
            return False, f"Validation error: {str(e)}", info
    
    @staticmethod
    async def mock_publish_game(file_path: str, user_id: int) -> Tuple[bool, str, dict]:
        """
        Mock the game publishing process
        Returns: (success, message, publish_info)
        """
        try:
            # Simulate processing time
            await asyncio.sleep(Config.MOCK_PUBLISH_DELAY)
            
            # Generate mock publish information
            publish_info = {
                'game_id': f"mock_{uuid.uuid4().hex[:12]}",
                'universe_id': f"universe_{uuid.uuid4().hex[:8]}",
                'place_id': f"place_{uuid.uuid4().hex[:10]}",
                'published_at': datetime.now().isoformat(),
                'status': 'published',
                'visibility': 'private',
                'url': f"https://www.roblox.com/games/mock_{uuid.uuid4().hex[:12]}"
            }
            
            logger.info(f"Mock published game for user {user_id}: {publish_info['game_id']}")
            return True, "Game published successfully!", publish_info
            
        except Exception as e:
            logger.error(f"Mock publish error: {e}")
            return False, f"Publishing failed: {str(e)}", {}
    
    @staticmethod
    async def cleanup_old_files(max_age_hours: int = 24):
        """Clean up old uploaded files"""
        try:
            current_time = datetime.now().timestamp()
            deleted_count = 0
            
            for filename in os.listdir(Config.UPLOAD_DIR):
                if filename == '.gitkeep':
                    continue
                    
                file_path = os.path.join(Config.UPLOAD_DIR, filename)
                file_time = os.path.getctime(file_path)
                
                age_hours = (current_time - file_time) / 3600
                
                if age_hours > max_age_hours:
                    os.remove(file_path)
                    deleted_count += 1
                    logger.info(f"Deleted old file: {filename}")
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old files")
                
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
