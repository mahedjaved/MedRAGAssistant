"""Persona: PII Detector"""

"""This module is responsible for detecting Personally Identifiable Information (PII) in text using the Presidio Analyzer and spaCy library. It provides functionality to identify sensitive information such as names, addresses, phone numbers, and other PII entities in the input text.
The module initializes the Presidio Analyzer and spaCy NLP model, and defines a function `detect"""


import re
import hashlib

from fastapi import HTTPException
from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_analyzer import RecognizerResult
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from .pii_recognizers import (
    PatientIdRecognizer,
    InsuranceIdRecognizer,
    PharmacyIdRecognizer,
    CustomMedicalLicenseRecognizer,
)
from ..config import settings
from ..logger import logger
from ..modules.db_logger import log_pii_redaction
import spacy

# load the spACy model for English language
nlp = spacy.load("en_core_web_md")

# set registry
registry = RecognizerRegistry(
    global_regex_flags=(re.DOTALL | re.MULTILINE | re.IGNORECASE)
)

# load the predefined recognizers and add custom recognizers to the registry
registry.load_predefined_recognizers()
registry.add_recognizer(PatientIdRecognizer())
registry.add_recognizer(InsuranceIdRecognizer())
registry.add_recognizer(PharmacyIdRecognizer())
registry.add_recognizer(CustomMedicalLicenseRecognizer())

# instantiate analyzer engine and pass the registry
analyzer = AnalyzerEngine(registry=registry)

# instantiate anonymizer engine
anonymizer = AnonymizerEngine()

CUSTOM_ENTITIES = ["PATIENT_ID", "INSURANCE_ID", "PHARMACY_ID", "MEDICAL_LICENSE"]


# function to detect and redact PII in the input text
async def detect_and_redact(text: str) -> str:
    """
    Detects and redacts Personally Identifiable Information (PII) in the input text.

    Args:
        text (str): The input text to analyze for PII.

    Returns:
        str: The redacted text with PII replaced according to settings.
    """
    # guard for enabled detection and redaction settings
    if not settings.pii_detection_enabled:
        logger.info("PII detection is disabled. Returning original text.")
        return text

    # analyze the text for PII entities
    results = analyzer.analyze(
        text=text,
        entities=CUSTOM_ENTITIES,
        language="en",
    )

    # pii_strict_mode — raise 422 if PII found
    if results and settings.pii_strict_mode:
        raise HTTPException(
            status_code=422,
            detail="Please remove personal information from your query.",
        )

    # log the detected PII entities
    logger.info(f"Detected PII entities: {results}")

    # if no PII found, return original text
    if not results:
        return text

    # build operators dict based on pii_redaction_mode
    if settings.pii_redaction_mode == "mask":
        operators = {
            entity: OperatorConfig(
                "mask",
                {"masking_char": "*", "chars_to_mask": 3, "from_end": False},
            )
            for entity in CUSTOM_ENTITIES
        }
    else:
        operators = {
            entity: OperatorConfig("replace", {"new_value": "[REDACTED]"})
            for entity in CUSTOM_ENTITIES
        }

    # redact the detected PII entities in the text
    redacted_text = anonymizer.anonymize(
        text=text,
        analyzer_results=results,
        operators=operators,
    )

    # log redactions if enabled
    if settings.pii_log_redactions:
        query_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
        for result in results:
            original_snippet = text[result.start : result.end]
            redacted_snippet = redacted_text.text[result.start : result.end]
            try:
                await log_pii_redaction(
                    query_hash=query_hash,
                    entity_type=result.entity_type,
                    original_snippet=original_snippet,
                    redacted_snippet=redacted_snippet,
                )
            except Exception as e:
                logger.exception(f"Failed to log PII redaction: {e}")

    return redacted_text.text
