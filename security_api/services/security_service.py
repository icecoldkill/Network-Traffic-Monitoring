import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

# Import security components
from security_components.siem.core import SIEMCore
from security_components.ids.core import IntrusionDetectionSystem
from security_components.ips.core import IntrusionPreventionSystem
from security_components.ml.reinforcement_learning import ThreatResponseAgent
from security_components.common.database import SessionLocal, SecurityEvent, Alert, RLAction, ThreatIntelligence

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecurityService:
    """Service layer for security operations"""
    
    def __init__(self):
        self.db = SessionLocal()
        self.siem = SIEMCore()
        self.ids = IntrusionDetectionSystem(siem=self.siem)
        self.ips = IntrusionPreventionSystem(siem=self.siem, ids=self.ids)
        
        # Initialize RL agent
        try:
            self.rl_agent = ThreatResponseAgent(model_path="models/threat_response_model_final.pth")
        except Exception as e:
            logger.warning(f"Could not load RL model: {e}. Initializing new model.")
            self.rl_agent = ThreatResponseAgent()
    
    def process_network_packet(self, packet_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a network packet through the security pipeline"""
        try:
            # 1. First, check if source IP is blocked
            if self.ips.is_ip_blocked(packet_data.get('source_ip', '')):
                return {
                    "status": "blocked",
                    "reason": "Source IP is blocked",
                    "action": "block"
                }
            
            # 2. Analyze with IDS
            ids_result = self.ids.analyze_traffic(packet_data)
            
            if ids_result:
                # 3. Get RL-based action recommendation
                state = self._create_state_representation(ids_result, packet_data)
                action = self.rl_agent.predict_action(state)
                
                # 4. Take action based on RL recommendation
                if action == "block_ip":
                    self.ips._block_ip(
                        packet_data['source_ip'],
                        f"Blocked by RL agent after {ids_result.event_type}"
                    )
                
                return {
                    "status": "threat_detected",
                    "threat_type": ids_result.event_type,
                    "severity": ids_result.severity,
                    "recommended_action": action,
                    "details": {
                        "signature": getattr(ids_result, 'signature_match', None),
                        "anomaly_score": getattr(ids_result, 'anomaly_score', None)
                    }
                }
            
            return {"status": "clean"}
            
        except Exception as e:
            logger.error(f"Error processing network packet: {e}")
            return {"status": "error", "message": str(e)}
    
    def _create_state_representation(self, event, packet_data: Dict) -> List[float]:
        """Create a state representation for the RL agent"""
        # This is a simplified example - in a real system, you'd want to include
        # more relevant features for your specific use case
        return [
            1.0 if event.severity == 'critical' else 0.5 if event.severity == 'high' else 0.2,  # severity
            float(len(self.db.query(SecurityEvent).filter(
                SecurityEvent.source_ip == packet_data.get('source_ip'),
                SecurityEvent.timestamp >= datetime.utcnow() - timedelta(hours=1)
            ).all())) / 100.0,  # events from this IP in last hour (normalized)
            float(packet_data.get('packet_size', 0)) / 1500.0,  # normalized packet size
            1.0 if packet_data.get('protocol') in ['HTTP', 'HTTPS'] else 0.0,  # is web traffic
            # Add more features as needed
        ]
    
    def get_security_events(self, limit: int = 100) -> List[Dict]:
        """Get recent security events"""
        try:
            events = self.db.query(SecurityEvent)\
                          .order_by(SecurityEvent.timestamp.desc())\
                          .limit(limit)\
                          .all()
            return [self._serialize_event(e) for e in events]
        except Exception as e:
            logger.error(f"Error getting security events: {e}")
            return []
    
    def get_alerts(self, status: str = None, limit: int = 50) -> List[Dict]:
        """Get alerts, optionally filtered by status"""
        try:
            query = self.db.query(Alert)
            if status:
                query = query.filter(Alert.status == status)
            
            alerts = query.order_by(Alert.timestamp.desc())\
                         .limit(limit)\
                         .all()
            return [self._serialize_alert(a) for a in alerts]
        except Exception as e:
            logger.error(f"Error getting alerts: {e}")
            return []
    
    def update_alert_status(self, alert_id: int, status: str, notes: str = None) -> bool:
        """Update alert status and add notes"""
        try:
            alert = self.db.query(Alert).filter(Alert.id == alert_id).first()
            if not alert:
                return False
            
            alert.status = status
            if notes:
                alert.notes = notes
            
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error updating alert status: {e}")
            self.db.rollback()
            return False
    
    def get_threat_intel(self, ioc: str = None) -> List[Dict]:
        """Get threat intelligence data"""
        try:
            query = self.db.query(ThreatIntelligence)
            if ioc:
                query = query.filter(ThreatIntelligence.ioc_value == ioc)
            
            threats = query.order_by(ThreatIntelligence.last_seen.desc())\
                          .limit(100)\
                          .all()
            return [self._serialize_threat(t) for t in threats]
        except Exception as e:
            logger.error(f"Error getting threat intel: {e}")
            return []
    
    def _serialize_event(self, event: SecurityEvent) -> Dict:
        """Serialize SecurityEvent for API response"""
        return {
            "id": event.id,
            "timestamp": event.timestamp.isoformat(),
            "event_type": event.event_type,
            "severity": event.severity,
            "source_ip": event.source_ip,
            "destination_ip": event.destination_ip,
            "protocol": event.protocol,
            "port": event.port,
            "details": event.details or {},
            "is_mitigated": event.is_mitigated,
            "mitigation_action": event.mitigation_action
        }
    
    def _serialize_alert(self, alert: Alert) -> Dict:
        """Serialize Alert for API response"""
        return {
            "id": alert.id,
            "event_id": alert.event_id,
            "timestamp": alert.timestamp.isoformat(),
            "status": alert.status,
            "assigned_to": alert.assigned_to,
            "notes": alert.notes,
            "event": self._serialize_event(alert.security_event) if alert.security_event else None
        }
    
    def _serialize_threat(self, threat) -> Dict:
        """Serialize ThreatIntelligence for API response"""
        return {
            "id": threat.id,
            "ioc_type": threat.ioc_type,
            "ioc_value": threat.ioc_value,
            "threat_type": threat.threat_type,
            "confidence": threat.confidence,
            "first_seen": threat.first_seen.isoformat(),
            "last_seen": threat.last_seen.isoformat(),
            "source": threat.source,
            "is_active": threat.is_active
        }
    
    def __del__(self):
        """Cleanup database connection"""
        self.db.close()

# Singleton instance
security_service = SecurityService()
