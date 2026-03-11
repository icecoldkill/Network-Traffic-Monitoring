# mcp_server.py
"""
Model Context Protocol (MCP) Server — Network Security Tools
AI407L Lab Mid Exam - Spring 2026 | Part B Task 1
Student: Ahsan Saleem (2022074)

Standalone MCP server that exposes structured network security tools
to any MCP-compatible client. This is SEPARATE from the Part A agent system.

Architecture:
  Model (LLM) ←→ Context (MCP Protocol) ←→ Tools (this server) ←→ Execution Layer

Tools exposed:
  1. scan_network    — Simulate network scanning of an IP range
  2. check_vulnerability — Lookup CVE vulnerability details
  3. get_threat_intel   — Query threat intelligence for an IP/domain
"""

import json
import random
import hashlib
from datetime import datetime, timedelta
from mcp.server.fastmcp import FastMCP

# ═══════════════════════════════════════════════════════════════════════════
# 1. CREATE THE MCP SERVER
# ═══════════════════════════════════════════════════════════════════════════

mcp = FastMCP("NetworkSecurityMCP")


# ═══════════════════════════════════════════════════════════════════════════
# 2. TOOL DEFINITIONS WITH STRUCTURED I/O SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
def scan_network(ip_range: str, scan_type: str = "quick") -> str:
    """
    Scan a network IP range for open ports and active hosts.

    Args:
        ip_range: IP range to scan (e.g., "192.168.1.0/24")
        scan_type: Type of scan — "quick", "full", or "stealth"

    Returns:
        JSON string with scan results including discovered hosts and open ports.
    """
    # Deterministic simulation based on input
    seed = int(hashlib.md5(ip_range.encode()).hexdigest()[:8], 16)
    random.seed(seed)

    num_hosts = random.randint(3, 12)
    base_ip = ip_range.split("/")[0].rsplit(".", 1)[0]

    hosts = []
    for i in range(num_hosts):
        host_ip = f"{base_ip}.{random.randint(1, 254)}"
        common_ports = [22, 80, 443, 3306, 5432, 8080, 8443, 3389, 21, 25, 53, 110]
        open_ports = sorted(random.sample(common_ports, random.randint(1, 5)))

        port_details = []
        port_services = {
            22: "ssh", 80: "http", 443: "https", 3306: "mysql",
            5432: "postgresql", 8080: "http-proxy", 8443: "https-alt",
            3389: "rdp", 21: "ftp", 25: "smtp", 53: "dns", 110: "pop3",
        }
        for p in open_ports:
            port_details.append({
                "port": p,
                "state": "open",
                "service": port_services.get(p, "unknown"),
                "version": f"v{random.randint(1,9)}.{random.randint(0,9)}",
            })

        hosts.append({
            "ip": host_ip,
            "status": "up",
            "os_guess": random.choice([
                "Linux 5.x", "Windows Server 2022", "Ubuntu 22.04",
                "CentOS 8", "FreeBSD 13", "macOS 14"
            ]),
            "open_ports": port_details,
        })

    result = {
        "scan_type": scan_type,
        "target_range": ip_range,
        "hosts_discovered": num_hosts,
        "scan_duration_seconds": round(random.uniform(2.5, 45.0), 2),
        "timestamp": datetime.now().isoformat(),
        "hosts": hosts,
    }
    return json.dumps(result, indent=2)


