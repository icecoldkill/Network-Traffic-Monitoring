# report_generation.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import nltk
from nltk.tokenize import word_tokenize
from transformers import pipeline, AutoModelForSeq2SeqLM, AutoTokenizer
import os
import json

# Download required NLTK resources
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('wordnet')

class NetworkReportGenerator:
    def __init__(self, output_dir="./reports", model_name="t5-small"):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # Load the NLP model
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
            self.summarizer = pipeline("summarization", model=model_name)
        except:
            print(f"Could not load {model_name}. Using template-based generation only.")
            self.summarizer = None
        
        # Protocol name mapping
        self.protocol_map = {
            1: "ICMP",
            6: "TCP", 
            17: "UDP",
            'TCP': "TCP",
            'UDP': "UDP",
            'ICMP': "ICMP"
        }
    
    def extract_key_statistics(self, df):
        """Extract key statistics from the traffic data"""
        stats = {}
        
        # Convert timestamp to datetime if it's not already
        if 'timestamp' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Time range
        stats['start_time'] = df['timestamp'].min()
        stats['end_time'] = df['timestamp'].max()
        stats['duration'] = (stats['end_time'] - stats['start_time']).total_seconds()
        
        # Traffic volume
        stats['total_packets'] = len(df)
        stats['total_bytes'] = df['packet_size'].sum() if 'packet_size' in df.columns else 'N/A'
        stats['avg_packet_size'] = df['packet_size'].mean() if 'packet_size' in df.columns else 'N/A'
        
        # Protocol distribution
        if 'protocol' in df.columns:
            protocol_counts = df['protocol'].value_counts()
            stats['protocol_counts'] = protocol_counts.to_dict()
            stats['most_common_protocol'] = protocol_counts.index[0]
        
        # Source and destination statistics
        if 'src_ip' in df.columns and 'dst_ip' in df.columns:
            stats['unique_src_ips'] = df['src_ip'].nunique()
            stats['unique_dst_ips'] = df['dst_ip'].nunique()
            stats['top_src_ips'] = df['src_ip'].value_counts().head(5).to_dict()
            stats['top_dst_ips'] = df['dst_ip'].value_counts().head(5).to_dict()
        
        # Port statistics
        if 'src_port' in df.columns and 'dst_port' in df.columns:
            stats['top_src_ports'] = df['src_port'].value_counts().head(5).to_dict()
            stats['top_dst_ports'] = df['dst_port'].value_counts().head(5).to_dict()
        
        return stats
    
    def detect_events(self, df, window_size='1min', std_threshold=3.0):
        """Detect significant events in the traffic data"""
        # Convert timestamp to datetime if it's not already
        if 'timestamp' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Resample data into time windows
        df = df.set_index('timestamp')
        
        # Count packets per window
        packet_counts = df.resample(window_size).size()
        
        # Calculate rolling statistics
        rolling_mean = packet_counts.rolling(window='5min', min_periods=1).mean()
        rolling_std = packet_counts.rolling(window='5min', min_periods=1).std().fillna(0)
        
        # Detect anomalies
        anomalies = (packet_counts > (rolling_mean + std_threshold * rolling_std)) | \
                    (packet_counts < (rolling_mean - std_threshold * rolling_std))
        
        # Extract events
        events = []
        for timestamp, is_anomaly in anomalies.items():
            if is_anomaly:
                window_data = df.loc[timestamp - pd.Timedelta(window_size):timestamp]
                
                # Get the dominant protocol in this window
                if 'protocol' in window_data.columns:
                    dominant_protocol = window_data['protocol'].value_counts().index[0]
                else:
                    dominant_protocol = 'Unknown'
                
                # Get the dominant source IP
                if 'src_ip' in window_data.columns:
                    dominant_src = window_data['src_ip'].value_counts().index[0]
                else:
                    dominant_src = 'Unknown'
                
                packet_count = len(window_data)
                avg_size = window_data['packet_size'].mean() if 'packet_size' in window_data.columns else 0
                
                events.append({
                    'timestamp': timestamp,
                    'packet_count': packet_count,
                    'dominant_protocol': dominant_protocol,
                    'dominant_src_ip': dominant_src,
                    'avg_packet_size': avg_size,
                    'deviation_ratio': packet_counts[timestamp] / (rolling_mean[timestamp] if rolling_mean[timestamp] > 0 else 1)
                })
        
        return events
    
    def generate_template_report(self, stats, events, anomalies=None):
        """Generate a report using templates"""
        report = f"Network Traffic Report\n"
        report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # Time range information
        report += f"Time Period: {stats['start_time']} to {stats['end_time']}\n"
        report += f"Duration: {timedelta(seconds=stats['duration'])}\n\n"
        
        # Traffic overview
        report += f"Traffic Overview:\n"
        report += f"- Total packets: {stats['total_packets']}\n"
        report += f"- Total bytes: {stats['total_bytes']}\n"
        report += f"- Average packet size: {stats['avg_packet_size']:.2f} bytes\n\n"
        
        # Protocol distribution
        report += f"Protocol Distribution:\n"
        for protocol, count in stats['protocol_counts'].items():
            protocol_name = self.protocol_map.get(protocol, protocol)
            percentage = (count / stats['total_packets']) * 100
            report += f"- {protocol_name}: {count} packets ({percentage:.2f}%)\n"
        
        report += f"\nMost common protocol: {stats['most_common_protocol']}\n\n"
        
        # Source and destination information
        if 'unique_src_ips' in stats:
            report += f"Source and Destination Information:\n"
            report += f"- Unique source IPs: {stats['unique_src_ips']}\n"
            report += f"- Unique destination IPs: {stats['unique_dst_ips']}\n\n"
            
            report += f"Top Source IPs:\n"
            for ip, count in stats['top_src_ips'].items():
                report += f"- {ip}: {count} packets\n"
            
            report += f"\nTop Destination IPs:\n"
            for ip, count in stats['top_dst_ips'].items():
                report += f"- {ip}: {count} packets\n\n"
        
        # Significant events
        if events:
            report += f"Significant Events ({len(events)}):\n"
            for i, event in enumerate(events):
                protocol_name = self.protocol_map.get(event['dominant_protocol'], event['dominant_protocol'])
                report += f"{i+1}. At {event['timestamp']}, detected unusual traffic:\n"
                report += f"   {event['packet_count']} packets ({event['deviation_ratio']:.2f}x normal rate)\n"
                report += f"   Protocol: {protocol_name}, Source: {event['dominant_src_ip']}\n"
                report += f"   Average packet size: {event['avg_packet_size']:.2f} bytes\n\n"
        else:
            report += "No significant events detected during this period.\n\n"
        
        # Visual anomalies detected
        if anomalies and len(anomalies) > 0:
            report += f"Visual Anomalies Detected ({len(anomalies)}):\n"
            for i, anomaly in enumerate(anomalies):
                report += f"{i+1}. Anomaly detected (confidence: {anomaly['probability']:.2f})\n"
                if 'description' in anomaly:
                    report += f"   Description: {anomaly['description']}\n"
                report += f"   Image index: {anomaly['image_index']}\n\n"
        
        report += "End of Report"
        return report
    
    def generate_nlp_report(self, stats, events, anomalies=None):
        """Generate a report using NLP summarization"""
        if self.summarizer is None:
            return self.generate_template_report(stats, events, anomalies)
        
        # Create a detailed input for summarization
        input_text = f"Network traffic report from {stats['start_time']} to {stats['end_time']}. "
        input_text += f"Total packets: {stats['total_packets']}, total bytes: {stats['total_bytes']}. "
        
        # Add protocol information
        input_text += "Protocol distribution: "
        for protocol, count in stats['protocol_counts'].items():
            protocol_name = self.protocol_map.get(protocol, protocol)
            percentage = (count / stats['total_packets']) * 100
            input_text += f"{protocol_name} {percentage:.1f}%, "
        
        # Add source and destination information
        if 'unique_src_ips' in stats:
            input_text += f"Unique source IPs: {stats['unique_src_ips']}, "
            input_text += f"Unique destination IPs: {stats['unique_dst_ips']}. "
            
            # Add top IPs
            input_text += "Top source IP: "
            top_src = list(stats['top_src_ips'].items())[0]
            input_text += f"{top_src[0]} with {top_src[1]} packets. "
            
            top_dst = list(stats['top_dst_ips'].items())[0]
            input_text += f"Top destination IP: {top_dst[0]} with {top_dst[1]} packets. "
        
        # Add event information
        if events:
            input_text += f"Detected {len(events)} significant events: "
            for event in events:
                protocol_name = self.protocol_map.get(event['dominant_protocol'], event['dominant_protocol'])
                input_text += f"At {event['timestamp']}, {event['packet_count']} packets "
                input_text += f"({event['deviation_ratio']:.1f}x normal) using {protocol_name} "
                input_text += f"from {event['dominant_src_ip']}. "
        else:
            input_text += "No significant events detected during this period. "
        
        # Add anomaly information
        if anomalies and len(anomalies) > 0:
            input_text += f"Detected {len(anomalies)} visual anomalies in network traffic patterns. "
            for anomaly in anomalies:
                if 'description' in anomaly:
                    input_text += f"Anomaly description: {anomaly['description']}. "
        
        # Request a comprehensive summary and analysis
        prompt = "Summarize this network traffic information and highlight security concerns: " + input_text
        
        # Generate the summary
        summary = self.summarizer(prompt, max_length=500, min_length=100, do_sample=False)[0]['summary_text']
        
        # Format the final report
        report = f"Network Traffic Report\n"
        report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        report += f"Time Period: {stats['start_time']} to {stats['end_time']}\n"
        report += f"Duration: {timedelta(seconds=stats['duration'])}\n\n"
        report += "Summary:\n"
        report += summary + "\n\n"
        
        # Add detailed metrics
        report += "Detailed Metrics:\n"
        report += f"- Total packets: {stats['total_packets']}\n"
        report += f"- Total bytes: {stats['total_bytes']}\n"
        report += f"- Average packet size: {stats['avg_packet_size']:.2f} bytes\n"
        report += f"- Unique source IPs: {stats.get('unique_src_ips', 'N/A')}\n"
        report += f"- Unique destination IPs: {stats.get('unique_dst_ips', 'N/A')}\n"
        
        return report
    
    def generate_incident_report(self, event, df=None):
        """Generate a focused report for a specific incident"""
        if df is not None and 'timestamp' in df.columns:
            # Get data around the event time
            if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            event_time = event['timestamp']
            window_start = event_time - pd.Timedelta(minutes=5)
            window_end = event_time + pd.Timedelta(minutes=5)
            
            window_df = df[(df['timestamp'] >= window_start) & (df['timestamp'] <= window_end)]
            stats = self.extract_key_statistics(window_df)
        else:
            stats = {}
        
        # Build a detailed incident description
        protocol_name = self.protocol_map.get(event['dominant_protocol'], event['dominant_protocol'])
        
        incident = f"Network Incident Report\n"
        incident += f"Time: {event['timestamp']}\n\n"
        
        incident += f"Incident Summary:\n"
        incident += f"Detected unusual network traffic activity with {event['packet_count']} packets "
        incident += f"({event['deviation_ratio']:.2f}x normal rate).\n"
        incident += f"Protocol: {protocol_name}\n"
        incident += f"Primary Source IP: {event['dominant_src_ip']}\n"
        incident += f"Average Packet Size: {event['avg_packet_size']:.2f} bytes\n\n"
        
        # Add interpretation
        incident += "Incident Interpretation:\n"
        
        # Pattern-match types of incidents
        if event['deviation_ratio'] > 10 and event['dominant_protocol'] == 'TCP':
            incident += "POSSIBLE TCP FLOOD ATTACK: Extremely high volume of TCP traffic\n"
            incident += "detected from a single source IP. This pattern is consistent with\n"
            incident += "denial-of-service attack techniques.\n\n"
        elif event['deviation_ratio'] > 5 and event['dominant_protocol'] == 'UDP':
            incident += "POSSIBLE UDP FLOOD: Unusually high volume of UDP traffic detected.\n"
            incident += "This could indicate a UDP flood attack or abnormal application behavior.\n\n"
        elif event['deviation_ratio'] > 3 and event['dominant_protocol'] == 'ICMP':
            incident += "POSSIBLE PING FLOOD: Higher than normal ICMP traffic detected.\n"
            incident += "This could be someone conducting network reconnaissance or a ping flood attack.\n\n"
        elif event['avg_packet_size'] < 100 and event['packet_count'] > 100:
            incident += "POSSIBLE PORT SCAN: Large number of small packets detected.\n"
            incident += "This pattern is consistent with port scanning activity.\n\n"
        else:
            incident += "UNUSUAL TRAFFIC PATTERN: The detected traffic pattern is abnormal\n"
            incident += "compared to baseline. Further investigation is recommended.\n\n"
        
        # Add recommended actions
        incident += "Recommended Actions:\n"
        incident += "1. Investigate traffic from source IP " + event['dominant_src_ip'] + "\n"
        incident += "2. Check logs for connection attempts and their success/failure\n"
        incident += "3. Review firewall rules for this traffic type\n"
        incident += "4. Consider temporarily blocking the source IP if malicious\n\n"
        
        # Add context from statistics if available
        if stats:
            incident += "Context Information:\n"
            incident += f"- Time window: {stats['start_time']} to {stats['end_time']}\n"
            incident += f"- Total packets in window: {stats['total_packets']}\n"
            if 'unique_src_ips' in stats:
                incident += f"- Unique source IPs in window: {stats['unique_src_ips']}\n"
                incident += f"- Unique destination IPs in window: {stats['unique_dst_ips']}\n"
        
        return incident
    
    def generate_report(self, df, anomalies=None, report_type='template'):
        """Generate a comprehensive report on network traffic"""
        # Extract statistics
        stats = self.extract_key_statistics(df)
        
        # Detect events
        events = self.detect_events(df)
        
        # Generate report based on specified type
        if report_type == 'template':
            report = self.generate_template_report(stats, events, anomalies)
        elif report_type == 'nlp':
            report = self.generate_nlp_report(stats, events, anomalies)
        else:
            raise ValueError(f"Unsupported report type: {report_type}")
        
        # Save report to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.output_dir}/network_report_{timestamp}.txt"
        with open(filename, 'w') as f:
            f.write(report)
        print(f"Report saved to {filename}")
        
        # Generate individual incident reports for significant events
        incident_reports = []
        for event in events:
            incident = self.generate_incident_report(event, df)
            incident_reports.append(incident)
            
            # Save individual incident reports
            event_time = event['timestamp'].strftime("%Y%m%d_%H%M%S")
            incident_filename = f"{self.output_dir}/incident_{event_time}.txt"
            with open(incident_filename, 'w') as f:
                f.write(incident)
        
        return {
            'main_report': report,
            'incident_reports': incident_reports,
            'stats': stats,
            'events': events
        }