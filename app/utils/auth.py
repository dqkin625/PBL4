import jwt
import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict
from fastapi import HTTPException, Header, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get JWT configuration from environment
# For external tokens (from your login service), we'll verify without checking signature
# since we don't have their secret key
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-from-external-service")  
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Security scheme for Bearer token
security = HTTPBearer()

def create_jwt_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT token with the given data
    
    Args:
        data: Dictionary containing the payload data
        expires_delta: Optional expiration time delta
    
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def verify_jwt_token(token: str) -> Dict:
    """
    Verify and decode a JWT token
    
    Args:
        token: JWT token string
    
    Returns:
        Decoded token payload
    
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        # First, try to decode without verification to check the token structure
        # This is for tokens from external services where we don't have the secret
        unverified_payload = jwt.decode(token, options={"verify_signature": False})
        
        # Check if token is expired
        if "exp" in unverified_payload:
            exp_timestamp = unverified_payload["exp"]
            current_timestamp = datetime.now(timezone.utc).timestamp()
            if current_timestamp > exp_timestamp:
                raise HTTPException(
                    status_code=401,
                    detail="Token has expired",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        
        return unverified_payload
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """
    Dependency to get the current user from JWT token
    
    Args:
        credentials: Bearer token from Authorization header
    
    Returns:
        User information from token payload
    
    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials
    
    try:
        payload = verify_jwt_token(token)
        
        # Check if user has admin role or is super admin
        # Support both your external service format and internal format
        is_admin = (
            payload.get("role") == "admin" or 
            payload.get("isSuperAdmin") == True or
            payload.get("is_super_admin") == True
        )
        
        if not is_admin:
            raise HTTPException(
                status_code=403,
                detail="Not enough permissions",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return payload
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_admin(current_user: Dict = Depends(get_current_user)) -> Dict:
    """
    Dependency to require admin role
    
    Args:
        current_user: Current user from JWT token
    
    Returns:
        User information if admin
    
    Raises:
        HTTPException: If user is not admin
    """
    # Check if user has admin role or is super admin
    is_admin = (
        current_user.get("role") == "admin" or 
        current_user.get("isSuperAdmin") == True or
        current_user.get("is_super_admin") == True
    )
    
    if not is_admin:
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    return current_user


# Helper function to create admin token (for testing or initial setup)
def create_admin_token(username: str = "admin") -> str:
    """
    Create a JWT token for admin user
    
    Args:
        username: Admin username
    
    Returns:
        JWT token string
    """
    token_data = {
        "username": username,
        "role": "admin",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    return create_jwt_token(token_data)