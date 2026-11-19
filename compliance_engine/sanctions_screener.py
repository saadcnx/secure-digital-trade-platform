import json
from pathlib import Path
from typing import Dict, Any, List
from rapidfuzz import fuzz

BASE_DIR = Path(__file__).resolve().parent
SANCTIONS_PATH = BASE_DIR / "data" / "sanctions_list.json"

class SanctionsScreener:
    """
    Screens buyers, sellers, and destination countries against OFAC, UN, EU, and BIS
    Denied Party Lists using fuzzy phonetic/typographical string matching.
    """

    def __init__(self, match_threshold: float = 84.0):
        with open(SANCTIONS_PATH, "r", encoding="utf-8") as f:
            self.data = json.load(f)
        self.threshold = match_threshold

    def screen_party_and_route(
        self,
        buyer_name: str,
        origin_country: str,
        destination_country: str
    ) -> Dict[str, Any]:
        violations: List[str] = []
        matched_entities: List[Dict[str, Any]] = []
        highest_score = 0.0

        orig = origin_country.upper()
        dest = destination_country.upper()
        embargoed = self.data["embargoed_countries"]

        # 1. Check Country-Level Embargoes
        if orig in embargoed:
            violations.append(f"EMBARGOED_ORIGIN_COUNTRY: {orig} - {embargoed[orig]}")
        if dest in embargoed:
            violations.append(f"EMBARGOED_DESTINATION_COUNTRY: {dest} - {embargoed[dest]}")

        # 2. Fuzzy Match Buyer/Consignee Name against Denied Party Lists + Aliases
        clean_buyer = buyer_name.strip().lower()
        for party in self.data["denied_parties"]:
            candidate_names = [party["name"]] + party.get("aliases", [])
            best_party_score = 0.0

            for candidate in candidate_names:
                score = max(
                    fuzz.WRatio(clean_buyer, candidate.lower()),
                    fuzz.token_sort_ratio(clean_buyer, candidate.lower())
                )
                if score > best_party_score:
                    best_party_score = score

            if best_party_score > highest_score:
                highest_score = round(best_party_score, 2)

            if best_party_score >= self.threshold:
                matched_entities.append({
                    "entity_id": party["entity_id"],
                    "listed_name": party["name"],
                    "list_source": party["list_source"],
                    "category": party["category"],
                    "similarity_score_pct": round(best_party_score, 2)
                })
                violations.append(
                    f"DENIED_PARTY_MATCH ({round(best_party_score, 1)}%): '{buyer_name}' matched '{party['name']}' [{party['list_source']}]"
                )

        is_sanctioned = len(violations) > 0
        return {
            "sanctions_passed": not is_sanctioned,
            "highest_fuzzy_match_pct": highest_score,
            "matched_denied_parties": matched_entities,
            "sanctions_violations": violations
        }
