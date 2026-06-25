"""
Immutable Audit Logging System
Tracks all predictions, user actions, and system events for compliance
"""

import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
from enum import Enum
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Audit event types"""
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    CRIME_PREDICTION = "crime_prediction"
    DATA_ACCESS = "data_access"
    MODEL_TRAINING = "model_training"
    MODEL_UPDATE = "model_update"
    REPORT_EXPORT = "report_export"
    PERMISSION_DENIED = "permission_denied"
    DATA_ANONYMIZATION = "data_anonymization"
    SYSTEM_ERROR = "system_error"


class AuditLog:
    """
    Immutable audit logging system for government compliance
    Records every prediction, user action, and system event
    """
    
    def __init__(self, write_once_path: str = "logs/audit_trail.jsonl"):
        """
        Initialize audit logger
        
        Args:
            write_once_path (str): Path to immutable audit log file
        """
        self.write_once_path = write_once_path
        self.audit_entries = []
        self._ensure_log_file_exists()
    
    def _ensure_log_file_exists(self) -> None:
        """Create audit log file if it doesn't exist"""
        try:
            import os
            os.makedirs(os.path.dirname(self.write_once_path), exist_ok=True)
            if not os.path.exists(self.write_once_path):
                with open(self.write_once_path, 'w') as f:
                    pass
                logger.info(f"Created audit log file: {self.write_once_path}")
        except Exception as e:
            logger.error(f"Error creating audit log: {str(e)}")
    
    def log_prediction(
        self,
        user_id: str,
        user_role: str,
        input_features: Dict[str, Any],
        predicted_class: int,
        confidence_score: float,
        feature_importance: Dict[str, float],
        timestamp: Optional[datetime] = None
    ) -> str:
        """
        Log a crime classification prediction
        
        Args:
            user_id (str): User who made the prediction
            user_role (str): User's role
            input_features (Dict): Input crime features
            predicted_class (int): Model's prediction
            confidence_score (float): Prediction confidence (0-1)
            feature_importance (Dict): XAI feature importance weights
            timestamp (datetime): Event timestamp
            
        Returns:
            str: Audit entry ID
        """
        entry_id = str(uuid.uuid4())
        
        entry = {
            'entry_id': entry_id,
            'timestamp': (timestamp or datetime.now()).isoformat(),
            'event_type': AuditEventType.CRIME_PREDICTION.value,
            'user_id': user_id,
            'user_role': user_role,
            'input_features': input_features,
            'prediction': {
                'predicted_class': predicted_class,
                'confidence_score': float(confidence_score)
            },
            'xai_explanation': {
                'top_contributing_features': dict(
                    sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:3]
                ),
                'all_feature_weights': feature_importance
            }
        }
        
        self._write_immutable_entry(entry)
        self.audit_entries.append(entry)
        logger.info(f"Logged prediction: {entry_id}")
        
        return entry_id
    
    def log_user_event(
        self,
        user_id: str,
        user_role: str,
        event_type: AuditEventType,
        details: Dict[str, Any],
        timestamp: Optional[datetime] = None
    ) -> str:
        """
        Log user action (login, logout, data access)
        
        Args:
            user_id (str): User ID
            user_role (str): User role
            event_type (AuditEventType): Type of event
            details (Dict): Event details
            timestamp (datetime): Event timestamp
            
        Returns:
            str: Audit entry ID
        """
        entry_id = str(uuid.uuid4())
        
        entry = {
            'entry_id': entry_id,
            'timestamp': (timestamp or datetime.now()).isoformat(),
            'event_type': event_type.value,
            'user_id': user_id,
            'user_role': user_role,
            'details': details
        }
        
        self._write_immutable_entry(entry)
        self.audit_entries.append(entry)
        logger.info(f"Logged user event: {entry_id} ({event_type.value})")
        
        return entry_id
    
    def log_data_access(
        self,
        user_id: str,
        user_role: str,
        resource_accessed: str,
        query_params: Dict[str, Any],
        timestamp: Optional[datetime] = None
    ) -> str:
        """
        Log data access event
        
        Args:
            user_id (str): User ID
            user_role (str): User role
            resource_accessed (str): What resource was accessed
            query_params (Dict): Query parameters
            timestamp (datetime): Event timestamp
            
        Returns:
            str: Audit entry ID
        """
        entry_id = str(uuid.uuid4())
        
        entry = {
            'entry_id': entry_id,
            'timestamp': (timestamp or datetime.now()).isoformat(),
            'event_type': AuditEventType.DATA_ACCESS.value,
            'user_id': user_id,
            'user_role': user_role,
            'resource_accessed': resource_accessed,
            'query_parameters': query_params
        }
        
        self._write_immutable_entry(entry)
        self.audit_entries.append(entry)
        logger.info(f"Logged data access: {entry_id}")
        
        return entry_id
    
    def log_permission_denied(
        self,
        user_id: str,
        user_role: str,
        attempted_action: str,
        reason: str,
        timestamp: Optional[datetime] = None
    ) -> str:
        """
        Log permission denial event
        
        Args:
            user_id (str): User ID
            user_role (str): User role
            attempted_action (str): Action user tried to perform
            reason (str): Reason for denial
            timestamp (datetime): Event timestamp
            
        Returns:
            str: Audit entry ID
        """
        entry_id = str(uuid.uuid4())
        
        entry = {
            'entry_id': entry_id,
            'timestamp': (timestamp or datetime.now()).isoformat(),
            'event_type': AuditEventType.PERMISSION_DENIED.value,
            'user_id': user_id,
            'user_role': user_role,
            'attempted_action': attempted_action,
            'denial_reason': reason
        }
        
        self._write_immutable_entry(entry)
        self.audit_entries.append(entry)
        logger.warning(f"Permission denied: {entry_id}")
        
        return entry_id
    
    def log_system_error(
        self,
        error_message: str,
        error_type: str,
        user_id: Optional[str] = None,
        context: Optional[Dict] = None,
        timestamp: Optional[datetime] = None
    ) -> str:
        """
        Log system error for debugging and compliance
        
        Args:
            error_message (str): Error message
            error_type (str): Type of error
            user_id (str): User ID if applicable
            context (Dict): Additional context
            timestamp (datetime): Event timestamp
            
        Returns:
            str: Audit entry ID
        """
        entry_id = str(uuid.uuid4())
        
        entry = {
            'entry_id': entry_id,
            'timestamp': (timestamp or datetime.now()).isoformat(),
            'event_type': AuditEventType.SYSTEM_ERROR.value,
            'error_message': error_message,
            'error_type': error_type,
            'user_id': user_id,
            'context': context or {}
        }
        
        self._write_immutable_entry(entry)
        self.audit_entries.append(entry)
        logger.error(f"System error logged: {entry_id}")
        
        return entry_id
    
    def _write_immutable_entry(self, entry: Dict) -> None:
        """
        Write entry to immutable log file (append-only)
        
        Args:
            entry (Dict): Audit entry to write
        """
        try:
            with open(self.write_once_path, 'a') as f:
                f.write(json.dumps(entry) + '\n')
        except Exception as e:
            logger.error(f"Error writing to audit log: {str(e)}")
            raise
    
    def retrieve_audit_trail(
        self,
        user_id: Optional[str] = None,
        event_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[Dict]:
        """
        Retrieve audit trail entries with filtering
        
        Args:
            user_id (str): Filter by user
            event_type (str): Filter by event type
            start_date (datetime): Filter by start date
            end_date (datetime): Filter by end date
            limit (int): Maximum entries to return
            
        Returns:
            List[Dict]: Filtered audit entries
        """
        filtered = self.audit_entries.copy()
        
        if user_id:
            filtered = [e for e in filtered if e.get('user_id') == user_id]
        
        if event_type:
            filtered = [e for e in filtered if e.get('event_type') == event_type]
        
        if start_date or end_date:
            filtered = [
                e for e in filtered
                if self._is_within_date_range(e.get('timestamp'), start_date, end_date)
            ]
        
        return filtered[-limit:]
    
    @staticmethod
    def _is_within_date_range(
        timestamp_str: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> bool:
        """Check if timestamp is within date range"""
        try:
            ts = datetime.fromisoformat(timestamp_str)
            if start_date and ts < start_date:
                return False
            if end_date and ts > end_date:
                return False
            return True
        except:
            return False
    
    def generate_compliance_report(self, start_date: datetime, end_date: datetime) -> Dict:
        """
        Generate compliance report for government audits
        
        Args:
            start_date (datetime): Report start date
            end_date (datetime): Report end date
            
        Returns:
            Dict: Compliance report
        """
        entries = self.retrieve_audit_trail(start_date=start_date, end_date=end_date, limit=10000)
        
        report = {
            'report_generated': datetime.now().isoformat(),
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'total_events': len(entries),
            'event_summary': self._summarize_events(entries),
            'user_activity': self._summarize_user_activity(entries),
            'predictions_made': len([e for e in entries if e.get('event_type') == 'crime_prediction']),
            'security_events': len([e for e in entries if e.get('event_type') == 'permission_denied'])
        }
        
        return report
    
    @staticmethod
    def _summarize_events(entries: List[Dict]) -> Dict:
        """Summarize events by type"""
        summary = {}
        for entry in entries:
            event_type = entry.get('event_type', 'unknown')
            summary[event_type] = summary.get(event_type, 0) + 1
        return summary
    
    @staticmethod
    def _summarize_user_activity(entries: List[Dict]) -> Dict:
        """Summarize activity by user"""
        summary = {}
        for entry in entries:
            user_id = entry.get('user_id', 'unknown')
            summary[user_id] = summary.get(user_id, 0) + 1
        return summary


if __name__ == "__main__":
    # Example usage
    audit = AuditLog()
    # audit.log_prediction("user1", "field_officer", {...}, 0, 0.95, {...})
    # audit.log_user_event("user1", "field_officer", AuditEventType.USER_LOGIN, {})
