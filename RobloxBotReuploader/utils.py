import os
import hashlib
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class Utils:
    """Utility functions for the Discord bot"""
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.2f} {size_names[i]}"
    
    @staticmethod
    def calculate_file_hash(file_path: str) -> str:
        """Calculate SHA256 hash of a file"""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating file hash: {e}")
            return ""
    
    @staticmethod
    def is_file_expired(file_path: str, max_age_hours: int = 24) -> bool:
        """Check if a file is older than the specified age"""
        try:
            file_time = os.path.getctime(file_path)
            current_time = datetime.now().timestamp()
            age_hours = (current_time - file_time) / 3600
            return age_hours > max_age_hours
        except Exception as e:
            logger.error(f"Error checking file age: {e}")
            return False
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename to prevent path traversal and other issues"""
        # Remove path separators and other dangerous characters
        dangerous_chars = ['/', '\\', '..', '<', '>', ':', '"', '|', '?', '*']
        
        sanitized = filename
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '_')
        
        # Limit filename length
        if len(sanitized) > 100:
            name, ext = os.path.splitext(sanitized)
            sanitized = name[:95] + ext
        
        return sanitized
    
    @staticmethod
    def create_embed_from_template(title: str, description: str, color: int, fields: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a Discord embed template"""
        embed_data = {
            "title": title,
            "description": description,
            "color": color,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if fields:
            embed_data["fields"] = fields
        
        return embed_data
    
    @staticmethod
    async def async_file_operation(operation, *args, **kwargs):
        """Execute a file operation asynchronously"""
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(None, operation, *args, **kwargs)
        except Exception as e:
            logger.error(f"Async file operation error: {e}")
            raise
    
    @staticmethod
    def get_file_info(file_path: str) -> Dict[str, Any]:
        """Get comprehensive file information"""
        try:
            stat = os.stat(file_path)
            return {
                'size': stat.st_size,
                'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'accessed': datetime.fromtimestamp(stat.st_atime).isoformat(),
                'name': os.path.basename(file_path),
                'extension': os.path.splitext(file_path)[1],
                'directory': os.path.dirname(file_path)
            }
        except Exception as e:
            logger.error(f"Error getting file info: {e}")
            return {}
    
    @staticmethod
    def validate_discord_message_length(content: str, max_length: int = 2000) -> bool:
        """Validate if message content fits Discord's limits"""
        return len(content) <= max_length
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 1000, suffix: str = "...") -> str:
        """Truncate text to fit within specified length"""
        if len(text) <= max_length:
            return text
        
        return text[:max_length - len(suffix)] + suffix
    
    @staticmethod
    def format_timestamp(timestamp: str) -> str:
        """Format ISO timestamp to readable format"""
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        except Exception as e:
            logger.error(f"Error formatting timestamp: {e}")
            return timestamp
    
    @staticmethod
    def get_storage_stats(directory: str) -> Dict[str, Any]:
        """Get storage statistics for a directory"""
        try:
            total_size = 0
            file_count = 0
            file_types = {}
            
            for filename in os.listdir(directory):
                if filename == '.gitkeep':
                    continue
                    
                file_path = os.path.join(directory, filename)
                if os.path.isfile(file_path):
                    file_size = os.path.getsize(file_path)
                    total_size += file_size
                    file_count += 1
                    
                    # Track file types
                    ext = os.path.splitext(filename)[1].lower()
                    file_types[ext] = file_types.get(ext, 0) + 1
            
            return {
                'total_size': total_size,
                'total_size_formatted': Utils.format_file_size(total_size),
                'file_count': file_count,
                'file_types': file_types,
                'average_file_size': total_size / file_count if file_count > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting storage stats: {e}")
            return {
                'total_size': 0,
                'total_size_formatted': '0 B',
                'file_count': 0,
                'file_types': {},
                'average_file_size': 0
            }
