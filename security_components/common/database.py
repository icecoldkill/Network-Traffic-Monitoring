from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///security_monitor.db')

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Dependency to get DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Database Models
class SecurityEvent(Base):
    __tablename__ = "security_events"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    event_type = Column(String(100), index=True)  # e.g., 'login_attempt', 'port_scan', 'ddos_attack'
    severity = Column(String(20), index=True)     # 'low', 'medium', 'high', 'critical'
    source_ip = Column(String(45))                # Support both IPv4 and IPv6
    destination_ip = Column(String(45))
    protocol = Column(String(20))
    port = Column(Integer)
    details = Column(JSON)                        # Store additional event data
    is_mitigated = Column(Boolean, default=False)
    mitigation_action = Column(String(100))
    confidence_score = Column(Float, default=0.0)
    
    # Relationships
    related_alerts = relationship("Alert", back_populates="security_event")
    rl_actions = relationship("RLAction", back_populates="security_event")

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey('security_events.id'))
    timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default='open')  # 'open', 'in_progress', 'resolved', 'false_positive'
    assigned_to = Column(String(100))
    notes = Column(String(1000))
    
    # Relationships
    security_event = relationship("SecurityEvent", back_populates="related_alerts")

class RLAction(Base):
    __tablename__ = "rl_actions"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey('security_events.id'))
    action_type = Column(String(50))  # 'block_ip', 'rate_limit', 'alert_only', 'quarantine'
    action_params = Column(JSON)      # Parameters for the action
    reward = Column(Float)            # Reward signal for RL
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    security_event = relationship("SecurityEvent", back_populates="rl_actions")

class ThreatIntelligence(Base):
    __tablename__ = "threat_intelligence"
    
    id = Column(Integer, primary_key=True, index=True)
    ioc_type = Column(String(50))     # 'ip', 'domain', 'hash', 'url'
    ioc_value = Column(String(500), unique=True, index=True)
    threat_type = Column(String(100))
    confidence = Column(Float)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    source = Column(String(100))       # 'internal', 'external_feed_1', etc.
    is_active = Column(Boolean, default=True)

# Create tables
def init_db():
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")

if __name__ == "__main__":
    init_db()
