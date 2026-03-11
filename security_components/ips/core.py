import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
from sqlalchemy.orm import Session
import ipaddress

# Import database models
from ..common.database import SessionLocal, SecurityEvent, Alert, RLAction

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IntrusionPreventionSystem:
    def __init__(self, siem=None, ids=None):
        self.db = SessionLocal()
        self.siem = siem
        self.ids = ids
        self.blocked_ips: Set[str] = set()
        self.rate_limits: Dict[str, Tuple[int, float]] = {}  # IP -> (request_count, window_end)
        self.policy = self._load_policies()
        self._load_blocked_ips()

    def _load_policies(self) -> Dict:
        """Load prevention policies"""
        return {
            "block_duration": 3600,  # 1 hour in seconds
            "max_requests_per_minute": 1000,
            "auto_block_high_confidence": True,
            "auto_block_medium_confidence": False,
            "rate_limit_strategy": "temporary_block",  # or 'throttle'
            "threat_categories": {
                "sql_injection": {"action": "block", "severity": "high"},
                "xss": {"action": "block", "severity": "high"},
                "brute_force": {"action": "rate_limit", "severity": "medium"},
                "port_scan": {"action": "alert", "severity": "medium"}
            }
        }

    def _load_blocked_ips(self):
        """Load blocked IPs from database"""
        try:
            # Get IPs with active blocks
            time_threshold = datetime.utcnow() - timedelta(hours=24)  # Last 24 hours
            events = self.db.query(SecurityEvent).filter(
                SecurityEvent.is_mitigated == True,
                SecurityEvent.mitigation_action.like('%block%'),
                SecurityEvent.timestamp >= time_threshold
            ).all()
            
            self.blocked_ips = {e.source_ip for e in events if e.source_ip}
            logger.info(f"Loaded {len(self.blocked_ips)} blocked IPs from database")
            
        except Exception as e:
            logger.error(f"Error loading blocked IPs: {e}")
            self.blocked_ips = set()

    def process_alert(self, alert: Alert) -> bool:
        """Process an alert and take appropriate action"""
        try:
            if not alert.security_event:
                logger.warning("Alert has no associated security event")
                return False
                
            event = alert.security_event
            threat_type = self._classify_threat(event)
            
            # Get policy for this threat type
            policy = self.policy['threat_categories'].get(threat_type, {})
            action = policy.get('action', 'alert')
            
            # Take action based on policy
            if action == 'block':
                return self._block_ip(event.source_ip, f"Blocked due to {threat_type}")
            elif action == 'rate_limit':
                return self._rate_limit_ip(event.source_ip, 60, 100)  # 100 req/min
            elif action == 'alert':
                logger.info(f"Alert only for {threat_type} from {event.source_ip}")
                return True
            else:
                logger.warning(f"No action defined for {threat_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error processing alert: {e}")
            return False

    def _classify_threat(self, event: SecurityEvent) -> str:
        """Classify the type of threat"""
        event_type = event.event_type.lower()
        details = event.details or {}
        
        if 'sql' in event_type or any(k in str(details).lower() for k in ['select', 'union', 'drop table']):
            return 'sql_injection'
        elif 'xss' in event_type or any(k in str(details).lower() for k in ['<script>', 'javascript:', 'onerror=']):
            return 'xss'
        elif 'brute' in event_type or 'login' in event_type:
            return 'brute_force'
        elif 'port_scan' in event_type or 'scan' in event_type:
            return 'port_scan'
        else:
            return 'unknown'

    def _block_ip(self, ip: str, reason: str) -> bool:
        """Block an IP address"""
        if not ip or ip in ['127.0.0.1', '0.0.0.0']:
            return False
            
        try:
            # Add to blocked IPs set
            self.blocked_ips.add(ip)
            
            # Update database
            event = SecurityEvent(
                event_type='ip_blocked',
                severity='high',
                source_ip=ip,
                details={'reason': reason},
                is_mitigated=True,
                mitigation_action='block_ip'
            )
            
            self.db.add(event)
            self.db.commit()
            
            # Log the action
            logger.warning(f"Blocked IP {ip}: {reason}")
            
            # In a real system, update firewall rules here
            self._update_firewall_rules()
            
            return True
            
        except Exception as e:
            logger.error(f"Error blocking IP {ip}: {e}")
            self.db.rollback()
            return False

    def _rate_limit_ip(self, ip: str, window_seconds: int, max_requests: int) -> bool:
        """Apply rate limiting to an IP address"""
        current_time = time.time()
        
        # Initialize or update rate limit counter
        if ip not in self.rate_limits or current_time > self.rate_limits[ip][1]:
            # New time window
            self.rate_limits[ip] = (1, current_time + window_seconds)
        else:
            # Increment counter in existing window
            count, window_end = self.rate_limits[ip]
            self.rate_limits[ip] = (count + 1, window_end)
            
            # Check if rate limit exceeded
            if count >= max_requests:
                # Apply temporary block
                return self._block_ip(
                    ip, 
                    f"Rate limit exceeded: {count} requests in {window_seconds} seconds"
                )
        
        return True

    def _update_firewall_rules(self):
        """Update system firewall rules (placeholder for actual implementation)"""
        # In a real system, this would update iptables, Windows Firewall, etc.
        logger.info(f"Updating firewall rules. Currently blocking {len(self.blocked_ips)} IPs")
        
    def is_ip_blocked(self, ip: str) -> bool:
        """Check if an IP is blocked"""
        return ip in self.blocked_ips
        
    def get_blocked_ips(self) -> List[str]:
        """Get list of currently blocked IPs"""
        return list(self.blocked_ips)
        
    def unblock_ip(self, ip: str, reason: str) -> bool:
        """Unblock a previously blocked IP"""
        try:
            if ip in self.blocked_ips:
                self.blocked_ips.remove(ip)
                
                # Log the action
                event = SecurityEvent(
                    event_type='ip_unblocked',
                    severity='info',
                    source_ip=ip,
                    details={'reason': reason},
                    is_mitigated=True,
                    mitigation_action='unblock_ip'
                )
                
                self.db.add(event)
                self.db.commit()
                
                # Update firewall rules
                self._update_firewall_rules()
                logger.info(f"Unblocked IP {ip}: {reason}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error unblocking IP {ip}: {e}")
            self.db.rollback()
            return False

    def __del__(self):
        """Cleanup database connection"""
        self.db.close()

# Example usage
if __name__ == "__main__":
    ips = IntrusionPreventionSystem()
    
    # Example: Block an IP
    ips._block_ip("192.168.1.100", "Test block")
    
    # Check if IP is blocked
    print(f"Is 192.168.1.100 blocked? {ips.is_ip_blocked('192.168.1.100')}")
    
    # Unblock the IP
    ips.unblock_ip("192.168.1.100", "Test complete")
    print(f"Is 192.168.1.100 blocked? {ips.is_ip_blocked('192.168.1.100')}")
