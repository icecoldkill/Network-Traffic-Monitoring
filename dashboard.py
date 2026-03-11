# dashboard.py
# At the top with other imports
from dash import callback_context, no_update, dcc, html
from flask import Flask, request, jsonify, send_file, make_response
from flask_cors import CORS  # Add this import at the top
import matplotlib

# Global variable to store the last visualization data for debugging
last_visualization_data = None
matplotlib.use('Agg')  # Use non-GUI backend
import threading
from io import StringIO, BytesIO
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import base64
import io
from datetime import datetime, timedelta
import os
import cv2
from PIL import Image
import time
import socket
import platform
import psutil
import scapy.all as scapy
import requests
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the Groq chatbot
from llm_chatbot import GroqChatbot


# Import our custom modules
# Import the fixed AnomalyDetector
from anomaly_detection_fix import AnomalyDetector

# Initialize detector with your trained model
detector = AnomalyDetector(model_path="/Users/ahsansaleem/Desktop/cv_project/models/simple_cnn_best_model.h5")
from data_collection import NetworkTrafficCollector
from visualization import NetworkTrafficVisualizer
from report_generation import NetworkReportGenerator
#default_model_path = "./models/simple_cnn_final_model.h5"
#detector = AnomalyDetector(default_model_path) if os.path.exists(default_model_path) else None
# Global variables
UPLOAD_DIRECTORY = "./uploads"
if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)

# Create other necessary directories
os.makedirs("./data", exist_ok=True)
os.makedirs("./visualizations", exist_ok=True)
os.makedirs("./models", exist_ok=True)
os.makedirs("./reports", exist_ok=True)
os.makedirs("./anomalies", exist_ok=True)

# Initialize components
collector = NetworkTrafficCollector()
visualizer = NetworkTrafficVisualizer()
# Initialize detector with default model path if available
default_model_path = "./models/simple_cnn_final_model.h5"
detector = AnomalyDetector(default_model_path) if os.path.exists(default_model_path) else None
report_generator = NetworkReportGenerator()

# Global variables for live monitoring
live_capture_active = False
live_capture_thread = None
live_data = pd.DataFrame()

# Get available network interfaces
def get_available_interfaces():
    try:
        # Different approaches based on OS
        if platform.system() == "Windows":
            # Windows approach
            return [iface for iface in scapy.get_windows_if_list()]
        else:
            # Unix-like systems (Linux, MacOS)
            interfaces = []
            for iface in psutil.net_if_addrs().keys():
                interfaces.append(iface)
            return interfaces
    except Exception as e:
        print(f"Error getting interfaces: {e}")
        # Fallback: return common interface names
        return ['eth0', 'wlan0', 'en0', 'lo']
    

# Update your capture_live_traffic function to always use synthetic data in web mode
def capture_live_traffic(interface='eth0', packet_count=100, stop_event=None):
    global live_data
    try:
        # Check if we can use a real capture with python outside of web context
        web_mode = True  # Set to True when deploying to web
        
        if not web_mode and platform.system() != "Darwin":
            try:
                # Try to capture with scapy (will only work locally with proper permissions)
                # Process packets...
                # ...
                # df = process_packets(packets)
                df = generate_enhanced_synthetic_data(n_samples=packet_count)
            except Exception as e:
                print(f"Failed to capture: {e}")
                df = generate_enhanced_synthetic_data(n_samples=packet_count)
        else:
            # In web mode, always use enhanced synthetic data
            print("Using enhanced synthetic data for web mode")
            df = generate_enhanced_synthetic_data(
                n_samples=packet_count
            )
        
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"./data/traffic_{timestamp}.csv"
        df.to_csv(filename, index=False)
        print(f"Data saved to {filename}")
        
        # Update live data
        live_data = df
        return df
    except Exception as e:
        print(f"Error in capture: {e}")
        df = generate_enhanced_synthetic_data(n_samples=packet_count)
        live_data = df
        return df

# Add an enhanced synthetic data generation function
def generate_enhanced_synthetic_data(n_samples=100, anomaly_ratio=0.1):
    """Generate more realistic synthetic network traffic data"""
    # Current time range
    now = datetime.now()
    start_time = now - timedelta(minutes=5)
    
    # Create synthetic data dictionary
    data = {
        'timestamp': [start_time + timedelta(seconds=i) for i in range(n_samples)],
        'src_ip': [f"192.168.1.{np.random.randint(1, 255)}" for _ in range(n_samples)],
        'dst_ip': [f"{np.random.randint(1, 255)}.{np.random.randint(0, 255)}.{np.random.randint(0, 255)}.{np.random.randint(1, 255)}" for _ in range(n_samples)],
        'protocol': np.random.choice([1, 6, 17], size=n_samples, p=[0.1, 0.7, 0.2]),  # ICMP, TCP, UDP
        'src_port': [np.random.randint(1024, 65535) for _ in range(n_samples)],
        'dst_port': [np.random.choice([80, 443, 22, 53, 3389, 8080, 8443]) for _ in range(n_samples)],
        'packet_size': [np.random.randint(64, 1500) for _ in range(n_samples)]
    }
    
    # Create anomalies
    is_anomaly = [0] * n_samples
    anomaly_indices = np.random.choice(range(n_samples), int(n_samples * anomaly_ratio), replace=False)
    
    for idx in anomaly_indices:
        is_anomaly[idx] = 1
        # Make anomalies more distinct
        anomaly_type = np.random.choice(['size', 'port', 'scanning'])
        
        if anomaly_type == 'size':
            # Unusually large packets
            data['packet_size'][idx] = np.random.randint(1500, 9000)
        elif anomaly_type == 'port':
            # Unusual ports
            data['dst_port'][idx] = np.random.randint(10000, 65000)
        else:
            # Port scanning behavior - sequential ports
            data['dst_port'][idx] = idx % 1000
            data['packet_size'][idx] = 40  # Small packets typical of port scans
    
    data['is_anomaly'] = is_anomaly
    return pd.DataFrame(data)

def capture_live_traffic(interface='eth0', packet_count=100):
    try:
        # Try to use the backend service
        
        response = requests.post('http://localhost:5000/api/capture', json={
            'interface': interface,
            'packet_count': packet_count
        })
        
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'success':
                # Convert to DataFrame
                df = pd.DataFrame(data['data'])
                return df
        
        # Fall back to synthetic data if API call fails
        print("API call failed, generating synthetic data instead")
        return collector.generate_synthetic_data(n_samples=packet_count, anomaly_ratio=0.1)
    
    except Exception as e:
        print(f"Error during live capture: {e}")
        return collector.generate_synthetic_data(n_samples=packet_count, anomaly_ratio=0.1)
    

# Function for continuous monitoring in a thread
def continuous_capture(interface, interval, packet_count, stop_event):
    global live_data
    while not stop_event.is_set():
        try:
            df = capture_live_traffic(interface, packet_count)
            live_data = df
            time.sleep(interval)
        except Exception as e:
            print(f"Error in continuous capture: {e}")
            time.sleep(interval)

# Initialize the Flask server
server = Flask(__name__)

