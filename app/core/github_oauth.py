"""
GitHub OAuth service for handling authentication and token management
"""
import os
import httpx
import json
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from urllib.parse import urlencode

from app.core.models import User
from app.core.config import settings


class GitHubOAuthService:
    """Service for handling GitHub OAuth flow"""

    BASE_URL = "https://github.com"
    API_URL = "https://api.github.com"

    def __init__(self):
        self.client_id = os.getenv("GITHUB_CLIENT_ID")
        self.client_secret = os.getenv("GITHUB_CLIENT_SECRET")
        self.callback_url = os.getenv("GITHUB_CALLBACK_URL")
        
        if not all([self.client_id, self.client_secret, self.callback_url]):
            raise ValueError("Missing GitHub OAuth configuration in environment variables")

    def get_authorization_url(self, state: str) -> str:
        """Generate GitHub authorization URL"""
        # For GitHub Apps, we don't specify scopes in the URL
        # Permissions are set at the app level in GitHub settings
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.callback_url,
            "state": state,
            "allow_signup": "true"
        }
        return f"{self.BASE_URL}/login/oauth/authorize?{urlencode(params)}"

    async def get_device_code(self) -> Dict[str, Any]:
        """Get device code for GitHub OAuth device flow"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/login/device/code",
                data={
                    "client_id": self.client_id,
                    "scope": "read:user repo gist"  # Add back scopes for device flow
                },
                headers={"Accept": "application/json"},
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()

    async def poll_for_token(self, device_code: str, interval: int = 5, expires_in: int = 900) -> Dict[str, Any]:
        """Poll for access token using device code"""
        import time
        start_time = time.time()
        max_wait_time = expires_in  # Use the expires_in from device code response
        
        async with httpx.AsyncClient() as client:
            while True:
                # Check if we've exceeded the maximum wait time
                elapsed_time = time.time() - start_time
                if elapsed_time > max_wait_time:
                    raise Exception("Device code expired. Please request a new device code.")
                
                response = await client.post(
                    f"{self.BASE_URL}/login/oauth/access_token",
                    data={
                        "client_id": self.client_id,
                        "device_code": device_code,
                        "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                    },
                    headers={"Accept": "application/json"},
                    timeout=30.0
                )
                
                token_data = response.json()
                
                if "access_token" in token_data:
                    return token_data
                elif token_data.get("error") == "authorization_pending":
                    await asyncio.sleep(interval)
                    continue
                elif token_data.get("error") == "slow_down":
                    await asyncio.sleep(interval + 5)
                    continue
                elif token_data.get("error") == "expired_token":
                    raise Exception("Device code expired. Please request a new device code.")
                elif token_data.get("error") == "access_denied":
                    raise Exception("User denied authorization.")
                else:
                    raise Exception(f"Device code authorization failed: {token_data.get('error_description', token_data.get('error'))}")

    async def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/login/oauth/access_token",
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "redirect_uri": self.callback_url,
                },
                headers={"Accept": "application/json"},
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()

    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Fetch GitHub user information"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.API_URL}/user",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github.v3+json",
                },
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()

    async def get_user_email(self, access_token: str) -> Optional[str]:
        """Fetch GitHub user primary email"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.API_URL}/user/emails",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Accept": "application/vnd.github.v3+json",
                    },
                    timeout=30.0
                )
                
                if response.status_code == 403:
                    print(f"GitHub API 403 Forbidden for emails endpoint. Response: {response.text}")
                    print(f"Token being used: {access_token[:20]}...")
                    # Try to get user info first to check if token is valid
                    user_response = await client.get(
                        f"{self.API_URL}/user",
                        headers={
                            "Authorization": f"Bearer {access_token}",
                            "Accept": "application/vnd.github.v3+json",
                        },
                        timeout=30.0
                    )
                    print(f"User info response status: {user_response.status_code}")
                    if user_response.status_code == 200:
                        user_data = user_response.json()
                        print(f"User data: {user_data}")
                        # Return email from user endpoint if available
                        return user_data.get("email")
                    else:
                        print(f"User info also failed: {user_response.text}")
                
                response.raise_for_status()
                emails = response.json()
                
                # Find primary email
                for email_obj in emails:
                    if email_obj.get("primary"):
                        return email_obj.get("email")
                
                # Fallback to first verified email
                for email_obj in emails:
                    if email_obj.get("verified"):
                        return email_obj.get("email")
                
                return None
        except Exception as e:
            print(f"Error fetching user email: {str(e)}")
            # Try fallback to user endpoint
            try:
                async with httpx.AsyncClient() as client:
                    user_response = await client.get(
                        f"{self.API_URL}/user",
                        headers={
                            "Authorization": f"Bearer {access_token}",
                            "Accept": "application/vnd.github.v3+json",
                        },
                        timeout=30.0
                    )
                    if user_response.status_code == 200:
                        user_data = user_response.json()
                        return user_data.get("email")
            except Exception as fallback_error:
                print(f"Fallback also failed: {str(fallback_error)}")
            
            return None

    async def authenticate_user(self, auth_input: str, db: Session, is_token: bool = False) -> Dict[str, Any]:
        """Complete OAuth flow and save user to database"""
        try:
            if is_token:
                # auth_input is already an access token from device flow
                access_token = auth_input
                refresh_token = None
                token_type = "bearer"
                expires_in = None
            else:
                # auth_input is an authorization code from web flow
                token_response = await self.exchange_code_for_token(auth_input)
                
                if "error" in token_response:
                    raise Exception(f"GitHub OAuth error: {token_response.get('error_description')}")

                access_token = token_response.get("access_token")
                refresh_token = token_response.get("refresh_token")
                token_type = token_response.get("token_type")
                expires_in = token_response.get("expires_in")

            # Fetch user info
            user_info = await self.get_user_info(access_token)
            
            # Try to get email, but don't fail if it doesn't work
            user_email = None
            try:
                user_email = await self.get_user_email(access_token)
            except Exception as email_error:
                # Use email from user info as fallback
                user_email = user_info.get("email")

            # Calculate token expiration
            token_expires_at = None
            if expires_in:
                token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

            # Find or create user in database
            user_id = str(user_info.get("id"))
            user = db.query(User).filter(User.github_id == user_id).first()

            if user:
                # Update existing user
                user.access_token = access_token
                user.refresh_token = refresh_token or user.refresh_token
                user.token_expires_at = token_expires_at
                user.last_login = datetime.utcnow()
            else:
                # Create new user
                user = User(
                    id=user_id,
                    github_login=user_info.get("login"),
                    github_id=user_id,
                    email=user_email or user_info.get("email"),
                    avatar_url=user_info.get("avatar_url"),
                    access_token=access_token,
                    refresh_token=refresh_token,
                    token_expires_at=token_expires_at,
                    last_login=datetime.utcnow(),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(user)

            db.commit()
            db.refresh(user)

            return {
                "user": user,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": token_type,
                "expires_in": expires_in,
                "token_expires_at": token_expires_at.isoformat() if token_expires_at else None
            }

        except Exception as e:
            db.rollback()
            raise

    async def refresh_access_token(self, user: User) -> Dict[str, Any]:
        """Refresh GitHub access token using refresh token"""
        if not user.refresh_token:
            raise Exception("No refresh token available for this user")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/login/oauth/access_token",
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "grant_type": "refresh_token",
                    "refresh_token": user.refresh_token,
                },
                headers={"Accept": "application/json"},
                timeout=30.0
            )
            response.raise_for_status()
            token_response = response.json()

            if "error" in token_response:
                raise Exception(f"Token refresh error: {token_response.get('error_description')}")

            return token_response


# Global instance
github_oauth_service = GitHubOAuthService()
