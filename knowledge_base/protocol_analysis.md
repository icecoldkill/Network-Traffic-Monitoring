# Protocol Analysis Guide

## TCP (Transmission Control Protocol)
TCP is a connection-oriented protocol that provides reliable, ordered delivery of data between applications. It operates at the Transport Layer (Layer 4) of the OSI model.

### TCP Header Fields
- **Source Port (16 bits)**: Port number of the sending application (1024-65535 for ephemeral ports).
- **Destination Port (16 bits)**: Port number of the receiving application (well-known ports: 0-1023).
- **Sequence Number (32 bits)**: Used for ordered data delivery and reassembly.
- **Acknowledgment Number (32 bits)**: Confirms receipt of data segments.
- **Flags**: SYN, ACK, FIN, RST, PSH, URG — control connection state and data flow.
- **Window Size**: Controls flow rate and congestion management.

### TCP Three-Way Handshake
1. Client sends SYN (synchronize) to server
2. Server responds with SYN-ACK (synchronize-acknowledge)
3. Client sends ACK (acknowledge)

### TCP Attack Indicators
- **SYN Flood**: High volume of SYN packets without corresponding ACK completions.
- **RST Attacks**: Unexpected RST packets disrupting established connections.
- **FIN Scan**: FIN packets sent to closed ports trigger RST responses.

## UDP (User Datagram Protocol)
UDP is a connectionless protocol providing fast, unreliable data delivery. Used for DNS (port 53), DHCP, streaming, gaming.

### UDP Attack Indicators
- **UDP Flood**: Large volumes of UDP packets to random ports.
- **DNS Amplification**: Small DNS queries generating large responses directed at victim.
- **NTP Amplification**: Exploiting NTP monlist command for traffic amplification.

## ICMP (Internet Control Message Protocol)
ICMP is used for network diagnostics and error reporting. Common types:
- **Echo Request/Reply (Type 8/0)**: Used by ping utility.
- **Destination Unreachable (Type 3)**: Indicates unreachable host or port.
- **Time Exceeded (Type 11)**: TTL expired, used by traceroute.

### ICMP Attack Indicators
- **Ping Flood**: Overwhelming target with ICMP echo requests.
- **Ping of Death**: Sending oversized ICMP packets to crash systems.
- **ICMP Tunneling**: Hiding data within ICMP packets for covert communication.

## Common Port Numbers
| Port | Service | Protocol | Security Notes |
|------|---------|----------|----------------|
| 22 | SSH | TCP | Brute force target, use key-based auth |
| 23 | Telnet | TCP | Unencrypted, avoid in production |
| 53 | DNS | TCP/UDP | Amplification attack vector |
| 80 | HTTP | TCP | Web traffic, monitor for web attacks |
| 443 | HTTPS | TCP | Encrypted web traffic |
| 3389 | RDP | TCP | Remote desktop, common attack target |
| 8080 | HTTP-Alt | TCP | Alternative web server port |

## Traffic Analysis Techniques
- **Flow Analysis**: Examine network flows (source, destination, port, protocol, duration, bytes).
- **Payload Inspection**: Deep packet inspection for malicious content.
- **Behavioral Analysis**: Baseline normal patterns, detect deviations.
- **Statistical Analysis**: Use packet size distributions, inter-arrival times, and flow durations to identify anomalies.