# Initialize the Groq chatbot
chatbot = GroqChatbot(api_key=os.getenv("GROQ_API_KEY"), model_name="llama3-70b-8192")

# Enable CORS for all routes with more permissive settings for development
CORS(server, resources={
    r"/api/*": {
        "origins": "*",  # Allow all origins for development
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        "allow_headers": ["*"],  # Allow all headers
        "expose_headers": ["*"],  # Expose all headers
        "supports_credentials": True
    }
})

# Initialize the Dash app with the Flask server
app = dash.Dash(__name__, 
               server=server,  # Use the Flask server with CORS
               suppress_callback_exceptions=True, 
               meta_tags=[{'name': 'viewport',
                         'content': 'width=device-width, initial-scale=1.0, maximum-scale=1.2, minimum-scale=0.5'}])

# Initialize the Groq chatbot
try:
    chatbot = GroqChatbot(api_key=os.getenv("GROQ_API_KEY"))
    logger.info("Groq chatbot initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Groq chatbot: {str(e)}")
    chatbot = None

# Available interfaces
available_interfaces = get_available_interfaces()
default_interface = available_interfaces[0] if available_interfaces else 'eth0'

app.layout = html.Div([
    html.H1("Network Traffic Visualization and Anomaly Detection"),
    
    # Chatbot interface
    html.Div([
        html.H3("Security Assistant"),
        html.Div(id="chat-messages", style={
            "height": "300px",
            "overflowY": "scroll",
            "border": "1px solid #ddd",
            "padding": "10px",
            "marginBottom": "10px",
            "borderRadius": "5px",
            "backgroundColor": "#f9f9f9"
        }),
        dcc.Input(
            id="chat-input",
            type="text",
            placeholder="Ask me about network security...",
            style={"width": "80%", "padding": "10px", "marginRight": "10px"}
        ),
        html.Button("Send", id="send-button", style={"padding": "10px 20px"}),
        dcc.Store(id='chat-history', data=json.dumps([{"role": "assistant", "content": "Hello! I'm your security assistant. How can I help you with network security today?"}]))
    ], style={"marginBottom": "30px", "padding": "20px", "border": "1px solid #eee", "borderRadius": "5px"}),
    
    # Tabs for different sections
    dcc.Tabs([
        # Data tab
        dcc.Tab(label="Data Collection", children=[
            html.Div([
                html.H3("Upload Network Traffic Data"),
                dcc.Upload(
                    id='upload-data',
                    children=html.Div([
                        'Drag and Drop or ',
                        html.A('Select Files')
                    ]),
                    style={
                        'width': '100%',
                        'height': '60px',
                        'lineHeight': '60px',
                        'borderWidth': '1px',
                        'borderStyle': 'dashed',
                        'borderRadius': '5px',
                        'textAlign': 'center',
                        'margin': '10px'
                    },
                    multiple=False
                ),
                html.Div(id='upload-output'),
                
                html.H3("Or Generate Synthetic Data"),
                html.Div([
                    html.Label("Number of samples:"),
                    dcc.Input(id='synthetic-samples', type='number', value=1000),
                    html.Label("Anomaly ratio:"),
                    dcc.Input(id='anomaly-ratio', type='number', value=0.05, step=0.01, 
                             min=0, max=1),
                    html.Button('Generate', id='generate-button')
                ], style={'margin': '10px'}),
                html.Div(id='synthetic-output'),
                
                html.H3("Live Capture"),
                html.Div([
                    html.Label("Interface:"),
                    dcc.Dropdown(
                        id='capture-interface',
                        options=[{'label': iface, 'value': iface} for iface in available_interfaces],
                        value=default_interface
                    ),
                    html.Label("Packet count:"),
                    dcc.Input(id='capture-packet-count', type='number', value=100),
                    html.Button('Start Capture', id='capture-button'),
                    html.Button('Stop Capture', id='stop-capture-button', disabled=True)
                ], style={'margin': '10px'}),
                html.Div(id='capture-output')
            ])
        ]),
        
        # Visualization tab
        dcc.Tab(label="Visualization", children=[
            html.Div([
                html.H3("Traffic Visualizations"),
                
                # Dropdown to select visualization type
                html.Label("Select Visualization Type:"),
                dcc.Dropdown(
                    id='visualization-type',
                    options=[
                        {'label': 'Time Series', 'value': 'time-series'},
                        {'label': 'Heatmap', 'value': 'heatmap'},
                        {'label': 'Protocol Distribution', 'value': 'protocol-distribution'},
                        {'label': 'Temporal Heatmap', 'value': 'temporal-heatmap'},
                        {'label': 'Traffic Flow', 'value': 'traffic-flow'}
                    ],
                    value='time-series',
                    style={'marginBottom': '20px'}
                ),
                
                # Visualization parameters
                html.Div(id='visualization-params'),
                
                # Button to generate visualization
                html.Button('Generate Visualization', id='visualize-button'),
                
                # Output area for visualization
                html.Div(id='visualization-output')
            ])
        ]),
        
        # Anomaly Detection tab
        dcc.Tab(label="Anomaly Detection", children=[
            html.Div([
                html.H3("Anomaly Detection"),
                
                # Model selection
                html.Label("Select or Upload Model:"),
                dcc.RadioItems(
                    id='model-source',
                    options=[
                        {'label': 'Use default model', 'value': 'default'},
                        {'label': 'Upload custom model', 'value': 'upload'}
                    ],
                    value='default'
                ),
                
                # Model upload
                html.Div(id='model-upload-container', style={'display': 'none'}, children=[
                    dcc.Upload(
                        id='upload-model',
                        children=html.Div([
                            'Drag and Drop or ',
                            html.A('Select Model File')
                        ]),
                        style={
                            'width': '100%',
                            'height': '60px',
                            'lineHeight': '60px',
                            'borderWidth': '1px',
                            'borderStyle': 'dashed',
                            'borderRadius': '5px',
                            'textAlign': 'center',
                            'margin': '10px'
                        }
                    )
                ]),
                
                html.Div(id='model-status'),
                
                # Detection parameters
                html.Label("Anomaly Threshold:"),
                dcc.Slider(
                    id='anomaly-threshold',
                    min=0.1,
                    max=0.9,
                    step=0.05,
                    value=0.5,
                    marks={i/10: str(i/10) for i in range(1, 10)}
                ),
                
                # Button to run detection
                html.Button('Detect Anomalies', id='detect-button'),
                
                # Output area for detection results
                html.Div(id='detection-output')
            ])
        ]),
        
        # Reports tab
        dcc.Tab(label="Reports", children=[
            html.Div([
                html.H3("Network Traffic Reports"),
                
                # Report type selection
                html.Label("Report Type:"),
                dcc.RadioItems(
                    id='report-type',
                    options=[
                        {'label': 'Template-based', 'value': 'template'},
                        {'label': 'NLP-based', 'value': 'nlp'}
                    ],
                    value='template'
                ),
                
                # Button to generate report
                html.Button('Generate Report', id='report-button'),
                
                # Output area for report
                html.Div(id='report-output')
            ])
        ]),
        
        # Dashboard tab
        dcc.Tab(label="Live Dashboard", children=[
            html.Div([
                html.H3("Live Network Traffic Dashboard"),
                html.P("This dashboard updates automatically."),
                
                # Controls for live monitoring
                html.Div([
                    html.Label("Refresh Interval (seconds):"),
                    dcc.Input(id='refresh-interval', type='number', value=15, min=5, max=60),
                    html.Button('Start Live Monitoring', id='start-live-monitoring'),
                    html.Button('Stop Live Monitoring', id='stop-live-monitoring', disabled=True)
                ]),
                
                # Status indicator
                html.Div(id='live-status', children=[
                    html.P("Live monitoring inactive", style={'color': 'gray'})
                ]),
                
                # Interval component for updates
                dcc.Interval(
                    id='dashboard-update-interval',
                    interval=15*1000,  # in milliseconds (15 seconds default)
                    n_intervals=0,
                    disabled=True
                ),
                
                # Dashboard content
                html.Div([
                    # Traffic overview
                    html.Div([
                        html.H4("Traffic Overview"),
                        dcc.Graph(id='traffic-overview-graph')
                    ], style={'width': '50%', 'display': 'inline-block'}),
                    
                    # Protocol distribution
                    html.Div([
                        html.H4("Protocol Distribution"),
                        dcc.Graph(id='protocol-distribution-graph')
                    ], style={'width': '50%', 'display': 'inline-block'}),
                    
                    # Latest visualizations
                    html.Div([
                        html.H4("Latest Traffic Visualization"),
                        html.Div(id='dashboard-visualization')
                    ], style={'width': '100%'}),
                    
                    # Anomaly detection
                    html.Div([
                        html.H4("Anomaly Detection"),
                        html.Div(id='dashboard-anomaly')
                    ], style={'width': '50%', 'display': 'inline-block'}),
                    
                    # Live traffic stats
                    html.Div([
                        html.H4("Live Traffic Statistics"),
                        html.Div(id='traffic-stats')
                    ], style={'width': '50%', 'display': 'inline-block'}),
                    
                    # Latest report
                    html.Div([
                        html.H4("Latest Traffic Report"),
                        html.Div(id='dashboard-report')
                    ])
                ])
            ])
        ])
    ]),
    
    # Store components for sharing data between callbacks
    dcc.Store(id='traffic-data-store'),
    dcc.Store(id='visualization-store'),
    dcc.Store(id='anomaly-store'),
    dcc.Store(id='report-store'),
    dcc.Store(id='live-data-store')
])

