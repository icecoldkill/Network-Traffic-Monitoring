import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import numpy as np
from sqlalchemy.orm import Session

# Import database models
from ..common.database import SessionLocal, SecurityEvent, Alert, ThreatIntelligence

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SIEMCore:
    def __init__(self):
        self.db = SessionLocal()
        self.rules = self._load_rules()
        self.correlation_window = timedelta(minutes=5)  # Time window for correlation
        self.suspicious_ips = set()  # In-memory cache for suspicious IPs
        self._load_threat_intel()

    def _load_rules(self) -> List[Dict]:
        """Load detection rules from a file or database"""
        # In a real system, this would load from a database or config file
        return [
            {
                "id": "rule-001",
                "name": "Multiple Failed Logins",
                "description": "Detect multiple failed login attempts from the same IP",
                "query": "event_type:'login_failed'",
                "threshold": 5,
                "time_window": 300,  # 5 minutes in seconds
                "severity": "high",
                "action": "alert"
            },
            # Add more rules as needed
        ]

    def _load_threat_intel(self):
        """Load threat intelligence data"""
        try:
            threats = self.db.query(ThreatIntelligence).filter_by(is_active=True).all()
            self.suspicious_ips = {t.ioc_value for t in threats if t.ioc_type == 'ip'}
            logger.info(f"Loaded {len(self.suspicious_ips)} suspicious IPs from threat intel")
        except Exception as e:
            logger.error(f"Error loading threat intelligence: {e}")
            self.suspicious_ips = set()

    def process_event(self, event_data: Dict[str, Any]) -> Optional[SecurityEvent]:
        """Process a security event"""
        try:
            # Create security event
            event = SecurityEvent(
                event_type=event_data.get('event_type', 'unknown'),
                severity=event_data.get('severity', 'low'),
                source_ip=event_data.get('source_ip'),
                destination_ip=event_data.get('destination_ip'),
                protocol=event_data.get('protocol'),
                port=event_data.get('port'),
                details=event_data.get('details', {})
            )

            # Check against threat intelligence
            self._check_threat_intel(event)

            # Apply detection rules
            self._apply_detection_rules(event)

            # Save to database
            self.db.add(event)
            self.db.commit()
            self.db.refresh(event)

            return event

        except Exception as e:
            logger.error(f"Error processing event: {e}")
            self.db.rollback()
            return None

    def _check_threat_intel(self, event: SecurityEvent):
        """Check event against threat intelligence"""
        if event.source_ip in self.suspicious_ips:
            event.severity = 'critical'
            event.details['threat_intel_match'] = True
            self._create_alert(
                event=event,
                rule_id="threat-intel-001",
                description=f"Source IP {event.source_ip} found in threat intelligence"
            )

    def _apply_detection_rules(self, event: SecurityEvent):
        """Apply detection rules to the event"""
        for rule in self.rules:
            try:
                # Simple rule matching (in a real system, use a rules engine)
                if rule['query'] in json.dumps(event.details):
                    self._evaluate_rule(event, rule)
            except Exception as e:
                logger.error(f"Error applying rule {rule.get('id')}: {e}")

    def _evaluate_rule(self, event: SecurityEvent, rule: Dict):
        """Evaluate a single rule against the event"""
        # Check if we've seen similar events recently
        time_threshold = datetime.utcnow() - timedelta(seconds=rule['time_window'])
        
        similar_events = self.db.query(SecurityEvent).filter(
            SecurityEvent.event_type == event.event_type,
            SecurityEvent.source_ip == event.source_ip,
            SecurityEvent.timestamp >= time_threshold
        ).count()

        # If threshold is exceeded, create an alert
        if similar_events >= rule['threshold']:
            self._create_alert(
                event=event,
                rule_id=rule['id'],
                description=f"Rule triggered: {rule['name']}"
            )

    def _create_alert(self, event: SecurityEvent, rule_id: str, description: str):
        """Create an alert for a security event"""
        alert = Alert(
            event_id=event.id,
            status='open',
            notes=description
        )
        self.db.add(alert)
        self.db.commit()
        logger.warning(f"Security alert created: {description}")

    def get_recent_events(self, limit: int = 100) -> List[SecurityEvent]:
        """Get recent security events"""
        return self.db.query(SecurityEvent)\
                     .order_by(SecurityEvent.timestamp.desc())\
                     .limit(limit)\
                     .all()

    def get_open_alerts(self) -> List[Alert]:
        """Get all open alerts"""
        return self.db.query(Alert)\
                     .filter(Alert.status == 'open')\
                     .order_by(Alert.timestamp.desc())\
                     .all()

    def __del__(self):
        """Cleanup database connection"""
        self.db.close()

# Example usage
if __name__ == "__main__":
    siem = SIEMCore()
    
    # Example event
    test_event = {
        'event_type': 'login_failed',
        'severity': 'medium',
        'source_ip': '192.168.1.100',
        'destination_ip': '10.0.0.1',
        'protocol': 'SSH',
        'port': 22,
        'details': {
            'username': 'admin',
            'reason': 'invalid_credentials'
        }
    }
    
    # Process the event
    siem.process_event(test_event)
    print("Event processed successfully")
