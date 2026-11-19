import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

BASE_DIR = Path(__file__).resolve().parent
DOCS_DIR = BASE_DIR / "customs_docs"

class CustomsDocumentGenerator:
    """
    Generates WCO Data Model v3.10 compliant Electronic Customs Declarations (CN23 / SAD)
    and Commercial Invoices with SHA-256 tamper-evident integrity hashes.
    """

    @staticmethod
    def issue_customs_declaration(
        order_id: str,
        buyer_name: str,
        origin_country: str,
        destination_country: str,
        shipping_mode: str,
        tariff_summary: Dict[str, Any],
        handling_controls: list
    ) -> Dict[str, Any]:
        DOCS_DIR.mkdir(parents=True, exist_ok=True)
        issued_at = datetime.now(timezone.utc).isoformat()

        declaration_payload = {
            "document_standard": "WCO_DATA_MODEL_V3_CN23_COMMERCIAL_INVOICE",
            "declaration_id": f"CUS-{order_id}",
            "issued_timestamp_utc": issued_at,
            "exporter_of_record": {
                "legal_name": "GlobalSecure Digital Marketplace Ltd.",
                "origin_country_iso": origin_country.upper(),
                "incoterms_2020": "DDP (Delivered Duty Paid)"
            },
            "consignee_importer": {
                "recipient_name": buyer_name,
                "destination_country_iso": destination_country.upper()
            },
            "transport_mode": shipping_mode.upper(),
            "commodity_and_tariff_assessment": tariff_summary,
            "regulatory_handling_directives": handling_controls,
            "clearance_channel": "GREEN_LANE_PRE_CLEARED"
        }

        # Compute SHA-256 Digital Integrity Hash for Customs & Blockchain Anchoring
        canonical_json = json.dumps(declaration_payload, sort_keys=True).encode("utf-8")
        doc_sha256 = hashlib.sha256(canonical_json).hexdigest()
        declaration_payload["document_sha256_hash"] = doc_sha256

        file_path = DOCS_DIR / f"CN23_{order_id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(declaration_payload, f, indent=2)

        return {
            "declaration_id": declaration_payload["declaration_id"],
            "clearance_channel": "GREEN_LANE_PRE_CLEARED",
            "document_sha256_hash": doc_sha256,
            "saved_artifact_path": str(file_path.relative_to(BASE_DIR.parent))
        }