# Callback for live capture controls
@app.callback(
    [Output('capture-button', 'disabled'),
     Output('stop-capture-button', 'disabled'),
     Output('capture-output', 'children'),
     Output('traffic-data-store', 'data', allow_duplicate=True)],
    [Input('capture-button', 'n_clicks'),
     Input('stop-capture-button', 'n_clicks')],
    [State('capture-interface', 'value'),
     State('capture-packet-count', 'value')],
    prevent_initial_call=True  # Make sure this is True
)
def control_live_capture(start_clicks, stop_clicks, interface, packet_count):
    global live_capture_active, live_capture_thread, live_data
    
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if trigger_id == 'capture-button' and start_clicks:
        # Start capture
        if live_capture_active:
            return True, False, html.Div("Capture already in progress"), dash.no_update
        
        try:
            # Single capture
            df = capture_live_traffic(interface, packet_count)
            
            # Display a preview of the data
            preview = html.Div([
                html.H4("Live Capture Results"),
                html.P(f"Captured {len(df)} packets from interface {interface}"),
                dash.dash_table.DataTable(
                    data=df.head(10).to_dict('records'),
                    columns=[{'name': i, 'id': i} for i in df.columns],
                    style_table={'overflowX': 'auto'}
                )
            ])
            
            # Store the data
            return False, True, preview, df.to_json(date_format='iso', orient='split')
        
        except Exception as e:
            error_msg = html.Div(f"Error during capture: {str(e)}")
            return False, True, error_msg, dash.no_update
    
    elif trigger_id == 'stop-capture-button' and stop_clicks:
        # Stop capture
        if live_capture_active and live_capture_thread:
            # Reset state
            live_capture_active = False
            live_capture_thread = None
        
        return False, True, html.Div("Capture stopped"), dash.no_update
    
    # Default - shouldn't reach here normally
    return False, True, html.Div("Ready to capture"), dash.no_update
@app.callback(
    [Output('capture-button', 'disabled', allow_duplicate=True),
     Output('stop-capture-button', 'disabled', allow_duplicate=True),
     Output('capture-output', 'children', allow_duplicate=True),
     Output('traffic-data-store', 'data', allow_duplicate=True)],
    [Input('capture-button', 'n_clicks')],
    [State('synthetic-samples', 'value'),
     State('anomaly-ratio', 'value')],
    prevent_initial_call=True
)
def generate_traffic_data(n_clicks, packet_count, anomaly_ratio):
    # Function body as described earlier
    if n_clicks is None:
        return False, True, html.Div("Click 'Generate Traffic' to create simulated traffic data."), None
    
    try:
        # Always use synthetic data in web environment
        print(f"Generating {packet_count} samples of traffic data...")
        
        # Use the enhanced synthetic data generation
        df = generate_enhanced_synthetic_data(
            n_samples=packet_count,
            anomaly_ratio=anomaly_ratio
        )
        
        # Display a preview
        preview = html.Div([
            html.H4("Generated Traffic Data", style={'color': '#2196F3'}),
            html.P([
                f"Created {len(df)} packets of simulated {environment} network traffic",
                html.Br(),
                f"Anomalies included: {include_anomalies == 'yes'}"
            ]),
            dash.dash_table.DataTable(
                data=df.head(10).to_dict('records'),
                columns=[{'name': i, 'id': i} for i in df.columns],
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'left'},
                style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'}
            )
        ])
        
        # Store the data
        return False, True, preview, df.to_json(date_format='iso', orient='split')
    
    except Exception as e:
        return False, True, html.Div(f"Error generating traffic data: {str(e)}"), None
    
