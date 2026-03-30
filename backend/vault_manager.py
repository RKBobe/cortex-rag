"""
CoreTexAI Secret Vault Manager
Proprietary product of Treelight Innovations.
Responsible for encrypted storage of enterprise credentials.
"""
import os
from pathlib import Path
from cryptography.fernet import Fernet
from core_config import settings

class SecretVault:
    """
    Manages the encryption and decryption of CoreTexAI gateway secrets.
    Ensures Treelight Innovations credentials are never stored in plain text.
    """
    def __init__(self):
        # Data root is 'vault' folder in core_config
        self.vault_dir = Path(settings.DATA_ROOT) 
        self.key_file = self.vault_dir / "master.key"
        self.secret_file = self.vault_dir / "secrets.crypt"
        
        self.vault_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_master_key()
        self.fernet = Fernet(self._get_master_key())

    def _ensure_master_key(self):
        """Generates a master key if one does not exist."""
        if not self.key_file.exists():
            key = Fernet.generate_key()
            with open(self.key_file, "wb") as f:
                f.write(key)

    def _get_master_key(self):
        with open(self.key_file, "rb") as f:
            return f.read()

    def store_secret(self, plain_text: str):
        """Encrypts and stores a plain text secret."""
        encrypted = self.fernet.encrypt(plain_text.encode())
        with open(self.secret_file, "wb") as f:
            f.write(encrypted)

    def retrieve_secret(self) -> str:
        """Decrypts and returns the stored secret."""
        if not self.secret_file.exists():
            # If no vault file, initialize with the config default
            self.store_secret(settings.CORETEX_API_KEY)
            return settings.CORETEX_API_KEY
        
        with open(self.secret_file, "rb") as f:
            encrypted = f.read()
        return self.fernet.decrypt(encrypted).decode()

# Initialize the vault singleton
vault = SecretVault()
