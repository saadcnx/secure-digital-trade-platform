from typing import Any

from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig


class PIIProtectionService:
    """Detects and redacts PII in English text for this educational demo."""

    def __init__(self) -> None:
        configuration = {
            "nlp_engine_name": "spacy",
            "models": [
                {
                    "lang_code": "en",
                    "model_name": "en_core_web_sm",
                }
            ],
        }

        provider = NlpEngineProvider(nlp_configuration=configuration)
        nlp_engine = provider.create_engine()

        self.analyzer = AnalyzerEngine(
            nlp_engine=nlp_engine,
            supported_languages=["en"],
        )
        self.anonymizer = AnonymizerEngine()

    def redact_text(self, text: str) -> dict[str, Any]:
        results = self.analyzer.analyze(
            text=text,
            language="en",
        )

        operators = {
            "PERSON": OperatorConfig("replace", {"new_value": "<PERSON>"}),
            "EMAIL_ADDRESS": OperatorConfig(
                "replace", {"new_value": "<EMAIL>"
            }),
            "PHONE_NUMBER": OperatorConfig(
                "replace", {"new_value": "<PHONE>"
            }),
            "LOCATION": OperatorConfig(
                "replace", {"new_value": "<LOCATION>"
            }),
            "default": OperatorConfig(
                "replace", {"new_value": "<PII>"
            }),
        }

        anonymized = self.anonymizer.anonymize(
            text=text,
            analyzer_results=results,
            operators=operators,
        )

        # Return entity types and count only—not the detected source text.
        entity_types = sorted({item.entity_type for item in results})

        return {
            "redacted_text": anonymized.text,
            "detected_entity_types": entity_types,
            "detection_count": len(results),
        }

    @staticmethod
    def redact_structured_customer_fields(
        customer: dict[str, str],
    ) -> dict[str, str]:
        """
        Structured PII is replaced by field type, regardless of whether
        automated detection recognizes the value.
        """
        return {
            "customer_name": "<PERSON>",
            "email": "<EMAIL>",
            "phone": "<PHONE>",
            "address": "<ADDRESS>",
        }