@app.callback(
    [Output('detection-output', 'children', allow_duplicate=True),
     Output('anomaly-store', 'data', allow_duplicate=True)],
    Input('detect-button', 'n_clicks'),
    [State('visualization-store', 'data'),
     State('anomaly-threshold', 'value')],
    prevent_initial_call=True
)
def detect_anomalies(n_clicks, viz_info, threshold):
    if n_clicks is None or viz_info is None:
        return html.Div("Click 'Detect Anomalies' to run detection."), None
    
    if detector is None:
        return html.Div("No model loaded. Please load a model first."), None
    
    try:
        # Load the visualization image
        img_path = viz_info['image_path']
        original_img = cv2.imread(img_path)
        
        if original_img is None:
            return html.Div(f"Error: Could not load image from {img_path}"), None
        
        # Run anomaly detection
        prob = detector.predict(original_img)
        is_anomaly = prob > threshold
        
        # Create result display
        if is_anomaly:
            try:
                # Try to generate highlighted image
                highlighted_img, heatmap = detector.apply_gradcam(original_img)
                
                # Save highlighted image
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                highlighted_path = f"./anomalies/anomaly_{timestamp}.png"
                os.makedirs(os.path.dirname(highlighted_path), exist_ok=True)
                cv2.imwrite(highlighted_path, highlighted_img)
                
                # Encode for display
                _, buffer = cv2.imencode('.png', highlighted_img)
                encoded_image = base64.b64encode(buffer).decode()
                
                # Create result display
                result = html.Div([
                    html.H4("Anomaly Detected!", style={'color': 'red'}),
                    html.P(f"Anomaly probability: {prob:.4f}"),
                    html.Img(src=f"data:image/png;base64,{encoded_image}", style={'width': '100%'}),
                    html.P("Areas contributing to anomaly detection are highlighted.")
                ])
                
                # Store anomaly info
                anomaly_info = {
                    'is_anomaly': True,
                    'probability': float(prob),
                    'image_path': highlighted_path,
                    'description': f"Detected anomaly in {viz_info['type']} visualization with probability {prob:.4f}"
                }
            except Exception as e:
                print(f"Error in highlighting: {e}")
                # Fallback to original image
                _, buffer = cv2.imencode('.png', original_img)
                encoded_image = base64.b64encode(buffer).decode()
                
                result = html.Div([
                    html.H4("Anomaly Detected!", style={'color': 'red'}),
                    html.P(f"Anomaly probability: {prob:.4f}"),
                    html.Img(src=f"data:image/png;base64,{encoded_image}", style={'width': '100%'})
                ])
                
                anomaly_info = {
                    'is_anomaly': True,
                    'probability': float(prob),
                    'image_path': img_path,
                    'description': f"Detected anomaly in {viz_info['type']} visualization with probability {prob:.4f}"
                }
        else:
            # No anomaly detected
            _, buffer = cv2.imencode('.png', original_img)
            encoded_image = base64.b64encode(buffer).decode()
            
            result = html.Div([
                html.H4("No Anomaly Detected", style={'color': 'green'}),
                html.P(f"Anomaly probability: {prob:.4f}"),
                html.Img(src=f"data:image/png;base64,{encoded_image}", style={'width': '100%'})
            ])
            
            anomaly_info = {
                'is_anomaly': False,
                'probability': float(prob)
            }
        
        return result, anomaly_info
    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Anomaly detection error details:\n{error_details}")
        return html.Div(f"Error during anomaly detection: {str(e)}"), None
# Callback for uploading data
@app.callback(
    [Output('upload-output', 'children'),
     Output('traffic-data-store', 'data')],
    Input('upload-data', 'contents'),
    State('upload-data', 'filename')
)
def update_output(contents, filename):
    if contents is None:
        return html.Div("No file uploaded."), None
    
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    
    try:
        if 'csv' in filename:
            # Read CSV
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        elif 'pcap' in filename:
            # Save pcap file temporarily
            filepath = os.path.join(UPLOAD_DIRECTORY, filename)
            with open(filepath, 'wb') as f:
                f.write(decoded)
            
            # Load pcap
            df = collector.load_from_pcap(filepath)
        else:
            return html.Div(f"Unsupported file type: {filename}"), None
        
        # Display a preview of the data
        preview = html.Div([
            html.H4(f"Data Preview: {filename}"),
            html.P(f"Loaded {len(df)} records"),
            dash.dash_table.DataTable(
                data=df.head(10).to_dict('records'),
                columns=[{'name': i, 'id': i} for i in df.columns],
                style_table={'overflowX': 'auto'}
            )
        ])
        
        # Store the data
        return preview, df.to_json(date_format='iso', orient='split')
    
    except Exception as e:
        return html.Div(f"Error processing file: {str(e)}"), None

# Callback for generating synthetic data
@app.callback(
    [Output('synthetic-output', 'children'),
     Output('traffic-data-store', 'data', allow_duplicate=True)],
    Input('generate-button', 'n_clicks'),
    [State('synthetic-samples', 'value'),
     State('anomaly-ratio', 'value')],
    prevent_initial_call=True  # Make sure this is True
)
def generate_synthetic_data(n_clicks, n_samples, anomaly_ratio):
    if n_clicks is None:
        return html.Div("Click 'Generate' to create synthetic data."), None
    
    try:
        df = collector.generate_synthetic_data(n_samples=n_samples, anomaly_ratio=anomaly_ratio)
        
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"./data/synthetic_traffic_{timestamp}.csv"
        df.to_csv(filename, index=False)
        print(f"Synthetic data saved to {filename}")
        
        # Check for the anomaly column or is_anomaly column
        anomaly_col = 'anomaly' if 'anomaly' in df.columns else 'is_anomaly' if 'is_anomaly' in df.columns else None
        
        # Display a preview of the data
        preview = html.Div([
            html.H4("Synthetic Data Generated"),
            html.P(f"Created {len(df)} records" + 
                  (f" with {df[anomaly_col].sum()} anomalies" if anomaly_col else "")),
            dash.dash_table.DataTable(
                data=df.head(10).to_dict('records'),
                columns=[{'name': i, 'id': i} for i in df.columns],
                style_table={'overflowX': 'auto'}
            )
        ])
        
        # Store the data
        return preview, df.to_json(date_format='iso', orient='split')
    
    except Exception as e:
        return html.Div(f"Error generating synthetic data: {str(e)}"), None

# Callback for visualization parameters
@app.callback(
    Output('visualization-params', 'children'),
    Input('visualization-type', 'value')
)
def update_visualization_params(viz_type):
    if viz_type == 'time-series':
        return html.Div([
            html.Label("Feature to Visualize:"),
            dcc.Dropdown(
                id='time-series-feature',
                options=[
                    {'label': 'Packet Size', 'value': 'packet_size'},
                    {'label': 'Source Port', 'value': 'src_port'},
                    {'label': 'Destination Port', 'value': 'dst_port'}
                ],
                value='packet_size'
            ),
            html.Label("Window Size:"),
            dcc.Input(id='window-size', type='number', value=100),
            html.Label("Step Size:"),
            dcc.Input(id='step-size', type='number', value=50)
        ])
    elif viz_type == 'heatmap':
        return html.Div([
            html.Label("Feature to Visualize:"),
            dcc.Dropdown(
                id='heatmap-feature',
                options=[
                    {'label': 'Packet Size', 'value': 'packet_size'},
                    {'label': 'Source Port', 'value': 'src_port'},
                    {'label': 'Destination Port', 'value': 'dst_port'}
                ],
                value='packet_size'
            ),
            html.Label("Time Bins:"),
            dcc.Input(id='time-bins', type='number', value=24),
            html.Label("IP Bins:"),
            dcc.Input(id='ip-bins', type='number', value=32)
        ])
    elif viz_type == 'protocol-spectrogram':
        return html.Div([
            html.Label("Window Size:"),
            dcc.Input(id='spec-window-size', type='number', value=100),
            html.Label("Step Size:"),
            dcc.Input(id='spec-step-size', type='number', value=20)
        ])
    return html.Div()

