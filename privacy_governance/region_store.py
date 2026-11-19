import json
import sqlite3
import uuid
from pathlib import Path
from typing import Any

from privacy_governance.pii_protection import PIIProtectionService


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
GLOBAL_DB = DATA_DIR / "global_analytics.sqlite"

EU_COUNTRIES = {
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR",
    "DE", "GR", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL",
    "PL", "PT", "RO", "SK", "SI", "ES", "SE",
}

APAC_COUNTRIES = {
    "AU", "BD", "CN", "HK", "ID", "IN", "JP", "KR", "LK",
    "MY", "NZ", "PH", "PK", "SG", "TH", "VN",
}

REGION_DATABASES = {
    "EU_SIMULATED": DATA_DIR / "region_eu.sqlite",
    "US_SIMULATED": DATA_DIR / "region_us.sqlite",
    "APAC_SIMULATED": DATA_DIR / "region_apac.sqlite",
}


class RegionRoutingError(ValueError):
    pass


def route_country(country_code: str) -> str:
    country = country_code.strip().upper()

    if country in EU_COUNTRIES:
        return "EU_SIMULATED"
    if country == "US":
        return "US_SIMULATED"
    if country in APAC_COUNTRIES:
        return "APAC_SIMULATED"

    raise RegionRoutingError(
        f"Country code {country!r} has no configured demo region."
    )


class RegionalPrivacyStore:
    def __init__(self, pii_service: PIIProtectionService) -> None:
        self.pii_service = pii_service
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def _connect(self, region: str) -> sqlite3.Connection:
        database_path = REGION_DATABASES[region]

        connection = sqlite3.connect(database_path)
        connection.row_factory = sqlite3.Row

        # Improve deletion behavior for this local demonstration.
        connection.execute("PRAGMA secure_delete = ON")

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS customer_records (
                user_id TEXT PRIMARY KEY,
                subject_ref TEXT NOT NULL UNIQUE,
                country_code TEXT NOT NULL,
                customer_payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # Global analytics DB is attached so the demo can write/delete both
        # records within a single SQLite connection.
        connection.execute("ATTACH DATABASE ? AS global_db", (str(GLOBAL_DB),))
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS global_db.analytics_records (
                subject_ref TEXT PRIMARY KEY,
                region TEXT NOT NULL,
                analytics_payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        try:
            database_path.chmod(0o600)
        except OSError:
            pass

        try:
            GLOBAL_DB.chmod(0o600)
        except OSError:
            pass

        return connection

    @staticmethod
    def _amount_band(amount_usd: float) -> str:
        if amount_usd < 50:
            return "UNDER_50"
        if amount_usd < 250:
            return "50_TO_249"
        if amount_usd < 1000:
            return "250_TO_999"
        return "1000_OR_MORE"

    def save_customer_order(self, payload: dict[str, Any]) -> dict[str, Any]:
        region = route_country(payload["country_code"])
        country_code = payload["country_code"].strip().upper()
        user_id = payload["user_id"].strip()

        pii_fields = {
            "customer_name": payload["customer_name"],
            "email": payload["email"],
            "phone": payload["phone"],
            "address": payload["address"],
        }

        notes_result = self.pii_service.redact_text(payload.get("notes", ""))

        # This simulated regional record contains raw demo PII.
        regional_payload = {
            **pii_fields,
            "notes": payload.get("notes", ""),
        }

        # Analytics gets no user_id, name, email, phone, address, or order ID.
        analytics_payload = {
            "destination_country": country_code,
            "amount_band": self._amount_band(float(payload["amount_usd"])),
            "notes_redacted": notes_result["redacted_text"],
            "pii_entity_types_detected_in_notes":
                notes_result["detected_entity_types"],
        }

        connection = self._connect(region)
        try:
            with connection:
                row = connection.execute(
                    "SELECT subject_ref FROM customer_records WHERE user_id = ?",
                    (user_id,),
                ).fetchone()

                subject_ref = (
                    row["subject_ref"] if row else f"subj_{uuid.uuid4().hex}"
                )

                connection.execute(
                    """
                    INSERT INTO customer_records
                        (user_id, subject_ref, country_code, customer_payload_json)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(user_id) DO UPDATE SET
                        country_code = excluded.country_code,
                        customer_payload_json = excluded.customer_payload_json
                    """,
                    (
                        user_id,
                        subject_ref,
                        country_code,
                        json.dumps(regional_payload, ensure_ascii=False),
                    ),
                )

                connection.execute(
                    """
                    INSERT INTO global_db.analytics_records
                        (subject_ref, region, analytics_payload_json)
                    VALUES (?, ?, ?)
                    ON CONFLICT(subject_ref) DO UPDATE SET
                        region = excluded.region,
                        analytics_payload_json = excluded.analytics_payload_json
                    """,
                    (
                        subject_ref,
                        region,
                        json.dumps(analytics_payload, ensure_ascii=False),
                    ),
                )
        finally:
            connection.close()

        return {
            "result": "stored",
            "region_route": region,
            "analytics_pii_handling": "structured PII removed; notes redacted",
            "presidio_detected_entity_types":
                notes_result["detected_entity_types"],
            "analytics_data": analytics_payload,
            "notice": (
                "Regional databases are local educational simulations, "
                "not actual geographic data-residency controls."
            ),
        }

    def erase_customer(self, user_id: str, country_code: str) -> dict[str, Any]:
        region = route_country(country_code)
        request_id = f"erase_{uuid.uuid4().hex}"
        database_path = REGION_DATABASES[region]

        connection = self._connect(region)
        regional_deleted = 0
        analytics_deleted = 0

        try:
            with connection:
                row = connection.execute(
                    "SELECT subject_ref FROM customer_records WHERE user_id = ?",
                    (user_id.strip(),),
                ).fetchone()

                if row is None:
                    raise KeyError("Customer record was not found in routed region.")

                subject_ref = row["subject_ref"]

                result = connection.execute(
                    "DELETE FROM customer_records WHERE user_id = ?",
                    (user_id.strip(),),
                )
                regional_deleted = result.rowcount

                result = connection.execute(
                    "DELETE FROM global_db.analytics_records WHERE subject_ref = ?",
                    (subject_ref,),
                )
                analytics_deleted = result.rowcount
        finally:
            connection.close()

        # The audit record intentionally excludes user_id, name, email,
        # address, subject_ref, and request body.
        audit_record = {
            "request_id": request_id,
            "action": "ERASURE_REQUEST_PROCESSED",
            "region_route": region,
            "regional_records_deleted": regional_deleted,
            "analytics_records_deleted": analytics_deleted,
        }

        audit_path = DATA_DIR / "privacy_audit.jsonl"
        with audit_path.open("a", encoding="utf-8") as audit_file:
            audit_file.write(json.dumps(audit_record) + "\n")

        try:
            audit_path.chmod(0o600)
            database_path.chmod(0o600)
            GLOBAL_DB.chmod(0o600)
        except OSError:
            pass

        return {
            **audit_record,
            "notice": (
                "Local demo deletion completed. Production deletion may also "
                "need to address backups, caches, replicas, and legal retention."
            ),
        }
