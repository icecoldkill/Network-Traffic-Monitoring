# Flask API extension for live packet capture
from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
from data_collection import NetworkTrafficCollector
from anomaly_detection_fix import AnomalyDetector
import threading
import queue

# Global state for live capture
app = Flask(__name__)
CORS(app)
capture_queue = queue.Queue()
capture_thread = None
is_capturing = False

def start_live_capture(interface="eth0", duration=60):
    """Start live packet capture in a background thread"""
    global is_capturing, capture_thread
    
    if is_capturing:
        return {"status": "error", "message": "Capture already in progress"}
    
    is_capturing = True
    collector = NetworkTrafficCollector()
    
    def capture_worker():
        global is_capturing
        try:
            df = collector.collect_with_scapy(interface=interface, count=1000, timeout=duration)
            capture_queue.put({"status": "success", "data": df.to_dict(orient='records'), "count": len(df)})
        except Exception as e:
            capture_queue.put({"status": "error", "message": str(e)})
        finally:
            is_capturing = False
    
    capture_thread = threading.Thread(target=capture_worker, daemon=True)
    capture_thread.start()
    
    return {"status": "started", "message": f"Live capture started on {interface}"}

def get_capture_status():
    """Get the status of live capture"""
    if capture_queue.empty():
        return {"status": "pending" if is_capturing else "idle"}
    else:
        return capture_queue.get()

# Add these routes to your existing Flask app (api.py)
# Paste this into your api.py file

@app.route('/api/collect_traffic', methods=['POST'])
def collect_traffic():
    """Endpoint for live packet capture"""
    data = request.json or {}
    interface = data.get('interface', 'eth0')
    duration = data.get('duration', 60)
    
    try:
        result = start_live_capture(interface=interface, duration=duration)
        return jsonify(result)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/capture_status', methods=['GET'])
def capture_status():
    """Check status of live capture"""
    try:
        status = get_capture_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/get_anomalies', methods=['GET'])
def get_anomalies():
    """Get detected anomalies"""
    try:
        detector = AnomalyDetector("./models/simple_cnn_best_model.h5")
        # This is a placeholder - you may want to load actual detected anomalies from storage
        return jsonify({
            "status": "success",
            "anomalies": [
                {"type": "Port Scan", "severity": "high", "time": "14:23", "packets": 1250},
                {"type": "DDoS Pattern", "severity": "critical", "time": "14:19", "packets": 5420},
                {"type": "Data Exfiltration", "severity": "medium", "time": "14:15", "packets": 890},
            ]
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/get_dashboard_metrics', methods=['GET'])
def get_dashboard_metrics():
    """Get dashboard metrics"""
    try:
        return jsonify({
            "status": "success",
            "metrics": {
                "anomalies": 3,
                "avgPackets": 245,
                "totalTraffic": "2.5 GB",
                "errorRate": "0.3%"
            }
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