# Callback for generating visualizations
# Modified callback for generating visualizations
# Ultra-simple callback for generating visualizations
@app.callback(
    [Output('visualization-output', 'children'),
     Output('visualization-store', 'data')],
    Input('visualize-button', 'n_clicks'),
    [State('visualization-type', 'value'),
     State('traffic-data-store', 'data')],
    prevent_initial_call=True
)
def generate_visualization(n_clicks, viz_type, json_data):
    global last_visualization_data
    
    if n_clicks is None:
        logger.debug("Visualization button not clicked yet")
        return html.Div("Click 'Generate Visualization' to create visualization."), None
        
    if json_data is None:
        logger.error("No data available for visualization")
        return html.Div("Error: No data available. Please load or generate data first."), None
    
    try:
        # Import at the top level
        from io import StringIO
        
        # Debug: Log the raw JSON data (first 200 chars)
        logger.debug(f"Raw JSON data (first 200 chars): {str(json_data)[:200]}...")
        
        # Store the data for debugging
        last_visualization_data = json_data
        
        try:
            # Load the data
            df = pd.read_json(StringIO(json_data), orient='split')
            logger.debug(f"Successfully loaded DataFrame with shape: {df.shape}")
            logger.debug(f"DataFrame columns: {df.columns.tolist()}")
        except Exception as e:
            logger.error(f"Error loading DataFrame: {str(e)}")
            return html.Div(f"Error loading data: {str(e)}"), None
        
        # Variables to store visualization results
        viz_info = {}
        
        # Generate visualization based on type
        if viz_type == 'time-series':
            try:
                fig = visualizer.create_time_series(df, title='Network Traffic Over Time')
                viz_info = {'type': 'time-series', 'figure': fig.to_dict()}
                return dcc.Graph(figure=fig), viz_info
            except Exception as e:
                logger.error(f"Error creating time series: {str(e)}")
                return html.Div(f"Error creating time series: {str(e)}"), None
                
        elif viz_type == 'heatmap':
            try:
                fig = visualizer.create_heatmap(df, title='Network Traffic Heatmap')
                viz_info = {'type': 'heatmap', 'figure': fig.to_dict()}
                return dcc.Graph(figure=fig), viz_info
            except Exception as e:
                logger.error(f"Error creating heatmap: {str(e)}")
                return html.Div(f"Error creating heatmap: {str(e)}"), None
                
        elif viz_type == 'protocol-distribution':
            try:
                fig = visualizer.create_protocol_distribution(df, title='Protocol Distribution')
                viz_info = {'type': 'protocol-distribution', 'figure': fig.to_dict()}
                return dcc.Graph(figure=fig), viz_info
            except Exception as e:
                logger.error(f"Error creating protocol distribution: {str(e)}")
                return html.Div(f"Error creating protocol distribution: {str(e)}"), None
                
        elif viz_type == 'temporal-heatmap':
            try:
                fig = visualizer.create_temporal_heatmap(df, title='Temporal Heatmap')
                viz_info = {'type': 'temporal-heatmap', 'figure': fig.to_dict()}
                return dcc.Graph(figure=fig), viz_info
            except Exception as e:
                logger.error(f"Error creating temporal heatmap: {str(e)}")
                return html.Div(f"Error creating temporal heatmap: {str(e)}"), None
                
        elif viz_type == 'traffic-flow':
            try:
                fig = visualizer.visualize_traffic_flow(df, title='Network Traffic Flow')
                viz_info = {'type': 'traffic-flow', 'figure': fig.to_dict()}
                return dcc.Graph(figure=fig), viz_info
            except Exception as e:
                logger.error(f"Error creating traffic flow: {str(e)}")
                return html.Div(f"Error creating traffic flow: {str(e)}"), None
            
        else:
            return html.Div(f"Unsupported visualization type: {viz_type}"), None
        
        # If we get here, the visualization type wasn't handled
        return html.Div(f"Unsupported visualization type: {viz_type}"), None
        
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        print(f"ERROR DETAILS: {error_msg}")
        return html.Div(f"Error generating visualization: {str(e)}"), None

# Callback to show/hide model upload
@app.callback(
    Output('model-upload-container', 'style'),
    Input('model-source', 'value')
)
def toggle_model_upload(source):
    if source == 'upload':
        return {'display': 'block'}
    return {'display': 'none'}

# Callback for model loading
@app.callback(
    Output('model-status', 'children'),
    [Input('model-source', 'value'),
     Input('upload-model', 'contents')],
    State('upload-model', 'filename')
)
def load_model(source, contents, filename):
    global detector
    
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if triggered_id == 'model-source' and source == 'default':
        # Use default model
        model_path = "./models/simple_cnn_final_model.h5"
        if os.path.exists(model_path):
            try:
                detector = AnomalyDetector(model_path)
                return html.Div("Default model loaded successfully.", style={'color': 'green'})
            except Exception as e:
                return html.Div(f"Error loading default model: {str(e)}", style={'color': 'red'})
        else:
            return html.Div("Default model not found. Please train a model first.", style={'color': 'red'})
    
    elif triggered_id == 'upload-model' and contents is not None:
        try:
            # Decode and save the model file
            content_type, content_string = contents.split(',')
            decoded = base64.b64decode(content_string)
            
            model_path = os.path.join(UPLOAD_DIRECTORY, filename)
            with open(model_path, 'wb') as f:
                f.write(decoded)
            
            # Load the model
            detector = AnomalyDetector(model_path)
            return html.Div(f"Custom model '{filename}' loaded successfully.", style={'color': 'green'})
        
        except Exception as e:
            return html.Div(f"Error loading model: {str(e)}", style={'color': 'red'})
    
    return html.Div("No model loaded.")

