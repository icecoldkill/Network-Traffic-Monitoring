import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
from sqlalchemy.orm import Session

# Import database models
from ..common.database import SessionLocal, SecurityEvent, Alert

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IntrusionDetectionSystem:
    def __init__(self, siem=None):
        self.db = SessionLocal()
        self.siem = siem
        self.signatures = self._load_signatures()
        self.anomaly_threshold = 0.8  # Threshold for anomaly detection
        self._init_anomaly_detection()

    def _load_signatures(self) -> List[Dict]:
        """Load attack signatures"""
        return [
            {
                "id": "sig-001",
                "name": "SQL Injection Attempt",
                "description": "Detects common SQL injection patterns",
                "severity": "high",
                "patterns": [
                    r'(?i)select\s.*from',
                    r'(?i)union\s+select',
                    r'(?i)drop\s+table',
                    r'(?i)1=1',
                    r'(?i)or\s+1=1',
                    r'(?i)exec\s*\(',
                    r'(?i)waitfor\s+delay',
                    r'(?i);\s*--',
                    r'(?i)/\*.*\*/'
                ]
            },
            {
                "id": "sig-002",
                "name": "XSS Attempt",
                "description": "Detects cross-site scripting attempts",
                "severity": "high",
                "patterns": [
                    r'<script[^>]*>',
                    r'javascript:',
                    r'onerror\s*=',
                    r'onload\s*=',
                    r'<iframe',
                    r'<img\s+src=.*?onerror='
                ]
            },
            # Add more signatures as needed
        ]

    def _init_anomaly_detection(self):
        """Initialize anomaly detection models"""
        # In a real system, this would load pre-trained models
        self.request_rate_baseline = 100  # Requests per minute baseline
        self.anomaly_model = None  # Placeholder for ML model
        
    def analyze_traffic(self, packet_data: Dict[str, Any]) -> Optional[SecurityEvent]:
        """Analyze network traffic for intrusions"""
        try:
            # Check for signature matches
            signature_match = self._check_signatures(packet_data)
            if signature_match:
                return self._handle_signature_match(packet_data, signature_match)
            
            # Check for anomalies
            if self._detect_anomalies(packet_data):
                return self._handle_anomaly(packet_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error analyzing traffic: {e}")
            return None

    def _check_signatures(self, packet_data: Dict) -> Optional[Dict]:
        """Check packet data against known attack signatures"""
        payload = packet_data.get('payload', '')
        if not payload:
            return None
            
        for signature in self.signatures:
            for pattern in signature.get('patterns', []):
                if re.search(pattern, payload, re.IGNORECASE):
                    return {
                        'signature_id': signature['id'],
                        'signature_name': signature['name'],
                        'severity': signature['severity'],
                        'pattern': pattern
                    }
        return None

    def _detect_anomalies(self, packet_data: Dict) -> bool:
        """Detect anomalous network behavior"""
        try:
            # Simple rate limiting check
            if self._check_request_rate(packet_data):
                return True
                
            # Add more anomaly detection logic here
            # - Unusual protocol usage
            # - Port scanning patterns
            # - Data exfiltration attempts
            
            return False
            
        except Exception as e:
            logger.error(f"Error in anomaly detection: {e}")
            return False

    def _check_request_rate(self, packet_data: Dict) -> bool:
        """Check if request rate exceeds threshold"""
        # In a real system, this would use a sliding window counter
        src_ip = packet_data.get('source_ip')
        if not src_ip:
            return False
            
        # Count requests from this IP in the last minute
        time_threshold = datetime.utcnow() - timedelta(minutes=1)
        request_count = self.db.query(SecurityEvent).filter(
            SecurityEvent.source_ip == src_ip,
            SecurityEvent.timestamp >= time_threshold
        ).count()
        
        # If requests exceed 3x the baseline, it's an anomaly
        return request_count > (self.request_rate_baseline * 3)

    def _handle_signature_match(self, packet_data: Dict, signature_match: Dict) -> SecurityEvent:
        """Handle a signature match"""
        event = SecurityEvent(
            event_type=f'intrusion_attempt_{signature_match["signature_id"]}',
            severity=signature_match['severity'],
            source_ip=packet_data.get('source_ip'),
            destination_ip=packet_data.get('destination_ip'),
            protocol=packet_data.get('protocol'),
            port=packet_data.get('destination_port'),
            details={
                'signature': signature_match['signature_name'],
                'pattern': signature_match['pattern'],
                'payload_preview': str(packet_data.get('payload', ''))[:500],
                'detection_method': 'signature'
            }
        )
        
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        
        # Create alert
        self._create_alert(
            event=event,
            description=f"Intrusion detected: {signature_match['signature_name']}",
            severity=signature_match['severity']
        )
        
        return event

    def _handle_anomaly(self, packet_data: Dict) -> SecurityEvent:
        """Handle an anomaly detection"""
        event = SecurityEvent(
            event_type='suspicious_activity',
            severity='high',
            source_ip=packet_data.get('source_ip'),
            destination_ip=packet_data.get('destination_ip'),
            protocol=packet_data.get('protocol'),
            port=packet_data.get('destination_port'),
            details={
                'anomaly_type': 'unusual_traffic_pattern',
                'detection_method': 'behavioral_analysis',
                'payload_preview': str(packet_data.get('payload', ''))[:500]
            }
        )
        
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        
        # Create alert
        self._create_alert(
            event=event,
            description="Anomalous network traffic detected",
            severity='high'
        )
        
        return event

    def _create_alert(self, event: SecurityEvent, description: str, severity: str = 'medium'):
        """Create an alert for a detected intrusion"""
        alert = Alert(
            event_id=event.id,
            status='open',
            notes=description
        )
        
        self.db.add(alert)
        self.db.commit()
        
        # If SIEM is connected, forward the alert
        if self.siem:
            self.siem.process_event({
                'event_type': 'intrusion_alert',
                'severity': severity,
                'source_ip': event.source_ip,
                'destination_ip': event.destination_ip,
                'details': {
                    'description': description,
                    'event_id': event.id
                }
            })

    def train_anomaly_model(self, training_data: List[Dict]):
        """Train the anomaly detection model"""
        # In a real system, this would train an ML model
        logger.info("Training anomaly detection model...")
        # Training logic would go here
        logger.info("Anomaly detection model training complete")

    def __del__(self):
        """Cleanup database connection"""
        self.db.close()

# Example usage
if __name__ == "__main__":
    ids = IntrusionDetectionSystem()
    
    # Example packet data
    test_packet = {
        'source_ip': '192.168.1.100',
        'destination_ip': '10.0.0.1',
        'source_port': 54321,
        'destination_port': 80,
        'protocol': 'HTTP',
        'payload': "GET /index.php?id=1 OR 1=1--"
    }
    
    # Analyze the packet
    result = ids.analyze_traffic(test_packet)
    if result:
        print(f"Intrusion detected! Event ID: {result.id}")
