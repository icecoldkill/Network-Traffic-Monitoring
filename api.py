from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import pandas as pd
from io import StringIO
import base64
import numpy as np
import sys
import argparse
import asyncio
from typing import Dict, Any, List

# Import your existing modules
try:
    from data_collection import NetworkTrafficCollector
    from visualization import NetworkTrafficVisualizer
    from anomaly_detection_fix import AnomalyDetector
    from report_generation import NetworkReportGenerator
except ImportError as e:
    print(f"Warning: Could not import module: {e}")

# Import chat service
try:
    from services.chat_service import ChatService
except ImportError as e:
    print(f"Warning: Could not import chat service: {e}")
    ChatService = None

import json
import logging
import socket
import os

app = Flask(__name__)

# Configure CORS
app.config['CORS_HEADERS'] = 'Content-Type'
cors = CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"],
        "supports_credentials": True
    }
})

# Add CORS headers to all responses
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    return response

# Initialize components (wrapped in try-except for safety)
try:
    collector = NetworkTrafficCollector()
    visualizer = NetworkTrafficVisualizer()
    detector = AnomalyDetector("./models/simple_cnn_best_model.h5")
    report_generator = NetworkReportGenerator()
    
    # Initialize chat service with API key from environment variable
    groq_api_key = os.getenv('GROQ_API_KEY')
    if not groq_api_key:
        print("Warning: GROQ_API_KEY environment variable not set. Chat functionality will be disabled.")
        chat_service = None
    else:
        chat_service = ChatService(api_key=groq_api_key)
        print("Chat service initialized successfully")
        
except Exception as e:
    print(f"Warning: Could not initialize components: {e}")
    collector = None
    visualizer = None
    detector = None
    report_generator = None
    chat_service = None

@app.route('/')
def home():
    return jsonify({"status": "success", "message": "Network Traffic Analysis API is running!"})

# Test endpoint
@app.route('/test', methods=['GET'])
def test():
    return jsonify({"status": "success", "message": "Test endpoint is working!"})

