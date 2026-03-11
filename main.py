import os
import argparse
import pandas as pd
import numpy as np
from datetime import datetime
import cv2
# Import our modules
from data_collection import NetworkTrafficCollector
from visualization import NetworkTrafficVisualizer
from model_training import NetworkAnomalyDetector
from anomaly_detection_fix import AnomalyDetector
from report_generation import NetworkReportGenerator
from dashboard import app

def parse_arguments():
    parser = argparse.ArgumentParser(description='Network Traffic Visualization and Anomaly Detection')
    
    # Mode selection
    parser.add_argument('--mode', type=str, choices=['collect', 'visualize', 'train', 'detect', 'report', 'dashboard'],
                       default='dashboard', help='Operation mode')
    
    # Data collection argumentspip
    parser.add_argument('--interface', type=str, default='eth0', help='Network interface to capture')
    parser.add_argument('--duration', type=int, default=60, help='Duration of capture in seconds')
    parser.add_argument('--output', type=str, default='data/traffic.csv', help='Output file path')
    
    # Visualization arguments
    parser.add_argument('--input', type=str, default='data/traffic.csv', help='Input traffic data file')
    parser.add_argument('--vis_type', type=str, choices=['heatmap', 'spectrogram', 'timeseries'], 
                        default='heatmap', help='Visualization type')
    parser.add_argument('--vis_output', type=str, default='visualizations/',
                        help='Directory to save visualizations')
    
    # Model training arguments
    parser.add_argument('--train_data', type=str, default='data/training_data/', 
                        help='Directory containing training data')
    parser.add_argument('--model_output', type=str, default='models/anomaly_detector.h5', 
                        help='Path to save trained model')
    parser.add_argument('--epochs', type=int, default=10, help='Number of training epochs')
    parser.add_argument('--pretrained_weights', type=str, default=None,
                    help='/Users/ahsansaleem/Desktop/cv_project/models/simple_cnn_best_model.h5')
    
    # Anomaly detection arguments
    parser.add_argument('--model_path', type=str, default='models/anomaly_detector.h5', 
                        help='Path to trained model')
    parser.add_argument('--threshold', type=float, default=0.8, 
                        help='Anomaly detection threshold')
    
    # Report generation arguments
    parser.add_argument('--report_output', type=str, default='reports/', 
                        help='Directory to save generated reports')
    
    # Dashboard arguments
    parser.add_argument('--port', type=int, default=5000, help='Dashboard port (default: 5000)')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Dashboard host (default: 0.0.0.0)')
    
    return parser.parse_args()

def main():
    # Parse command line arguments
    args = parse_arguments()
    
    # Create necessary directories
    os.makedirs('data', exist_ok=True)
    os.makedirs('visualizations', exist_ok=True)
    os.makedirs('models', exist_ok=True)
    os.makedirs('reports', exist_ok=True)
    
    # Handle different modes
    if args.mode == 'collect':
        print(f"Collecting network traffic from {args.interface} for {args.duration} seconds...")
        collector = NetworkTrafficCollector(interface=args.interface)
        df = collector.collect_traffic(duration=args.duration)
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        df.to_csv(args.output, index=False)
        print(f"Traffic data saved to {args.output}")
        
    elif args.mode == 'visualize':
        print(f"Visualizing network traffic from {args.input}...")
        visualizer = NetworkTrafficVisualizer()
        df = pd.read_csv(args.input)
        os.makedirs(args.vis_output, exist_ok=True)
        visualizer.create_visualizations(df, output_dir=args.vis_output, vis_type=args.vis_type)
        print(f"Visualizations saved to {args.vis_output}")
        
    elif args.mode == 'train':
        print(f"Training anomaly detection model using data from {args.train_data}...")
        trainer = NetworkAnomalyDetector()
        
        # Load pre-trained weights if specified
        if args.pretrained_weights and os.path.exists(args.pretrained_weights):
            print(f"Loading pre-trained weights from {args.pretrained_weights}")
            trainer.load_model(args.pretrained_weights)
            
        X_train, y_train = trainer.prepare_training_data(args.train_data)
        
        # Use the loaded model if available, otherwise create a new one
        if args.pretrained_weights and os.path.exists(args.pretrained_weights) and trainer.model is not None:
            print(f"Continuing training from pre-trained model")
            model = trainer.train_model(X_train, y_train, epochs=args.epochs, pretrained_model=trainer.model)
        else:
            model = trainer.train_model(X_train, y_train, epochs=args.epochs)
            
        os.makedirs(os.path.dirname(args.model_output), exist_ok=True)
        trainer.save_model(model, args.model_output)
        print(f"Trained model saved to {args.model_output}")
        
    elif args.mode == 'detect':
        print(f"Running anomaly detection on {args.input} using model {args.model_path}...")
        detector = AnomalyDetector(model_path=args.model_path, threshold=args.threshold)
        df = pd.read_csv(args.input)
        anomalies = detector.detect_anomalies(df)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"data/anomalies_{timestamp}.csv"
        anomalies.to_csv(output_file, index=False)
        print(f"Detected anomalies saved to {output_file}")
        
    elif args.mode == 'report':
        print(f"Generating reports from traffic data {args.input}...")
        generator = NetworkReportGenerator()
        df = pd.read_csv(args.input)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(args.report_output, f"report_{timestamp}.txt")
        os.makedirs(args.report_output, exist_ok=True)
        generator.generate_report(df, output_file=report_file)
        print(f"Report generated at {report_file}")
        
    elif args.mode == 'dashboard':
        print(f"Starting dashboard on {args.host}:{args.port}...")
        app.run(debug=True, host=args.host, port=args.port)
        
    else:
        print(f"Invalid mode: {args.mode}")

if __name__ == "__main__":
    main()