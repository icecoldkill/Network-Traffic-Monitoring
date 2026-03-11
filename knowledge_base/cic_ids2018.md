# CIC-IDS2018 Dataset Description

## Overview
The CSE-CIC-IDS2018 dataset is a comprehensive intrusion detection evaluation dataset created by the Canadian Institute for Cybersecurity (CIC) at the University of New Brunswick. It contains both benign and malicious network traffic captured in a realistic enterprise network environment.

## Dataset Architecture
The dataset was generated using a testbed consisting of:
- **Attack Infrastructure**: 50 machines used to generate attack traffic
- **Victim Infrastructure**: 5 departments with 420 machines and 30 servers
- **Network Topology**: Realistic enterprise network with switches, routers, firewalls

## Attack Scenarios
The dataset includes seven different attack scenarios executed over 10 days:
1. **Brute Force (SSH and FTP)**: Automated credential guessing attacks against SSH and FTP services
2. **DoS attacks (Hulk, GoldenEye, Slowloris, Slowhttptest)**: Various denial of service techniques
3. **DDoS (LOIC-HTTP, LOIC-UDP, HOIC)**: Distributed denial of service using multiple attack tools
4. **Web Attacks (SQL Injection, XSS, Brute Force)**: Attacks targeting web applications
5. **Infiltration**: Network infiltration using Metasploit and custom exploits
6. **Botnet (ARES)**: Botnet command and control communications
7. **Heartbleed**: Exploitation of the OpenSSL Heartbleed vulnerability (CVE-2014-0160)

## Key Features
The dataset provides 80+ network traffic features extracted using CICFlowMeter:
- **Flow Duration**: Total duration of the flow in microseconds
- **Total Forward/Backward Packets**: Count of packets in each direction
- **Packet Length Statistics**: Min, max, mean, standard deviation of packet lengths
- **Flow Bytes/s**: Rate of bytes per second in the flow
- **Flow Packets/s**: Rate of packets per second
- **Inter-Arrival Time (IAT)**: Time between consecutive packets
- **Flag Counts**: SYN, FIN, RST, PSH, ACK, URG, CWE, ECE flag counts
- **Header Length**: Average header length in forward and backward directions
- **Segment Size**: Average segment size
- **Subflow Statistics**: Forward and backward subflow metrics
- **Active/Idle Time**: Statistics about active and idle periods

## Labels
Each flow is labeled as either:
- **Benign**: Normal, legitimate network traffic
- **Attack Type**: Specific attack category (e.g., "FTP-BruteForce", "DoS-Hulk", "DDoS-LOIC-HTTP")

## Usage in Network Security
The CIC-IDS2018 dataset is widely used for:
- Training and evaluating machine learning-based intrusion detection systems
- Benchmarking anomaly detection algorithms
- Research in network security and threat classification
- Testing deep learning models (CNN, RNN, Autoencoders) for traffic classification

## Data Format
The dataset is available in CSV format with each row representing a network flow and columns representing extracted features. The 'Label' column indicates whether the flow is benign or the specific attack type.
