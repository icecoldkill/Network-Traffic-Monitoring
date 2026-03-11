from fastapi import APIRouter, HTTPException, Depends, WebSocket
from typing import List, Dict, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
import json
import asyncio

from ...services.security_service import security_service
from ...security_components.common.database import SessionLocal

router = APIRouter(
    prefix="/api/security",
    tags=["security"],
    responses={404: {"description": "Not found"}},
)

# Request/Response Models
class NetworkPacket(BaseModel):
    source_ip: str
    destination_ip: str
    source_port: int
    destination_port: int
    protocol: str
    payload: Optional[str] = None
    timestamp: Optional[datetime] = None
    packet_size: Optional[int] = None

class SecurityEventResponse(BaseModel):
    id: int
    timestamp: datetime
    event_type: str
    severity: str
    source_ip: Optional[str]
    destination_ip: Optional[str]
    protocol: Optional[str]
    port: Optional[int]
    details: Dict
    is_mitigated: bool
    mitigation_action: Optional[str]

class AlertResponse(BaseModel):
    id: int
    event_id: int
    timestamp: datetime
    status: str
    assigned_to: Optional[str]
    notes: Optional[str]
    event: Optional[SecurityEventResponse]

class ThreatIntelResponse(BaseModel):
    id: int
    ioc_type: str
    ioc_value: str
    threat_type: str
    confidence: float
    first_seen: datetime
    last_seen: datetime
    source: str
    is_active: bool

# API Endpoints
@router.post("/process-packet", response_model=Dict)
async def process_packet(packet: NetworkPacket):
    """Process a network packet through the security pipeline"""
    try:
        result = security_service.process_network_packet(packet.dict())
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/events", response_model=List[SecurityEventResponse])
async def get_events(limit: int = 100):
    """Get recent security events"""
    try:
        return security_service.get_security_events(limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/alerts", response_model=List[AlertResponse])
async def get_alerts(status: str = None, limit: int = 50):
    """Get alerts, optionally filtered by status"""
    try:
        return security_service.get_alerts(status=status, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/alerts/{alert_id}")
async def update_alert(alert_id: int, status: str, notes: str = None):
    """Update alert status and notes"""
    try:
        success = security_service.update_alert_status(alert_id, status, notes)
        if not success:
            raise HTTPException(status_code=404, detail="Alert not found")
        return {"status": "success", "message": "Alert updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/threat-intel", response_model=List[ThreatIntelResponse])
async def get_threat_intel(ioc: str = None):
    """Get threat intelligence data"""
    try:
        return security_service.get_threat_intel(ioc=ioc)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/blocked-ips", response_model=List[str])
async def get_blocked_ips():
    """Get list of currently blocked IPs"""
    try:
        return security_service.ips.get_blocked_ips()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/block-ip/{ip_address}")
async def block_ip(ip_address: str, reason: str = "Manual block"):
    """Manually block an IP address"""
    try:
        success = security_service.ips._block_ip(ip_address, reason)
        if not success:
            raise HTTPException(status_code=400, detail="Invalid IP address")
        return {"status": "success", "message": f"IP {ip_address} blocked"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/unblock-ip/{ip_address}")
async def unblock_ip(ip_address: str, reason: str = "Manual unblock"):
    """Unblock a previously blocked IP address"""
    try:
        success = security_service.ips.unblock_ip(ip_address, reason)
        if not success:
            raise HTTPException(status_code=404, detail="IP not found in blocked list")
        return {"status": "success", "message": f"IP {ip_address} unblocked"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket endpoint for real-time security events
@router.websocket("/ws/events")
async def websocket_events(websocket: WebSocket):
    """WebSocket endpoint for real-time security events"""
    await websocket.accept()
    try:
        while True:
            # Get recent events (in a real implementation, you'd use a pub/sub system)
            events = security_service.get_security_events(limit=10)
            await websocket.send_json({
                "type": "events_update",
                "data": events,
                "timestamp": datetime.utcnow().isoformat()
            })
            await asyncio.sleep(5)  # Send updates every 5 seconds
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()