# Callback for anomaly detection
@app.callback(
    [Output('detection-output', 'children'),
     Output('anomaly-store', 'data')],
    Input('detect-button', 'n_clicks'),
    [State('visualization-store', 'data'),
     State('anomaly-threshold', 'value')],
    prevent_initial_call=True
)
def detect_anomalies(n_clicks, viz_info, threshold):
    if n_clicks is None or viz_info is None:
        return html.Div("Click 'Detect Anomalies' to run detection."), None
    
    if detector is None:
        return html.Div("No model loaded. Please load a model first."), None
    
    try:
        # Load the visualization image
        img_path = viz_info['image_path']
        original_img = cv2.imread(img_path)
        
        if original_img is None:
            return html.Div(f"Error: Could not load image from {img_path}"), None
        
        # Calculate appropriate dimensions: 4608 ÷ 3 = 1536 pixels
        # 32 × 48 = 1536, which is a reasonable aspect ratio
        target_height, target_width = 32, 48
        
        # Resize the image to match the model's expected input dimensions
        resized_img = cv2.resize(original_img, (target_width, target_height))
        
        # Print diagnostic information
        print(f"Original image shape: {original_img.shape}")
        print(f"Resized image shape: {resized_img.shape}")
        print(f"Resized flattened size: {target_height * target_width * 3}")
        
        # Run anomaly detection on the resized image
        prob = detector.predict(resized_img)
        is_anomaly = prob > threshold
        
        # Create result display
        if is_anomaly:
            try:
                # Apply GradCAM on the resized image (if supported)
                highlighted_img, heatmap = detector.apply_gradcam(resized_img)
                
                # Resize the highlighted image back to original size for display
                highlighted_img_display = cv2.resize(highlighted_img, (original_img.shape[1], original_img.shape[0]))
                
                # Save highlighted image
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                highlighted_path = f"./anomalies/anomaly_{timestamp}.png"
                os.makedirs(os.path.dirname(highlighted_path), exist_ok=True)
                cv2.imwrite(highlighted_path, highlighted_img_display)
                
                # Encode for display
                _, buffer = cv2.imencode('.png', highlighted_img_display)
                encoded_image = base64.b64encode(buffer).decode()
                
                # Create result display
                result = html.Div([
                    html.H4("Anomaly Detected!", style={'color': 'red'}),
                    html.P(f"Anomaly probability: {prob:.4f}"),
                    html.Img(src=f"data:image/png;base64,{encoded_image}", style={'width': '100%'}),
                    html.P("Areas contributing to anomaly detection are highlighted.")
                ])
                
                # Store anomaly info
                anomaly_info = {
                    'is_anomaly': True,
                    'probability': float(prob),
                    'image_path': highlighted_path,
                    'description': f"Detected anomaly in {viz_info['type']} visualization with probability {prob:.4f}"
                }
            except Exception as e:
                print(f"Error applying GradCAM: {e}")
                # Fall back to showing the original image
                _, buffer = cv2.imencode('.png', original_img)
                encoded_image = base64.b64encode(buffer).decode()
                
                result = html.Div([
                    html.H4("Anomaly Detected!", style={'color': 'red'}),
                    html.P(f"Anomaly probability: {prob:.4f}"),
                    html.Img(src=f"data:image/png;base64,{encoded_image}", style={'width': '100%'}),
                    html.P("Note: Advanced visualization unavailable.")
                ])
                
                anomaly_info = {
                    'is_anomaly': True,
                    'probability': float(prob),
                    'image_path': img_path,
                    'description': f"Detected anomaly in {viz_info['type']} visualization with probability {prob:.4f}"
                }
        else:
            # No anomaly detected - show original image
            _, buffer = cv2.imencode('.png', original_img)
            encoded_image = base64.b64encode(buffer).decode()
            
            result = html.Div([
                html.H4("No Anomaly Detected", style={'color': 'green'}),
                html.P(f"Anomaly probability: {prob:.4f}"),
                html.Img(src=f"data:image/png;base64,{encoded_image}", style={'width': '100%'})
            ])
            
            anomaly_info = {
                'is_anomaly': False,
                'probability': float(prob)
            }
        
        return result, anomaly_info
    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Anomaly detection error details:\n{error_details}")
        return html.Div(f"Error during anomaly detection: {str(e)}"), None
    

# Find this in your dashboard.py and replace it
@app.callback(
    [Output('report-output', 'children'),
     Output('report-store', 'data')],
    Input('report-button', 'n_clicks'),
    [State('traffic-data-store', 'data'),
     State('anomaly-store', 'data'),
     State('report-type', 'value')],
    prevent_initial_call=True
)
def generate_report(n_clicks, json_data, anomaly_info, report_type):
    if n_clicks is None or json_data is None:
        return html.Div("Click 'Generate Report' to create a report."), None
    
    try:
        # Load the data
        df = pd.read_json(StringIO(json_data), orient='split')  # Fix the JSON warning here
        
        # Generate the report - CHANGE THIS LINE
        report_data = report_generator.generate_report(df, anomalies=anomaly_info, report_type=report_type)
        
        # Get the main report text
        report = report_data['main_report']
        
        # Format for display
        report_display = html.Div([
            html.H4("Network Traffic Report"),
            html.Pre(report, style={'whiteSpace': 'pre-wrap', 'wordBreak': 'break-word',
                                    'border': '1px solid #ddd', 'padding': '10px',
                                    'maxHeight': '500px', 'overflowY': 'auto'})
        ])
        
        # If there are incident reports, add them
        if report_data['incident_reports']:
            incident_displays = []
            
            for i, incident in enumerate(report_data['incident_reports']):
                incident_displays.append(html.Div([
                    html.H5(f"Incident Report #{i+1}"),
                    html.Pre(incident, style={'whiteSpace': 'pre-wrap', 'wordBreak': 'break-word',
                                             'border': '1px solid #ddd', 'padding': '10px',
                                             'maxHeight': '300px', 'overflowY': 'auto'})
                ]))
            
            report_display.children.append(html.H4("Incident Reports"))
            report_display.children.extend(incident_displays)
        
        # Store report info
        report_info = {
            'type': report_type,
            'timestamp': datetime.now().isoformat(),
            'stats': {k: str(v) if isinstance(v, (pd.Timestamp, datetime)) else v 
                     for k, v in report_data['stats'].items()},
            'events_count': len(report_data['events'])
        }
        
        return report_display, report_info
    
    except Exception as e:
        return html.Div(f"Error generating report: {str(e)}"), None

# Callback for live monitoring controls
@app.callback(
    [Output('start-live-monitoring', 'disabled'),
     Output('stop-live-monitoring', 'disabled'),
     Output('dashboard-update-interval', 'disabled'),
     Output('dashboard-update-interval', 'interval'),
     Output('live-status', 'children')],
    [Input('start-live-monitoring', 'n_clicks'),
     Input('stop-live-monitoring', 'n_clicks')],
    [State('refresh-interval', 'value'),
     State('capture-interface', 'value')],
    prevent_initial_call=True
)
def control_live_monitoring(start_clicks, stop_clicks, interval, interface):
    global live_capture_active, live_capture_thread
    
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if trigger_id == 'start-live-monitoring' and start_clicks:
        # Start live monitoring
        if not live_capture_active:
            # Convert interval to milliseconds
            interval_ms = max(5000, min(60000, interval * 1000))
            
            return True, False, False, interval_ms, html.Div([
                html.P("Live monitoring active", style={'color': 'green', 'font-weight': 'bold'}),
                html.P(f"Monitoring interface: {interface}"),
                html.P(f"Refresh interval: {interval} seconds")
            ])
    
    elif trigger_id == 'stop-live-monitoring' and stop_clicks:
        # Stop live monitoring
        if live_capture_active and live_capture_thread:
            # Reset state
            live_capture_active = False
            live_capture_thread = None
            
        return False, True, True, 60000, html.Div([
            html.P("Live monitoring stopped", style={'color': 'gray'})
        ])
    
    # Default - shouldn't reach here normally
    return False, True, True, 60000, html.Div([
        html.P("Live monitoring inactive", style={'color': 'gray'})
    ])
# Modified callback for generating visualizations

