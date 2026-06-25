"""
Authentication and Authorization Module
Implements Role-Based Access Control (RBAC) for government security standards
"""

from typing import Dict, List, Tuple
from datetime import datetime
import hashlib
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class User:
    """Represents a system user with role-based permissions"""
    
    def __init__(self, user_id: str, username: str, role: str, badge_id: str = None):
        """
        Initialize user
        
        Args:
            user_id (str): Unique user identifier
            username (str): Username for login
            role (str): User role (field_officer, commander, data_analyst, admin)
            badge_id (str): Police badge/employee ID for audit trail
        """
        self.user_id = user_id
        self.username = username
        self.role = role
        self.badge_id = badge_id
        self.is_authenticated = False
        self.last_login = None
        self.login_history = []
    
    def __repr__(self):
        return f"User(id={self.user_id}, role={self.role})"


class RoleBasedAccessControl:
    """
    Manages role-based access control and permission enforcement
    Ensures security compliance with government standards
    """
    
    # Define role permissions
    ROLE_PERMISSIONS = {
        'field_officer': {
            'view_dashboard': True,
            'view_maps': True,
            'classify_crime': True,
            'view_audit_logs': False,
            'modify_models': False,
            'export_reports': False,
            'admin_panel': False
        },
        'commander': {
            'view_dashboard': True,
            'view_maps': True,
            'classify_crime': True,
            'view_audit_logs': True,
            'modify_models': False,
            'export_reports': True,
            'admin_panel': False
        },
        'data_analyst': {
            'view_dashboard': True,
            'view_maps': True,
            'classify_crime': False,
            'view_audit_logs': True,
            'modify_models': True,
            'export_reports': True,
            'admin_panel': True
        },
        'admin': {
            'view_dashboard': True,
            'view_maps': True,
            'classify_crime': True,
            'view_audit_logs': True,
            'modify_models': True,
            'export_reports': True,
            'admin_panel': True
        }
    }
    
    def __init__(self):
        """Initialize RBAC system"""
        self.users: Dict[str, User] = {}
        self.active_sessions = {}
        self.audit_log = []
    
    def register_user(self, user_id: str, username: str, role: str, badge_id: str = None) -> User:
        """
        Register new user in system
        
        Args:
            user_id (str): Unique user ID
            username (str): Username
            role (str): User role
            badge_id (str): Police badge ID
            
        Returns:
            User: Created user object
        """
        if user_id in self.users:
            raise ValueError(f"User {user_id} already registered")
        
        if role not in self.ROLE_PERMISSIONS:
            raise ValueError(f"Invalid role: {role}")
        
        user = User(user_id, username, role, badge_id)
        self.users[user_id] = user
        
        self._log_audit_event(f"User registered: {username} ({role})")
        logger.info(f"User registered: {username} with role {role}")
        
        return user
    
    def authenticate_user(self, user_id: str, password_hash: str) -> Tuple[bool, str]:
        """
        Authenticate user login (simplified for demo)
        
        Args:
            user_id (str): User ID
            password_hash (str): Password hash
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        if user_id not in self.users:
            self._log_audit_event(f"Login failed: Unknown user {user_id}")
            return False, "User not found"
        
        user = self.users[user_id]
        user.is_authenticated = True
        user.last_login = datetime.now()
        user.login_history.append(datetime.now())
        
        session_token = self._generate_session_token(user_id)
        self.active_sessions[user_id] = {
            'token': session_token,
            'timestamp': datetime.now(),
            'role': user.role
        }
        
        self._log_audit_event(f"User authenticated: {user.username} ({user.role})")
        logger.info(f"User {user.username} authenticated successfully")
        
        return True, session_token
    
    def check_permission(self, user_id: str, permission: str) -> bool:
        """
        Check if user has permission for action
        
        Args:
            user_id (str): User ID
            permission (str): Permission name
            
        Returns:
            bool: True if user has permission
        """
        if user_id not in self.users:
            logger.warning(f"Permission check for unknown user {user_id}")
            return False
        
        user = self.users[user_id]
        if user.role not in self.ROLE_PERMISSIONS:
            logger.warning(f"Unknown role: {user.role}")
            return False
        
        has_permission = self.ROLE_PERMISSIONS[user.role].get(permission, False)
        
        if not has_permission:
            self._log_audit_event(
                f"Permission denied: {user.username} attempted {permission}"
            )
            logger.warning(f"Permission denied for {user.username}: {permission}")
        
        return has_permission
    
    def get_user_permissions(self, user_id: str) -> Dict[str, bool]:
        """
        Get all permissions for a user
        
        Args:
            user_id (str): User ID
            
        Returns:
            Dict: User permissions
        """
        if user_id not in self.users:
            raise ValueError(f"User {user_id} not found")
        
        user = self.users[user_id]
        return self.ROLE_PERMISSIONS.get(user.role, {})
    
    def logout_user(self, user_id: str) -> bool:
        """
        Log out user and close session
        
        Args:
            user_id (str): User ID
            
        Returns:
            bool: Success status
        """
        if user_id in self.active_sessions:
            del self.active_sessions[user_id]
            user = self.users.get(user_id)
            if user:
                self._log_audit_event(f"User logged out: {user.username}")
                logger.info(f"User {user.username} logged out")
            return True
        return False
    
    def _generate_session_token(self, user_id: str) -> str:
        """
        Generate secure session token
        
        Args:
            user_id (str): User ID
            
        Returns:
            str: Session token
        """
        data = f"{user_id}{datetime.now().isoformat()}".encode()
        return hashlib.sha256(data).hexdigest()
    
    def _log_audit_event(self, event: str) -> None:
        """
        Log security audit event
        
        Args:
            event (str): Event description
        """
        audit_entry = {
            'timestamp': datetime.now().isoformat(),
            'event': event
        }
        self.audit_log.append(audit_entry)
    
    def get_audit_log(self, limit: int = 100) -> List[Dict]:
        """
        Retrieve audit log entries
        
        Args:
            limit (int): Maximum entries to return
            
        Returns:
            List[Dict]: Audit log entries
        """
        return self.audit_log[-limit:]
    
    def is_session_valid(self, user_id: str) -> bool:
        """
        Check if user session is valid
        
        Args:
            user_id (str): User ID
            
        Returns:
            bool: Session validity
        """
        return user_id in self.active_sessions and self.users[user_id].is_authenticated


if __name__ == "__main__":
    # Example usage
    rbac = RoleBasedAccessControl()
    
    # Register users
    officer = rbac.register_user("001", "officer_john", "field_officer", "BADGE-001")
    commander = rbac.register_user("002", "commander_maria", "commander", "BADGE-002")
    analyst = rbac.register_user("003", "analyst_bob", "data_analyst", "BADGE-003")
    
    # Authenticate
    # rbac.authenticate_user("001", "password")
    
    # Check permissions
    # print(rbac.check_permission("001", "view_dashboard"))
    # print(rbac.check_permission("001", "modify_models"))