@app.route('/data/generate', methods=['POST'])
def generate_data():
    data = request.json or {}
    network_type = data.get('networkType', 'office')
    sample_size = data.get('sampleSize', 1000)  # Default to 1000 as per frontend
    include_anomalies = data.get('includeAnomalies', True)
    
    try:
        if collector is None:
            return jsonify({'status': 'error', 'message': 'Collector not initialized'}), 500
            
        df = collector.generate_synthetic_data(
            n_samples=sample_size,
            anomaly_ratio=0.05 if include_anomalies else 0
        )
        
        return jsonify({
            'status': 'success',
            'data': df.to_dict(orient='records'),
            'count': len(df)
        })
    except Exception as e:
        print(f"Error in generate_data: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/visualize', methods=['POST'])
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

@app.route('/dashboard/metrics', methods=['GET'])
def get_dashboard_metrics():
    try:
        # This is a placeholder - replace with actual metrics collection
        metrics = {
            'anomalies': 12,
            'avgPackets': 245,
            'totalTraffic': '1.2 TB',
            'errorRate': '0.5%'
        }
        return jsonify({'status': 'success', 'metrics': metrics})
    except Exception as e:
        print(f"Error in get_dashboard_metrics: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/anomalies', methods=['GET'])
def get_anomalies():
    try:
        # This is a placeholder - replace with actual anomaly detection
        anomalies = [
            {'id': 1, 'severity': 'high', 'description': 'Suspicious port scanning detected'},
            {'id': 2, 'severity': 'medium', 'description': 'Unusual outbound traffic'},
            {'id': 3, 'severity': 'low', 'description': 'Potential false positive'}
        ]
        return jsonify({'status': 'success', 'anomalies': anomalies})
    except Exception as e:
        print(f"Error in get_anomalies: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Add missing endpoints
@app.route('/api/generate-data', methods=['POST'])
def api_generate_data():
    return generate_data()

@app.route('/api/visualize', methods=['POST'])
def api_visualize():
    return create_visualization()

@app.route('/api/anomalies', methods=['GET'])
def api_get_anomalies():
    return get_anomalies()

@app.route('/api/dashboard/metrics', methods=['GET'])
def api_get_dashboard_metrics():
    return get_dashboard_metrics()

@app.route('/api/set_anomaly_threshold', methods=['POST'])
def set_anomaly_threshold():
    try:
        data = request.json or {}
        threshold = data.get('threshold', 0.5)
        # Here you would typically update the threshold in your anomaly detector
        # detector.set_threshold(threshold)
        return jsonify({
            'status': 'success',
            'message': f'Anomaly threshold set to {threshold}',
            'threshold': threshold
        })
    except Exception as e:
        print(f"Error in set_anomaly_threshold: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/train_model', methods=['POST'])
def train_model():
    try:
        data = request.json or {}
        epochs = data.get('epochs', 10)
        batch_size = data.get('batch_size', 32)
        
        # Here you would typically call your training function
        # training_result = detector.train(epochs=epochs, batch_size=batch_size)
        
        return jsonify({
            'status': 'success',
            'message': 'Model training completed',
            'epochs': epochs,
            'batch_size': batch_size,
            # Include actual training results here
            'training_metrics': {
                'loss': 0.1,
                'accuracy': 0.95,
                'val_loss': 0.15,
                'val_accuracy': 0.93
            }
        })
    except Exception as e:
        print(f"Error in train_model: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/generate_report', methods=['POST'])
def generate_report():
    try:
        data = request.json or {}
        report_type = data.get('type', 'summary')
        
        # Here you would typically generate a report
        # report = report_generator.generate(report_type)
        
        return jsonify({
            'status': 'success',
            'message': f'Generated {report_type} report',
            'report': {
                'id': 'report_123',
                'type': report_type,
                'timestamp': '2023-11-13T04:30:00Z',
                'content': 'This is a sample report. Implement report generation in report_generator.py'
            }
        })
    except Exception as e:
        print(f"Error in generate_report: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/get_reports', methods=['GET'])
def get_reports():
    try:
        # Here you would typically fetch the list of reports
        reports = [
            {
                'id': 'report_123',
                'type': 'summary',
                'timestamp': '2023-11-13T04:30:00Z',
                'title': 'Daily Network Summary'
            },
            {
                'id': 'report_124',
                'type': 'anomaly',
                'timestamp': '2023-11-13T03:45:00Z',
                'title': 'Anomaly Detection Report'
            }
        ]
        return jsonify({
            'status': 'success',
            'reports': reports
        })
    except Exception as e:
        print(f"Error in get_reports: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/get_anomalies', methods=['GET'])
def api_get_anomalies_wrapper():
    """Wrapper endpoint for /api/get_anomalies that calls the existing get_anomalies function"""
    return get_anomalies()

@app.route('/api/download_report/<report_id>', methods=['GET'])
def download_report(report_id):
    try:
        # In a real implementation, you would fetch the report file based on report_id
        # For now, we'll return a sample report
        return jsonify({
            'status': 'success',
            'report_id': report_id,
            'content': 'This is a sample report content. Implement actual report generation in report_generator.py',
            'format': 'txt'
        })
    except Exception as e:
        print(f"Error in download_report: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Catch-all route for undefined endpoints
@app.route('/api/chat', methods=['POST'])
async def chat():
    """Handle chat messages and return AI responses"""
    if not chat_service:
        return jsonify({
            'status': 'error',
            'message': 'Chat service not initialized'
        }), 500
    
    try:
        data = request.get_json()
        messages = data.get('messages', [])
        
        if not messages:
            return jsonify({
                'status': 'error',
                'message': 'No messages provided'
            }), 400
        
        # Process the chat message
        response = await chat_service.process_chat(messages)
        
        if response.get('status') == 'error':
            return jsonify({
                'status': 'error',
                'message': response.get('error', 'Unknown error')
            }), 500
        
        return jsonify({
            'status': 'success',
            'response': response.get('response', '')
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error processing chat: {str(e)}'
        }), 500

@app.route('/api/chat/stream', methods=['POST'])
async def chat_stream():
    """Stream chat responses for a more interactive experience"""
    if not chat_service:
        return jsonify({
            'status': 'error',
            'message': 'Chat service not initialized'
        }), 500
    
    async def generate():
        try:
            data = request.get_json()
            messages = data.get('messages', [])
            
            if not messages:
                yield 'data: ' + json.dumps({
                    'status': 'error',
                    'message': 'No messages provided'
                }) + '\n\n'
            # Process the chat message
            response = await chat_service.process_chat(messages)
            
            if response.get('status') == 'error':
                yield 'data: ' + json.dumps({
                    'status': 'error',
                    'message': response.get('error', 'Unknown error')
                }) + '\n\n'
            else:
                # Stream the response in chunks for better UX
                response_text = response.get('response', '')
                chunk_size = 20
                for i in range(0, len(response_text), chunk_size):
                    yield 'data: ' + json.dumps({
                        'status': 'success',
                        'chunk': response_text[i:i+chunk_size],
                        'done': i + chunk_size >= len(response_text)
                    }) + '\n\n'
                    # Small delay to simulate streaming
                    await asyncio.sleep(0.01)
                    
        except Exception as e:
            yield 'data: ' + json.dumps({
                'status': 'error',
                'message': f'Error processing chat: {str(e)}'
            }) + '\n\n'
    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@app.route('/<path:path>')
def catch_all(path):
    return jsonify({
        'status': 'error',
        'message': f'Endpoint not found: /{path}'
    }), 404

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=5005, help='Port to run Flask app on')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to run Flask app on')
    args = parser.parse_args()
    app.run(host=args.host, port=args.port, debug=False)
