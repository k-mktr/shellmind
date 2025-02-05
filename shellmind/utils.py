"""
Utility functions for ShellMind
"""
import os
import platform
import re
from typing import Optional

def get_os_type() -> str:
    """Detect Linux distribution"""
    try:
        with open('/etc/os-release') as f:
            content = f.read()
            if 'fedora' in content.lower():
                return 'Fedora'
            if 'debian' in content.lower() or 'ubuntu' in content.lower():
                return 'Debian'
    except FileNotFoundError:
        pass
    return 'Linux'  # Fallback

def is_destructive_command(command: str) -> bool:
    """Check for potentially dangerous commands (deprecated, now handled by AI)."""
    return False  # Safety checks are now handled by the AI prompt

def validate_api_key() -> bool:
    """Check if API key is present when needed"""
    # Now handled in CLI with more context
    return True  # Modified logic moved to CLI