# Callback for dashboard updates
@app.callback(
    [Output('traffic-overview-graph', 'figure'),
     Output('protocol-distribution-graph', 'figure'),
     Output('dashboard-visualization', 'children'),
     Output('dashboard-anomaly', 'children', allow_duplicate=True),
     Output('traffic-stats', 'children'),
     Output('dashboard-report', 'children'),
     Output('live-data-store', 'data')],
    [Input('dashboard-update-interval', 'n_intervals'),
     Input('capture-interface', 'value')],
    [State('live-data-store', 'data'),
     State('visualization-store', 'data'),
     State('anomaly-store', 'data'),
     State('report-store', 'data')],
    prevent_initial_call=True
)
def update_dashboard(n_intervals, interface, live_json_data, viz_info, anomaly_info, report_info):
    # Function body stays the same
    # Rest of the function unchanged
    ...
    # Create empty figures in case data is not available
    empty_fig = go.Figure()
    empty_fig.update_layout(title="No data available")
    
    # Default components
    visualization_component = html.Div("No visualization available")
    anomaly_component = html.Div("No anomaly detection results available")
    traffic_stats_component = html.Div("No traffic statistics available")
    report_component = html.Div("No report available")
    
    # Check if this is the first update
    is_first_update = n_intervals == 0
    
    # Try to get live data from the store or capture new data
    try:
        if live_json_data and not is_first_update:
            # Use stored data
            df = pd.read_json(live_json_data, orient='split')
        else:
            # Capture new data for the dashboard
            try:
                df = capture_live_traffic(interface=interface, packet_count=100)
                print(f"Dashboard captured {len(df)} packets")
            except Exception as e:
                print(f"Error in dashboard capture: {e}")
                # Use synthetic data as fallback
                df = collector.generate_synthetic_data(n_samples=100, anomaly_ratio=0.05)
                print("Using synthetic data for dashboard")
        
        # Check if we got data
        if df is None or len(df) == 0:
            return empty_fig, empty_fig, visualization_component, anomaly_component, traffic_stats_component, report_component, None
        
        # Convert timestamp to datetime if it's not already
        if 'timestamp' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Store for next update
        json_data = df.to_json(date_format='iso', orient='split')
        
        # Create traffic overview figure
        if 'packet_size' in df.columns:
            if 'timestamp' in df.columns:
                # Group by timestamp if available
                df['time_window'] = df['timestamp'].dt.floor('10s')
                traffic_summary = df.groupby('time_window').agg(
                    packet_count=('packet_size', 'count'),
                    total_bytes=('packet_size', 'sum'),
                    avg_packet_size=('packet_size', 'mean')
                ).reset_index()
                
                fig_overview = px.line(traffic_summary, x='time_window', y=['packet_count', 'avg_packet_size'],
                                     title='Network Traffic Overview')
            else:
                # Just use packet index if no timestamp
                df['packet_index'] = range(len(df))
                fig_overview = px.line(df, x='packet_index', y='packet_size',
                                     title='Packet Size Distribution')
        else:
            fig_overview = empty_fig
        
        # Create protocol distribution figure
        if 'protocol' in df.columns:
            # Map protocol numbers to names
            protocol_map = {1: 'ICMP', 6: 'TCP', 17: 'UDP'}
            df['protocol_name'] = df['protocol'].map(lambda x: protocol_map.get(x, f'Protocol {x}'))
            
            protocol_counts = df['protocol_name'].value_counts().reset_index()
            protocol_counts.columns = ['protocol', 'count']
            
            fig_protocol = px.pie(protocol_counts, values='count', names='protocol',
                                title='Protocol Distribution')
        else:
            fig_protocol = empty_fig
        
        # Create a live visualization on the fly for the dashboard
        try:
            # Generate a new visualization based on the latest data
            if 'packet_size' in df.columns:
                # Create a heatmap visualization
                heatmap = visualizer.create_heatmap(df, feature='packet_size',
                                                  time_bins=12, ip_bins=12)
                if heatmap is not None:
                    # Convert to base64 for display
                    if isinstance(heatmap, np.ndarray):
                        # Handle different image formats
                        if len(heatmap.shape) == 2:  # Grayscale
                            img_pil = Image.fromarray(heatmap)
                        else:  # Color
                            img_pil = Image.fromarray(heatmap)
                        
                        buf = io.BytesIO()
                        img_pil.save(buf, format='PNG')
                        encoded_image = base64.b64encode(buf.getvalue()).decode()
                        
                        visualization_component = html.Div([
                            html.P("Live Traffic Heatmap"),
                            html.Img(src=f"data:image/png;base64,{encoded_image}", style={'width': '100%'})
                        ])
            
            # Run anomaly detection on the visualization if model is available
            if detector is not None and heatmap is not None:
                try:
                    # Predict anomaly probability
                    prob = detector.predict(heatmap)
                    is_anomaly = prob > 0.5  # Use default threshold
                    
                    if is_anomaly:
                        anomaly_component = html.Div([
                            html.P("Potential Anomaly Detected!", style={'color': 'red', 'font-weight': 'bold'}),
                            html.P(f"Probability: {prob:.4f}")
                        ])
                    else:
                        anomaly_component = html.Div([
                            html.P("No Anomaly Detected", style={'color': 'green'}),
                            html.P(f"Probability: {prob:.4f}")
                        ])
                except Exception as e:
                    print(f"Dashboard anomaly detection error: {e}")
                    anomaly_component = html.Div([
                        html.P("Anomaly detection unavailable", style={'color': 'gray'}),
                        html.P(f"Error: {str(e)}")
                    ])
        except Exception as e:
            print(f"Dashboard visualization error: {e}")
        
        # Generate traffic statistics
        traffic_stats = []
        
        # Total packets
        traffic_stats.append(html.P(f"Total Packets: {len(df)}"))
        
        # Total traffic volume
        if 'packet_size' in df.columns:
            total_bytes = df['packet_size'].sum()
            traffic_stats.append(html.P(f"Total Traffic: {total_bytes:,} bytes"))
            avg_size = df['packet_size'].mean()
            traffic_stats.append(html.P(f"Average Packet Size: {avg_size:.2f} bytes"))
        
        # Protocol distribution
        if 'protocol' in df.columns:
            protocol_counts = df['protocol'].value_counts().to_dict()
            protocol_items = []
            
            for proto, count in protocol_counts.items():
                proto_name = protocol_map.get(proto, f"Protocol {proto}")
                percentage = count / len(df) * 100
                protocol_items.append(html.Li(f"{proto_name}: {count} packets ({percentage:.1f}%)"))
            
            traffic_stats.append(html.P("Protocol Distribution:"))
            traffic_stats.append(html.Ul(protocol_items))
        
        traffic_stats_component = html.Div(traffic_stats)
        
        # Automatically generate a simple report
        try:
            if df is not None and len(df) > 0:
                # Create a simple report summary
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                summary = f"Traffic Summary Report - {timestamp}\n\n"
                
                # Add basic statistics
                summary += f"Total packets analyzed: {len(df)}\n"
                if 'packet_size' in df.columns:
                    summary += f"Total traffic volume: {df['packet_size'].sum():,} bytes\n"
                    summary += f"Average packet size: {df['packet_size'].mean():.2f} bytes\n\n"
                
                # Add protocol distribution
                if 'protocol' in df.columns:
                    summary += "Protocol Distribution:\n"
                    for proto, count in df['protocol'].value_counts().items():
                        proto_name = protocol_map.get(proto, f"Protocol {proto}")
                        percentage = count / len(df) * 100
                        summary += f"  - {proto_name}: {count} packets ({percentage:.1f}%)\n"
                
                # Add info about any detected anomalies
                if anomaly_info and anomaly_info.get('is_anomaly', False):
                    summary += f"\nANOMALY DETECTED!\n"
                    summary += f"Anomaly probability: {anomaly_info['probability']:.4f}\n"
                    if 'description' in anomaly_info:
                        summary += f"Description: {anomaly_info['description']}\n"
                
                report_component = html.Div([
                    html.P("Automatic Traffic Report"),
                    html.Pre(summary, style={'whiteSpace': 'pre-wrap', 'wordBreak': 'break-word',
                                         'border': '1px solid #ddd', 'padding': '10px',
                                         'maxHeight': '300px', 'overflowY': 'auto'})
                ])
        except Exception as e:
            print(f"Dashboard report generation error: {e}")
        
        # Return all components
        return fig_overview, fig_protocol, visualization_component, anomaly_component, traffic_stats_component, report_component, json_data
    
    except Exception as e:
        print(f"Dashboard update error: {e}")
        return empty_fig, empty_fig, visualization_component, anomaly_component, traffic_stats_component, report_component, None

