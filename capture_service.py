# Create a file called capture_service.py
import flask
from flask import Flask, jsonify, request
from flask_cors import CORS
import scapy.all as scapy
import pandas as pd
import json
import threading
import time

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests

@app.route('/api/capture', methods=['POST'])
def capture_traffic():
    data = request.json
    interface = data.get('interface', 'eth0')
    packet_count = int(data.get('packet_count', 100))
    
    try:
        # Start capture in a separate thread
        packets = scapy.sniff(iface=interface, count=packet_count)
        
        # Process packets into a DataFrame
        results = []
        for pkt in packets:
            packet_info = {
                'timestamp': time.time(),
                'src_ip': pkt.src if hasattr(pkt, 'src') else None,
                'dst_ip': pkt.dst if hasattr(pkt, 'dst') else None
            }
            
            # Extract protocol
            if scapy.TCP in pkt:
                packet_info['protocol'] = 6  # TCP
                packet_info['src_port'] = pkt[scapy.TCP].sport
                packet_info['dst_port'] = pkt[scapy.TCP].dport
            elif scapy.UDP in pkt:
                packet_info['protocol'] = 17  # UDP
                packet_info['src_port'] = pkt[scapy.UDP].sport
                packet_info['dst_port'] = pkt[scapy.UDP].dport
            elif scapy.ICMP in pkt:
                packet_info['protocol'] = 1  # ICMP
                packet_info['src_port'] = 0
                packet_info['dst_port'] = 0
            else:
                packet_info['protocol'] = 0
                packet_info['src_port'] = 0
                packet_info['dst_port'] = 0
            
            packet_info['packet_size'] = len(pkt)
            results.append(packet_info)
        
        return jsonify({
            'status': 'success',
            'data': results,
            'count': len(results)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)