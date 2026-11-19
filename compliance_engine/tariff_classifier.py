import json
from pathlib import Path
from typing import Dict, Any

BASE_DIR = Path(__file__).resolve().parent
TARIFF_PATH = BASE_DIR / "data" / "hs_tariffs.json"

class TariffClassifier:
    """
    Classifies products under WCO Harmonized System (HS) codes and computes
    landed cross-border customs duties, de-minimis exemptions, and VAT/GST.
    """

    def __init__(self):
        with open(TARIFF_PATH, "r", encoding="utf-8") as f:
            self.catalog = json.load(f)

    def calculate_landed_cost(
        self,
        product_category: str,
        declared_value_usd: float,
        destination_country: str
    ) -> Dict[str, Any]:
        cat_key = product_category.upper()
        products = self.catalog["product_categories"]
        item = products.get(cat_key, {
            "hs_code": "9999.00",
            "description": "General Unclassified Merchandise",
            "base_duty_rate": 0.10,
            "export_control_eccn": "EAR99"
        })

        dest = destination_country.upper()
        tax_profile = self.catalog["country_tax_profiles"].get(
            dest, self.catalog["country_tax_profiles"]["DEFAULT"]
        )

        # Apply De-Minimis Customs Duty Exemption Rule
        de_minimis = tax_profile["de_minimis_usd"]
        duty_exempt = declared_value_usd <= de_minimis
        applied_duty_rate = 0.0 if duty_exempt else item["base_duty_rate"]

        customs_duty_usd = round(declared_value_usd * applied_duty_rate, 2)
        taxable_cif_base = declared_value_usd + customs_duty_usd
        import_vat_usd = round(taxable_cif_base * tax_profile["vat_gst_rate"], 2)
        total_landed_cost_usd = round(declared_value_usd + customs_duty_usd + import_vat_usd, 2)

        return {
            "wco_hs_code": item["hs_code"],
            "hs_description": item["description"],
            "export_control_eccn": item["export_control_eccn"],
            "declared_value_usd": round(declared_value_usd, 2),
            "de_minimis_threshold_usd": de_minimis,
            "de_minimis_duty_exempt": duty_exempt,
            "applied_duty_rate_pct": round(applied_duty_rate * 100, 2),
            "customs_duty_usd": customs_duty_usd,
            "destination_vat_rate_pct": round(tax_profile["vat_gst_rate"] * 100, 2),
            "import_vat_usd": import_vat_usd,
            "total_landed_cost_usd": total_landed_cost_usd
        }