@mcp.tool()
def check_vulnerability(cve_id: str) -> str:
    """
    Look up vulnerability details by CVE ID.

    Args:
        cve_id: CVE identifier (e.g., "CVE-2024-1234")

    Returns:
        JSON string with vulnerability details including severity, description,
        affected systems, and remediation steps.
    """
    # Simulated vulnerability database
    vuln_db = {
        "CVE-2024-1234": {
            "cve_id": "CVE-2024-1234",
            "title": "Remote Code Execution in OpenSSL",
            "severity": "CRITICAL",
            "cvss_score": 9.8,
            "description": "A buffer overflow vulnerability in OpenSSL allows remote attackers to execute arbitrary code via crafted TLS handshake messages.",
            "affected_software": ["OpenSSL 3.0.x < 3.0.12", "OpenSSL 1.1.1x < 1.1.1w"],
            "remediation": "Upgrade OpenSSL to version 3.0.12 or 1.1.1w. Apply vendor patches immediately.",
            "references": ["https://nvd.nist.gov/vuln/detail/CVE-2024-1234"],
            "published_date": "2024-03-15",
        },
        "CVE-2024-5678": {
            "cve_id": "CVE-2024-5678",
            "title": "SQL Injection in Apache HTTP Server mod_rewrite",
            "severity": "HIGH",
            "cvss_score": 8.1,
            "description": "Improper input validation in mod_rewrite allows attackers to inject SQL commands via crafted URLs.",
            "affected_software": ["Apache HTTP Server 2.4.x < 2.4.59"],
            "remediation": "Update to Apache HTTP Server 2.4.59 or later.",
            "references": ["https://nvd.nist.gov/vuln/detail/CVE-2024-5678"],
            "published_date": "2024-06-20",
        },
        "CVE-2014-0160": {
            "cve_id": "CVE-2014-0160",
            "title": "Heartbleed — OpenSSL TLS Heartbeat Extension",
            "severity": "CRITICAL",
            "cvss_score": 9.4,
            "description": "The Heartbleed bug allows attackers to read memory of systems protected by vulnerable OpenSSL versions, potentially exposing private keys and user data.",
            "affected_software": ["OpenSSL 1.0.1 through 1.0.1f"],
            "remediation": "Upgrade to OpenSSL 1.0.1g or later. Revoke and reissue all TLS certificates.",
            "references": ["https://heartbleed.com", "https://nvd.nist.gov/vuln/detail/CVE-2014-0160"],
            "published_date": "2014-04-07",
        },
    }

    if cve_id.upper() in vuln_db:
        return json.dumps(vuln_db[cve_id.upper()], indent=2)

    # Generate a plausible result for unknown CVEs
    seed = int(hashlib.md5(cve_id.encode()).hexdigest()[:8], 16)
    random.seed(seed)
    severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
    result = {
        "cve_id": cve_id.upper(),
        "title": f"Vulnerability {cve_id.upper()}",
        "severity": severity,
        "cvss_score": round(random.uniform(3.0, 10.0), 1),
        "description": f"Details for {cve_id.upper()} found in vulnerability database.",
        "affected_software": ["Various versions"],
        "remediation": "Apply latest vendor patches and review security advisories.",
        "published_date": "2024-01-01",
    }
    return json.dumps(result, indent=2)


@mcp.tool()
def get_threat_intel(indicator: str, indicator_type: str = "ip") -> str:
    """
    Query threat intelligence for a given indicator (IP address or domain).

    Args:
        indicator: The IP address or domain name to look up
        indicator_type: Type of indicator — "ip" or "domain"

    Returns:
        JSON string with threat intelligence including risk score,
        associated threats, geographic information, and recommendations.
    """
    seed = int(hashlib.md5(indicator.encode()).hexdigest()[:8], 16)
    random.seed(seed)

    risk_score = random.randint(0, 100)

    if risk_score > 70:
        threat_level = "HIGH"
        threats = random.sample([
            "Known botnet C2 server", "Malware distribution",
            "Phishing infrastructure", "Brute force attacker",
            "Port scanning activity", "Data exfiltration endpoint",
        ], min(3, random.randint(1, 4)))
    elif risk_score > 40:
        threat_level = "MEDIUM"
        threats = random.sample([
            "Suspicious activity detected", "Associated with spam networks",
            "Proxy/VPN endpoint", "Tor exit node",
        ], min(2, random.randint(1, 3)))
    else:
        threat_level = "LOW"
        threats = ["No significant threats detected"]

    countries = ["US", "CN", "RU", "DE", "BR", "IN", "KR", "NL", "GB", "FR"]
    isps = ["CloudFlare", "AWS", "DigitalOcean", "OVH", "Hetzner", "Linode", "Google Cloud"]

    result = {
        "indicator": indicator,
        "indicator_type": indicator_type,
        "risk_score": risk_score,
        "threat_level": threat_level,
        "associated_threats": threats,
        "first_seen": (datetime.now() - timedelta(days=random.randint(1, 365))).strftime("%Y-%m-%d"),
        "last_seen": datetime.now().strftime("%Y-%m-%d"),
        "geo_info": {
            "country": random.choice(countries),
            "isp": random.choice(isps),
        },
        "recommendations": [
            "Block at perimeter firewall" if risk_score > 70 else "Monitor traffic",
            "Add to watchlist" if risk_score > 40 else "No action required",
            "Report to threat feed" if risk_score > 80 else "",
        ],
        "query_timestamp": datetime.now().isoformat(),
    }
    return json.dumps(result, indent=2)


# ═══════════════════════════════════════════════════════════════════════════
# 3. RUN THE SERVER
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("  MCP Server — Network Security Tools")
    print("  AI407L Mid-Exam | Ahsan Saleem (2022074)")
    print("=" * 60)
    print("\nStarting MCP server via stdio transport…")
    print("Tools exposed: scan_network, check_vulnerability, get_threat_intel\n")
    mcp.run(transport="stdio")
