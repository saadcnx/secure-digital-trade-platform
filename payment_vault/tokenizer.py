import base64
import os
import secrets
import sqlite3
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "secure_vault.db"

# Demo-only test PAN. Do not use real payment-card data in this project.
DEMO_TEST_PAN = "4242424242424242"


class TokenizationError(ValueError):
    """Raised when demo card input or vault configuration is invalid."""


def _load_aes_key() -> bytes:
    load_dotenv()

    encoded_key = os.getenv("PAYMENT_AES_KEY_B64")
    if not encoded_key:
        raise RuntimeError("PAYMENT_AES_KEY_B64 is missing from .env")

    try:
        key = base64.b64decode(encoded_key, validate=True)
    except Exception as exc:
        raise RuntimeError("PAYMENT_AES_KEY_B64 is not valid Base64") from exc

    if len(key) != 32:
        raise RuntimeError("AES-256 requires a key of exactly 32 bytes")

    return key


def _normalise_pan(pan: str) -> str:
    """Remove spaces/hyphens. This demo accepts only the published test PAN."""
    normalised = pan.replace(" ", "").replace("-", "")

    if not normalised.isdigit():
        raise TokenizationError("Card number must contain digits only.")

    if normalised != DEMO_TEST_PAN:
        raise TokenizationError(
            "Demo accepts only test PAN 4242424242424242. "
            "Do not submit a real card number."
        )

    return normalised


def _mask_pan(pan: str) -> str:
    return f"**** **** **** {pan[-4:]}"


def _get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS payment_tokens (
            token TEXT PRIMARY KEY,
            last4 TEXT NOT NULL,
            card_brand TEXT NOT NULL,
            nonce BLOB NOT NULL,
            encrypted_pan BLOB NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    connection.commit()

    # Restrict the local demo database to the current OS user.
    try:
        os.chmod(DB_PATH, 0o600)
    except OSError:
        pass

    return connection


class PaymentTokenizer:
    def __init__(self) -> None:
        self._aes = AESGCM(_load_aes_key())

    def tokenize(self, card_number: str) -> dict[str, Any]:
        pan = _normalise_pan(card_number)

        # Opaque random reference; it does not reveal the PAN.
        token = "tok_demo_" + secrets.token_urlsafe(24)
        nonce = os.urandom(12)

        # Bind the ciphertext to this token, so moving ciphertext to another
        # token record will fail AES-GCM authentication.
        aad = token.encode("utf-8")
        encrypted_pan = self._aes.encrypt(
            nonce,
            pan.encode("utf-8"),
            aad,
        )

        connection = _get_connection()
        try:
            connection.execute(
                """
                INSERT INTO payment_tokens
                    (token, last4, card_brand, nonce, encrypted_pan)
                VALUES (?, ?, ?, ?, ?)
                """,
                (token, pan[-4:], "VISA_TEST", nonce, encrypted_pan),
            )
            connection.commit()
        finally:
            connection.close()

        return {
            "payment_token": token,
            "masked_card": _mask_pan(pan),
            "card_brand": "VISA_TEST",
            "storage": "PAN encrypted with AES-256-GCM in local demo vault",
        }
