from presidio_analyzer import PatternRecognizer, Pattern


class PatientIdRecognizer(PatternRecognizer):
    COUNTRY_CODE = "us"

    def __init__(self):
        super().__init__(
            supported_entity="PATIENT_ID",
            context=["patient", "mrn", "medical record", "MRN"],
            patterns=[
                Pattern(
                    "strict_patient_id",
                    r"Patient\s+ID:\s*[A-Z0-9\-]{4,12}",
                    0.85,
                ),
                Pattern(
                    "strict_mrn",
                    r"MRN:\s*[A-Z0-9\-]{4,12}",
                    0.75,
                ),
                Pattern(
                    "fallback_medical_record",
                    r"Medical\s+Record\s*#?:?\s*[A-Z0-9\-]{4,12}",
                    0.65,
                ),
            ],
        )


class InsuranceIdRecognizer(PatternRecognizer):
    COUNTRY_CODE = "us"

    def __init__(self):
        super().__init__(
            supported_entity="INSURANCE_ID",
            context=["insurance", "member", "policy"],
            patterns=[
                Pattern(
                    "strict_insurance_id",
                    r"Insurance\s+ID:\s*[A-Z0-9\-]{4,12}",
                    0.85,
                ),
                Pattern(
                    "fallback_policy_number",
                    r"Policy\s*#?:?\s*[A-Z0-9\-]{4,12}",
                    0.65,
                ),
            ],
        )


class PharmacyIdRecognizer(PatternRecognizer):
    COUNTRY_CODE = "us"

    def __init__(self):
        super().__init__(
            supported_entity="PHARMACY_ID",
            context=["pharmacy", "drug", "rx", "prescription"],
            patterns=[
                Pattern(
                    "strict_pharmacy_id",
                    r"Rx\s*#?:?\s*\d{4,10}",
                    0.85,
                ),
                Pattern(
                    "fallback_prescription_number",
                    r"Pharmacy\s+ID:\s*[A-Z0-9\-]{4,12}",
                    0.65,
                ),
            ],
        )


class CustomMedicalLicenseRecognizer(PatternRecognizer):
    COUNTRY_CODE = "us"

    def __init__(self):
        super().__init__(
            supported_entity="MEDICAL_LICENSE",
            context=["medical", "license", "dea", "physician", "medical license"],
            patterns=[
                Pattern(
                    "strict_medical_license",
                    r"DEA\s*#?:?\s*[A-Z]{2}\d{7}",
                    0.85,
                ),
                Pattern(
                    "fallback_medical_license",
                    r"Medical\s+License:\s*[A-Z0-9\-]{4,12}",
                    0.65,
                ),
            ],
        )
