interface NetworkStatus {
  status: 'online' | 'offline' | 'degraded';
  activeConnections: number;
  blockedIPs: string[];
  threats: Threat[];
}

interface Threat {
  id: string;
  type: 'port_scan' | 'brute_force' | 'ddos' | 'suspicious_activity' | 'malware';
  severity: 'low' | 'medium' | 'high' | 'critical';
  sourceIP: string;
  timestamp: string;
  description: string;
  status: 'active' | 'mitigated' | 'investigating';
}

class NetworkService {
  private blockedIPs: Set<string> = new Set();
  private threats: Threat[] = [];
  private static instance: NetworkService;

  private constructor() {
    // Initialize with some default blocked IPs
    this.blockedIPs = new Set([
      '192.168.1.100',
      '10.0.0.15',
      '172.16.0.5'
    ]);
    
    // Simulate some initial threats
    this.simulateThreats();
  }

  public static getInstance(): NetworkService {
    if (!NetworkService.instance) {
      NetworkService.instance = new NetworkService();
    }
    return NetworkService.instance;
  }

  public async getNetworkStatus(): Promise<NetworkStatus> {
    // Simulate network status check
    return {
      status: 'online',
      activeConnections: Math.floor(Math.random() * 100) + 1,
      blockedIPs: Array.from(this.blockedIPs),
      threats: this.threats.filter(t => t.status === 'active')
    };
  }

  public async blockIP(ip: string): Promise<{ success: boolean; message: string }> {
    if (!this.isValidIP(ip)) {
      return { success: false, message: 'Invalid IP address format' };
    }
    
    this.blockedIPs.add(ip);
    return { success: true, message: `Successfully blocked IP: ${ip}` };
  }

  public async unblockIP(ip: string): Promise<{ success: boolean; message: string }> {
    if (!this.blockedIPs.has(ip)) {
      return { success: false, message: 'IP is not currently blocked' };
    }
    
    this.blockedIPs.delete(ip);
    return { success: true, message: `Successfully unblocked IP: ${ip}` };
  }

  public async getBlockedIPs(): Promise<string[]> {
    return Array.from(this.blockedIPs);
  }

  public async getActiveThreats(): Promise<Threat[]> {
    return this.threats.filter(t => t.status === 'active');
  }

  public async mitigateThreat(threatId: string): Promise<{ success: boolean; message: string }> {
    const threat = this.threats.find(t => t.id === threatId);
    if (!threat) {
      return { success: false, message: 'Threat not found' };
    }
    
    threat.status = 'mitigated';
    this.blockedIPs.add(threat.sourceIP);
    
    return { 
      success: true, 
      message: `Successfully mitigated threat from ${threat.sourceIP}`
    };
  }

  private isValidIP(ip: string): boolean {
    // Simple IP validation regex
    const ipRegex = /^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
    return ipRegex.test(ip);
  }

  private simulateThreats(): void {
    // Simulate some threats
    const threatTypes: Threat['type'][] = [
      'port_scan',
      'brute_force',
      'ddos',
      'suspicious_activity',
      'malware'
    ];

    const severities: Threat['severity'][] = ['low', 'medium', 'high', 'critical'];
    
    // Generate 3-5 random threats
    const numThreats = Math.floor(Math.random() * 3) + 3;
    
    for (let i = 0; i < numThreats; i++) {
      const randomIP = `${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}`;
      
      this.threats.push({
        id: `threat-${Date.now()}-${i}`,
        type: threatTypes[Math.floor(Math.random() * threatTypes.length)],
        severity: severities[Math.floor(Math.random() * severities.length)],
        sourceIP: randomIP,
        timestamp: new Date().toISOString(),
        description: `Detected ${threatTypes[Math.floor(Math.random() * threatTypes.length)]} activity from ${randomIP}`,
        status: 'active'
      });
    }
  }
}

export const networkService = NetworkService.getInstance();
export type { NetworkStatus, Threat };
