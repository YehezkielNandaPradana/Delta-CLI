import hashlib
import os
import secrets
import sys
from typing import Optional

from delta.core.config import DeltaConfig


def hash_password(password: str, salt: str) -> str:
    return hashlib.sha256(f"{salt}:{password}".encode("utf-8")).hexdigest()


def generate_salt() -> str:
    return secrets.token_hex(16)


def set_credentials(config: DeltaConfig, username: str, password: str) -> None:
    salt = generate_salt()
    config.auth_username = username
    config.auth_password_salt = salt
    config.auth_password_hash = hash_password(password, salt)
    config.auth_enabled = True
    config.save()


def verify_credentials(config: DeltaConfig, username: str, password: str) -> bool:
    if not config.auth_username or not config.auth_password_hash:
        return False
    if username != config.auth_username:
        return False
    expected = config.auth_password_hash
    actual = hash_password(password, config.auth_password_salt)
    return secrets.compare_digest(expected, actual)


def _read_secret(prompt: str) -> str:
    import getpass
    return getpass.getpass(prompt)


def login_required(config: DeltaConfig, max_attempts: int = 3) -> bool:
    """Prompt for username/password. Returns True if authenticated."""
    if not config.auth_enabled or not config.auth_username:
        return True

    import getpass

    print()
    print("=" * 52)
    print("   Delta Secure Access")
    print("   Only the owner may use Delta")
    print("=" * 52)

    attempts = 0
    while attempts < max_attempts:
        username = input("  Username: ").strip()
        password = getpass.getpass("  Password: ")

        if verify_credentials(config, username, password):
            print("  Access granted.")
            print("=" * 52)
            print()
            return True

        attempts += 1
        remaining = max_attempts - attempts
        if remaining > 0:
            print(f"  Access denied. {remaining} attempt(s) remaining.")
        else:
            print("  Access denied. Too many failed attempts.")
    print("=" * 52)
    return False
