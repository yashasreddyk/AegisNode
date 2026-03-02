"""
Agent Identity Module for Proof of Action (PoA)
Handles Ed25519 key generation and signing.
"""
import base58
from nacl.signing import SigningKey, VerifyKey
from nacl.encoding import RawEncoder

# The multicodec prefix for ed25519-pub is 0xed01. 
# In varint encoding this is [0xed, 0x01]
ED25519_MULTICODEC = b'\xed\x01'

class AgentIdentity:
    """
    Handles Ed25519 keypair generation and DID creation for an AI Agent.
    """
    def __init__(self, private_key: bytes | None = None):
        """
        Initializes the agent identity. Generates a new keypair if no private key is provided.
        """
        if private_key:
            self._signing_key = SigningKey(private_key, encoder=RawEncoder)
        else:
            self._signing_key = SigningKey.generate()
            
        self._verify_key = self._signing_key.verify_key
        
        # Generate the did:key
        pub_bytes = self._verify_key.encode(encoder=RawEncoder)
        multicodec_bytes = ED25519_MULTICODEC + pub_bytes
        encoded_did = base58.b58encode(multicodec_bytes).decode('utf-8')
        
        self.did = f"did:key:z{encoded_did}"

    @property
    def public_key_bytes(self) -> bytes:
        return self._verify_key.encode(encoder=RawEncoder)

    def sign(self, message: bytes) -> bytes:
        """
        Signs a message using the agent's private key.
        
        Args:
            message: The raw bytes to sign.
            
        Returns:
            The signature as raw bytes.
        """
        signed = self._signing_key.sign(message)
        return signed.signature

    def verify(self, message: bytes, signature: bytes) -> bool:
        """
        Verifies a signature using the agent's public key.
        """
        try:
            self._verify_key.verify(message, signature)
            return True
        except Exception:
            return False

    @classmethod
    def verify_signature(cls, did: str, message: bytes, signature: bytes) -> bool:
        """
        Verifies a signature given a DID.
        """
        if not did.startswith("did:key:z"):
            raise ValueError("Invalid DID format. Must start with 'did:key:z'")
            
        encoded = did[9:]
        decoded = base58.b58decode(encoded)
        
        if not decoded.startswith(ED25519_MULTICODEC):
            raise ValueError("Invalid multicodec prefix for Ed25519")
            
        pub_bytes = decoded[len(ED25519_MULTICODEC):]
        verify_key = VerifyKey(pub_bytes, encoder=RawEncoder)
        
        try:
            verify_key.verify(message, signature)
            return True
        except Exception:
            return False