# Callback for chat functionality
@app.callback(
    [Output("chat-messages", "children"),
     Output("chat-input", "value"),
     Output("chat-history", "data")],
    [Input("send-button", "n_clicks"),
     Input("chat-input", "n_submit")],
    [State("chat-input", "value"),
     State("chat-history", "data")]
)
def update_chat(n_clicks, n_submit, user_input, history_data):
    if n_clicks is None and n_submit is None:
        return no_update, "", no_update
    
    if not user_input or not user_input.strip():
        return no_update, "", no_update
    
    try:
        # Get conversation history
        conversation_history = json.loads(history_data)
        
        # Add user message to history
        conversation_history.append({"role": "user", "content": user_input})
        
        # Get assistant's response
        if chatbot:
            response = chatbot.chat(user_input, conversation_history[:-1])  # Exclude current user message
            assistant_response = response["response"]
            conversation_history = response["conversation_history"]
        else:
            assistant_response = "I'm sorry, the chatbot is currently unavailable. Please try again later."
            conversation_history.append({"role": "assistant", "content": assistant_response})
        
        # Create chat bubbles
        chat_messages = []
        for msg in conversation_history:
            if msg["role"] == "user":
                chat_messages.append(
                    html.Div(
                        html.Div(
                            msg["content"],
                            style={
                                "padding": "10px 15px",
                                "borderRadius": "15px",
                                "backgroundColor": "#e3f2fd",
                                "display": "inline-block",
                                "maxWidth": "80%",
                                "textAlign": "left"
                            }
                        ),
                        style={"textAlign": "right", "margin": "10px 0"}
                    )
                )
            else:
                chat_messages.append(
                    html.Div(
                        html.Div(
                            msg["content"],
                            style={
                                "padding": "10px 15px",
                                "borderRadius": "15px",
                                "backgroundColor": "#f1f1f1",
                                "display": "inline-block",
                                "maxWidth": "80%",
                                "textAlign": "left"
                            }
                        ),
                        style={"textAlign": "left", "margin": "10px 0"}
                    )
                )
        
        return chat_messages, "", json.dumps(conversation_history)
    
    except Exception as e:
        logger.error(f"Error in chat callback: {str(e)}")
        error_msg = f"Error: {str(e)}"
        return html.Div(error_msg, style={"color": "red"}), "", no_update

# Callback to handle visualization data
@app.callback(
    Output('visualization-container', 'children'),
    [Input('generate-viz', 'n_clicks')],
    [State('viz-type', 'value'),
     State('traffic-data-store', 'data')]
)
def update_visualization(n_clicks, viz_type, data):
    if n_clicks is None or not data:
        return "Upload or generate data first, then click 'Generate Visualization'"
    
    try:
        df = pd.read_json(data, orient='split')
        visualizer = NetworkTrafficVisualizer()
        
        # Generate the appropriate visualization based on type
        if viz_type == 'heatmap':
            fig = visualizer.create_heatmap(df)
            return dcc.Graph(figure=fig)
            
        elif viz_type == 'timeseries':
            fig = visualizer.create_time_series(df)
            return dcc.Graph(figure=fig)
            
        elif viz_type == 'protocol_dist':
            fig = visualizer.create_protocol_distribution(df)
            return dcc.Graph(figure=fig)
            
        else:
            return "Unsupported visualization type"
            
    except Exception as e:
        logger.error(f"Error generating visualization: {str(e)}")
        return f"Error generating visualization: {str(e)}"

# API Endpoint for generating synthetic data
@app.server.route('/api/generate-data', methods=['POST'])
def generate_data_api():
    """API endpoint to generate synthetic network traffic data"""
    try:
        data = request.get_json()
        network_type = data.get('networkType', 'office')
        sample_size = int(data.get('sampleSize', 100))
        include_anomalies = data.get('includeAnomalies', True)
        
        # Generate synthetic data
        df = generate_enhanced_synthetic_data(
            n_samples=sample_size,
            anomaly_ratio=0.05 if include_anomalies else 0.0
        )
        
        # Save to file (optional)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"./data/traffic_{timestamp}.csv"
        df.to_csv(filename, index=False)
        
        return jsonify({
            "status": "success",
            "message": "Data generated successfully",
            "count": len(df),
            "data": df.to_dict(orient='records'),
            "file": filename
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# API Endpoint for chatbot
@app.server.route('/api/chat', methods=['POST'])
def chat():
    """API endpoint for the LLM chatbot"""
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({"status": "error", "message": "No message provided"}), 400
        
        # Get response from chatbot
        if chatbot:
            response = chatbot.chat(user_message)
        else:
            response = "Chatbot not initialized. Please check your API key."
        
        return jsonify({
            "status": "success",
            "response": response
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Add a debug route to check the data store
@app.server.route('/debug/store')
def debug_store():
    global last_visualization_data
    
    # Return a simple HTML page showing the last data
    return f"""
    <html>
        <head><title>Debug: Data Store</title></head>
        <body>
            <h1>Debug: Data Store</h1>
            <h2>Last Visualization Data:</h2>
            <pre>{str(last_visualization_data)[:2000] if last_visualization_data else 'No data available'}</pre>
            <p><a href="/">Back to Dashboard</a></p>
        </body>
    </html>
    """

# Add CORS headers to all responses
@server.after_request
def after_request(response):
    # Allow all origins for development
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', '*')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS, PATCH')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    response.headers.add('Access-Control-Expose-Headers', '*')
    response.headers.add('Cache-Control', 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0')
    response.headers.add('Pragma', 'no-cache')
    response.headers.add('Expires', '0')
    return response

# Run the application
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5005, dev_tools_hot_reload=True)