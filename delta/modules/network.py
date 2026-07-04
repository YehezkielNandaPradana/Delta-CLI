# delta/modules/network.py
"""
Network Module - Ping sweep, traceroute, and network discovery.
"""

import socket
import struct
import time
import os
import platform
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed


@dataclass
class PingResult:
    """Ping result for a single host."""
    host: str
    ip: str
    alive: bool = False
    rtt_ms: float = 0.0
    error: str = ""


@dataclass
class TracerouteHop:
    """A single traceroute hop."""
    hop: int
    ip: str = ""
    hostname: str = ""
    rtt_ms: float = 0.0
    reached: bool = False


class NetworkModule:
    """
    Network discovery and analysis module.
    Provides ping, traceroute, and network scanning capabilities.
    """

    def ping(self, host: str, count: int = 3, timeout: float = 2.0) -> PingResult:
        """Ping a host using system ping command with fallback."""
        result = PingResult(host=host, ip="")
        
        try:
            result.ip = socket.gethostbyname(host)
        except socket.gaierror:
            result.error = "Cannot resolve hostname"
            return result

        # Use system ping command
        try:
            param = "-n" if platform.system().lower() == "windows" else "-c"
            cmd = ["ping", param, str(count), "-W", str(int(timeout)), host]
            
            import subprocess
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 2)
            
            if p.returncode == 0:
                result.alive = True
                # Extract RTT from output
                for line in p.stdout.split("\n"):
                    if "time=" in line.lower() or "time<" in line.lower():
                        try:
                            # Parse different ping output formats
                            if "time=" in line.lower():
                                time_part = line.lower().split("time=")[1].split()[0]
                                result.rtt_ms = float(time_part.replace("ms", ""))
                            elif "time<" in line.lower():
                                result.rtt_ms = 0.1
                        except (ValueError, IndexError):
                            pass
                        break
            else:
                result.alive = False
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            result.error = str(e)
        
        return result

    def ping_sweep(self, network: str, timeout: float = 1.0) -> List[PingResult]:
        """Ping sweep a subnet to find alive hosts."""
        results = []
        
        # Parse network range
        hosts = self._parse_network_range(network)
        
        def ping_host(host: str) -> PingResult:
            return self.ping(host, count=1, timeout=timeout)
        
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = {executor.submit(ping_host, h): h for h in hosts}
            for future in as_completed(futures):
                result = future.result()
                if result.alive:
                    results.append(result)
        
        return sorted(results, key=lambda r: r.ip)

    def _parse_network_range(self, network: str) -> List[str]:
        """Parse network range notation (CIDR or range)."""
        hosts = []
        
        if "/" in network:
            # CIDR notation
            import ipaddress
            try:
                network_obj = ipaddress.ip_network(network, strict=False)
                hosts = [str(ip) for ip in network_obj.hosts()]
            except ValueError:
                pass
        elif "-" in network:
            # Range notation 192.168.1.1-254
            parts = network.split("-")
            base = parts[0].rsplit(".", 1)[0]
            start = int(parts[0].rsplit(".", 1)[1])
            end = int(parts[1]) if len(parts) > 1 else start
            hosts = [f"{base}.{i}" for i in range(start, end + 1)]
        else:
            hosts = [network]
        
        return hosts[:255]  # Limit to /24

    def traceroute(self, host: str, max_hops: int = 30, timeout: float = 3.0) -> List[TracerouteHop]:
        """Perform traceroute to a host using UDP method."""
        hops = []
        
        try:
            dest_ip = socket.gethostbyname(host)
        except socket.gaierror:
            return hops

        for ttl in range(1, max_hops + 1):
            hop = TracerouteHop(hop=ttl)
            
            try:
                # Create UDP socket for sending
                tx_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                tx_sock.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, ttl)
                tx_sock.settimeout(timeout)
                
                # Create ICMP socket for receiving
                rx_sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
                rx_sock.settimeout(timeout)
                rx_sock.bind(("", 33434 + ttl))
                
                start = time.time()
                tx_sock.sendto(b"", (dest_ip, 33434 + ttl))
                
                try:
                    data, addr = rx_sock.recvfrom(512)
                    hop.rtt_ms = (time.time() - start) * 1000
                    hop.ip = addr[0]
                    hop.reached = True
                    
                    try:
                        hop.hostname = socket.gethostbyaddr(hop.ip)[0]
                    except socket.herror:
                        pass
                    
                except socket.timeout:
                    pass
                
                tx_sock.close()
                rx_sock.close()
                
                hops.append(hop)
                
                if hop.ip == dest_ip:
                    break
                    
            except Exception:
                hops.append(hop)
                break
        
        return hops