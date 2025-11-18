"""
Configuration Management for Web RPA

Handles configuration settings for web automation experiments.
"""

import os
from dataclasses import dataclass
from typing import Optional
from pathlib import Path


@dataclass
class RPAConfig:
    """Configuration for RPA experiments"""

    # Browser settings
    headless: bool = False
    browser_type: str = "chrome"  # chrome, firefox, edge
    window_width: int = 1920
    window_height: int = 1080

    # Timeout settings (seconds)
    page_load_timeout: int = 30
    implicit_wait: int = 10
    explicit_wait: int = 15

    # Retry settings
    max_retries: int = 3
    retry_delay: int = 2

    # Screenshot settings
    screenshot_on_error: bool = True
    screenshot_dir: str = "web_rpa/screenshots"

    # Logging settings
    log_level: str = "INFO"
    log_file: Optional[str] = "web_rpa/logs/rpa.log"

    # Security settings
    enable_credentials_encryption: bool = True
    credentials_file: str = ".env"

    # Rate limiting
    min_action_delay: float = 0.5  # Minimum delay between actions
    max_action_delay: float = 2.0  # Maximum delay between actions

    def __post_init__(self):
        """Create necessary directories"""
        Path(self.screenshot_dir).mkdir(parents=True, exist_ok=True)
        if self.log_file:
            Path(self.log_file).parent.mkdir(parents=True, exist_ok=True)


class CredentialsManager:
    """
    Secure credentials management

    WARNING: In production, use proper secret management solutions
    like AWS Secrets Manager, HashiCorp Vault, or encrypted key stores.

    For experiments, use environment variables or .env files (git-ignored).
    """

    def __init__(self, credentials_file: str = ".env"):
        self.credentials_file = credentials_file
        self._credentials = {}
        self._load_from_env()

    def _load_from_env(self):
        """Load credentials from environment variables"""
        # Example: Load from environment
        self._credentials = {
            "username": os.getenv("BOATRACE_USERNAME", ""),
            "password": os.getenv("BOATRACE_PASSWORD", ""),
            "pin": os.getenv("BOATRACE_PIN", ""),
        }

    def get_credential(self, key: str) -> str:
        """
        Get credential by key

        Args:
            key: Credential key (username, password, etc.)

        Returns:
            Credential value (empty string if not found)
        """
        return self._credentials.get(key, "")

    def has_credentials(self) -> bool:
        """Check if all required credentials are available"""
        required = ["username", "password"]
        return all(self._credentials.get(key) for key in required)

    def clear_credentials(self):
        """Clear credentials from memory"""
        self._credentials.clear()


# Global configuration instance
default_config = RPAConfig()
