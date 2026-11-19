from typing import Dict, Any, List

class JurisdictionPolicyEngine:
    """
    Policy-as-Code engine validating cross-border import/export controls,
    EAR dual-use restrictions, IATA hazmat transport rules, and licensing.
    """

    DUAL_USE_RESTRICTED_DESTINATIONS = {"RU", "BY", "CN", "VE", "MM"}

    @classmethod
    def evaluate_regulations(
        cls,
        product_category: str,
        eccn_code: str,
        destination_country: str,
        shipping_mode: str,
        has_export_license: bool = False
    ) -> Dict[str, Any]:
        cat = product_category.upper()
        dest = destination_country.upper()
        mode = shipping_mode.upper()

        policy_violations: List[str] = []
        mandatory_requirements: List[str] = []

        # Rule 1: Export Administration Regulations (EAR) Dual-Use Check
        if eccn_code == "3A090_DUAL_USE" and dest in cls.DUAL_USE_RESTRICTED_DESTINATIONS:
            if not has_export_license:
                policy_violations.append(
                    f"EXPORT_CONTROL_BLOCK (ECCN 3A090): Dual-Use AI Semiconductors restricted to '{dest}' without BIS Export License."
                )

        # Rule 2: IATA Dangerous Goods / Hazmat Transport Check
        if cat == "LITHIUM_BATTERY_PACK" and mode == "AIR_EXPRESS":
            policy_violations.append(
                "IATA_HAZMAT_CLASS9_VIOLATION: Standalone high-capacity Lithium-Ion packs prohibited on AIR_EXPRESS; require SEA_FREIGHT or CARGO_FREIGHTER."
            )

        # Rule 3: Pharmaceutical Cold-Chain Compliance Check
        if cat == "COLD_CHAIN_PHARMA":
            mandatory_requirements.append("WHO_GDP_IOT_COLD_CHAIN_TELEMETRY_REQUIRED (2C-8C)")
            mandatory_requirements.append("CERTIFICATE_OF_ORIGIN_AND_BATCH_PROVENANCE")

        return {
            "jurisdiction_compliant": len(policy_violations) == 0,
            "policy_violations": policy_violations,
            "mandatory_handling_controls": mandatory_requirements
        }
