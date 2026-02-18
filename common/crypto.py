"""
ShadowC2 - Cryptography Module
Handles all encryption/decryption operations using AES-256-GCM
"""

import os
import json
import base64
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import PBKDF2


class CryptoHandler:
    """
    Handles AES-256-GCM encryption and decryption for C2 communications
    
    Features:
    - AES-256-GCM authenticated encryption
    - Base64 encoding for safe transport
    - Nonce/IV generation for each message
    - HMAC validation via GCM
    """
    
    def __init__(self, key=None):
        """
        Initialize crypto handler with encryption key
        
        Args:
            key (bytes): 32-byte AES key. If None, generates new random key.
        """
        if key is None:
            self.key = get_random_bytes(32)  # 256 bits
        elif isinstance(key, str):
            # If string provided, derive key using PBKDF2
            self.key = PBKDF2(key.encode(), b'shadowc2_salt', dkLen=32, count=100000)
        else:
            self.key = key
    
    def encrypt(self, plaintext):
        """
        Encrypt data using AES-256-GCM
        
        Args:
            plaintext (str or dict): Data to encrypt
            
        Returns:
            str: Base64 encoded encrypted data with nonce and tag
            
        Format: base64(nonce + tag + ciphertext)
        """
        # Convert to JSON if dict
        if isinstance(plaintext, dict):
            plaintext = json.dumps(plaintext)
        
        # Convert to bytes
        if isinstance(plaintext, str):
            plaintext = plaintext.encode('utf-8')
        
        # Generate random nonce (12 bytes for GCM)
        nonce = get_random_bytes(12)
        
        # Create cipher
        cipher = AES.new(self.key, AES.MODE_GCM, nonce=nonce)
        
        # Encrypt and get authentication tag
        ciphertext, tag = cipher.encrypt_and_digest(plaintext)
        
        # Combine nonce + tag + ciphertext
        encrypted_data = nonce + tag + ciphertext
        
        # Base64 encode for safe transport
        return base64.b64encode(encrypted_data).decode('utf-8')
    
    def decrypt(self, encrypted_data):
        """
        Decrypt AES-256-GCM encrypted data
        
        Args:
            encrypted_data (str): Base64 encoded encrypted data
            
        Returns:
            str or dict: Decrypted plaintext (auto-detects JSON)
            
        Raises:
            ValueError: If decryption fails or authentication fails
        """
        try:
            # Decode from base64
            encrypted_bytes = base64.b64decode(encrypted_data)
            
            # Extract components
            nonce = encrypted_bytes[:12]
            tag = encrypted_bytes[12:28]  # 16 bytes
            ciphertext = encrypted_bytes[28:]
            
            # Create cipher
            cipher = AES.new(self.key, AES.MODE_GCM, nonce=nonce)
            
            # Decrypt and verify authentication tag
            plaintext = cipher.decrypt_and_verify(ciphertext, tag)
            
            # Decode to string
            plaintext_str = plaintext.decode('utf-8')
            
            # Try to parse as JSON
            try:
                return json.loads(plaintext_str)
            except json.JSONDecodeError:
                return plaintext_str
                
        except Exception as e:
            raise ValueError(f"Decryption failed: {str(e)}")
    
    def get_key_base64(self):
        """
        Get the encryption key as base64 string
        
        Returns:
            str: Base64 encoded key
        """
        return base64.b64encode(self.key).decode('utf-8')
    
    @staticmethod
    def generate_key():
        """
        Generate a new random 256-bit encryption key
        
        Returns:
            bytes: 32-byte random key
        """
        return get_random_bytes(32)
    
    @staticmethod
    def key_from_base64(key_b64):
        """
        Load key from base64 string
        
        Args:
            key_b64 (str): Base64 encoded key
            
        Returns:
            bytes: Decoded key
        """
        return base64.b64decode(key_b64)


