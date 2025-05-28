import os
import zipfile
import xml.etree.ElementTree as ET
from typing import Tuple, Dict, Any
import logging

logger = logging.getLogger(__name__)

class RobloxFileValidator:
    """Validator class for Roblox game files"""
    
    @staticmethod
    def validate_file_extension(filename: str) -> bool:
        """Check if file has valid Roblox extension"""
        valid_extensions = ['.rbxl', '.rbxlx']
        return any(filename.lower().endswith(ext) for ext in valid_extensions)
    
    @staticmethod
    def validate_file_size(file_size: int, max_size: int = 100 * 1024 * 1024) -> bool:
        """Check if file size is within limits"""
        return file_size <= max_size
    
    @staticmethod
    def get_file_type(filename: str) -> str:
        """Determine Roblox file type"""
        if filename.lower().endswith('.rbxlx'):
            return 'RBXLX'
        elif filename.lower().endswith('.rbxl'):
            return 'RBXL'
        return 'UNKNOWN'
    
    @staticmethod
    def validate_rbxlx_structure(file_path: str) -> Tuple[bool, str, Dict[str, Any]]:
        """Validate RBXLX XML structure"""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Check root tag
            if root.tag.lower() != 'roblox':
                return False, "Invalid root tag (expected 'roblox')", {}
            
            # Check for essential services
            services_found = []
            workspace_found = False
            
            for item in root.iter('Item'):
                class_name = item.get('class', '')
                if class_name:
                    services_found.append(class_name)
                    if class_name == 'Workspace':
                        workspace_found = True
            
            if not workspace_found:
                return False, "Missing Workspace service", {}
            
            metadata = {
                'services_count': len(set(services_found)),
                'services': list(set(services_found)),
                'has_workspace': workspace_found
            }
            
            return True, "Valid RBXLX structure", metadata
            
        except ET.ParseError as e:
            return False, f"XML parsing error: {str(e)}", {}
        except Exception as e:
            return False, f"Validation error: {str(e)}", {}
    
    @staticmethod
    def validate_rbxl_structure(file_path: str) -> Tuple[bool, str, Dict[str, Any]]:
        """Validate RBXL binary structure"""
        try:
            with open(file_path, 'rb') as f:
                # Read file header
                header = f.read(256)
                
                # Basic signature check for Roblox binary files
                # Note: Actual RBXL format is complex and proprietary
                if b'<roblox' in header.lower() or b'roblox' in header.lower():
                    metadata = {
                        'format': 'binary',
                        'header_check': 'passed'
                    }
                    return True, "Valid RBXL format detected", metadata
                else:
                    return False, "Invalid RBXL format", {}
                    
        except Exception as e:
            return False, f"Binary validation error: {str(e)}", {}
    
    @staticmethod
    def extract_game_metadata(file_path: str) -> Dict[str, Any]:
        """Extract metadata from Roblox game file"""
        metadata = {
            'name': 'Unknown Game',
            'description': '',
            'creator': 'Unknown',
            'file_size': 0,
            'file_type': 'Unknown'
        }
        
        try:
            # Get file stats
            stat = os.stat(file_path)
            metadata['file_size'] = stat.st_size
            
            filename = os.path.basename(file_path)
            metadata['file_type'] = RobloxFileValidator.get_file_type(filename)
            
            if filename.lower().endswith('.rbxlx'):
                # Try to extract XML metadata
                try:
                    tree = ET.parse(file_path)
                    root = tree.getroot()
                    
                    # Look for game name in Workspace or other services
                    for item in root.iter('Item'):
                        if item.get('class') == 'Workspace':
                            for props in item.iter('Properties'):
                                for string_prop in props.iter('string'):
                                    if string_prop.get('name') == 'Name':
                                        if string_prop.text:
                                            metadata['name'] = string_prop.text
                                        break
                            break
                    
                    # Count services for additional info
                    services = set()
                    for item in root.iter('Item'):
                        class_name = item.get('class')
                        if class_name:
                            services.add(class_name)
                    
                    metadata['services_count'] = len(services)
                    metadata['services'] = list(services)
                    
                except ET.ParseError:
                    pass  # Keep default metadata if parsing fails
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
        
        return metadata
