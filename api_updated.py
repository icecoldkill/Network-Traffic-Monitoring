from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
from io import StringIO
import base64
import numpy as np
import sys
import argparse

# Import your existing modules
try:
    from data_collection import NetworkTrafficCollector
    from visualization import NetworkTrafficVisualizer
    from anomaly_detection_fix import AnomalyDetector
    from report_generation import NetworkReportGenerator
except ImportError as e:
    print(f"Warning: Could not import module: {e}")

import json
import logging
import socket
import os

app = Flask(__name__)
CORS(app)  # Enable cross-origin requests

# Initialize components (wrapped in try-except for safety)
try:
    collector = NetworkTrafficCollector()
    visualizer = NetworkTrafficVisualizer()
    detector = AnomalyDetector("./models/simple_cnn_best_model.h5")
    report_generator = NetworkReportGenerator()
except Exception as e:
    print(f"Warning: Could not initialize components: {e}")
    collector = None
    visualizer = None
    detector = None
    report_generator = None

@app.route('/')
def home():
    return "Flask API is running on port 5005!"

@app.route('/api/generate-data', methods=['POST'])
def generate_data():
    data = request.json
    network_type = data.get('networkType', 'office')
    sample_size = data.get('sampleSize', 100)
    include_anomalies = data.get('includeAnomalies', True)
    
    try:
        if collector is None:
            return jsonify({'status': 'error', 'message': 'Collector not initialized'}), 500
            
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
        if visualizer is None:
            return jsonify({'status': 'error', 'message': 'Visualizer not initialized'}), 500
            
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
        
        buffer = io.BytesIO()
        
        if isinstance(img, np.ndarray):
            if img.dtype != np.uint8:
                img_min, img_max = float(np.min(img)), float(np.max(img))
                if img_max > img_min:
                    img = ((img - img_min) / (img_max - img_min) * 255.0).astype(np.uint8)
                else:
                    img = np.zeros_like(img, dtype=np.uint8)

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
        import traceback
        return jsonify({'status': 'error', 'message': str(e), 'trace': traceback.format_exc()}), 500

@app.route('/api/get_dashboard_metrics', methods=['GET'])
def get_dashboard_metrics():
    try:
        if collector is None:
            return jsonify({'status': 'error', 'message': 'Collector not initialized'}), 500
        
        df = collector.generate_synthetic_data(n_samples=100, network_profile='office')
        
        return jsonify({
            'status': 'success',
            'metrics': {
                'total_packets': len(df),
                'avg_packet_size': float(df['packet_size'].mean()) if 'packet_size' in df else 0,
                'protocols': df['protocol'].value_counts().to_dict() if 'protocol' in df else {},
                'top_ips': df['src_ip'].value_counts().head(5).to_dict() if 'src_ip' in df else {},
            }
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/get_anomalies', methods=['GET'])
def get_anomalies():
    try:
        if detector is None or collector is None:
            return jsonify({'status': 'error', 'message': 'Detector or Collector not initialized'}), 500
        
        df = collector.generate_synthetic_data(n_samples=100, anomaly_ratio=0.1, network_profile='office')
        anomalies = detector.detect_anomalies(df)
        
        return jsonify({
            'status': 'success',
            'anomalies': anomalies.to_dict(orient='records') if len(anomalies) > 0 else [],
            'count': len(anomalies)
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=5005, help='Port to run Flask app on')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to run Flask app on')
    args = parser.parse_args()
    
    app.run(host=args.host, port=args.port, debug=True)
