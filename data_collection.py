# data_collection.py
import os
import time
import pandas as pd
import numpy as np
from scapy.all import sniff, IP, TCP, UDP, ICMP
from datetime import datetime
import pyshark

class NetworkTrafficCollector:
    def __init__(self, output_dir="./data"):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
    def collect_with_scapy(self, interface="eth0", count=1000, timeout=60):
        """Collect network packets using Scapy"""
        print(f"Capturing {count} packets on {interface}...")
        
        packet_data = []
        
        def packet_callback(packet):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            
            if IP in packet:
                src_ip = packet[IP].src
                dst_ip = packet[IP].dst
                protocol = None
                src_port = None
                dst_port = None
                packet_size = len(packet)
                flags = None
                
                if TCP in packet:
                    protocol = "TCP"
                    src_port = packet[TCP].sport
                    dst_port = packet[TCP].dport
                    flags = packet[TCP].flags
                elif UDP in packet:
                    protocol = "UDP"
                    src_port = packet[UDP].sport
                    dst_port = packet[UDP].dport
                elif ICMP in packet:
                    protocol = "ICMP"
                
                packet_data.append({
                    'timestamp': timestamp,
                    'src_ip': src_ip,
                    'dst_ip': dst_ip,
                    'protocol': protocol,
                    'src_port': src_port,
                    'dst_port': dst_port,
                    'packet_size': packet_size,
                    'flags': flags
                })
        
        sniff(iface=interface, prn=packet_callback, count=count, timeout=timeout)
        
        df = pd.DataFrame(packet_data)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.output_dir}/traffic_data_{timestamp}.csv"
        df.to_csv(filename, index=False)
        print(f"Data saved to {filename}")
        return df

    def collect_with_pyshark(self, interface="eth0", capture_time=60, display_filter=None):
        """Collect network packets using PyShark (Wireshark wrapper)"""
        capture = pyshark.LiveCapture(interface=interface, display_filter=display_filter)
        
        packet_data = []
        start_time = time.time()
        
        print(f"Capturing packets on {interface} for {capture_time} seconds...")
        
        # Start capture with timeout
        capture.sniff(timeout=capture_time)
        
        for packet in capture:
            try:
                # Extract basic IP info if available
                if hasattr(packet, 'ip'):
                    src_ip = packet.ip.src
                    dst_ip = packet.ip.dst
                    protocol = packet.transport_layer if hasattr(packet, 'transport_layer') else 'Unknown'
                    
                    # Extract ports if available
                    src_port = None
                    dst_port = None
                    if hasattr(packet, 'tcp'):
                        src_port = packet.tcp.srcport
                        dst_port = packet.tcp.dstport
                    elif hasattr(packet, 'udp'):
                        src_port = packet.udp.srcport
                        dst_port = packet.udp.dstport
                    
                    # Get timestamp and length
                    timestamp = packet.sniff_time.strftime("%Y-%m-%d %H:%M:%S.%f")
                    packet_size = packet.length
                    
                    packet_data.append({
                        'timestamp': timestamp,
                        'src_ip': src_ip,
                        'dst_ip': dst_ip,
                        'protocol': protocol,
                        'src_port': src_port,
                        'dst_port': dst_port,
                        'packet_size': packet_size
                    })
            except AttributeError:
                # Skip packets that don't have the required attributes
                continue
        
        df = pd.DataFrame(packet_data)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.output_dir}/traffic_data_{timestamp}.csv"
        df.to_csv(filename, index=False)
        print(f"Data saved to {filename}")
        return df
    
    def load_from_pcap(self, pcap_file):
        """Load packets from a PCAP file"""
        print(f"Loading packets from {pcap_file}...")
        
        cap = pyshark.FileCapture(pcap_file)
        packet_data = []
        
        for packet in cap:
            try:
                if hasattr(packet, 'ip'):
                    src_ip = packet.ip.src
                    dst_ip = packet.ip.dst
                    protocol = packet.transport_layer if hasattr(packet, 'transport_layer') else 'Unknown'
                    
                    src_port = None
                    dst_port = None
                    if hasattr(packet, 'tcp'):
                        src_port = packet.tcp.srcport
                        dst_port = packet.tcp.dstport
                    elif hasattr(packet, 'udp'):
                        src_port = packet.udp.srcport
                        dst_port = packet.udp.dstport
                    
                    timestamp = packet.sniff_time.strftime("%Y-%m-%d %H:%M:%S.%f")
                    packet_size = packet.length
                    
                    packet_data.append({
                        'timestamp': timestamp,
                        'src_ip': src_ip,
                        'dst_ip': dst_ip,
                        'protocol': protocol,
                        'src_port': src_port,
                        'dst_port': dst_port,
                        'packet_size': int(packet_size)
                    })
            except AttributeError:
                continue
        
        df = pd.DataFrame(packet_data)
        cap.close()
        return df
    
    def generate_synthetic_data(self, n_samples=10000, anomaly_ratio=0.05):
        """Generate synthetic network traffic data for testing"""
        np.random.seed(42)  # For reproducibility
        
        # Generate timestamps in sequence
        start_time = pd.Timestamp('2023-01-01 00:00:00')
        timestamps = [start_time + pd.Timedelta(seconds=i) for i in range(n_samples)]
        
        # Generate normal traffic pattern
        packet_sizes = np.random.normal(500, 150, n_samples).astype(int)
        # Ensure no negative packet sizes
        packet_sizes = np.clip(packet_sizes, 64, 1500)
        
        # Generate IPs
        src_ips = [f"192.168.1.{np.random.randint(1, 254)}" for _ in range(n_samples)]
        dst_ips = [f"10.0.0.{np.random.randint(1, 254)}" for _ in range(n_samples)]
        
        # Generate protocols
        protocols = np.random.choice(['TCP', 'UDP', 'ICMP'], n_samples, p=[0.7, 0.25, 0.05])
        
        # Generate ports
        src_ports = np.random.randint(1024, 65535, n_samples)
        dst_ports = np.random.choice([80, 443, 22, 53, 8080], n_samples, p=[0.4, 0.3, 0.1, 0.1, 0.1])
        
        # Create dataframe
        df = pd.DataFrame({
            'timestamp': [t.strftime("%Y-%m-%d %H:%M:%S.%f") for t in timestamps],
            'src_ip': src_ips,
            'dst_ip': dst_ips,
            'protocol': protocols,
            'src_port': src_ports,
            'dst_port': dst_ports,
            'packet_size': packet_sizes,
        })
        
        # Add anomalies
        n_anomalies = int(n_samples * anomaly_ratio)
        anomaly_indices = np.random.choice(n_samples, n_anomalies, replace=False)
        
        # Type 1: Large packet anomalies
        large_packet_indices = anomaly_indices[:n_anomalies//3]
        df.loc[large_packet_indices, 'packet_size'] = np.random.randint(1500, 9000, len(large_packet_indices))
        
        # Type 2: Protocol concentration anomalies (all TCP to same destination)
        proto_indices = anomaly_indices[n_anomalies//3:2*n_anomalies//3]
        df.loc[proto_indices, 'protocol'] = 'TCP'
        df.loc[proto_indices, 'dst_ip'] = '10.0.0.1'  # Target IP
        df.loc[proto_indices, 'dst_port'] = 80  # Target port
        
        # Type 3: Scanning behavior (many destinations from one source)
        scan_indices = anomaly_indices[2*n_anomalies//3:]
        df.loc[scan_indices, 'src_ip'] = '192.168.1.100'  # Attacker IP
        # Different destination IPs
        df.loc[scan_indices, 'dst_ip'] = [f"10.0.0.{i}" for i in range(len(scan_indices))]
        df.loc[scan_indices, 'dst_port'] = np.random.choice([22, 80, 443, 8080], len(scan_indices))
        
        # Add anomaly label (1 for anomaly, 0 for normal)
        df['anomaly'] = 0
        df.loc[anomaly_indices, 'anomaly'] = 1
        
        # Save synthetic data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.output_dir}/synthetic_traffic_{timestamp}.csv"
        df.to_csv(filename, index=False)
        print(f"Synthetic data saved to {filename}")
        
        return df