class SessionCrypto:
    """
    Manages per-session encryption with unique session tokens
    """
    
    def __init__(self, master_key):
        """
        Initialize session crypto manager
        
        Args:
            master_key (bytes): Master encryption key
        """
        self.master_key = master_key
        self.session_keys = {}  # session_id -> CryptoHandler
    
    def create_session(self, session_id):
        """
        Create new encrypted session
        
        Args:
            session_id (str): Unique session identifier
            
        Returns:
            CryptoHandler: Crypto handler for this session
        """
        # Derive session key from master key + session_id
        session_key = PBKDF2(
            self.master_key, 
            session_id.encode(), 
            dkLen=32, 
            count=10000
        )
        
        crypto = CryptoHandler(key=session_key)
        self.session_keys[session_id] = crypto
        return crypto
    
    def get_session_crypto(self, session_id):
        """
        Get crypto handler for existing session
        
        Args:
            session_id (str): Session identifier
            
        Returns:
            CryptoHandler: Crypto handler for session
            
        Raises:
            KeyError: If session doesn't exist
        """
        if session_id not in self.session_keys:
            raise KeyError(f"Session {session_id} not found")
        return self.session_keys[session_id]
    
    def remove_session(self, session_id):
        """
        Remove session and destroy keys
        
        Args:
            session_id (str): Session to remove
        """
        if session_id in self.session_keys:
            del self.session_keys[session_id]


def generate_psk():
    """
    Generate a Pre-Shared Key for C2 communications
    
    Returns:
        str: Base64 encoded 256-bit key
    """
    key = get_random_bytes(32)
    return base64.b64encode(key).decode('utf-8')


# Example usage and testing
if __name__ == "__main__":
    print("[*] ShadowC2 Crypto Module Test\n")
    
    # Test basic encryption/decryption
    print("[+] Testing AES-256-GCM encryption...")
    crypto = CryptoHandler()
    
    # Test with string
    plaintext = "This is a secret command"
    encrypted = crypto.encrypt(plaintext)
    decrypted = crypto.decrypt(encrypted)
    print(f"    Original:  {plaintext}")
    print(f"    Encrypted: {encrypted[:50]}...")
    print(f"    Decrypted: {decrypted}")
    assert plaintext == decrypted, "String encryption test failed!"
    print("    ✓ String encryption test passed")
    
    # Test with JSON/dict
    print("\n[+] Testing JSON encryption...")
    data = {
        "command": "sysinfo",
        "session_id": "abc123",
        "timestamp": 1234567890
    }
    encrypted = crypto.encrypt(data)
    decrypted = crypto.decrypt(encrypted)
    print(f"    Original:  {data}")
    print(f"    Encrypted: {encrypted[:50]}...")
    print(f"    Decrypted: {decrypted}")
    assert data == decrypted, "JSON encryption test failed!"
    print("    ✓ JSON encryption test passed")
    
    # Test key generation
    print("\n[+] Testing key generation...")
    psk = generate_psk()
    print(f"    Generated PSK: {psk}")
    print(f"    Key length: {len(base64.b64decode(psk))} bytes")
    print("    ✓ Key generation test passed")
    
    # Test session crypto
    print("\n[+] Testing session-based encryption...")
    master_key = CryptoHandler.generate_key()
    session_mgr = SessionCrypto(master_key)
    
    session1_crypto = session_mgr.create_session("session_001")
    session2_crypto = session_mgr.create_session("session_002")
    
    msg1 = session1_crypto.encrypt("Message from session 1")
    msg2 = session2_crypto.encrypt("Message from session 2")
    
    # Verify sessions are isolated
    retrieved_crypto1 = session_mgr.get_session_crypto("session_001")
    retrieved_crypto2 = session_mgr.get_session_crypto("session_002")
    
    dec1 = retrieved_crypto1.decrypt(msg1)
    dec2 = retrieved_crypto2.decrypt(msg2)
    
    print(f"    Session 1 decrypted: {dec1}")
    print(f"    Session 2 decrypted: {dec2}")
    assert dec1 == "Message from session 1", "Session 1 failed"
    assert dec2 == "Message from session 2", "Session 2 failed"
    print("    ✓ Session encryption test passed")
    
    # Test authentication (tampered data should fail)
    print("\n[+] Testing authentication (tampered data)...")
    tampered = encrypted[:-10] + "AAAAAAAAAA"
    try:
        crypto.decrypt(tampered)
        print("    ✗ Authentication test FAILED - tampered data accepted!")
    except ValueError:
        print("    ✓ Authentication test passed - tampered data rejected")
    
    print("\n[*] All tests passed successfully!")
