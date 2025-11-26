"""
Workspace File Service

Provides direct access to agent workspace files via shared Docker volume.
This service reads/writes files directly from the mounted volume instead of
making API calls to the container.
"""

import os
import stat
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime


class WorkspaceService:
    """Service for accessing agent workspace files via shared volume"""
    
    # Base path for the mounted volume
    VOLUME_BASE_PATH = os.environ.get("WORKSPACE_VOLUME_PATH", "/mnt/volume")
    
    # Default workspace directory inside session folder
    DEFAULT_WORKSPACE_DIR = "workspace"
    
    def __init__(self, session_id: str):
        """
        Initialize workspace service for a session.
        
        Args:
            session_id: The session identifier
        """
        self.session_id = session_id
        self.session_path = Path(self.VOLUME_BASE_PATH) / session_id
        self.workspace_path = self.session_path / self.DEFAULT_WORKSPACE_DIR
    
    def ensure_workspace_exists(self) -> bool:
        """
        Ensure the workspace directory exists.
        
        Returns:
            True if workspace exists or was created, False otherwise
        """
        try:
            self.workspace_path.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            print(f"Failed to create workspace directory: {e}")
            return False
    
    def get_workspace_root(self) -> str:
        """Get the absolute path to the workspace root"""
        return str(self.workspace_path)
    
    def _resolve_path(self, relative_path: str) -> Path:
        """
        Resolve a relative path to an absolute path within the workspace.
        Prevents path traversal attacks.
        
        Args:
            relative_path: Path relative to workspace root
            
        Returns:
            Resolved absolute path
            
        Raises:
            ValueError: If path tries to escape workspace
        """
        # Normalize the path
        if relative_path.startswith('/'):
            relative_path = relative_path[1:]
        
        # Resolve to absolute path
        resolved = (self.workspace_path / relative_path).resolve()
        
        # Security check: ensure path is within workspace
        try:
            resolved.relative_to(self.workspace_path.resolve())
        except ValueError:
            raise ValueError(f"Path '{relative_path}' is outside workspace")
        
        return resolved
    
    def list_directory(self, path: str = "/") -> Dict[str, Any]:
        """
        List files and directories at the given path.
        
        Args:
            path: Path relative to workspace root
            
        Returns:
            Dictionary with path and entries list
        """
        self.ensure_workspace_exists()
        
        try:
            resolved_path = self._resolve_path(path)
            
            if not resolved_path.exists():
                # Return empty list for non-existent directories
                return {
                    "path": path,
                    "entries": [],
                    "exists": False
                }
            
            if not resolved_path.is_dir():
                raise ValueError(f"'{path}' is not a directory")
            
            entries = []
            for item in sorted(resolved_path.iterdir()):
                # Get relative path from workspace root
                rel_path = "/" + str(item.relative_to(self.workspace_path))
                
                entry = {
                    "name": item.name,
                    "path": rel_path,
                    "type": "directory" if item.is_dir() else "file"
                }
                
                # Add file-specific info
                if item.is_file():
                    try:
                        stat_info = item.stat()
                        entry["size"] = stat_info.st_size
                        entry["modified"] = datetime.fromtimestamp(stat_info.st_mtime).isoformat()
                    except OSError:
                        pass
                
                entries.append(entry)
            
            return {
                "path": path,
                "entries": entries,
                "exists": True
            }
            
        except ValueError:
            raise
        except Exception as e:
            raise Exception(f"Failed to list directory: {str(e)}")
    
    def read_file(self, path: str) -> Dict[str, Any]:
        """
        Read file content.
        
        Args:
            path: Path relative to workspace root
            
        Returns:
            Dictionary with path, content, and encoding
        """
        self.ensure_workspace_exists()
        
        try:
            resolved_path = self._resolve_path(path)
            
            if not resolved_path.exists():
                raise FileNotFoundError(f"File '{path}' not found")
            
            if not resolved_path.is_file():
                raise ValueError(f"'{path}' is not a file")
            
            # Try to read as text first
            try:
                content = resolved_path.read_text(encoding='utf-8')
                encoding = 'utf-8'
            except UnicodeDecodeError:
                # Fall back to binary (base64)
                import base64
                content = base64.b64encode(resolved_path.read_bytes()).decode('ascii')
                encoding = 'base64'
            
            stat_info = resolved_path.stat()
            
            return {
                "path": path,
                "content": content,
                "encoding": encoding,
                "size": stat_info.st_size,
                "modified": datetime.fromtimestamp(stat_info.st_mtime).isoformat()
            }
            
        except (FileNotFoundError, ValueError):
            raise
        except Exception as e:
            raise Exception(f"Failed to read file: {str(e)}")
    
    def write_file(self, path: str, content: str, encoding: str = 'utf-8') -> Dict[str, Any]:
        """
        Write content to a file.
        
        Args:
            path: Path relative to workspace root
            content: File content to write
            encoding: Content encoding ('utf-8' or 'base64')
            
        Returns:
            Dictionary with success status and file info
        """
        self.ensure_workspace_exists()
        
        try:
            resolved_path = self._resolve_path(path)
            
            # Create parent directories if needed
            resolved_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write content
            if encoding == 'base64':
                import base64
                resolved_path.write_bytes(base64.b64decode(content))
            else:
                resolved_path.write_text(content, encoding='utf-8')
            
            stat_info = resolved_path.stat()
            
            return {
                "path": path,
                "success": True,
                "size": stat_info.st_size,
                "modified": datetime.fromtimestamp(stat_info.st_mtime).isoformat()
            }
            
        except ValueError:
            raise
        except Exception as e:
            raise Exception(f"Failed to write file: {str(e)}")
    
    def delete_file(self, path: str) -> Dict[str, Any]:
        """
        Delete a file.
        
        Args:
            path: Path relative to workspace root
            
        Returns:
            Dictionary with success status
        """
        try:
            resolved_path = self._resolve_path(path)
            
            if not resolved_path.exists():
                raise FileNotFoundError(f"File '{path}' not found")
            
            if resolved_path.is_dir():
                raise ValueError(f"'{path}' is a directory, use delete_directory")
            
            resolved_path.unlink()
            
            return {
                "path": path,
                "success": True,
                "message": "File deleted successfully"
            }
            
        except (FileNotFoundError, ValueError):
            raise
        except Exception as e:
            raise Exception(f"Failed to delete file: {str(e)}")
    
    def create_directory(self, path: str) -> Dict[str, Any]:
        """
        Create a directory.
        
        Args:
            path: Path relative to workspace root
            
        Returns:
            Dictionary with success status
        """
        self.ensure_workspace_exists()
        
        try:
            resolved_path = self._resolve_path(path)
            resolved_path.mkdir(parents=True, exist_ok=True)
            
            return {
                "path": path,
                "success": True,
                "message": "Directory created successfully"
            }
            
        except ValueError:
            raise
        except Exception as e:
            raise Exception(f"Failed to create directory: {str(e)}")
    
    def delete_directory(self, path: str, recursive: bool = False) -> Dict[str, Any]:
        """
        Delete a directory.
        
        Args:
            path: Path relative to workspace root
            recursive: If True, delete directory and all contents
            
        Returns:
            Dictionary with success status
        """
        try:
            resolved_path = self._resolve_path(path)
            
            if not resolved_path.exists():
                raise FileNotFoundError(f"Directory '{path}' not found")
            
            if not resolved_path.is_dir():
                raise ValueError(f"'{path}' is not a directory")
            
            if recursive:
                import shutil
                shutil.rmtree(resolved_path)
            else:
                resolved_path.rmdir()  # Will fail if not empty
            
            return {
                "path": path,
                "success": True,
                "message": "Directory deleted successfully"
            }
            
        except (FileNotFoundError, ValueError):
            raise
        except OSError as e:
            if "not empty" in str(e).lower() or "directory not empty" in str(e).lower():
                raise ValueError(f"Directory '{path}' is not empty. Use recursive=True to delete")
            raise Exception(f"Failed to delete directory: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to delete directory: {str(e)}")
    
    def file_exists(self, path: str) -> bool:
        """Check if a file exists"""
        try:
            resolved_path = self._resolve_path(path)
            return resolved_path.is_file()
        except:
            return False
    
    def directory_exists(self, path: str) -> bool:
        """Check if a directory exists"""
        try:
            resolved_path = self._resolve_path(path)
            return resolved_path.is_dir()
        except:
            return False
    
    def rename_file(self, old_path: str, new_path: str) -> Dict[str, Any]:
        """
        Rename a file or directory.
        
        Args:
            old_path: Current path relative to workspace root
            new_path: New path relative to workspace root
            
        Returns:
            Dictionary with success status
        """
        try:
            resolved_old = self._resolve_path(old_path)
            resolved_new = self._resolve_path(new_path)
            
            if not resolved_old.exists():
                raise FileNotFoundError(f"Path '{old_path}' not found")
            
            if resolved_new.exists():
                raise ValueError(f"Destination '{new_path}' already exists")
            
            # Create parent directories for destination if needed
            resolved_new.parent.mkdir(parents=True, exist_ok=True)
            
            resolved_old.rename(resolved_new)
            
            return {
                "old_path": old_path,
                "new_path": new_path,
                "success": True,
                "message": "Renamed successfully"
            }
            
        except (FileNotFoundError, ValueError):
            raise
        except Exception as e:
            raise Exception(f"Failed to rename: {str(e)}")


def get_workspace_service(session_id: str) -> WorkspaceService:
    """Factory function to create a workspace service instance"""
    return WorkspaceService(session_id)
