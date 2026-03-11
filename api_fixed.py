from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
from io import StringIO
import base64
import numpy as np
import argparse

# Import your existing modules
from data_collection import NetworkTrafficCollector
from visualization import NetworkTrafficVisualizer
from anomaly_detection_fix import AnomalyDetector
from report_generation import NetworkReportGenerator
import json
import logging
import socket
import os

app = Flask(__name__)
CORS(app)

# Initialize components
collector = NetworkTrafficCollector()
visualizer = NetworkTrafficVisualizer()
detector = AnomalyDetector("./models/simple_cnn_best_model.h5")
report_generator = NetworkReportGenerator()

@app.route('/')
def home():
    return "Flask API is running!"

@app.route('/api/generate-data', methods=['POST'])
def generate_data():
    data = request.json
    network_type = data.get('networkType', 'office')
    sample_size = data.get('sampleSize', 100)
    include_anomalies = data.get('includeAnomalies', True)
    
    try:
        df = collector.generate_synthetic_data(
            n_samples=sample_size,
            anomaly_ratio=0.05 if include_anomalies else 0,
            network_profile=network_type
        )
        
        return jsonify({
            'status': 'success',
            'data': df.to_dict(orient='records'),
            'count': len(df)
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/visualize', methods=['POST'])
def create_visualization():
    data = request.json
    traffic_data = pd.DataFrame(data.get('data', []))
    viz_type = data.get('type', 'heatmap')
    
    try:
        if viz_type == 'heatmap':
            img = visualizer.create_heatmap(traffic_data)
        elif viz_type == 'time-series':
            img = visualizer.create_time_series_image(traffic_data)
        elif viz_type == 'protocol-spectrogram':
            img = visualizer.create_protocol_spectrogram(traffic_data)
        else:
            return jsonify({'status': 'error', 'message': f'Unsupported visualization type: {viz_type}'}), 400
        
        if img is None:
            return jsonify({'status': 'error', 'message': 'Visualization returned no image'}), 400
        
        import io
        from PIL import Image
        try:
            import cv2
            _has_cv2 = True
        except Exception:
            _has_cv2 = False
        
        buffer = io.BytesIO()
        
        if isinstance(img, np.ndarray):
            if img.dtype != np.uint8:
                img_min, img_max = float(np.min(img)), float(np.max(img))
                if img_max > img_min:
                    img = ((img - img_min) / (img_max - img_min) * 255.0).astype(np.uint8)
                else:
                    img = np.zeros_like(img, dtype=np.uint8)
            
            if _has_cv2 and img.ndim == 3 and img.shape[2] == 3:
                try:
                    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    pil_img = Image.fromarray(rgb)
                except Exception:
                    pil_img = Image.fromarray(img)
            else:
                pil_img = Image.fromarray(img)
            pil_img.save(buffer, format='PNG')
        else:
            img.save(buffer, format='PNG')
            
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return jsonify({
            'status': 'success',
            'image': img_str
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/get_dashboard_metrics', methods=['GET'])
def get_dashboard_metrics():
    try:
        df = collector.generate_synthetic_data(n_samples=100, anomaly_ratio=0.05)
        
        protocols = df.get('protocol', pd.Series()).value_counts().to_dict() if 'protocol' in df.columns else {}
        
        metrics = {
            'status': 'success',
            'totalPackets': len(df),
            'averageLatency': float(df.get('latency', pd.Series([0])).mean()) if 'latency' in df.columns else 0,
            'threatLevel': 'Low',
            'protocols': protocols,
            'topSources': df.get('source_ip', pd.Series()).value_counts().head(5).to_dict() if 'source_ip' in df.columns else {}
        }
        return jsonify(metrics)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/get_anomalies', methods=['GET'])
def get_anomalies():
    try:
        df = collector.generate_synthetic_data(n_samples=100, anomaly_ratio=0.05)
        predictions = detector.predict(df) if len(df) > 0 else np.array([])
        
        anomalies = []
        if len(predictions) > 0:
            for idx, pred in enumerate(predictions):
                if pred > 0.5:  # Threshold
                    anomalies.append({
                        'id': f'anomaly_{idx}',
                        'severity': 'high' if pred > 0.8 else 'medium',
                        'type': 'Suspicious Traffic',
                        'timestamp': pd.Timestamp.now().isoformat(),
                        'description': f'Anomaly detected with score: {float(pred):.2f}'
                    })
        
        return jsonify({
            'status': 'success',
            'anomalies': anomalies[:5],
            'total': len(anomalies)
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e), 'anomalies': []}), 500

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=5000, help='Port to run Flask on')
    args = parser.parse_args()
    
    app.run(host='0.0.0.0', port=args.port, debug=True)
