import aiohttp
import asyncio
import json
import logging
from typing import Optional, Tuple, Dict, Any
from config import Config

logger = logging.getLogger(__name__)

class RobloxAPI:
    """Handles real Roblox API interactions for publishing games"""
    
    def __init__(self):
        self.session = None
    
    async def create_session(self):
        """Create aiohttp session if not exists"""
        if not self.session:
            self.session = aiohttp.ClientSession()
    
    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def get_user_info(self, cookie: str) -> Tuple[bool, str, Dict[str, Any]]:
        """Get user information from Roblox cookie"""
        try:
            await self.create_session()
            
            headers = {
                'Cookie': f'.ROBLOSECURITY={cookie}',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            async with self.session.get(
                'https://users.roblox.com/v1/users/authenticated',
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return True, "User authenticated", {
                        'id': data.get('id'),
                        'name': data.get('name'),
                        'displayName': data.get('displayName')
                    }
                else:
                    return False, f"Authentication failed: {response.status}", {}
                    
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return False, f"Error: {str(e)}", {}
    
    async def get_csrf_token(self, cookie: str) -> Tuple[bool, str]:
        """Get CSRF token needed for Roblox API requests"""
        try:
            await self.create_session()
            
            headers = {
                'Cookie': f'.ROBLOSECURITY={cookie}',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            # Make a request that will return the CSRF token in headers
            async with self.session.post(
                'https://auth.roblox.com/v2/logout',
                headers=headers
            ) as response:
                csrf_token = response.headers.get('x-csrf-token')
                if csrf_token:
                    return True, csrf_token
                else:
                    return False, "Could not get CSRF token"
                    
        except Exception as e:
            logger.error(f"Error getting CSRF token: {e}")
            return False, f"Error: {str(e)}"
    
    async def upload_place_file(self, cookie: str, file_path: str, place_id: Optional[int] = None) -> Tuple[bool, str, Dict[str, Any]]:
        """Upload a Roblox place file to Roblox"""
        try:
            await self.create_session()
            
            # Get CSRF token
            csrf_success, csrf_token = await self.get_csrf_token(cookie)
            if not csrf_success:
                return False, f"Failed to get CSRF token: {csrf_token}", {}
            
            headers = {
                'Cookie': f'.ROBLOSECURITY={cookie}',
                'X-CSRF-TOKEN': csrf_token,
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            # Read the file
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            if place_id:
                # Update existing place
                url = f'https://data.roblox.com/Data/Upload.ashx?assetid={place_id}'
            else:
                # Create new place
                url = 'https://data.roblox.com/Data/Upload.ashx?assetTypeId=9&name=New Place&description=Uploaded via Discord Bot'
            
            async with self.session.post(
                url,
                headers=headers,
                data=file_data
            ) as response:
                if response.status == 200:
                    response_text = await response.text()
                    
                    # Parse response (Roblox returns plain text with place ID)
                    if response_text.isdigit():
                        new_place_id = int(response_text)
                        return True, "Upload successful", {
                            'place_id': new_place_id,
                            'upload_type': 'update' if place_id else 'new'
                        }
                    else:
                        return False, f"Unexpected response: {response_text}", {}
                else:
                    error_text = await response.text()
                    return False, f"Upload failed ({response.status}): {error_text}", {}
                    
        except Exception as e:
            logger.error(f"Error uploading place file: {e}")
            return False, f"Upload error: {str(e)}", {}
    
    async def publish_place(self, cookie: str, place_id: int, name: str = None, description: str = None) -> Tuple[bool, str, Dict[str, Any]]:
        """Publish a place to make it accessible"""
        try:
            await self.create_session()
            
            # Get CSRF token
            csrf_success, csrf_token = await self.get_csrf_token(cookie)
            if not csrf_success:
                return False, f"Failed to get CSRF token: {csrf_token}", {}
            
            headers = {
                'Cookie': f'.ROBLOSECURITY={cookie}',
                'X-CSRF-TOKEN': csrf_token,
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            # Update place settings
            place_data = {
                'name': name or 'Discord Bot Upload',
                'description': description or 'Uploaded and published via Discord Bot'
            }
            
            async with self.session.patch(
                f'https://develop.roblox.com/v1/places/{place_id}',
                headers=headers,
                json=place_data
            ) as response:
                if response.status == 200:
                    return True, "Place published successfully", {
                        'place_id': place_id,
                        'name': name or 'Discord Bot Upload',
                        'url': f'https://www.roblox.com/games/{place_id}',
                        'edit_url': f'https://www.roblox.com/develop/places/{place_id}/overview'
                    }
                else:
                    error_text = await response.text()
                    return False, f"Publish failed ({response.status}): {error_text}", {}
                    
        except Exception as e:
            logger.error(f"Error publishing place: {e}")
            return False, f"Publish error: {str(e)}", {}
    
    async def get_place_info(self, place_id: int) -> Tuple[bool, str, Dict[str, Any]]:
        """Get information about a place"""
        try:
            await self.create_session()
            
            async with self.session.get(
                f'https://games.roblox.com/v1/games/multiget-place-details?placeIds={place_id}'
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data and len(data) > 0:
                        place_info = data[0]
                        return True, "Place info retrieved", {
                            'id': place_info.get('placeId'),
                            'name': place_info.get('name'),
                            'description': place_info.get('description'),
                            'url': place_info.get('url'),
                            'builder': place_info.get('builder')
                        }
                    else:
                        return False, "Place not found", {}
                else:
                    return False, f"Failed to get place info: {response.status}", {}
                    
        except Exception as e:
            logger.error(f"Error getting place info: {e}")
            return False, f"Error: {str(e)}", {}

# Global instance
roblox_api = RobloxAPI()