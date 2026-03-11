# Network Attack Taxonomy

## Overview
Network attacks are malicious activities that target computer networks to disrupt, damage, or gain unauthorized access to systems and data. Understanding attack types is critical for building effective Intrusion Detection Systems (IDS) and Intrusion Prevention Systems (IPS).

## Denial of Service (DoS) and Distributed Denial of Service (DDoS)
DoS attacks aim to make a network service unavailable by overwhelming it with traffic. DDoS attacks use multiple compromised systems (botnets) to amplify the attack. Common types include:
- **SYN Flood**: Exploits TCP handshake by sending many SYN requests without completing the handshake, exhausting server resources.
- **UDP Flood**: Sends large numbers of UDP packets to random ports, causing the host to check for applications and send ICMP "Destination Unreachable" packets.
- **HTTP Flood**: Sends seemingly legitimate HTTP GET or POST requests to overwhelm a web server.
- **Slowloris**: Opens many connections to the target server and keeps them open as long as possible by sending partial HTTP requests.
- **Amplification Attacks**: Uses DNS, NTP, or SSDP amplification to multiply traffic volume.

## Port Scanning
Port scanning is a reconnaissance technique used to identify open ports and services on a target system. Types include:
- **TCP SYN Scan**: Sends SYN packets and analyzes responses. Open ports respond with SYN-ACK.
- **TCP Connect Scan**: Completes the full TCP handshake to determine port status.
- **UDP Scan**: Sends UDP packets to identify open UDP ports.
- **FIN Scan**: Sends FIN packets; closed ports respond with RST, open ports do not respond.
- **XMAS Scan**: Sends packets with FIN, URG, and PUSH flags set.

## Brute Force Attacks
Brute force attacks attempt to gain access by systematically trying all possible combinations of credentials. Variants include:
- **SSH Brute Force**: Attempting multiple username/password combinations against SSH services (port 22).
- **FTP Brute Force**: Targeting FTP services (port 21) with credential guessing.
- **Web Login Brute Force**: Automating login attempts against web applications.
- **Dictionary Attacks**: Using common password lists rather than exhaustive enumeration.

## Infiltration Attacks
Infiltration attacks involve gaining unauthorized access to a network and moving laterally:
- **Phishing**: Social engineering to trick users into revealing credentials.
- **Man-in-the-Middle (MITM)**: Intercepting communication between two parties.
- **DNS Spoofing**: Corrupting DNS cache to redirect traffic to malicious servers.
- **ARP Spoofing**: Linking attacker's MAC address with a legitimate IP address.

## Botnet Activity
Botnets are networks of compromised computers controlled by an attacker:
- **Command and Control (C2)**: Communication between botnet and controller.
- **Spam Bots**: Used for sending massive volumes of spam email.
- **Click Fraud**: Automated clicking on advertisements for financial gain.

## Web Application Attacks
- **SQL Injection**: Inserting malicious SQL code through application inputs.
- **Cross-Site Scripting (XSS)**: Injecting client-side scripts into web pages.
- **Cross-Site Request Forgery (CSRF)**: Forcing authenticated users to perform unintended actions.

## Detection Indicators
Key network traffic indicators for detecting attacks:
- **Unusual packet sizes**: Very large or very small packets outside normal distribution.
- **Traffic volume spikes**: Sudden increases in packets per second or bandwidth usage.
- **Protocol anomalies**: Unexpected protocol usage or malformed packets.
- **Port concentration**: Many connections to the same port from different sources (DDoS) or from one source to many ports (scanning).
- **Geographic anomalies**: Traffic from unusual geographic locations.
- **Temporal patterns**: Activity at unusual hours or patterns inconsistent with normal business operations.
